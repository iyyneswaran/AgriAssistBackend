import { Router, Request, Response, urlencoded } from 'express';
import rateLimit from 'express-rate-limit';
import { verifyAccessToken } from '../valid/jwt';
import authorizeRole from '../valid/role';
import { ownPhone, publicVoiceUrl, validTwilioSignature, verifyTwilioWebhook } from './security';
import twilio from 'twilio';
import { WebSocketServer, WebSocket } from 'ws';
import { Server as HttpServer, IncomingMessage } from 'http';
import { connectToElevenLabs } from './llm';
import smsRouter from './sms';
import addressSmsRouter from './addressSms';
import networkFallbackRouter from './networkFallback';

// ─────────────────────────────────────────────
// Voice Agent Routes
// All endpoints are mounted under /api/voice-agent
// ─────────────────────────────────────────────

const voiceAgentRouter = Router();

const providerPaths = new Set(['/sms-inbound', '/voice', '/incoming-call', '/fallback-voice-twiml']);
const routePath = (req: Request) => req.path.toLowerCase().replace(/\/+$/, '') || '/';
voiceAgentRouter.use(urlencoded({ extended: false, limit: '32kb' }));
voiceAgentRouter.use((req, res, next) => {
    if (req.method === 'GET' && routePath(req) === '/health') return next();
    if (providerPaths.has(routePath(req))) return verifyTwilioWebhook(req, res, next);
    return verifyAccessToken(req, res, next);
});
const voiceLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, limit: 5,
    keyGenerator: req => req.user!.id,
});
voiceAgentRouter.use((req, res, next) => {
    if (providerPaths.has(routePath(req)) || routePath(req) === '/health') return next();
    return voiceLimiter(req, res, next);
});
voiceAgentRouter.use(['/sms-outbound', '/request-address'], authorizeRole('ADMIN'));
voiceAgentRouter.use(['/make-call', '/network-fallback', '/stored-address'], ownPhone);

// Mount sub-routers
voiceAgentRouter.use('/', smsRouter);
voiceAgentRouter.use('/', addressSmsRouter);
voiceAgentRouter.use('/', networkFallbackRouter);

// Health check
voiceAgentRouter.get('/health', (_req: Request, res: Response) => {
    res.json({ status: 'ok', service: 'voice-agent' });
});

// Twilio webhook — returns TwiML for the call
voiceAgentRouter.post('/voice', (req: Request, res: Response) => {
    const response = new twilio.twiml.VoiceResponse();
    response.say('Hello! This is your AI voice agent. Let me connect you.');

    const connect = response.connect();
    connect.stream({
        url: publicVoiceUrl('/media-stream').replace('https:', 'wss:')
    });

    res.type('text/xml');
    res.send(response.toString());
});

// Inbound call webhook — Twilio hits this when someone calls your number
voiceAgentRouter.post('/incoming-call', (req: Request, res: Response) => {
    const callerNumber = req.body?.From || 'Unknown';
    console.log(`📲 Incoming call from: ${callerNumber}`);

    const response = new twilio.twiml.VoiceResponse();
    response.say('Hello! Welcome. I am your AI assistant. How can I help you today?');

    const connect = response.connect();
    connect.stream({
        url: publicVoiceUrl('/media-stream').replace('https:', 'wss:')
    });

    res.type('text/xml');
    res.send(response.toString());
});

// Endpoint to trigger outbound call
voiceAgentRouter.post('/make-call', async (req: Request, res: Response) => {
    const to = req.user!.phoneNumber;

    try {
        const twilioClient = twilio(
            process.env.VOICE_AGENT_TWILIO_ACCOUNT_SID,
            process.env.VOICE_AGENT_TWILIO_AUTH_TOKEN
        );

        const call = await twilioClient.calls.create({
            to,
            from: process.env.VOICE_AGENT_TWILIO_PHONE_NUMBER!,
            url: `${process.env.VOICE_AGENT_PUBLIC_URL}/api/voice-agent/voice`,
        });

        console.log(`📞 Call initiated to ${to}! SID: ${call.sid}`);
        res.json({ success: true, callSid: call.sid, to });
    } catch (error: any) {
        console.error('❌ Error making call:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});


// ─────────────────────────────────────────────
// WebSocket setup for Twilio media streams
// Called from the main server index.ts
// ─────────────────────────────────────────────

export function setupVoiceAgentWebSocket(server: HttpServer): void {
    const wss = new WebSocketServer({
        server, path: '/media-stream', maxPayload: 64 * 1024,
        verifyClient: (info: { req: IncomingMessage }) => validTwilioSignature(info.req, info.req.url || '/media-stream', {}, true),
    });

    wss.on('connection', (twilioWs: WebSocket) => {
        let streamSid: string | null = null;
        let elevenLabsWs: WebSocket | null = null;

        twilioWs.on('message', (data: string) => {
            let message: any;
            try { message = JSON.parse(data.toString()); }
            catch { twilioWs.close(1008, 'Invalid message'); return; }
            if (!message || typeof message !== 'object') { twilioWs.close(1008); return; }

            switch (message.event) {
                case 'connected':
                    console.log('📞 Twilio stream connected');
                    break;

                case 'start':
                    if (elevenLabsWs || typeof message.start?.streamSid !== 'string') {
                        twilioWs.close(1008, 'Invalid stream start');
                        return;
                    }
                    streamSid = message.start.streamSid;
                    console.log('🎙️ Call started - StreamSid:', streamSid);

                    elevenLabsWs = connectToElevenLabs(
                        process.env.ELEVENLABS_AGENT_ID!,
                        process.env.ELEVENLABS_API_KEY!
                    );

                    setupElevenLabsHandlers(elevenLabsWs, twilioWs, streamSid!);
                    break;

                case 'media':
                    if (elevenLabsWs?.readyState === WebSocket.OPEN && typeof message.media?.payload === 'string') {
                        elevenLabsWs.send(JSON.stringify({
                            user_audio_chunk: message.media.payload
                        }));
                    }
                    break;

                case 'stop':
                    console.log('🛑 Call ended');
                    elevenLabsWs?.close();
                    break;
            }
        });

        twilioWs.on('close', () => {
            elevenLabsWs?.close();
        });
    });

    console.log('🔌 Voice Agent WebSocket endpoint: /media-stream');
}


function setupElevenLabsHandlers(
    elevenLabsWs: WebSocket,
    twilioWs: WebSocket,
    streamSid: string
) {
    elevenLabsWs.on('message', (data: string) => {
        const message = JSON.parse(data);

        switch (message.type) {
            case 'audio':
                if (message.audio_event?.audio_base_64) {
                    twilioWs.send(JSON.stringify({
                        event: 'media',
                        streamSid: streamSid,
                        media: {
                            payload: message.audio_event.audio_base_64
                        }
                    }));
                }
                break;

            case 'user_transcript':
                console.log('👤 User:', message.user_transcription_event.user_transcript);
                break;

            case 'agent_response':
                console.log('🤖 AI:', message.agent_response_event?.agent_response);
                break;

            case 'conversation_initiation_metadata':
                const meta = message.conversation_initiation_metadata_event;
                console.log(`✅ ElevenLabs ready (in: ${meta.user_input_audio_format}, out: ${meta.agent_output_audio_format})`);
                break;
        }
    });

    elevenLabsWs.on('error', (error) => {
        console.error('❌ ElevenLabs error:', error);
    });

    elevenLabsWs.on('close', () => {
        console.log('🔌 ElevenLabs disconnected');
    });
}

export default voiceAgentRouter;

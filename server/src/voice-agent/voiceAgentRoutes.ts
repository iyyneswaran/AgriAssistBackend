import { Router, Request, Response } from 'express';
import twilio from 'twilio';
import { WebSocketServer, WebSocket } from 'ws';
import { Server as HttpServer } from 'http';
import { connectToElevenLabs } from './llm';
import smsRouter from './sms';
import addressSmsRouter from './addressSms';
import networkFallbackRouter from './networkFallback';

// ─────────────────────────────────────────────
// Voice Agent Routes
// All endpoints are mounted under /api/voice-agent
// ─────────────────────────────────────────────

const voiceAgentRouter = Router();

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
        url: `wss://${req.headers.host}/media-stream`
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
        url: `wss://${req.headers.host}/media-stream`
    });

    res.type('text/xml');
    res.send(response.toString());
});

// Endpoint to trigger outbound call
voiceAgentRouter.post('/make-call', async (req: Request, res: Response) => {
    const { phoneNumber } = req.body ?? {};
    const to = phoneNumber || process.env.VOICE_AGENT_MY_PHONE_NUMBER!;

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
    const wss = new WebSocketServer({ server, path: '/media-stream' });

    wss.on('connection', (twilioWs: WebSocket) => {
        let streamSid: string | null = null;
        let elevenLabsWs: WebSocket | null = null;

        twilioWs.on('message', (data: string) => {
            const message = JSON.parse(data);

            switch (message.event) {
                case 'connected':
                    console.log('📞 Twilio stream connected');
                    break;

                case 'start':
                    streamSid = message.start.streamSid;
                    console.log('🎙️ Call started - StreamSid:', streamSid);

                    elevenLabsWs = connectToElevenLabs(
                        process.env.ELEVENLABS_AGENT_ID!,
                        process.env.ELEVENLABS_API_KEY!
                    );

                    setupElevenLabsHandlers(elevenLabsWs, twilioWs, streamSid!);
                    break;

                case 'media':
                    if (elevenLabsWs?.readyState === WebSocket.OPEN) {
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

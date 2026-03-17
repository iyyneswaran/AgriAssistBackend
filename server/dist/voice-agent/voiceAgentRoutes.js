"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.setupVoiceAgentWebSocket = setupVoiceAgentWebSocket;
const express_1 = require("express");
const twilio_1 = __importDefault(require("twilio"));
const ws_1 = require("ws");
const llm_1 = require("./llm");
const sms_1 = __importDefault(require("./sms"));
const addressSms_1 = __importDefault(require("./addressSms"));
const networkFallback_1 = __importDefault(require("./networkFallback"));
// ─────────────────────────────────────────────
// Voice Agent Routes
// All endpoints are mounted under /api/voice-agent
// ─────────────────────────────────────────────
const voiceAgentRouter = (0, express_1.Router)();
// Mount sub-routers
voiceAgentRouter.use('/', sms_1.default);
voiceAgentRouter.use('/', addressSms_1.default);
voiceAgentRouter.use('/', networkFallback_1.default);
// Health check
voiceAgentRouter.get('/health', (_req, res) => {
    res.json({ status: 'ok', service: 'voice-agent' });
});
// Twilio webhook — returns TwiML for the call
voiceAgentRouter.post('/voice', (req, res) => {
    const response = new twilio_1.default.twiml.VoiceResponse();
    response.say('Hello! This is your AI voice agent. Let me connect you.');
    const connect = response.connect();
    connect.stream({
        url: `wss://${req.headers.host}/media-stream`
    });
    res.type('text/xml');
    res.send(response.toString());
});
// Inbound call webhook — Twilio hits this when someone calls your number
voiceAgentRouter.post('/incoming-call', (req, res) => {
    const callerNumber = req.body?.From || 'Unknown';
    console.log(`📲 Incoming call from: ${callerNumber}`);
    const response = new twilio_1.default.twiml.VoiceResponse();
    response.say('Hello! Welcome. I am your AI assistant. How can I help you today?');
    const connect = response.connect();
    connect.stream({
        url: `wss://${req.headers.host}/media-stream`
    });
    res.type('text/xml');
    res.send(response.toString());
});
// Endpoint to trigger outbound call
voiceAgentRouter.post('/make-call', async (req, res) => {
    const { phoneNumber } = req.body ?? {};
    const to = phoneNumber || process.env.VOICE_AGENT_MY_PHONE_NUMBER;
    try {
        const twilioClient = (0, twilio_1.default)(process.env.VOICE_AGENT_TWILIO_ACCOUNT_SID, process.env.VOICE_AGENT_TWILIO_AUTH_TOKEN);
        const call = await twilioClient.calls.create({
            to,
            from: process.env.VOICE_AGENT_TWILIO_PHONE_NUMBER,
            url: `${process.env.VOICE_AGENT_PUBLIC_URL}/api/voice-agent/voice`,
        });
        console.log(`📞 Call initiated to ${to}! SID: ${call.sid}`);
        res.json({ success: true, callSid: call.sid, to });
    }
    catch (error) {
        console.error('❌ Error making call:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});
// ─────────────────────────────────────────────
// WebSocket setup for Twilio media streams
// Called from the main server index.ts
// ─────────────────────────────────────────────
function setupVoiceAgentWebSocket(server) {
    const wss = new ws_1.WebSocketServer({ server, path: '/media-stream' });
    wss.on('connection', (twilioWs) => {
        let streamSid = null;
        let elevenLabsWs = null;
        twilioWs.on('message', (data) => {
            const message = JSON.parse(data);
            switch (message.event) {
                case 'connected':
                    console.log('📞 Twilio stream connected');
                    break;
                case 'start':
                    streamSid = message.start.streamSid;
                    console.log('🎙️ Call started - StreamSid:', streamSid);
                    elevenLabsWs = (0, llm_1.connectToElevenLabs)(process.env.ELEVENLABS_AGENT_ID, process.env.ELEVENLABS_API_KEY);
                    setupElevenLabsHandlers(elevenLabsWs, twilioWs, streamSid);
                    break;
                case 'media':
                    if (elevenLabsWs?.readyState === ws_1.WebSocket.OPEN) {
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
function setupElevenLabsHandlers(elevenLabsWs, twilioWs, streamSid) {
    elevenLabsWs.on('message', (data) => {
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
exports.default = voiceAgentRouter;
//# sourceMappingURL=voiceAgentRoutes.js.map
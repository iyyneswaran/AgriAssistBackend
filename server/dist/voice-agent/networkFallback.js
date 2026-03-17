"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const twilio_1 = __importDefault(require("twilio"));
const llm_1 = require("./llm");
const sms_1 = require("./sms");
const crypto_1 = __importDefault(require("crypto"));
/** Temporarily holds LLM responses for pending fallback calls. */
const pendingFallbackCalls = new Map();
// Clean up stale fallback entries older than 10 minutes
setInterval(() => {
    const tenMinutesAgo = new Date(Date.now() - 10 * 60 * 1000);
    for (const [id, entry] of pendingFallbackCalls.entries()) {
        if (entry.createdAt < tenMinutesAgo) {
            pendingFallbackCalls.delete(id);
            console.log(`🗑️ Stale fallback call entry expired: ${id}`);
        }
    }
}, 60 * 1000); // check every minute
// ─────────────────────────────────────────────
// Express Router
// ─────────────────────────────────────────────
const networkFallbackRouter = (0, express_1.Router)();
/**
 * POST /network-fallback
 *
 * Called by the frontend when it detects degraded network.
 * Resumes the chat session and delivers the LLM answer via SMS or Call.
 *
 * Body:
 *   chatId      – Session key (phone number) for memory continuity
 *   failedQuery – The user message that failed to send over the web
 *   phoneNumber – Where to deliver the fallback response
 *   channel     – "sms" | "call"
 */
networkFallbackRouter.post('/network-fallback', async (req, res) => {
    const { chatId, failedQuery, phoneNumber, channel } = req.body ?? {};
    // ── Validation ──────────────────────────────
    if (!chatId || !failedQuery || !phoneNumber || !channel) {
        res.status(400).json({
            success: false,
            error: 'Missing required fields: chatId, failedQuery, phoneNumber, channel',
        });
        return;
    }
    if (channel !== 'sms' && channel !== 'call') {
        res.status(400).json({
            success: false,
            error: 'channel must be "sms" or "call"',
        });
        return;
    }
    console.log(`🌐 Network fallback request — chatId: ${chatId}, channel: ${channel}`);
    console.log(`   Failed query: "${failedQuery}"`);
    // ── Resume session & get LLM response ───────
    const session = (0, sms_1.getSession)(chatId);
    // Append the failed query as if the user had sent it
    session.messages.push({ role: 'user', content: failedQuery });
    let llmResponse;
    try {
        llmResponse = await (0, llm_1.chatWithOllama)(session.messages);
        session.messages.push({ role: 'assistant', content: llmResponse });
        console.log(`🤖 Fallback LLM response: "${llmResponse}"`);
    }
    catch (err) {
        console.error('❌ Ollama error during network fallback:', err);
        res.status(500).json({ success: false, error: 'LLM processing failed' });
        return;
    }
    // ── Deliver via chosen channel ──────────────
    try {
        if (channel === 'sms') {
            await deliverViaSms(phoneNumber, failedQuery, llmResponse);
        }
        else {
            await deliverViaCall(phoneNumber, failedQuery, llmResponse);
        }
        res.json({
            success: true,
            channel,
            phoneNumber,
            failedQuery,
            response: llmResponse,
        });
    }
    catch (err) {
        console.error(`❌ Fallback ${channel} delivery error:`, err);
        res.status(500).json({ success: false, error: err.message });
    }
});
/**
 * POST /fallback-voice-twiml?id=<fallbackId>
 *
 * TwiML webhook hit by Twilio when the fallback call connects.
 * Speaks the welcome + LLM answer, then connects to the live
 * AI media stream for continued conversation.
 */
networkFallbackRouter.post('/fallback-voice-twiml', (req, res) => {
    const fallbackId = req.query.id;
    const twiml = new twilio_1.default.twiml.VoiceResponse();
    const entry = fallbackId ? pendingFallbackCalls.get(fallbackId) : undefined;
    if (!entry) {
        // Graceful fallback if the entry expired or ID is invalid
        twiml.say('Hi, this is your AI assistant. It seems there was a network issue. How can I help you?');
        const connect = twiml.connect();
        connect.stream({ url: `wss://${req.headers.host}/media-stream` });
    }
    else {
        // Speak the welcome + the answer to the failed query
        twiml.say(`Hi, this is your AI assistant following up because your network had trouble. ` +
            `You asked: "${entry.failedQuery}". ` +
            `Here is the answer: ${entry.response}`);
        // Connect to live AI conversation so the user can keep talking
        const connect = twiml.connect();
        connect.stream({ url: `wss://${req.headers.host}/media-stream` });
        // Clean up
        pendingFallbackCalls.delete(fallbackId);
        console.log(`📞 Fallback call TwiML served for ID: ${fallbackId}`);
    }
    res.type('text/xml').send(twiml.toString());
});
// ─────────────────────────────────────────────
// Delivery helpers
// Uses VOICE_AGENT_TWILIO_* env vars
// ─────────────────────────────────────────────
async function deliverViaSms(phoneNumber, failedQuery, llmResponse) {
    // Welcome message
    await (0, sms_1.sendOutboundSms)(phoneNumber, `Hi! Your network seems unstable, so I'm reaching out via SMS to continue our conversation.`);
    // LLM answer to the failed query
    await (0, sms_1.sendOutboundSms)(phoneNumber, llmResponse);
    console.log(`📤 Fallback SMS delivered to ${phoneNumber}`);
}
async function deliverViaCall(phoneNumber, failedQuery, llmResponse) {
    const twilioClient = (0, twilio_1.default)(process.env.VOICE_AGENT_TWILIO_ACCOUNT_SID, process.env.VOICE_AGENT_TWILIO_AUTH_TOKEN);
    // Generate a unique ID to link this call to its TwiML response
    const fallbackId = crypto_1.default.randomUUID();
    // Store the response so the TwiML webhook can read it
    pendingFallbackCalls.set(fallbackId, {
        response: llmResponse,
        failedQuery,
        createdAt: new Date(),
    });
    const call = await twilioClient.calls.create({
        to: phoneNumber,
        from: process.env.VOICE_AGENT_TWILIO_PHONE_NUMBER,
        url: `${process.env.VOICE_AGENT_PUBLIC_URL}/api/voice-agent/fallback-voice-twiml?id=${fallbackId}`,
    });
    console.log(`📞 Fallback call initiated to ${phoneNumber} (SID: ${call.sid}, fallbackId: ${fallbackId})`);
}
exports.default = networkFallbackRouter;
//# sourceMappingURL=networkFallback.js.map
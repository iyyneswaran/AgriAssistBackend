"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getSession = getSession;
exports.sendOutboundSms = sendOutboundSms;
const express_1 = require("express");
const twilio_1 = __importDefault(require("twilio"));
const llm_1 = require("./llm");
const addressSms_1 = require("./addressSms");
// ─────────────────────────────────────────────
// Session store  (in-memory, per phone number)
// ─────────────────────────────────────────────
const SYSTEM_PROMPT = `You are a helpful AI assistant replying over SMS.
Keep your responses brief (2-3 sentences max) because they are delivered as text messages.
Be friendly, direct, and accurate.`;
const sessions = new Map();
function getSession(phoneNumber) {
    if (!sessions.has(phoneNumber)) {
        sessions.set(phoneNumber, {
            messages: [{ role: 'system', content: SYSTEM_PROMPT }],
            lastActive: new Date(),
        });
    }
    const session = sessions.get(phoneNumber);
    session.lastActive = new Date();
    return session;
}
// Clean up sessions older than 1 hour
setInterval(() => {
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
    for (const [key, session] of sessions.entries()) {
        if (session.lastActive < oneHourAgo) {
            sessions.delete(key);
            console.log(`🗑️ SMS session expired for ${key}`);
        }
    }
}, 10 * 60 * 1000); // check every 10 minutes
// ─────────────────────────────────────────────
// Inbound SMS Handler
// POST /sms-inbound  (Twilio webhook)
// ─────────────────────────────────────────────
async function handleInboundSms(req, res) {
    const from = req.body?.From ?? 'Unknown';
    const body = req.body?.Body ?? '';
    console.log(`📩 Inbound SMS from ${from}: "${body}"`);
    const twiml = new twilio_1.default.twiml.MessagingResponse();
    if (!body.trim()) {
        twiml.message('Hi! Send me a message and I\'ll do my best to help.');
        res.type('text/xml').send(twiml.toString());
        return;
    }
    // ── Address reply interception ──────────────
    // If this number has a pending address request, treat the reply
    // as an address — do NOT forward it to the LLM chat session.
    if ((0, addressSms_1.hasPendingAddressRequest)(from)) {
        const ack = (0, addressSms_1.handleAddressReply)(from, body.trim());
        twiml.message(ack);
        res.type('text/xml').send(twiml.toString());
        return;
    }
    const session = getSession(from);
    // Append the user's message to history
    session.messages.push({ role: 'user', content: body.trim() });
    try {
        const reply = await (0, llm_1.chatWithOllama)(session.messages);
        console.log(`🤖 Agent reply to ${from}: "${reply}"`);
        // Append the assistant's reply to history
        session.messages.push({ role: 'assistant', content: reply });
        twiml.message(reply);
    }
    catch (err) {
        console.error('❌ Ollama error during SMS reply:', err);
        twiml.message('Sorry, I\'m having trouble right now. Please try again in a moment.');
    }
    res.type('text/xml').send(twiml.toString());
}
// ─────────────────────────────────────────────
// Outbound SMS  (agent initiates)
// ─────────────────────────────────────────────
/**
 * Send an outbound SMS from the AI agent to a user.
 * Records the message in the user's session so the conversation stays coherent.
 *
 * Uses VOICE_AGENT_TWILIO_* env vars (separate from OTP Twilio credentials).
 */
async function sendOutboundSms(to, message) {
    const twilioClient = (0, twilio_1.default)(process.env.VOICE_AGENT_TWILIO_ACCOUNT_SID, process.env.VOICE_AGENT_TWILIO_AUTH_TOKEN);
    const from = process.env.VOICE_AGENT_TWILIO_PHONE_NUMBER;
    // Record the outbound message in session so the next inbound reply has context
    const session = getSession(to);
    session.messages.push({ role: 'assistant', content: message });
    const result = await twilioClient.messages.create({ to, from, body: message });
    console.log(`📤 Outbound SMS sent to ${to}: "${message}" (SID: ${result.sid})`);
}
// ─────────────────────────────────────────────
// Express Router
// ─────────────────────────────────────────────
const smsRouter = (0, express_1.Router)();
// Twilio hits this when the user texts the Twilio number
smsRouter.post('/sms-inbound', handleInboundSms);
// Convenience endpoint to trigger an outbound SMS (for testing)
// GET /sms-outbound?to=+917550205578&message=Hello+from+AI
smsRouter.get('/sms-outbound', async (req, res) => {
    const to = req.query.to || process.env.VOICE_AGENT_MY_PHONE_NUMBER;
    const message = req.query.message || 'Hello! This is your AI agent. How can I help you today?';
    try {
        await sendOutboundSms(to, message);
        res.json({ success: true, to, message });
    }
    catch (err) {
        console.error('❌ Outbound SMS error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});
exports.default = smsRouter;
//# sourceMappingURL=sms.js.map
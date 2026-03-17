"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.hasPendingAddressRequest = hasPendingAddressRequest;
exports.handleAddressReply = handleAddressReply;
exports.getStoredAddress = getStoredAddress;
exports.requestAddress = requestAddress;
const express_1 = require("express");
const twilio_1 = __importDefault(require("twilio"));
/** Numbers that have been asked for their address but haven't replied yet. */
const pendingAddressRequests = new Map();
/** Latest address collected per phone number. */
const addressStore = new Map();
// Clean up stale pending requests older than 1 hour
setInterval(() => {
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
    for (const [phone, pending] of pendingAddressRequests.entries()) {
        if (pending.requestedAt < oneHourAgo) {
            pendingAddressRequests.delete(phone);
            console.log(`🗑️ Stale address request expired for ${phone}`);
        }
    }
}, 10 * 60 * 1000); // check every 10 minutes
// ─────────────────────────────────────────────
// Core helpers (exported for use in sms.ts)
// ─────────────────────────────────────────────
/** Returns true if this phone number has a pending address request. */
function hasPendingAddressRequest(phoneNumber) {
    return pendingAddressRequests.has(phoneNumber);
}
/**
 * Handle an inbound SMS that is a reply to an address request.
 * Stores the address, clears the pending flag, and returns an
 * acknowledgement message to send back to the user.
 */
function handleAddressReply(phoneNumber, body) {
    addressStore.set(phoneNumber, {
        address: body,
        receivedAt: new Date(),
    });
    pendingAddressRequests.delete(phoneNumber);
    console.log(`📍 Address received from ${phoneNumber}: "${body}"`);
    return 'Thank you! Your address has been saved for location tracking.';
}
/** Retrieve the stored address for a phone number (if any). */
function getStoredAddress(phoneNumber) {
    return addressStore.get(phoneNumber);
}
// ─────────────────────────────────────────────
// Send the address-request SMS
// Uses VOICE_AGENT_TWILIO_* env vars
// ─────────────────────────────────────────────
async function requestAddress(to) {
    const twilioClient = (0, twilio_1.default)(process.env.VOICE_AGENT_TWILIO_ACCOUNT_SID, process.env.VOICE_AGENT_TWILIO_AUTH_TOKEN);
    const from = process.env.VOICE_AGENT_TWILIO_PHONE_NUMBER;
    const message = 'Please reply with your address for location tracking.';
    // Mark this number as having a pending address request
    pendingAddressRequests.set(to, { requestedAt: new Date() });
    const result = await twilioClient.messages.create({ to, from, body: message });
    console.log(`📤 Address request sent to ${to} (SID: ${result.sid})`);
}
// ─────────────────────────────────────────────
// Express Router
// ─────────────────────────────────────────────
const addressSmsRouter = (0, express_1.Router)();
/** GET /request-address?to=+917550205578 — trigger an address-request SMS */
addressSmsRouter.get('/request-address', async (req, res) => {
    const to = req.query.to || process.env.VOICE_AGENT_MY_PHONE_NUMBER;
    try {
        await requestAddress(to);
        res.json({ success: true, to, message: 'Address request sent' });
    }
    catch (err) {
        console.error('❌ Address request error:', err);
        res.status(500).json({ success: false, error: err.message });
    }
});
/** GET /stored-address?phone=+917550205578 — retrieve the stored address */
addressSmsRouter.get('/stored-address', (req, res) => {
    const phone = req.query.phone;
    if (!phone) {
        res.status(400).json({ success: false, error: 'Missing ?phone= parameter' });
        return;
    }
    const stored = getStoredAddress(phone);
    if (!stored) {
        res.json({ success: true, phone, address: null, message: 'No address stored for this number' });
        return;
    }
    res.json({ success: true, phone, address: stored.address, receivedAt: stored.receivedAt });
});
exports.default = addressSmsRouter;
//# sourceMappingURL=addressSms.js.map
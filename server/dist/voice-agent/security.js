"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.publicVoiceUrl = publicVoiceUrl;
exports.validTwilioSignature = validTwilioSignature;
exports.verifyTwilioWebhook = verifyTwilioWebhook;
exports.ownPhone = ownPhone;
const twilio_1 = __importDefault(require("twilio"));
function publicVoiceUrl(path) {
    const base = new URL(process.env.VOICE_AGENT_PUBLIC_URL || '');
    if (base.protocol !== 'https:' || base.username || base.password || base.pathname !== '/') {
        throw new Error('VOICE_AGENT_PUBLIC_URL must be an HTTPS origin');
    }
    return `${base.origin}${path}`;
}
function validTwilioSignature(req, path, params = {}, websocket = false) {
    const secret = process.env.VOICE_AGENT_TWILIO_AUTH_TOKEN;
    const signature = req.headers['x-twilio-signature'];
    if (!secret || typeof signature !== 'string')
        return false;
    try {
        const url = publicVoiceUrl(path);
        const urls = websocket ? [url, url.replace('https:', 'wss:')] : [url];
        return urls.some(value => twilio_1.default.validateRequest(secret, signature, value, params));
    }
    catch {
        return false;
    }
}
function verifyTwilioWebhook(req, res, next) {
    if (!req.is('application/x-www-form-urlencoded') || !validTwilioSignature(req, req.originalUrl, req.body || {})) {
        return res.status(403).json({ error: 'Invalid provider signature' });
    }
    next();
}
function ownPhone(req, res, next) {
    const phone = req.user?.phoneNumber;
    if (!phone)
        return res.status(403).json({ error: 'Verified phone required' });
    const supplied = [req.body?.phoneNumber, req.query.phone];
    if (supplied.some(value => value !== undefined && value !== phone)) {
        return res.status(403).json({ error: 'Access denied' });
    }
    next();
}
//# sourceMappingURL=security.js.map
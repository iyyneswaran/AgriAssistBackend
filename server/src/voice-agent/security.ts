import { Request, Response, NextFunction } from 'express';
import { IncomingMessage } from 'http';
import twilio from 'twilio';

export function publicVoiceUrl(path: string): string {
    const base = new URL(process.env.VOICE_AGENT_PUBLIC_URL || '');
    if (base.protocol !== 'https:' || base.username || base.password || base.pathname !== '/') {
        throw new Error('VOICE_AGENT_PUBLIC_URL must be an HTTPS origin');
    }
    return `${base.origin}${path}`;
}

export function validTwilioSignature(req: IncomingMessage, path: string, params: Record<string, any> = {}, websocket = false): boolean {
    const secret = process.env.VOICE_AGENT_TWILIO_AUTH_TOKEN;
    const signature = req.headers['x-twilio-signature'];
    if (!secret || typeof signature !== 'string') return false;
    try {
        const url = publicVoiceUrl(path);
        const urls = websocket ? [url, url.replace('https:', 'wss:')] : [url];
        return urls.some(value => twilio.validateRequest(secret, signature, value, params));
    } catch {
        return false;
    }
}

export function verifyTwilioWebhook(req: Request, res: Response, next: NextFunction) {
    if (!req.is('application/x-www-form-urlencoded') || !validTwilioSignature(req, req.originalUrl, req.body || {})) {
        return res.status(403).json({ error: 'Invalid provider signature' });
    }
    next();
}

export function ownPhone(req: Request, res: Response, next: NextFunction) {
    const phone = req.user?.phoneNumber;
    if (!phone) return res.status(403).json({ error: 'Verified phone required' });
    const supplied = [req.body?.phoneNumber, req.query.phone];
    if (supplied.some(value => value !== undefined && value !== phone)) {
        return res.status(403).json({ error: 'Access denied' });
    }
    next();
}

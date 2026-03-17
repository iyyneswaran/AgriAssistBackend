import { OllamaMessage } from './llm';
interface SmsSession {
    messages: OllamaMessage[];
    lastActive: Date;
}
export declare function getSession(phoneNumber: string): SmsSession;
/**
 * Send an outbound SMS from the AI agent to a user.
 * Records the message in the user's session so the conversation stays coherent.
 *
 * Uses VOICE_AGENT_TWILIO_* env vars (separate from OTP Twilio credentials).
 */
export declare function sendOutboundSms(to: string, message: string): Promise<void>;
declare const smsRouter: import("express-serve-static-core").Router;
export default smsRouter;
//# sourceMappingURL=sms.d.ts.map
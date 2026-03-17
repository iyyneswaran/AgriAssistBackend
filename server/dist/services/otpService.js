"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.OTPService = void 0;
const twilio_1 = __importDefault(require("twilio"));
const accountSid = process.env.TWILIO_ACCOUNT_SID;
const authToken = process.env.TWILIO_AUTH_TOKEN;
const verifyServiceSid = process.env.TWILIO_VERIFY_SERVICE_SID;
const client = (0, twilio_1.default)(accountSid, authToken);
/**
 * OTP Service
 *
 * Handles generation, delivery, and verification of OTPs via Twilio Verify.
 */
class OTPService {
    /**
     * Sends a verification code via Twilio Verify.
     */
    static async sendVerification(phoneNumber) {
        try {
            if (!verifyServiceSid) {
                console.warn(`[TWILIO STUB] Would send OTP to ${phoneNumber} if credentials were set.`);
                return;
            }
            await client.verify.v2.services(verifyServiceSid)
                .verifications
                .create({ to: phoneNumber, channel: 'sms' });
            console.log(`[TWILIO] Verification sent to ${phoneNumber}`);
        }
        catch (error) {
            console.error(`[TWILIO] Error sending verification: ${error.message}`);
            throw new Error(`Failed to send verification code: ${error.message}`);
        }
    }
    /**
     * Checks a verification code via Twilio Verify.
     */
    static async checkVerification(phoneNumber, code) {
        try {
            if (!verifyServiceSid) {
                console.warn(`[TWILIO STUB] Verifying ${code} for ${phoneNumber} (STUB: always true if code is '123456')`);
                return code === '123456';
            }
            const verificationCheck = await client.verify.v2.services(verifyServiceSid)
                .verificationChecks
                .create({ to: phoneNumber, code });
            return verificationCheck.status === 'approved';
        }
        catch (error) {
            console.error(`[TWILIO] Error checking verification: ${error.message}`);
            return false;
        }
    }
    // Deprecated methods for compatibility or internal use if needed
    static generateOTP() { return ''; }
    static async hashOTP(otp) { return ''; }
    static async verifyOTP(otp, hashedOtp) { return false; }
    static async sendOTP(phoneNumber, otp) { }
}
exports.OTPService = OTPService;
//# sourceMappingURL=otpService.js.map
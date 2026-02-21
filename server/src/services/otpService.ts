import twilio from 'twilio';

const accountSid = process.env.TWILIO_ACCOUNT_SID;
const authToken = process.env.TWILIO_AUTH_TOKEN;
const verifyServiceSid = process.env.TWILIO_VERIFY_SERVICE_SID;

const client = twilio(accountSid, authToken);

/**
 * OTP Service
 * 
 * Handles generation, delivery, and verification of OTPs via Twilio Verify.
 */
export class OTPService {
    /**
     * Sends a verification code via Twilio Verify.
     */
    static async sendVerification(phoneNumber: string): Promise<void> {
        try {
            if (!verifyServiceSid) {
                console.warn(`[TWILIO STUB] Would send OTP to ${phoneNumber} if credentials were set.`);
                return;
            }

            await client.verify.v2.services(verifyServiceSid)
                .verifications
                .create({ to: phoneNumber, channel: 'sms' });

            console.log(`[TWILIO] Verification sent to ${phoneNumber}`);
        } catch (error: any) {
            console.error(`[TWILIO] Error sending verification: ${error.message}`);
            throw new Error(`Failed to send verification code: ${error.message}`);
        }
    }

    /**
     * Checks a verification code via Twilio Verify.
     */
    static async checkVerification(phoneNumber: string, code: string): Promise<boolean> {
        try {
            if (!verifyServiceSid) {
                console.warn(`[TWILIO STUB] Verifying ${code} for ${phoneNumber} (STUB: always true if code is '123456')`);
                return code === '123456';
            }

            const verificationCheck = await client.verify.v2.services(verifyServiceSid)
                .verificationChecks
                .create({ to: phoneNumber, code });

            return verificationCheck.status === 'approved';
        } catch (error: any) {
            console.error(`[TWILIO] Error checking verification: ${error.message}`);
            return false;
        }
    }

    // Deprecated methods for compatibility or internal use if needed
    static generateOTP(): string { return ''; }
    static async hashOTP(otp: string): Promise<string> { return ''; }
    static async verifyOTP(otp: string, hashedOtp: string): Promise<boolean> { return false; }
    static async sendOTP(phoneNumber: string, otp: string): Promise<void> { }
}

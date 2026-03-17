/**
 * OTP Service
 *
 * Handles generation, delivery, and verification of OTPs via Twilio Verify.
 */
export declare class OTPService {
    /**
     * Sends a verification code via Twilio Verify.
     */
    static sendVerification(phoneNumber: string): Promise<void>;
    /**
     * Checks a verification code via Twilio Verify.
     */
    static checkVerification(phoneNumber: string, code: string): Promise<boolean>;
    static generateOTP(): string;
    static hashOTP(otp: string): Promise<string>;
    static verifyOTP(otp: string, hashedOtp: string): Promise<boolean>;
    static sendOTP(phoneNumber: string, otp: string): Promise<void>;
}
//# sourceMappingURL=otpService.d.ts.map
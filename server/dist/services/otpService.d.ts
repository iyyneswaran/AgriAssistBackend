/**
 * OTP Service
 *
 * Handles generation, hashing, and verification of OTPs.
 * Designed to be modular so that Twilio or other SMS providers
 * can be integrated by replacing the sendOTP method.
 */
export declare class OTPService {
    private static readonly OTP_LENGTH;
    private static readonly BCRYPT_SALT_ROUNDS;
    /**
     * Generates a 6-digit numeric OTP.
     */
    static generateOTP(): string;
    /**
     * Hashes the OTP for secure storage.
     */
    static hashOTP(otp: string): Promise<string>;
    /**
     * Verifies the provided OTP against the stored hash.
     */
    static verifyOTP(otp: string, hashedOtp: string): Promise<boolean>;
    /**
     * Simulates sending an OTP via SMS.
     * INTEGRATION POINT: Replace this logic with Twilio SDK call later.
     */
    static sendOTP(phoneNumber: string, otp: string): Promise<void>;
}
//# sourceMappingURL=otpService.d.ts.map
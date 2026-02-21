"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.OTPService = void 0;
const bcryptjs_1 = __importDefault(require("bcryptjs"));
/**
 * OTP Service
 *
 * Handles generation, hashing, and verification of OTPs.
 * Designed to be modular so that Twilio or other SMS providers
 * can be integrated by replacing the sendOTP method.
 */
class OTPService {
    /**
     * Generates a 6-digit numeric OTP.
     */
    static generateOTP() {
        return Math.floor(100000 + Math.random() * 900000).toString();
    }
    /**
     * Hashes the OTP for secure storage.
     */
    static async hashOTP(otp) {
        return bcryptjs_1.default.hash(otp, this.BCRYPT_SALT_ROUNDS);
    }
    /**
     * Verifies the provided OTP against the stored hash.
     */
    static async verifyOTP(otp, hashedOtp) {
        return bcryptjs_1.default.compare(otp, hashedOtp);
    }
    /**
     * Simulates sending an OTP via SMS.
     * INTEGRATION POINT: Replace this logic with Twilio SDK call later.
     */
    static async sendOTP(phoneNumber, otp) {
        console.log(`[SMS STUB] Sending OTP ${otp} to ${phoneNumber}`);
        // Future Twilio Integration:
        // await twilioClient.messages.create({ body: `Your OTP is ${otp}`, to: phoneNumber, from: '...' });
    }
}
exports.OTPService = OTPService;
OTPService.OTP_LENGTH = 6;
OTPService.BCRYPT_SALT_ROUNDS = 10;
//# sourceMappingURL=otpService.js.map
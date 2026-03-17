"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.refresh = exports.verifyOTP = exports.requestOTP = void 0;
const db_1 = require("../db");
const jwt_1 = require("../valid/jwt");
const otpService_1 = require("../services/otpService");
/**
 * Request OTP for authentication.
 * If user doesn't exist, it still sends OTP to prevent account enumeration
 * (though in a prototype/startup context, we usually just send it).
 */
const requestOTP = async (req, res) => {
    try {
        const { phoneNumber } = req.body;
        // Send OTP via Twilio Verify
        await otpService_1.OTPService.sendVerification(phoneNumber);
        res.status(200).json({
            message: 'OTP sent successfully',
        });
    }
    catch (err) {
        res.status(500).json({ message: `Failed to request OTP: ${err.message}` });
    }
};
exports.requestOTP = requestOTP;
/**
 * Verify OTP and handle Login/Signup.
 */
const verifyOTP = async (req, res) => {
    try {
        const { phoneNumber, otp } = req.body;
        const isValid = await otpService_1.OTPService.checkVerification(phoneNumber, otp);
        if (!isValid) {
            return res.status(400).json({ message: 'Invalid or expired OTP' });
        }
        // Handle User creation or login
        let user = await db_1.db.user.findUnique({
            where: { phoneNumber },
        });
        if (!user) {
            // New User Flow
            user = await db_1.db.user.create({
                data: {
                    phoneNumber,
                    name: null,
                    interface: 'SOFTWARE', // Default for new users via phone
                    role: 'FARMER',
                },
            });
        }
        const accessToken = (0, jwt_1.signAccessToken)(user);
        const refreshToken = (0, jwt_1.signRefreshToken)(user);
        res.cookie("refreshToken", refreshToken, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: "strict",
        });
        res.status(200).json({
            message: user.name ? `Welcome back, ${user.name}` : 'Login successful',
            token: accessToken,
            user: {
                id: user.id,
                name: user.name,
                role: user.role,
                phoneNumber: user.phoneNumber,
            },
        });
    }
    catch (err) {
        res.status(500).json({ message: `Verification failed: ${err.message}` });
    }
};
exports.verifyOTP = verifyOTP;
/**
 * Standard Token Refresh
 */
const refresh = async (req, res) => {
    try {
        const user = req.user;
        if (!user) {
            return res.status(401).json({ message: "User not authenticated" });
        }
        const accessToken = (0, jwt_1.signAccessToken)(user);
        res.status(200).json({
            message: 'Token refreshed successfully',
            token: accessToken,
        });
    }
    catch (err) {
        res.status(500).json({ message: err.message });
    }
};
exports.refresh = refresh;
exports.default = {
    requestOTP: exports.requestOTP,
    verifyOTP: exports.verifyOTP,
    refresh: exports.refresh,
};
//# sourceMappingURL=auth.js.map
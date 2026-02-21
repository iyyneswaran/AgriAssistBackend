"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.refresh = exports.verifyOTP = exports.requestOTP = void 0;
const db_1 = require("../db");
const jwt_1 = require("../valid/jwt");
const otpService_1 = require("../services/otpService");
const truecallerService_1 = require("../services/truecallerService");
/**
 * Request OTP for authentication.
 * If user doesn't exist, it still sends OTP to prevent account enumeration
 * (though in a prototype/startup context, we usually just send it).
 */
const requestOTP = async (req, res) => {
    try {
        const { phoneNumber } = req.body;
        const otp = otpService_1.OTPService.generateOTP();
        const otpHash = await otpService_1.OTPService.hashOTP(otp);
        const expiresAt = new Date(Date.now() + 5 * 60 * 1000); // 5 minutes
        await db_1.db.oTP.upsert({
            where: { phoneNumber },
            update: {
                otpHash,
                expiresAt,
                attempts: 0,
            },
            create: {
                phoneNumber,
                otpHash,
                expiresAt,
            },
        });
        // Send OTP via stub (Future: Twilio)
        await otpService_1.OTPService.sendOTP(phoneNumber, otp);
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
        const storedOtp = await db_1.db.oTP.findUnique({
            where: { phoneNumber },
        });
        if (!storedOtp) {
            return res.status(400).json({ message: 'No OTP requested for this number' });
        }
        if (new Date() > storedOtp.expiresAt) {
            return res.status(400).json({ message: 'OTP has expired' });
        }
        if (storedOtp.attempts >= 3) {
            return res.status(400).json({ message: 'Too many failed attempts. Please request a new OTP' });
        }
        const isValid = await otpService_1.OTPService.verifyOTP(otp, storedOtp.otpHash);
        if (!isValid) {
            await db_1.db.oTP.update({
                where: { phoneNumber },
                data: { attempts: { increment: 1 } },
            });
            return res.status(400).json({ message: 'Invalid OTP' });
        }
        // OTP is valid - clear it
        await db_1.db.oTP.delete({ where: { phoneNumber } });
        // Handle User creation or login
        let user = await db_1.db.user.findUnique({
            where: { phoneNumber },
        });
        if (!user) {
            // New User Flow: Try Truecaller stub
            const profile = await truecallerService_1.TruecallerService.fetchProfile(phoneNumber);
            user = await db_1.db.user.create({
                data: {
                    phoneNumber,
                    name: profile?.name || null,
                    nameSource: profile?.source || null,
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
                nameSource: user.nameSource,
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
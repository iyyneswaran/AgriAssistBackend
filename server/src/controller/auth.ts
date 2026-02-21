import { Request, Response } from 'express';
import { db } from '../db';
import { signAccessToken, signRefreshToken } from '../valid/jwt';
import { Payload } from '../types/type';
import { OTPService } from '../services/otpService';

/**
 * Request OTP for authentication.
 * If user doesn't exist, it still sends OTP to prevent account enumeration
 * (though in a prototype/startup context, we usually just send it).
 */
export const requestOTP = async (req: Request, res: Response) => {
    try {
        const { phoneNumber } = req.body;

        // Send OTP via Twilio Verify
        await OTPService.sendVerification(phoneNumber);

        res.status(200).json({
            message: 'OTP sent successfully',
        });
    } catch (err: any) {
        res.status(500).json({ message: `Failed to request OTP: ${err.message}` });
    }
};

/**
 * Verify OTP and handle Login/Signup.
 */
export const verifyOTP = async (req: Request, res: Response) => {
    try {
        const { phoneNumber, otp } = req.body;

        const isValid = await OTPService.checkVerification(phoneNumber, otp);

        if (!isValid) {
            return res.status(400).json({ message: 'Invalid or expired OTP' });
        }

        // Handle User creation or login
        let user = await db.user.findUnique({
            where: { phoneNumber },
        });

        if (!user) {
            // New User Flow
            user = await db.user.create({
                data: {
                    phoneNumber,
                    name: null,
                    interface: 'SOFTWARE', // Default for new users via phone
                    role: 'FARMER',
                },
            });
        }

        const accessToken = signAccessToken(user as Payload);
        const refreshToken = signRefreshToken(user as Payload);

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

    } catch (err: any) {
        res.status(500).json({ message: `Verification failed: ${err.message}` });
    }
};

/**
 * Standard Token Refresh
 */
export const refresh = async (req: Request, res: Response) => {
    try {
        const user = req.user as Payload;
        if (!user) {
            return res.status(401).json({ message: "User not authenticated" });
        }

        const accessToken = signAccessToken(user);

        res.status(200).json({
            message: 'Token refreshed successfully',
            token: accessToken,
        });
    } catch (err: any) {
        res.status(500).json({ message: err.message });
    }
};

export default {
    requestOTP,
    verifyOTP,
    refresh,
};
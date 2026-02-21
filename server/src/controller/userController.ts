import { Request, Response } from 'express';
import { db } from '../db';
import { Payload } from '../types/type';
import { AuditLogger } from '../services/auditLogger';
import { OTPService } from '../services/otpService';
import { signAccessToken, signRefreshToken } from '../valid/jwt';

/**
 * Update User Profile (Name, Interface)
 */
export const updateProfile = async (req: Request, res: Response) => {
    try {
        const user = req.user as Payload;
        const { name, interface: interfaceType } = req.body;

        const updatedUser = await db.user.update({
            where: { id: user.id },
            data: {
                name: name || undefined,
                interface: interfaceType || undefined
            }
        });

        // Audit Log
        await AuditLogger.log(user.id, "PROFILE_UPDATED");

        res.status(200).json({
            message: "Profile updated successfully",
            user: {
                id: updatedUser.id,
                name: updatedUser.name,
                role: updatedUser.role,
                interface: updatedUser.interface,
                phoneNumber: updatedUser.phoneNumber
            }
        });

    } catch (err: any) {
        res.status(500).json({ message: `Failed to update profile: ${err.message}` });
    }
};

/**
 * Get current user profile
 */
export const getProfile = async (req: Request, res: Response) => {
    try {
        const user = req.user as Payload;

        const userData = await db.user.findUnique({
            where: { id: user.id }
        });

        if (!userData) {
            return res.status(404).json({ message: "User not found" });
        }

        res.status(200).json(userData);
    } catch (err: any) {
        res.status(500).json({ message: `Failed to retrieve profile: ${err.message}` });
    }
};

/**
 * Request OTP to update mobile number
 * Sends OTP to the NEW number
 */
export const requestMobileUpdate = async (req: Request, res: Response) => {
    try {
        const { newPhoneNumber } = req.body;

        // 1. Check if new number is already taken
        const existingUser = await db.user.findUnique({
            where: { phoneNumber: newPhoneNumber }
        });

        if (existingUser) {
            return res.status(400).json({ message: "This phone number is already associated with another account" });
        }

        // 2. Send OTP to new number
        await OTPService.sendVerification(newPhoneNumber);

        res.status(200).json({ message: "OTP sent to new phone number" });
    } catch (err: any) {
        res.status(500).json({ message: `Failed to request mobile update: ${err.message}` });
    }
};

/**
 * Verify OTP and update mobile number
 */
export const verifyMobileUpdate = async (req: Request, res: Response) => {
    try {
        const user = req.user as Payload;
        const { newPhoneNumber, otp } = req.body;

        // 1. Verify OTP
        const isValid = await OTPService.checkVerification(newPhoneNumber, otp);

        if (!isValid) {
            return res.status(400).json({ message: "Invalid or expired OTP" });
        }

        // 2. Perform Update
        const updatedUser = await db.user.update({
            where: { id: user.id },
            data: { phoneNumber: newPhoneNumber }
        });

        // 3. Log Audit
        await AuditLogger.log(user.id, "PHONE_NUMBER_UPDATED");

        // 4. Since token usually contains phone/id, we should issue new ones
        const accessToken = signAccessToken(updatedUser as Payload);
        const refreshToken = signRefreshToken(updatedUser as Payload);

        res.cookie("refreshToken", refreshToken, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: "strict",
        });

        res.status(200).json({
            message: "Phone number updated successfully",
            token: accessToken,
            user: {
                id: updatedUser.id,
                phoneNumber: updatedUser.phoneNumber
            }
        });

    } catch (err: any) {
        res.status(500).json({ message: `Failed to verify mobile update: ${err.message}` });
    }
};

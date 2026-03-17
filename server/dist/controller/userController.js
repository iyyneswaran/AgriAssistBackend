"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.verifyMobileUpdate = exports.requestMobileUpdate = exports.getProfile = exports.updateProfile = void 0;
const db_1 = require("../db");
const auditLogger_1 = require("../services/auditLogger");
const otpService_1 = require("../services/otpService");
const jwt_1 = require("../valid/jwt");
/**
 * Update User Profile (Name, Interface)
 */
const updateProfile = async (req, res) => {
    try {
        const user = req.user;
        const { name, interface: interfaceType } = req.body;
        const updatedUser = await db_1.db.user.update({
            where: { id: user.id },
            data: {
                name: name || undefined,
                interface: interfaceType || undefined
            }
        });
        // Audit Log
        await auditLogger_1.AuditLogger.log(user.id, "PROFILE_UPDATED");
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
    }
    catch (err) {
        res.status(500).json({ message: `Failed to update profile: ${err.message}` });
    }
};
exports.updateProfile = updateProfile;
/**
 * Get current user profile
 */
const getProfile = async (req, res) => {
    try {
        const user = req.user;
        const userData = await db_1.db.user.findUnique({
            where: { id: user.id }
        });
        if (!userData) {
            return res.status(404).json({ message: "User not found" });
        }
        res.status(200).json(userData);
    }
    catch (err) {
        res.status(500).json({ message: `Failed to retrieve profile: ${err.message}` });
    }
};
exports.getProfile = getProfile;
/**
 * Request OTP to update mobile number
 * Sends OTP to the NEW number
 */
const requestMobileUpdate = async (req, res) => {
    try {
        const { newPhoneNumber } = req.body;
        // 1. Check if new number is already taken
        const existingUser = await db_1.db.user.findUnique({
            where: { phoneNumber: newPhoneNumber }
        });
        if (existingUser) {
            return res.status(400).json({ message: "This phone number is already associated with another account" });
        }
        // 2. Send OTP to new number
        await otpService_1.OTPService.sendVerification(newPhoneNumber);
        res.status(200).json({ message: "OTP sent to new phone number" });
    }
    catch (err) {
        res.status(500).json({ message: `Failed to request mobile update: ${err.message}` });
    }
};
exports.requestMobileUpdate = requestMobileUpdate;
/**
 * Verify OTP and update mobile number
 */
const verifyMobileUpdate = async (req, res) => {
    try {
        const user = req.user;
        const { newPhoneNumber, otp } = req.body;
        // 1. Verify OTP
        const isValid = await otpService_1.OTPService.checkVerification(newPhoneNumber, otp);
        if (!isValid) {
            return res.status(400).json({ message: "Invalid or expired OTP" });
        }
        // 2. Perform Update
        const updatedUser = await db_1.db.user.update({
            where: { id: user.id },
            data: { phoneNumber: newPhoneNumber }
        });
        // 3. Log Audit
        await auditLogger_1.AuditLogger.log(user.id, "PHONE_NUMBER_UPDATED");
        // 4. Since token usually contains phone/id, we should issue new ones
        const accessToken = (0, jwt_1.signAccessToken)(updatedUser);
        const refreshToken = (0, jwt_1.signRefreshToken)(updatedUser);
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
    }
    catch (err) {
        res.status(500).json({ message: `Failed to verify mobile update: ${err.message}` });
    }
};
exports.verifyMobileUpdate = verifyMobileUpdate;
//# sourceMappingURL=userController.js.map
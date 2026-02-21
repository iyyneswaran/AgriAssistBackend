"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.verifyOTPValidation = exports.requestOTPValidation = void 0;
const joi_1 = __importDefault(require("joi"));
/**
 * Validation schemas for Authentication
 */
const phoneNumberSchema = joi_1.default.string()
    .pattern(/^\+[1-9]\d{1,14}$/)
    .required()
    .messages({
    'string.pattern.base': 'Phone number must be in E.164 format (e.g., +919876543210)',
    'any.required': 'Phone number is required',
});
const otpSchema = joi_1.default.string()
    .length(6)
    .pattern(/^\d{6}$/)
    .required()
    .messages({
    'string.length': 'OTP must be 6 digits',
    'string.pattern.base': 'OTP must contain only numbers',
    'any.required': 'OTP is required',
});
const requestOTPValidation = (req, res, next) => {
    const { error } = joi_1.default.object({
        phoneNumber: phoneNumberSchema,
    }).validate(req.body);
    if (error) {
        return res.status(400).json({ message: error.details[0]?.message || 'Validation error' });
    }
    next();
};
exports.requestOTPValidation = requestOTPValidation;
const verifyOTPValidation = (req, res, next) => {
    const { error } = joi_1.default.object({
        phoneNumber: phoneNumberSchema,
        otp: otpSchema,
    }).validate(req.body);
    if (error) {
        return res.status(400).json({ message: error.details[0]?.message || 'Validation error' });
    }
    next();
};
exports.verifyOTPValidation = verifyOTPValidation;
//# sourceMappingURL=authValid.js.map
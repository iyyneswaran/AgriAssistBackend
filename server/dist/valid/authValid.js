"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.verifyOTPValidation = exports.requestOTPValidation = void 0;
const zod_1 = require("zod");
/**
 * Common Zod validation middleware
 */
const validate = (schema) => async (req, res, next) => {
    try {
        await schema.parseAsync({
            body: req.body,
            query: req.query,
            params: req.params,
        });
        return next();
    }
    catch (error) {
        return res.status(400).json({
            message: "Validation failed",
            errors: error.errors || error.message
        });
    }
};
/**
 * Validation schemas for Authentication
 */
const phoneNumberSchema = zod_1.z.string()
    .regex(/^\+[1-9]\d{1,14}$/, "Phone number must be in E.164 format (e.g., +919876543210)");
const otpSchema = zod_1.z.string()
    .length(6, "OTP must be 6 digits")
    .regex(/^\d{6}$/, "OTP must contain only numbers");
exports.requestOTPValidation = validate(zod_1.z.object({
    body: zod_1.z.object({
        phoneNumber: phoneNumberSchema,
    })
}));
exports.verifyOTPValidation = validate(zod_1.z.object({
    body: zod_1.z.object({
        phoneNumber: phoneNumberSchema,
        otp: otpSchema,
    })
}));
//# sourceMappingURL=authValid.js.map
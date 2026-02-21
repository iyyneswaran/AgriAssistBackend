import { z, ZodObject } from 'zod';
import { Request, Response, NextFunction } from 'express';

/**
 * Common Zod validation middleware
 */
const validate = (schema: ZodObject<any>) => async (req: Request, res: Response, next: NextFunction) => {
    try {
        await schema.parseAsync({
            body: req.body,
            query: req.query,
            params: req.params,
        });
        return next();
    } catch (error: any) {
        return res.status(400).json({
            message: "Validation failed",
            errors: error.errors || error.message
        });
    }
};

/**
 * Validation schemas for Authentication
 */
const phoneNumberSchema = z.string()
    .regex(/^\+[1-9]\d{1,14}$/, "Phone number must be in E.164 format (e.g., +919876543210)");

const otpSchema = z.string()
    .length(6, "OTP must be 6 digits")
    .regex(/^\d{6}$/, "OTP must contain only numbers");

export const requestOTPValidation = validate(z.object({
    body: z.object({
        phoneNumber: phoneNumberSchema,
    })
}));

export const verifyOTPValidation = validate(z.object({
    body: z.object({
        phoneNumber: phoneNumberSchema,
        otp: otpSchema,
    })
}));

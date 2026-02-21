import { z, ZodObject } from 'zod';
import { Request, Response, NextFunction } from 'express';

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

export const updateProfileValidation = validate(z.object({
    body: z.object({
        name: z.string().min(2).optional(),
        interface: z.enum(['HELPLINE', 'SOFTWARE', 'SOFTWARE_WITH_HARDWARE']).optional()
    })
}));

export const requestMobileUpdateValidation = validate(z.object({
    body: z.object({
        newPhoneNumber: z.string().regex(/^\+[1-9]\d{1,14}$/, "Invalid phone number format (must be E.164, e.g., +919876543210)")
    })
}));

export const verifyMobileUpdateValidation = validate(z.object({
    body: z.object({
        newPhoneNumber: z.string().regex(/^\+[1-9]\d{1,14}$/),
        otp: z.string().length(6, "OTP must be 6 digits")
    })
}));

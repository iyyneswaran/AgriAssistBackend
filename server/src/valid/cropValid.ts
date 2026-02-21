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

export const CropAssignmentStatusEnum = z.enum(['ACTIVE', 'COMPLETED', 'FAILED']);

export const assignCropValidation = validate(z.object({
    body: z.object({
        fieldId: z.string().uuid("Invalid field ID"),
        cropId: z.string().uuid("Invalid crop ID"),
        sowingDate: z.string().datetime().or(z.date())
    })
}));

export const updateAssignmentStatusValidation = validate(z.object({
    body: z.object({
        status: CropAssignmentStatusEnum
    }),
    params: z.object({
        id: z.string().uuid("Invalid assignment ID")
    })
}));

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

export const AreaUnitEnum = z.enum(['HECTARE', 'ACRE', 'GROUND', 'CENT']);

export const registerLandValidation = validate(z.object({
    body: z.object({
        name: z.string().min(2, "Land name must be at least 2 characters"),
        totalArea: z.number().positive("Area must be positive"),
        areaUnit: AreaUnitEnum,
        soilType: z.string().min(2, "Soil type is required"),
        latitude: z.number().min(-90).max(90),
        longitude: z.number().min(-180).max(180),
        district: z.string().min(2, "District is required"),
        state: z.string().min(2, "State is required"),
        preferredLanguage: z.string().default("en"),
        notificationPref: z.string().default("PUSH")
    })
}));

export const updateLandValidation = validate(z.object({
    body: z.object({
        name: z.string().min(2).optional(),
        totalArea: z.number().positive().optional(),
        areaUnit: AreaUnitEnum.optional(),
        soilType: z.string().min(2).optional(),
        latitude: z.number().min(-90).max(90).optional(),
        longitude: z.number().min(-180).max(180).optional(),
        district: z.string().min(2).optional(),
        state: z.string().min(2).optional(),
    })
}));

export const fieldValidation = validate(z.object({
    body: z.object({
        name: z.string().min(2),
        area: z.number().positive().optional(),
        unit: AreaUnitEnum.optional()
    })
}));

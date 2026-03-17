"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.fieldValidation = exports.updateLandValidation = exports.registerLandValidation = exports.AreaUnitEnum = void 0;
const zod_1 = require("zod");
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
exports.AreaUnitEnum = zod_1.z.enum(['HECTARE', 'ACRE', 'GROUND', 'CENT']);
exports.registerLandValidation = validate(zod_1.z.object({
    body: zod_1.z.object({
        name: zod_1.z.string().min(2, "Land name must be at least 2 characters"),
        totalArea: zod_1.z.number().positive("Area must be positive"),
        areaUnit: exports.AreaUnitEnum,
        soilType: zod_1.z.string().min(2, "Soil type is required"),
        latitude: zod_1.z.number().min(-90).max(90),
        longitude: zod_1.z.number().min(-180).max(180),
        district: zod_1.z.string().min(2, "District is required"),
        state: zod_1.z.string().min(2, "State is required"),
        preferredLanguage: zod_1.z.string().default("en"),
        notificationPref: zod_1.z.string().default("PUSH")
    })
}));
exports.updateLandValidation = validate(zod_1.z.object({
    body: zod_1.z.object({
        name: zod_1.z.string().min(2).optional(),
        totalArea: zod_1.z.number().positive().optional(),
        areaUnit: exports.AreaUnitEnum.optional(),
        soilType: zod_1.z.string().min(2).optional(),
        latitude: zod_1.z.number().min(-90).max(90).optional(),
        longitude: zod_1.z.number().min(-180).max(180).optional(),
        district: zod_1.z.string().min(2).optional(),
        state: zod_1.z.string().min(2).optional(),
    })
}));
exports.fieldValidation = validate(zod_1.z.object({
    body: zod_1.z.object({
        name: zod_1.z.string().min(2),
        area: zod_1.z.number().positive().optional(),
        unit: exports.AreaUnitEnum.optional()
    })
}));
//# sourceMappingURL=landValid.js.map
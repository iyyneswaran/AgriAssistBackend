"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.updateAssignmentStatusValidation = exports.assignCropValidation = exports.CropAssignmentStatusEnum = void 0;
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
exports.CropAssignmentStatusEnum = zod_1.z.enum(['ACTIVE', 'COMPLETED', 'FAILED']);
exports.assignCropValidation = validate(zod_1.z.object({
    body: zod_1.z.object({
        fieldId: zod_1.z.string().uuid("Invalid field ID"),
        cropId: zod_1.z.string().uuid("Invalid crop ID"),
        sowingDate: zod_1.z.string().datetime().or(zod_1.z.date())
    })
}));
exports.updateAssignmentStatusValidation = validate(zod_1.z.object({
    body: zod_1.z.object({
        status: exports.CropAssignmentStatusEnum
    }),
    params: zod_1.z.object({
        id: zod_1.z.string().uuid("Invalid assignment ID")
    })
}));
//# sourceMappingURL=cropValid.js.map
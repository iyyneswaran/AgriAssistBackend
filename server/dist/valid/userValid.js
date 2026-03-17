"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.verifyMobileUpdateValidation = exports.requestMobileUpdateValidation = exports.updateProfileValidation = void 0;
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
exports.updateProfileValidation = validate(zod_1.z.object({
    body: zod_1.z.object({
        name: zod_1.z.string().min(2).optional(),
        interface: zod_1.z.enum(['HELPLINE', 'SOFTWARE', 'SOFTWARE_WITH_HARDWARE']).optional()
    })
}));
exports.requestMobileUpdateValidation = validate(zod_1.z.object({
    body: zod_1.z.object({
        newPhoneNumber: zod_1.z.string().regex(/^\+[1-9]\d{1,14}$/, "Invalid phone number format (must be E.164, e.g., +919876543210)")
    })
}));
exports.verifyMobileUpdateValidation = validate(zod_1.z.object({
    body: zod_1.z.object({
        newPhoneNumber: zod_1.z.string().regex(/^\+[1-9]\d{1,14}$/),
        otp: zod_1.z.string().length(6, "OTP must be 6 digits")
    })
}));
//# sourceMappingURL=userValid.js.map
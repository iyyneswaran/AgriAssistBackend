"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.addMessageValidation = exports.startConversationValidation = exports.conversationIdValidation = exports.paginationValidation = void 0;
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
exports.paginationValidation = validate(zod_1.z.object({
    query: zod_1.z.object({
        page: zod_1.z.string().optional().transform(val => val ? parseInt(val, 10) : 1),
        limit: zod_1.z.string().optional().transform(val => val ? parseInt(val, 10) : 20),
        fieldId: zod_1.z.string().uuid().optional(),
        cropAssignmentId: zod_1.z.string().uuid().optional()
    })
}));
exports.conversationIdValidation = validate(zod_1.z.object({
    params: zod_1.z.object({
        conversationId: zod_1.z.string().uuid("Invalid conversation ID")
    })
}));
exports.startConversationValidation = validate(zod_1.z.object({
    body: zod_1.z.object({
        fieldId: zod_1.z.string().uuid().optional(),
        cropAssignmentId: zod_1.z.string().uuid().optional()
    })
}));
exports.addMessageValidation = validate(zod_1.z.object({
    body: zod_1.z.object({
        sender: zod_1.z.enum(['USER', 'AI', 'SYSTEM']).optional(),
        messageType: zod_1.z.enum(['TEXT', 'IMAGE', 'DOCUMENT', 'VOICE']).optional(),
        language: zod_1.z.string().optional(),
        textContent: zod_1.z.string().optional(),
        filePath: zod_1.z.string().optional(),
        fileName: zod_1.z.string().optional(),
        mimeType: zod_1.z.string().optional(),
        fileSizeBytes: zod_1.z.number().optional()
    })
}).refine(data => data.body.textContent || data.body.filePath, {
    message: "Either textContent or filePath must be provided",
    path: ["body"]
}));
//# sourceMappingURL=chatValid.js.map
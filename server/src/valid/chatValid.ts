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

export const paginationValidation = validate(z.object({
    query: z.object({
        page: z.string().optional().transform(val => val ? parseInt(val, 10) : 1),
        limit: z.string().optional().transform(val => val ? parseInt(val, 10) : 20),
        fieldId: z.string().uuid().optional(),
        cropAssignmentId: z.string().uuid().optional()
    })
}));

export const conversationIdValidation = validate(z.object({
    params: z.object({
        conversationId: z.string().uuid("Invalid conversation ID")
    })
}));

export const startConversationValidation = validate(z.object({
    body: z.object({
        fieldId: z.string().uuid().optional(),
        cropAssignmentId: z.string().uuid().optional()
    })
}));

export const addMessageValidation = validate(z.object({
    body: z.object({
        sender: z.enum(['USER', 'AI', 'SYSTEM']).optional(),
        messageType: z.enum(['TEXT', 'IMAGE', 'DOCUMENT', 'VOICE']).optional(),
        language: z.string().optional(),
        textContent: z.string().optional(),
        filePath: z.string().optional(),
        fileName: z.string().optional(),
        mimeType: z.string().optional(),
        fileSizeBytes: z.number().optional()
    })
}).refine(data => data.body.textContent || data.body.filePath, {
    message: "Either textContent or filePath must be provided",
    path: ["body"]
}));

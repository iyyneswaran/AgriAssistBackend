import { Request, Response, NextFunction } from 'express';
import { ZodError } from 'zod';

/**
 * Global Error Handler
 * Standardizes error responses across the application.
 */
export const errorMiddleware = (err: any, req: Request, res: Response, next: NextFunction) => {
    console.error(`[Error] ${req.method} ${req.url}:`, err);

    // Handle Zod Validation Errors
    if (err instanceof ZodError) {
        return res.status(400).json({
            message: "Validation failed",
            errors: err.issues
        });
    }

    // Handle Custom Errors (if any)
    const statusCode = err.status || err.statusCode || 500;
    const message = err.message || "Internal Server Error";

    res.status(statusCode).json({
        message,
        // Only include stack trace in development
        stack: process.env.NODE_ENV === 'development' ? err.stack : undefined
    });
};

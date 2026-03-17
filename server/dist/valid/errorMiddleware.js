"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.errorMiddleware = void 0;
const zod_1 = require("zod");
/**
 * Global Error Handler
 * Standardizes error responses across the application.
 */
const errorMiddleware = (err, req, res, next) => {
    console.error(`[Error] ${req.method} ${req.url}:`, err);
    // Handle Zod Validation Errors
    if (err instanceof zod_1.ZodError) {
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
exports.errorMiddleware = errorMiddleware;
//# sourceMappingURL=errorMiddleware.js.map
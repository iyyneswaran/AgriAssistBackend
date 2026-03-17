import { Request, Response, NextFunction } from 'express';
/**
 * Global Error Handler
 * Standardizes error responses across the application.
 */
export declare const errorMiddleware: (err: any, req: Request, res: Response, next: NextFunction) => Response<any, Record<string, any>> | undefined;
//# sourceMappingURL=errorMiddleware.d.ts.map
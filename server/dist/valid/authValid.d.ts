import { Request, Response, NextFunction } from 'express';
export declare const requestOTPValidation: (req: Request, res: Response, next: NextFunction) => Promise<void | Response<any, Record<string, any>>>;
export declare const verifyOTPValidation: (req: Request, res: Response, next: NextFunction) => Promise<void | Response<any, Record<string, any>>>;
//# sourceMappingURL=authValid.d.ts.map
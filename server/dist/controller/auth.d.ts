import { Request, Response } from 'express';
/**
 * Request OTP for authentication.
 * If user doesn't exist, it still sends OTP to prevent account enumeration
 * (though in a prototype/startup context, we usually just send it).
 */
export declare const requestOTP: (req: Request, res: Response) => Promise<void>;
/**
 * Verify OTP and handle Login/Signup.
 */
export declare const verifyOTP: (req: Request, res: Response) => Promise<Response<any, Record<string, any>> | undefined>;
/**
 * Standard Token Refresh
 */
export declare const refresh: (req: Request, res: Response) => Promise<Response<any, Record<string, any>> | undefined>;
declare const _default: {
    requestOTP: (req: Request, res: Response) => Promise<void>;
    verifyOTP: (req: Request, res: Response) => Promise<Response<any, Record<string, any>> | undefined>;
    refresh: (req: Request, res: Response) => Promise<Response<any, Record<string, any>> | undefined>;
};
export default _default;
//# sourceMappingURL=auth.d.ts.map
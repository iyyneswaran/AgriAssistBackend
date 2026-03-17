import { Request, Response } from 'express';
/**
 * Update User Profile (Name, Interface)
 */
export declare const updateProfile: (req: Request, res: Response) => Promise<void>;
/**
 * Get current user profile
 */
export declare const getProfile: (req: Request, res: Response) => Promise<Response<any, Record<string, any>> | undefined>;
/**
 * Request OTP to update mobile number
 * Sends OTP to the NEW number
 */
export declare const requestMobileUpdate: (req: Request, res: Response) => Promise<Response<any, Record<string, any>> | undefined>;
/**
 * Verify OTP and update mobile number
 */
export declare const verifyMobileUpdate: (req: Request, res: Response) => Promise<Response<any, Record<string, any>> | undefined>;
//# sourceMappingURL=userController.d.ts.map
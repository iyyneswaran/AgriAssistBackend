import { Request, Response } from 'express';
/**
 * Register Land for a Farmer
 * Enforces "One Land per Farmer" rule.
 */
export declare const registerLand: (req: Request, res: Response) => Promise<Response<any, Record<string, any>> | undefined>;
/**
 * Get Farmer's Land details
 */
export declare const getMyLand: (req: Request, res: Response) => Promise<Response<any, Record<string, any>> | undefined>;
/**
 * Update Land details
 */
export declare const updateLand: (req: Request, res: Response) => Promise<Response<any, Record<string, any>> | undefined>;
//# sourceMappingURL=landController.d.ts.map
import { Request, Response } from 'express';
/**
 * Add a Field to Land
 */
export declare const addField: (req: Request, res: Response) => Promise<Response<any, Record<string, any>> | undefined>;
/**
 * Get all Fields for my Land
 */
export declare const getMyFields: (req: Request, res: Response) => Promise<void>;
/**
 * Delete a Field
 */
export declare const deleteField: (req: Request, res: Response) => Promise<Response<any, Record<string, any>> | undefined>;
//# sourceMappingURL=fieldController.d.ts.map
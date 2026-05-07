import { Request, Response } from 'express';
/**
 * List all available reference crops
 */
export declare const listCrops: (req: Request, res: Response) => Promise<Response<any, Record<string, any>> | undefined>;
/**
 * Assign a crop to a field (Start a cultivation cycle)
 */
export declare const assignCrop: (req: Request, res: Response) => Promise<Response<any, Record<string, any>> | undefined>;
/**
 * Update assignment status (Mark as COMPLETED/FAILED)
 */
export declare const updateAssignmentStatus: (req: Request, res: Response) => Promise<Response<any, Record<string, any>> | undefined>;
/**
 * Get current active assignments for the farmer
 */
export declare const getMyActiveAssignments: (req: Request, res: Response) => Promise<void>;
//# sourceMappingURL=cropController.d.ts.map
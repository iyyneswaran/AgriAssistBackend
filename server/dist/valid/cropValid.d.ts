import { z } from 'zod';
import { Request, Response, NextFunction } from 'express';
export declare const CropAssignmentStatusEnum: z.ZodEnum<{
    ACTIVE: "ACTIVE";
    COMPLETED: "COMPLETED";
    FAILED: "FAILED";
}>;
export declare const assignCropValidation: (req: Request, res: Response, next: NextFunction) => Promise<void | Response<any, Record<string, any>>>;
export declare const updateAssignmentStatusValidation: (req: Request, res: Response, next: NextFunction) => Promise<void | Response<any, Record<string, any>>>;
//# sourceMappingURL=cropValid.d.ts.map
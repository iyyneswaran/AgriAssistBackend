import { z } from 'zod';
import { Request, Response, NextFunction } from 'express';
export declare const AreaUnitEnum: z.ZodEnum<{
    HECTARE: "HECTARE";
    ACRE: "ACRE";
    GROUND: "GROUND";
    CENT: "CENT";
}>;
export declare const registerLandValidation: (req: Request, res: Response, next: NextFunction) => Promise<void | Response<any, Record<string, any>>>;
export declare const updateLandValidation: (req: Request, res: Response, next: NextFunction) => Promise<void | Response<any, Record<string, any>>>;
export declare const fieldValidation: (req: Request, res: Response, next: NextFunction) => Promise<void | Response<any, Record<string, any>>>;
//# sourceMappingURL=landValid.d.ts.map
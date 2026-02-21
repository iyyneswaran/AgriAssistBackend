import { Request, Response, NextFunction } from 'express';
export declare const signAccessToken: (user: any) => string;
export declare const signRefreshToken: (user: any) => string;
export declare const verifyAccessToken: (req: Request, res: Response, next: NextFunction) => Response<any, Record<string, any>> | undefined;
export declare const verifyRefreshToken: (req: Request, res: Response, next: NextFunction) => Response<any, Record<string, any>> | undefined;
//# sourceMappingURL=jwt.d.ts.map
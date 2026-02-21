import { Request, Response, NextFunction } from 'express';
declare const authorizeRole: (...allowedRoles: string[]) => (req: Request, res: Response, next: NextFunction) => Response<any, Record<string, any>> | undefined;
export default authorizeRole;
//# sourceMappingURL=role.d.ts.map
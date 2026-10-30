import { Request, Response, NextFunction } from 'express';
import { IncomingMessage } from 'http';
export declare function publicVoiceUrl(path: string): string;
export declare function validTwilioSignature(req: IncomingMessage, path: string, params?: Record<string, any>, websocket?: boolean): boolean;
export declare function verifyTwilioWebhook(req: Request, res: Response, next: NextFunction): Response<any, Record<string, any>> | undefined;
export declare function ownPhone(req: Request, res: Response, next: NextFunction): Response<any, Record<string, any>> | undefined;
//# sourceMappingURL=security.d.ts.map
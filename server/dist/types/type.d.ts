export {};
declare global {
    namespace Express {
        interface Request {
            user?: any;
        }
    }
}
export interface Payload {
    id: string;
    phoneNumber?: string;
    role?: string;
    email?: string;
}
//# sourceMappingURL=type.d.ts.map
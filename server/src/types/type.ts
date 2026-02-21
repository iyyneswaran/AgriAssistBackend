export { };

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
    email?: string; // Keep for compatibility if needed, but primarily using phoneNumber
}


import jwt from 'jsonwebtoken';
import { Request, Response, NextFunction } from 'express';
import { db } from '../db';
import { Payload } from '../types/type'


export const signAccessToken = (user: any) => {
    if (!process.env.JWT_SECRET) {
        throw new Error('JWT_SECRET is not defined');
    }
    return jwt.sign(
        { id: user.id, phoneNumber: user.phoneNumber, role: user.role },
        process.env.JWT_SECRET,
        { expiresIn: '6h', algorithm: 'HS256' }
    );
};

export const signRefreshToken = (user: any) => {
    if (!process.env.JWT_SECRET) {
        throw new Error('JWT_SECRET is not defined');
    }
    return jwt.sign(
        { id: user.id },
        process.env.JWT_SECRET,
        { expiresIn: '6h', algorithm: 'HS256' }
    );
};

export const verifyAccessToken = (req: Request, res: Response, next: NextFunction) => {
    const authHeader = req.headers.authorization;
    if (!authHeader) {
        return res.status(401).json({ message: "Missing token" });
    }

    const parts = authHeader.split(/\s+/);
    if (parts.length !== 2 || parts[0] !== 'Bearer') {
        return res.status(401).json({ message: "Invalid authorization header format" });
    }

    const token = parts[1];

    if (!process.env.JWT_SECRET) {
        return res.status(500).json({ message: "JWT_SECRET not configured" });
    }

    jwt.verify(token as string, process.env.JWT_SECRET as string, { algorithms: ['HS256'] }, async (err: any, decoded: any) => {
        if (err) {
            return res.status(403).json({ message: `Invalid Token: ${err.message}` });
        }
        try {
            const payload = decoded as Payload;
            const user = await db.user.findUnique({
                where: { id: payload.id },
                select: { id: true, name: true, phoneNumber: true, role: true }
            });

            if (!user) {
                return res.status(404).json({ message: "User Not Found or Token Expired" });
            }

            req.user = user;
            next();
        } catch (e) {
            next(e);
        }
    });
};


export const verifyRefreshToken = (req: Request, res: Response, next: NextFunction) => {

    const token: string = req.cookies.refreshToken;
    if (!token) {
        return res.status(401).json({ message: "Missing token" });
    }

    if (!process.env.JWT_SECRET) {
        return res.status(500).json({ message: "JWT_SECRET not configured" });
    }

    jwt.verify(token as string, process.env.JWT_SECRET as string, { algorithms: ['HS256'] }, async (err: any, decoded: any) => {
        if (err) {
            return res.status(403).json({ message: `Invalid RefreshToken: ${err.message}` });
        }
        try {
            const payload = decoded as Payload;
            const user = await db.user.findUnique({
                where: { id: payload.id },
                select: { id: true, name: true, phoneNumber: true, role: true }
            });

            if (!user) {
                return res.status(404).json({ message: "User RefreshToken Not Found or RefreshToken Expired" });

            }

            req.user = user;
            next();
        } catch (e) {
            next(e);
        }
    });
};
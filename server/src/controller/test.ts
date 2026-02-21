import { Request, Response } from 'express';

export const protectedTest = async (req: Request, res: Response) => {
    res.status(200).json({
        message: "You have accessed a protected route!",
        user: req.user
    });
};

export const adminTest = async (req: Request, res: Response) => {
    const user = req.user;
    if (user.role !== 'ADMIN') {
        return res.status(403).json({ message: "Access denied. Admin role required." });
    }
    res.status(200).json({
        message: "Welcome, Admin!",
        user: user
    });
};

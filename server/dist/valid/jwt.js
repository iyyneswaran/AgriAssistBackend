"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.verifyRefreshToken = exports.verifyAccessToken = exports.signRefreshToken = exports.signAccessToken = void 0;
const jsonwebtoken_1 = __importDefault(require("jsonwebtoken"));
const db_1 = require("../db");
const signAccessToken = (user) => {
    if (!process.env.JWT_SECRET) {
        throw new Error('JWT_SECRET is not defined');
    }
    return jsonwebtoken_1.default.sign({ id: user.id, phoneNumber: user.phoneNumber, role: user.role }, process.env.JWT_SECRET, { expiresIn: '6h', algorithm: 'HS256' });
};
exports.signAccessToken = signAccessToken;
const signRefreshToken = (user) => {
    if (!process.env.JWT_SECRET) {
        throw new Error('JWT_SECRET is not defined');
    }
    return jsonwebtoken_1.default.sign({ id: user.id }, process.env.JWT_SECRET, { expiresIn: '6h', algorithm: 'HS256' });
};
exports.signRefreshToken = signRefreshToken;
const verifyAccessToken = (req, res, next) => {
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
    jsonwebtoken_1.default.verify(token, process.env.JWT_SECRET, { algorithms: ['HS256'] }, async (err, decoded) => {
        if (err) {
            return res.status(403).json({ message: `Invalid Token: ${err.message}` });
        }
        try {
            const payload = decoded;
            const user = await db_1.db.user.findUnique({
                where: { id: payload.id },
                select: { id: true, name: true, phoneNumber: true, role: true }
            });
            if (!user) {
                return res.status(404).json({ message: "User Not Found or Token Expired" });
            }
            req.user = user;
            next();
        }
        catch (e) {
            next(e);
        }
    });
};
exports.verifyAccessToken = verifyAccessToken;
const verifyRefreshToken = (req, res, next) => {
    const token = req.cookies.refreshToken;
    if (!token) {
        return res.status(401).json({ message: "Missing token" });
    }
    if (!process.env.JWT_SECRET) {
        return res.status(500).json({ message: "JWT_SECRET not configured" });
    }
    jsonwebtoken_1.default.verify(token, process.env.JWT_SECRET, { algorithms: ['HS256'] }, async (err, decoded) => {
        if (err) {
            return res.status(403).json({ message: `Invalid RefreshToken: ${err.message}` });
        }
        try {
            const payload = decoded;
            const user = await db_1.db.user.findUnique({
                where: { id: payload.id },
                select: { id: true, name: true, phoneNumber: true, role: true }
            });
            if (!user) {
                return res.status(404).json({ message: "User RefreshToken Not Found or RefreshToken Expired" });
            }
            req.user = user;
            next();
        }
        catch (e) {
            next(e);
        }
    });
};
exports.verifyRefreshToken = verifyRefreshToken;
//# sourceMappingURL=jwt.js.map
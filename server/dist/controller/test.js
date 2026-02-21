"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.adminTest = exports.protectedTest = void 0;
const protectedTest = async (req, res) => {
    res.status(200).json({
        message: "You have accessed a protected route!",
        user: req.user
    });
};
exports.protectedTest = protectedTest;
const adminTest = async (req, res) => {
    const user = req.user;
    if (user.role !== 'ADMIN') {
        return res.status(403).json({ message: "Access denied. Admin role required." });
    }
    res.status(200).json({
        message: "Welcome, Admin!",
        user: user
    });
};
exports.adminTest = adminTest;
//# sourceMappingURL=test.js.map
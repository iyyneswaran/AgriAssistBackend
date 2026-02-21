"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const authorizeRole = (...allowedRoles) => {
    return (req, res, next) => {
        if (!req.user || !allowedRoles.includes(req.user.role)) {
            return res.status(403).json({ message: "Access denied" });
        }
        next();
    };
};
exports.default = authorizeRole;
//# sourceMappingURL=role.js.map
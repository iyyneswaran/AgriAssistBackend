"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AuditLogger = void 0;
const db_1 = require("../db");
/**
 * Audit Logger Service
 * Records system actions in the audit_logs table.
 */
exports.AuditLogger = {
    /**
     * Log a governance action
     * @param userId ID of the user performing the action
     * @param action Description of the action (e.g., LAND_REGISTERED)
     */
    log: async (userId, action) => {
        try {
            await db_1.db.auditLog.create({
                data: {
                    userId,
                    action
                }
            });
        }
        catch (err) {
            console.error("[AuditLogger] Failed to create audit log:", err);
            // We don't throw here to avoid failing the main request if logging fails
        }
    }
};
//# sourceMappingURL=auditLogger.js.map
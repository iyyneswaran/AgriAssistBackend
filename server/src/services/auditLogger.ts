import { db } from '../db';

/**
 * Audit Logger Service
 * Records system actions in the audit_logs table.
 */
export const AuditLogger = {
    /**
     * Log a governance action
     * @param userId ID of the user performing the action
     * @param action Description of the action (e.g., LAND_REGISTERED)
     */
    log: async (userId: string, action: string) => {
        try {
            await db.auditLog.create({
                data: {
                    userId,
                    action
                }
            });
        } catch (err) {
            console.error("[AuditLogger] Failed to create audit log:", err);
            // We don't throw here to avoid failing the main request if logging fails
        }
    }
};

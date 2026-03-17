/**
 * Audit Logger Service
 * Records system actions in the audit_logs table.
 */
export declare const AuditLogger: {
    /**
     * Log a governance action
     * @param userId ID of the user performing the action
     * @param action Description of the action (e.g., LAND_REGISTERED)
     */
    log: (userId: string, action: string) => Promise<void>;
};
//# sourceMappingURL=auditLogger.d.ts.map
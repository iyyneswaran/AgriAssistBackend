"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.deleteField = exports.getMyFields = exports.addField = void 0;
const db_1 = require("../db");
const areaConverter_1 = require("../services/areaConverter");
const auditLogger_1 = require("../services/auditLogger");
/**
 * Add a Field to Land
 */
const addField = async (req, res) => {
    try {
        const user = req.user;
        const { name, area, areaUnit } = req.body;
        // 1. Verify land ownership
        const land = await db_1.db.land.findFirst({
            where: { farmer: { userId: user.id } }
        });
        if (!land) {
            return res.status(404).json({ message: "You must register a land before adding fields" });
        }
        // 2. Default area to Land's total area if not provided
        let fieldHectares;
        if (area && areaUnit) {
            fieldHectares = (0, areaConverter_1.convertToHectares)(area, areaUnit);
        }
        else {
            fieldHectares = Number(land.totalArea);
        }
        // 3. Create Field
        const field = await db_1.db.field.create({
            data: {
                landId: land.id,
                name,
                area: fieldHectares
            }
        });
        // 4. Audit Log
        await auditLogger_1.AuditLogger.log(user.id, "FIELD_ADDED");
        res.status(201).json({
            message: "Field added successfully",
            field
        });
    }
    catch (err) {
        res.status(500).json({ message: `Failed to add field: ${err.message}` });
    }
};
exports.addField = addField;
/**
 * Get all Fields for my Land
 */
const getMyFields = async (req, res) => {
    try {
        const user = req.user;
        const fields = await db_1.db.field.findMany({
            where: { land: { farmer: { userId: user.id } } },
            include: { crops: { where: { status: 'ACTIVE' } } }
        });
        res.status(200).json(fields);
    }
    catch (err) {
        res.status(500).json({ message: `Failed to retrieve fields: ${err.message}` });
    }
};
exports.getMyFields = getMyFields;
/**
 * Delete a Field
 */
const deleteField = async (req, res) => {
    try {
        const user = req.user;
        const { id } = req.params;
        // Verify ownership before delete
        const field = await db_1.db.field.findFirst({
            where: {
                id: id,
                land: { farmer: { userId: user.id } }
            }
        });
        if (!field) {
            return res.status(404).json({ message: "Field not found or access denied" });
        }
        await db_1.db.field.delete({
            where: { id: id }
        });
        // Audit Log
        await auditLogger_1.AuditLogger.log(user.id, "FIELD_DELETED");
        res.status(200).json({ message: "Field deleted successfully" });
    }
    catch (err) {
        res.status(500).json({ message: `Failed to delete field: ${err.message}` });
    }
};
exports.deleteField = deleteField;
//# sourceMappingURL=fieldController.js.map
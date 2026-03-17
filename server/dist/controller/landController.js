"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.updateLand = exports.getMyLand = exports.registerLand = void 0;
const db_1 = require("../db");
const areaConverter_1 = require("../services/areaConverter");
const auditLogger_1 = require("../services/auditLogger");
/**
 * Register Land for a Farmer
 * Enforces "One Land per Farmer" rule.
 */
const registerLand = async (req, res) => {
    try {
        const user = req.user;
        const { name, totalArea, areaUnit, soilType, latitude, longitude, district, state, corners, plantedCropManual, preferredLanguage, notificationPref } = req.body;
        // Check if user is a farmer (role already verified by middleware, but good to be explicit)
        if (user.role !== 'FARMER') {
            return res.status(403).json({ message: "Only Farmers can register land" });
        }
        // 1. Get or Create Farmer record
        let farmer = await db_1.db.farmer.findUnique({
            where: { userId: user.id }
        });
        if (!farmer) {
            farmer = await db_1.db.farmer.create({
                data: {
                    userId: user.id,
                    preferredLanguage: preferredLanguage || "en",
                    notificationPref: notificationPref || "PUSH"
                }
            });
        }
        // 2. Check if land already exists for this farmer
        const existingLand = await db_1.db.land.findUnique({
            where: { farmerId: farmer.id }
        });
        if (existingLand) {
            return res.status(400).json({ message: "Farmer already has a registered land. Only one land per farmer allowed." });
        }
        // 3. Convert Area to Hectares
        const hectares = (0, areaConverter_1.convertToHectares)(totalArea, areaUnit);
        // 4. Create Land
        const land = await db_1.db.land.create({
            data: {
                farmerId: farmer.id,
                name,
                totalArea: hectares,
                soilType,
                latitude,
                longitude,
                district,
                state,
                corners,
                plantedCropManual
            }
        });
        // 5. Audit Log
        await auditLogger_1.AuditLogger.log(user.id, "LAND_REGISTERED");
        res.status(201).json({
            message: "Land registered successfully",
            land
        });
    }
    catch (err) {
        res.status(500).json({ message: `Failed to register land: ${err.message}` });
    }
};
exports.registerLand = registerLand;
/**
 * Get Farmer's Land details
 */
const getMyLand = async (req, res) => {
    try {
        const user = req.user;
        const land = await db_1.db.land.findFirst({
            where: { farmer: { userId: user.id } },
            include: { fields: true }
        });
        if (!land) {
            return res.status(404).json({ message: "No land registered for this user" });
        }
        res.status(200).json(land);
    }
    catch (err) {
        res.status(500).json({ message: `Failed to retrieve land: ${err.message}` });
    }
};
exports.getMyLand = getMyLand;
/**
 * Update Land details
 */
const updateLand = async (req, res) => {
    try {
        const user = req.user;
        const updateData = req.body;
        const land = await db_1.db.land.findFirst({
            where: { farmer: { userId: user.id } }
        });
        if (!land) {
            return res.status(404).json({ message: "Land not found" });
        }
        // If area/unit is updated, recalculate hectares
        if (updateData.totalArea || updateData.areaUnit) {
            const area = updateData.totalArea || land.totalArea;
            const unit = updateData.areaUnit || 'HECTARE';
            updateData.totalArea = (0, areaConverter_1.convertToHectares)(area, unit);
            delete updateData.areaUnit; // Don't try to save areaUnit to DB
        }
        const updatedLand = await db_1.db.land.update({
            where: { id: land.id },
            data: updateData
        });
        // 3. Audit Log
        await auditLogger_1.AuditLogger.log(user.id, "LAND_UPDATED");
        res.status(200).json({
            message: "Land updated successfully",
            land: updatedLand
        });
    }
    catch (err) {
        res.status(500).json({ message: `Failed to update land: ${err.message}` });
    }
};
exports.updateLand = updateLand;
//# sourceMappingURL=landController.js.map
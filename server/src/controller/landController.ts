import { Request, Response } from 'express';
import { db } from '../db';
import { Payload } from '../types/type';
import { convertToHectares, AreaUnit } from '../services/areaConverter';
import { AuditLogger } from '../services/auditLogger';

/**
 * Register Land for a Farmer
 * Enforces "One Land per Farmer" rule.
 */
export const registerLand = async (req: Request, res: Response) => {
    try {
        const user = req.user as Payload;
        const {
            name, totalArea, areaUnit, soilType,
            latitude, longitude, district, state,
            corners, plantedCropManual,
            preferredLanguage, notificationPref
        } = req.body;

        // Check if user is a farmer (role already verified by middleware, but good to be explicit)
        if (user.role !== 'FARMER') {
            return res.status(403).json({ message: "Only Farmers can register land" });
        }

        // 1. Get or Create Farmer record
        let farmer = await db.farmer.findUnique({
            where: { userId: user.id }
        });

        if (!farmer) {
            farmer = await db.farmer.create({
                data: {
                    userId: user.id,
                    preferredLanguage: preferredLanguage || "en",
                    notificationPref: notificationPref || "PUSH"
                }
            });
        }

        // 2. Check if land already exists for this farmer
        const existingLand = await db.land.findUnique({
            where: { farmerId: farmer.id }
        });

        if (existingLand) {
            return res.status(400).json({ message: "Farmer already has a registered land. Only one land per farmer allowed." });
        }

        // 3. Convert Area to Hectares
        const hectares = convertToHectares(totalArea, areaUnit as AreaUnit);

        // 4. Create Land
        const land = await db.land.create({
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
        await AuditLogger.log(user.id, "LAND_REGISTERED");

        res.status(201).json({
            message: "Land registered successfully",
            land
        });

    } catch (err: any) {
        res.status(500).json({ message: `Failed to register land: ${err.message}` });
    }
};

/**
 * Get Farmer's Land details
 */
export const getMyLand = async (req: Request, res: Response) => {
    try {
        const user = req.user as Payload;

        const land = await db.land.findFirst({
            where: { farmer: { userId: user.id } },
            include: { fields: true }
        });

        if (!land) {
            return res.status(404).json({ message: "No land registered for this user" });
        }

        res.status(200).json(land);
    } catch (err: any) {
        res.status(500).json({ message: `Failed to retrieve land: ${err.message}` });
    }
};

/**
 * Update Land details
 */
export const updateLand = async (req: Request, res: Response) => {
    try {
        const user = req.user as Payload;
        const updateData = req.body;

        const land = await db.land.findFirst({
            where: { farmer: { userId: user.id } }
        });

        if (!land) {
            return res.status(404).json({ message: "Land not found" });
        }

        // If area/unit is updated, recalculate hectares
        if (updateData.totalArea || updateData.areaUnit) {
            const area = updateData.totalArea || land.totalArea;
            const unit = updateData.areaUnit || 'HECTARE';
            updateData.totalArea = convertToHectares(area, unit as AreaUnit);
            delete updateData.areaUnit; // Don't try to save areaUnit to DB
        }

        const updatedLand = await db.land.update({
            where: { id: land.id },
            data: updateData
        });

        // 3. Audit Log
        await AuditLogger.log(user.id, "LAND_UPDATED");

        res.status(200).json({
            message: "Land updated successfully",
            land: updatedLand
        });
    } catch (err: any) {
        res.status(500).json({ message: `Failed to update land: ${err.message}` });
    }
};

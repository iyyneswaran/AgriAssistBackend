import { Request, Response } from 'express';
import { db } from '../db';
import { Payload } from '../types/type';
import { convertToHectares, AreaUnit } from '../services/areaConverter';
import { AuditLogger } from '../services/auditLogger';

/**
 * Add a Field to Land
 */
export const addField = async (req: Request, res: Response) => {
    try {
        const user = req.user as Payload;
        const { name, area, areaUnit } = req.body;

        // 1. Verify land ownership
        const land = await db.land.findFirst({
            where: { farmer: { userId: user.id } }
        });

        if (!land) {
            return res.status(404).json({ message: "You must register a land before adding fields" });
        }

        // 2. Default area to Land's total area if not provided
        let fieldHectares: number;
        if (area && areaUnit) {
            fieldHectares = convertToHectares(area, areaUnit as AreaUnit);
        } else {
            fieldHectares = Number(land.totalArea);
        }

        // 3. Create Field
        const field = await db.field.create({
            data: {
                landId: land.id,
                name,
                area: fieldHectares
            }
        });

        // 4. Audit Log
        await AuditLogger.log(user.id, "FIELD_ADDED");

        res.status(201).json({
            message: "Field added successfully",
            field
        });

    } catch (err: any) {
        res.status(500).json({ message: `Failed to add field: ${err.message}` });
    }
};

/**
 * Get all Fields for my Land
 */
export const getMyFields = async (req: Request, res: Response) => {
    try {
        const user = req.user as Payload;

        const fields = await db.field.findMany({
            where: { land: { farmer: { userId: user.id } } },
            include: { crops: { where: { status: 'ACTIVE' } } }
        });

        res.status(200).json(fields);
    } catch (err: any) {
        res.status(500).json({ message: `Failed to retrieve fields: ${err.message}` });
    }
};

/**
 * Delete a Field
 */
export const deleteField = async (req: Request, res: Response) => {
    try {
        const user = req.user as Payload;
        const { id } = req.params;

        // Verify ownership before delete
        const field = await db.field.findFirst({
            where: {
                id: id as string,
                land: { farmer: { userId: user.id } }
            }
        });

        if (!field) {
            return res.status(404).json({ message: "Field not found or access denied" });
        }

        await db.field.delete({
            where: { id: id as string }
        });

        // Audit Log
        await AuditLogger.log(user.id, "FIELD_DELETED");

        res.status(200).json({ message: "Field deleted successfully" });
    } catch (err: any) {
        res.status(500).json({ message: `Failed to delete field: ${err.message}` });
    }
};

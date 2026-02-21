import { Request, Response } from 'express';
import { db } from '../db';
import { Payload } from '../types/type';
import { AuditLogger } from '../services/auditLogger';

/**
 * List all available reference crops
 */
export const listCrops = async (req: Request, res: Response) => {
    try {
        const crops = await db.crop.findMany({
            orderBy: { name: 'asc' }
        });
        res.status(200).json(crops);
    } catch (err: any) {
        res.status(500).json({ message: `Failed to list crops: ${err.message}` });
    }
};

/**
 * Assign a crop to a field (Start a cultivation cycle)
 */
export const assignCrop = async (req: Request, res: Response) => {
    try {
        const user = req.user as Payload;
        const { fieldId, cropId, sowingDate } = req.body;

        // 1. Verify field ownership
        const field = await db.field.findFirst({
            where: {
                id: fieldId,
                land: { farmer: { userId: user.id } }
            }
        });

        if (!field) {
            return res.status(404).json({ message: "Field not found or access denied" });
        }

        // 2. Fetch crop details for growthDays
        const crop = await db.crop.findUnique({
            where: { id: cropId }
        });

        if (!crop) {
            return res.status(404).json({ message: "Crop type not found" });
        }

        // 3. Calculate Harvest Date (Sowing + GrowthDays)
        const sowing = new Date(sowingDate);
        const harvest = new Date(sowing);
        harvest.setDate(harvest.getDate() + crop.growthDays);

        // 4. Check for existing ACTIVE assignment in this field
        const activeAssignment = await db.cropAssignment.findFirst({
            where: {
                fieldId,
                status: 'ACTIVE'
            }
        });

        if (activeAssignment) {
            return res.status(400).json({
                message: "This field already has an active crop assignment. Complete or fail the current cycle first."
            });
        }

        // 5. Create Assignment
        const assignment = await db.cropAssignment.create({
            data: {
                fieldId,
                cropId,
                sowingDate: sowing,
                harvestDate: harvest,
                status: 'ACTIVE'
            },
            include: { crop: true }
        });

        // 6. Audit Log
        await AuditLogger.log(user.id, `CROP_ASSIGNED_${assignment.crop.name}`);

        res.status(201).json({
            message: "Crop assigned to field successfully",
            assignment
        });

    } catch (err: any) {
        res.status(500).json({ message: `Assignment failed: ${err.message}` });
    }
};

/**
 * Update assignment status (Mark as COMPLETED/FAILED)
 */
export const updateAssignmentStatus = async (req: Request, res: Response) => {
    try {
        const user = req.user as Payload;
        const { id } = req.params;
        const { status } = req.body;

        // 1. Verify ownership via field -> land -> farmer
        const assignment = await db.cropAssignment.findFirst({
            where: {
                id: id as string,
                field: { land: { farmer: { userId: user.id } } }
            }
        });

        if (!assignment) {
            return res.status(404).json({ message: "Assignment not found or access denied" });
        }

        // 2. Update status and set harvestDate if completed
        const updatedAssignment = await db.cropAssignment.update({
            where: { id: id as string },
            data: {
                status,
                harvestDate: status === 'COMPLETED' ? new Date() : null
            }
        });

        // 3. Audit Log
        await AuditLogger.log(user.id, `CROP_STATUS_UPDATED_${status}`);

        res.status(200).json({
            message: `Crop cycle marked as ${status}`,
            assignment: updatedAssignment
        });

    } catch (err: any) {
        res.status(500).json({ message: `Status update failed: ${err.message}` });
    }
};

/**
 * Get current active assignments for the farmer
 */
export const getMyActiveAssignments = async (req: Request, res: Response) => {
    try {
        const user = req.user as Payload;

        const assignments = await db.cropAssignment.findMany({
            where: {
                field: { land: { farmer: { userId: user.id } } },
                status: 'ACTIVE'
            },
            include: {
                field: true,
                crop: true
            }
        });

        res.status(200).json(assignments);
    } catch (err: any) {
        res.status(500).json({ message: `Failed to retrieve assignments: ${err.message}` });
    }
};

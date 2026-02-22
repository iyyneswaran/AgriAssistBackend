import { Request, Response } from 'express';
import { db } from '../db';
import { Payload } from '../types/type';

/**
 * List paginated AI Conversations for the user
 * Optional filtering by field or crop assignment
 */
export const getMyConversations = async (req: Request, res: Response) => {
    try {
        const user = req.user as Payload;
        const { page, limit, fieldId, cropAssignmentId } = req.query as any;

        const pageNum = parseInt(page as string) || 1;
        const limitNum = parseInt(limit as string) || 10;

        const skip = (pageNum - 1) * limitNum;

        const where: any = { userId: user.id };
        if (fieldId) where.fieldId = fieldId;
        if (cropAssignmentId) where.cropAssignmentId = cropAssignmentId;

        const [conversations, total] = await Promise.all([
            db.aIConversation.findMany({
                where,
                skip,
                take: limitNum,
                orderBy: { startedAt: 'desc' },
                include: {
                    field: { select: { name: true } },
                    cropAssignment: { include: { crop: { select: { name: true } } } }
                }
            }),
            db.aIConversation.count({ where })
        ]);

        res.status(200).json({
            data: conversations,
            pagination: {
                total,
                page: pageNum,
                limit: limitNum,
                totalPages: Math.ceil(total / limitNum)
            }
        });

    } catch (err: any) {
        res.status(500).json({ message: `Failed to retrieve conversations: ${err.message}` });
    }
};

/**
 * Get paginated messages for a specific conversation
 */
export const getConversationMessages = async (req: Request, res: Response) => {
    try {
        const user = req.user as Payload;
        const { conversationId } = req.params;
        const { page, limit } = req.query as any;

        const pageNum = parseInt(page as string) || 1;
        const limitNum = parseInt(limit as string) || 10;

        const skip = (pageNum - 1) * limitNum;

        // 1. Verify ownership
        const conversation = await db.aIConversation.findFirst({
            where: {
                id: conversationId as string,
                userId: user.id
            }
        });

        if (!conversation) {
            return res.status(404).json({ message: "Conversation not found or access denied" });
        }

        // 2. Fetch messages
        const [messages, total] = await Promise.all([
            db.aIChatMessage.findMany({
                where: { conversationId: conversationId as string },
                skip,
                take: limitNum,
                orderBy: { createdAt: 'asc' } // Linear chat flow
            }),
            db.aIChatMessage.count({
                where: { conversationId: conversationId as string }
            })
        ]);

        res.status(200).json({
            data: messages,
            pagination: {
                total,
                page: pageNum,
                limit: limitNum,
                totalPages: Math.ceil(total / limitNum)
            }
        });

    } catch (err: any) {
        res.status(500).json({ message: `Failed to retrieve messages: ${err.message}` });
    }
};

/**
 * Start a new AI Conversation (The Folder)
 */
export const startConversation = async (req: Request, res: Response) => {
    try {
        const user = req.user as Payload;
        const { fieldId, cropAssignmentId } = req.body;

        const conversation = await db.aIConversation.create({
            data: {
                userId: user.id,
                fieldId: fieldId || null,
                cropAssignmentId: cropAssignmentId || null,
                status: 'ACTIVE'
            }
        });

        res.status(201).json({
            message: "Conversation started successfully",
            conversation
        });
    } catch (err: any) {
        res.status(500).json({ message: `Failed to start conversation: ${err.message}` });
    }
};

/**
 * Add a message to a conversation (The Message Inside)
 */
export const addMessage = async (req: Request, res: Response) => {
    try {
        const user = req.user as Payload;
        const { conversationId } = req.params;
        const messageData = req.body;

        // 1. Verify ownership of the conversation
        const conversation = await db.aIConversation.findFirst({
            where: {
                id: conversationId as string,
                userId: user.id
            }
        });

        if (!conversation) {
            return res.status(404).json({ message: "Conversation not found or access denied" });
        }

        // 2. Create message
        const message = await db.aIChatMessage.create({
            data: {
                conversationId,
                ...messageData
            }
        });

        res.status(201).json(message);
    } catch (err: any) {
        res.status(500).json({ message: `Failed to add message: ${err.message}` });
    }
};

/**
 * Delete an AI Conversation and all its messages
 */
export const deleteConversation = async (req: Request, res: Response) => {
    try {
        const user = req.user as Payload;
        const { conversationId } = req.params;

        // 1. Verify ownership
        const conversation = await db.aIConversation.findFirst({
            where: {
                id: conversationId,
                userId: user.id
            }
        });

        if (!conversation) {
            return res.status(404).json({ message: "Conversation not found or access denied" });
        }

        // 2. The cascade delete in Prisma (if configured) or manual delete will remove messages.
        // Assuming Prisma schema has onDelete: "CASCADE" for aIChatMessages, but we can manually delete them to be safe
        await db.aIChatMessage.deleteMany({
            where: { conversationId }
        });

        // 3. Delete the parent conversation
        await db.aIConversation.delete({
            where: { id: conversationId }
        });

        res.status(200).json({ message: "Conversation deleted successfully" });
    } catch (err: any) {
        res.status(500).json({ message: `Failed to delete conversation: ${err.message}` });
    }
};

"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.deleteConversation = exports.addMessage = exports.startConversation = exports.getConversationMessages = exports.getMyConversations = void 0;
const db_1 = require("../db");
const axios_1 = __importDefault(require("axios"));
/**
 * List paginated AI Conversations for the user
 * Optional filtering by field or crop assignment
 */
const getMyConversations = async (req, res) => {
    try {
        const user = req.user;
        const { page, limit, fieldId, cropAssignmentId } = req.query;
        const pageNum = parseInt(page) || 1;
        const limitNum = parseInt(limit) || 10;
        const skip = (pageNum - 1) * limitNum;
        const where = { userId: user.id };
        if (fieldId)
            where.fieldId = fieldId;
        if (cropAssignmentId)
            where.cropAssignmentId = cropAssignmentId;
        const [conversations, total] = await Promise.all([
            db_1.db.aIConversation.findMany({
                where,
                skip,
                take: limitNum,
                orderBy: { startedAt: 'desc' },
                include: {
                    field: { select: { name: true } },
                    cropAssignment: { include: { crop: { select: { name: true } } } }
                }
            }),
            db_1.db.aIConversation.count({ where })
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
    }
    catch (err) {
        res.status(500).json({ message: `Failed to retrieve conversations: ${err.message}` });
    }
};
exports.getMyConversations = getMyConversations;
/**
 * Get paginated messages for a specific conversation
 */
const getConversationMessages = async (req, res) => {
    try {
        const user = req.user;
        const conversationId = req.params.conversationId;
        const { page, limit } = req.query;
        const pageNum = parseInt(page) || 1;
        const limitNum = parseInt(limit) || 10;
        const skip = (pageNum - 1) * limitNum;
        // 1. Verify ownership
        const conversation = await db_1.db.aIConversation.findFirst({
            where: {
                id: conversationId,
                userId: user.id
            }
        });
        if (!conversation) {
            return res.status(404).json({ message: "Conversation not found or access denied" });
        }
        // 2. Fetch messages
        const [messages, total] = await Promise.all([
            db_1.db.aIChatMessage.findMany({
                where: { conversationId: conversationId },
                skip,
                take: limitNum,
                orderBy: { createdAt: 'asc' } // Linear chat flow
            }),
            db_1.db.aIChatMessage.count({
                where: { conversationId: conversationId }
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
    }
    catch (err) {
        res.status(500).json({ message: `Failed to retrieve messages: ${err.message}` });
    }
};
exports.getConversationMessages = getConversationMessages;
/**
 * Start a new AI Conversation (The Folder)
 */
const startConversation = async (req, res) => {
    try {
        const user = req.user;
        const { fieldId, cropAssignmentId } = req.body;
        const conversation = await db_1.db.aIConversation.create({
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
    }
    catch (err) {
        res.status(500).json({ message: `Failed to start conversation: ${err.message}` });
    }
};
exports.startConversation = startConversation;
/**
 * Add a message to a conversation (The Message Inside)
 */
const addMessage = async (req, res) => {
    try {
        const user = req.user;
        const conversationId = req.params.conversationId;
        const messageData = req.body;
        // Extract language or default to English
        const language = messageData.language || 'en';
        // 1. Verify ownership of the conversation
        const conversation = await db_1.db.aIConversation.findFirst({
            where: {
                id: conversationId,
                userId: user.id
            }
        });
        if (!conversation) {
            return res.status(404).json({ message: "Conversation not found or access denied" });
        }
        // 2. Create USER message
        const userMessage = await db_1.db.aIChatMessage.create({
            data: {
                conversationId,
                sender: 'USER',
                messageType: messageData.messageType || 'TEXT',
                textContent: messageData.textContent,
                filePath: messageData.filePath || null
            }
        });
        // 3. Make HTTP call to Python backend for AI Response
        // Forwarding the user's token directly isn't strictly necessary if python backend trusts this network,
        // but we'll include the raw text content for the reasoning.
        try {
            const pythonUrl = process.env.PYTHON_BACKEND_URL || 'http://localhost:8001';
            const aiResponse = await axios_1.default.post(`${pythonUrl}/api/chat/generate`, {
                message: messageData.textContent,
                language: language,
                session_id: conversationId
            }, {
                headers: {
                    'Authorization': req.headers.authorization || '' // pass-through JWT
                }
            });
            const aiResponseText = aiResponse.data.response;
            // 4. Create AI message
            const aiMessage = await db_1.db.aIChatMessage.create({
                data: {
                    conversationId,
                    sender: 'AI',
                    messageType: 'TEXT',
                    textContent: aiResponseText,
                }
            });
            // Return both messages so the UI can quickly update
            res.status(201).json({
                userMessage,
                aiMessage
            });
            return;
        }
        catch (pythonErr) {
            console.error("Failed to generate AI response:", pythonErr.message);
            // Still create a fallback error message from AI 
            const errorAiMessage = await db_1.db.aIChatMessage.create({
                data: {
                    conversationId,
                    sender: 'AI',
                    messageType: 'TEXT',
                    textContent: "Sorry, I couldn't process your request right now. Please try again.",
                }
            });
            res.status(201).json({
                userMessage,
                aiMessage: errorAiMessage
            });
            return;
        }
    }
    catch (err) {
        res.status(500).json({ message: `Failed to add message: ${err.message}` });
    }
};
exports.addMessage = addMessage;
/**
 * Delete an AI Conversation and all its messages
 */
const deleteConversation = async (req, res) => {
    try {
        const user = req.user;
        const conversationId = req.params.conversationId;
        // 1. Verify ownership
        const conversation = await db_1.db.aIConversation.findFirst({
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
        await db_1.db.aIChatMessage.deleteMany({
            where: { conversationId }
        });
        // 3. Delete the parent conversation
        await db_1.db.aIConversation.delete({
            where: { id: conversationId }
        });
        res.status(200).json({ message: "Conversation deleted successfully" });
    }
    catch (err) {
        res.status(500).json({ message: `Failed to delete conversation: ${err.message}` });
    }
};
exports.deleteConversation = deleteConversation;
//# sourceMappingURL=chatController.js.map
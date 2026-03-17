import { Request, Response } from 'express';
/**
 * List paginated AI Conversations for the user
 * Optional filtering by field or crop assignment
 */
export declare const getMyConversations: (req: Request, res: Response) => Promise<void>;
/**
 * Get paginated messages for a specific conversation
 */
export declare const getConversationMessages: (req: Request, res: Response) => Promise<Response<any, Record<string, any>> | undefined>;
/**
 * Start a new AI Conversation (The Folder)
 */
export declare const startConversation: (req: Request, res: Response) => Promise<void>;
/**
 * Add a message to a conversation (The Message Inside)
 */
export declare const addMessage: (req: Request, res: Response) => Promise<Response<any, Record<string, any>> | undefined>;
/**
 * Delete an AI Conversation and all its messages
 */
export declare const deleteConversation: (req: Request, res: Response) => Promise<Response<any, Record<string, any>> | undefined>;
//# sourceMappingURL=chatController.d.ts.map
import { Router } from "express";
import { requestOTP, verifyOTP, refresh } from "../controller/auth";
import { registerLand, getMyLand, updateLand } from "../controller/landController";
import { addField, getMyFields, deleteField } from "../controller/fieldController";
import { listCrops, assignCrop, updateAssignmentStatus, getMyActiveAssignments } from "../controller/cropController";
import { getMyConversations, getConversationMessages, startConversation, addMessage } from "../controller/chatController";
import { updateProfile, getProfile, requestMobileUpdate, verifyMobileUpdate } from "../controller/userController";
import { protectedTest, adminTest } from "../controller/test";
import { verifyAccessToken, verifyRefreshToken } from "../valid/jwt";
import { authLimiter } from "../valid/valid";
import { requestOTPValidation, verifyOTPValidation } from "../valid/authValid";
import { registerLandValidation, updateLandValidation, fieldValidation } from "../valid/landValid";
import { assignCropValidation, updateAssignmentStatusValidation } from "../valid/cropValid";
import { paginationValidation, conversationIdValidation, startConversationValidation, addMessageValidation } from "../valid/chatValid";
import { updateProfileValidation, requestMobileUpdateValidation, verifyMobileUpdateValidation } from "../valid/userValid";

const router = Router();

// Auth Routes
router.post('/request-otp', authLimiter, requestOTPValidation, requestOTP);
router.post('/verify-otp', authLimiter, verifyOTPValidation, verifyOTP);
router.post('/refresh', authLimiter, verifyRefreshToken, refresh);

// User Profile Routes
router.get('/user/profile', verifyAccessToken, getProfile);
router.patch('/user/profile', verifyAccessToken, updateProfileValidation, updateProfile);
router.post('/user/request-mobile-update', verifyAccessToken, requestMobileUpdateValidation, requestMobileUpdate);
router.post('/user/verify-mobile-update', verifyAccessToken, verifyMobileUpdateValidation, verifyMobileUpdate);

// Governance - Land Routes
router.post('/governance/land', verifyAccessToken, registerLandValidation, registerLand);
router.get('/governance/land', verifyAccessToken, getMyLand);
router.patch('/governance/land', verifyAccessToken, updateLandValidation, updateLand);

// Governance - Field Routes
router.post('/governance/field', verifyAccessToken, fieldValidation, addField);
router.get('/governance/field', verifyAccessToken, getMyFields);
router.delete('/governance/field/:id', verifyAccessToken, deleteField);

// Governance - Crop & Assignment Routes
router.get('/governance/crops', verifyAccessToken, listCrops);
router.post('/governance/assignment', verifyAccessToken, assignCropValidation, assignCrop);
router.patch('/governance/assignment/:id', verifyAccessToken, updateAssignmentStatusValidation, updateAssignmentStatus);
router.get('/governance/active-assignments', verifyAccessToken, getMyActiveAssignments);

// Chat History Routes
router.get('/chat/conversations', verifyAccessToken, paginationValidation, getMyConversations);
router.post('/chat/conversations', verifyAccessToken, startConversationValidation, startConversation);
router.get('/chat/messages/:conversationId', verifyAccessToken, conversationIdValidation, paginationValidation, getConversationMessages);
router.post('/chat/conversations/:conversationId/messages', verifyAccessToken, conversationIdValidation, addMessageValidation, addMessage);

// Temporary test APIs
router.get('/test/protected', verifyAccessToken, protectedTest);
router.get('/test/admin', verifyAccessToken, adminTest);

export default router;
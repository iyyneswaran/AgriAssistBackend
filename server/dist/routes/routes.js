"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const auth_1 = require("../controller/auth");
const landController_1 = require("../controller/landController");
const fieldController_1 = require("../controller/fieldController");
const cropController_1 = require("../controller/cropController");
const chatController_1 = require("../controller/chatController");
const userController_1 = require("../controller/userController");
const test_1 = require("../controller/test");
const jwt_1 = require("../valid/jwt");
const valid_1 = require("../valid/valid");
const authValid_1 = require("../valid/authValid");
const landValid_1 = require("../valid/landValid");
const cropValid_1 = require("../valid/cropValid");
const chatValid_1 = require("../valid/chatValid");
const userValid_1 = require("../valid/userValid");
const router = (0, express_1.Router)();
// Auth Routes
router.post('/request-otp', valid_1.authLimiter, authValid_1.requestOTPValidation, auth_1.requestOTP);
router.post('/verify-otp', valid_1.authLimiter, authValid_1.verifyOTPValidation, auth_1.verifyOTP);
router.post('/refresh', valid_1.authLimiter, jwt_1.verifyRefreshToken, auth_1.refresh);
// User Profile Routes
router.get('/user/profile', jwt_1.verifyAccessToken, userController_1.getProfile);
router.patch('/user/profile', jwt_1.verifyAccessToken, userValid_1.updateProfileValidation, userController_1.updateProfile);
router.post('/user/request-mobile-update', jwt_1.verifyAccessToken, userValid_1.requestMobileUpdateValidation, userController_1.requestMobileUpdate);
router.post('/user/verify-mobile-update', jwt_1.verifyAccessToken, userValid_1.verifyMobileUpdateValidation, userController_1.verifyMobileUpdate);
// Governance - Land Routes
router.post('/governance/land', jwt_1.verifyAccessToken, landValid_1.registerLandValidation, landController_1.registerLand);
router.get('/governance/land', jwt_1.verifyAccessToken, landController_1.getMyLand);
router.patch('/governance/land', jwt_1.verifyAccessToken, landValid_1.updateLandValidation, landController_1.updateLand);
// Governance - Field Routes
router.post('/governance/field', jwt_1.verifyAccessToken, landValid_1.fieldValidation, fieldController_1.addField);
router.get('/governance/field', jwt_1.verifyAccessToken, fieldController_1.getMyFields);
router.delete('/governance/field/:id', jwt_1.verifyAccessToken, fieldController_1.deleteField);
// Governance - Crop & Assignment Routes
router.get('/governance/crops', jwt_1.verifyAccessToken, cropController_1.listCrops);
router.post('/governance/assignment', jwt_1.verifyAccessToken, cropValid_1.assignCropValidation, cropController_1.assignCrop);
router.patch('/governance/assignment/:id', jwt_1.verifyAccessToken, cropValid_1.updateAssignmentStatusValidation, cropController_1.updateAssignmentStatus);
router.get('/governance/active-assignments', jwt_1.verifyAccessToken, cropController_1.getMyActiveAssignments);
// Chat History Routes
router.get('/chat/conversations', jwt_1.verifyAccessToken, chatValid_1.paginationValidation, chatController_1.getMyConversations);
router.post('/chat/conversations', jwt_1.verifyAccessToken, chatValid_1.startConversationValidation, chatController_1.startConversation);
router.get('/chat/messages/:conversationId', jwt_1.verifyAccessToken, chatValid_1.conversationIdValidation, chatValid_1.paginationValidation, chatController_1.getConversationMessages);
router.post('/chat/conversations/:conversationId/messages', jwt_1.verifyAccessToken, chatValid_1.conversationIdValidation, chatValid_1.addMessageValidation, chatController_1.addMessage);
router.delete('/chat/conversations/:conversationId', jwt_1.verifyAccessToken, chatValid_1.conversationIdValidation, chatController_1.deleteConversation);
// Temporary test APIs
router.get('/test/protected', jwt_1.verifyAccessToken, test_1.protectedTest);
router.get('/test/admin', jwt_1.verifyAccessToken, test_1.adminTest);
exports.default = router;
//# sourceMappingURL=routes.js.map
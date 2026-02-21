"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const auth_1 = require("../controller/auth");
const test_1 = require("../controller/test");
const jwt_1 = require("../valid/jwt");
const valid_1 = require("../valid/valid");
const authValid_1 = require("../valid/authValid");
const router = (0, express_1.Router)();
router.post('/request-otp', valid_1.authLimiter, authValid_1.requestOTPValidation, auth_1.requestOTP);
router.post('/verify-otp', valid_1.authLimiter, authValid_1.verifyOTPValidation, auth_1.verifyOTP);
router.post('/refresh', valid_1.authLimiter, jwt_1.verifyRefreshToken, auth_1.refresh);
// Temporary test APIs
router.get('/test/protected', jwt_1.verifyAccessToken, test_1.protectedTest);
router.get('/test/admin', jwt_1.verifyAccessToken, test_1.adminTest);
exports.default = router;
//# sourceMappingURL=routes.js.map
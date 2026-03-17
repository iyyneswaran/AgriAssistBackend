"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
require("dotenv/config");
const http_1 = require("http");
const app_1 = __importDefault(require("./app"));
const routes_1 = __importDefault(require("./routes/routes"));
const voiceAgentRoutes_1 = __importStar(require("./voice-agent/voiceAgentRoutes"));
const PORT = process.env.PORT || 5000;
// Mount main API routes
app_1.default.use("/api", routes_1.default);
// Mount voice agent routes under /api/voice-agent
app_1.default.use("/api/voice-agent", voiceAgentRoutes_1.default);
app_1.default.use("/", (req, res) => {
    res.send("Hello World!");
});
// ─── Create HTTP server (required for WebSocket support) ────────────
const server = (0, http_1.createServer)(app_1.default);
// Set up Voice Agent WebSocket for Twilio media streams
(0, voiceAgentRoutes_1.setupVoiceAgentWebSocket)(server);
// ─── Process-level crash protection ─────────────────────────────────
// Prevent the server from silently crashing on unhandled errors.
process.on('unhandledRejection', (reason, promise) => {
    console.error('[Server] Unhandled Promise Rejection:', reason);
    // Don't exit — log it and keep running
});
process.on('uncaughtException', (err) => {
    console.error('[Server] Uncaught Exception:', err);
    // Don't exit — log it and keep running
});
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`Voice Agent API: /api/voice-agent`);
    console.log(`WebSocket endpoint: ws://localhost:${PORT}/media-stream`);
});
//# sourceMappingURL=index.js.map
"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const cors_1 = __importDefault(require("cors"));
const cookie_parser_1 = __importDefault(require("cookie-parser"));
const express_rate_limit_1 = __importDefault(require("express-rate-limit"));
const app = (0, express_1.default)();
// Trust one level of proxy (Railway's reverse proxy)
app.set("trust proxy", 1);
const allowedOrigins = [
    "https://agri-assist-frontend-seven.vercel.app",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    ...(process.env.ALLOWED_ORIGINS || '').split(',').map(value => value.trim()).filter(value => value && value !== '*'),
];
app.use((0, cors_1.default)({
    origin: (origin, callback) => {
        // Allow requests with no origin (mobile apps, server-to-server, curl)
        if (!origin)
            return callback(null, true);
        if (allowedOrigins.includes(origin)) {
            return callback(null, true);
        }
        return callback(null, false);
    },
    credentials: true,
    methods: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
    optionsSuccessStatus: 200,
}));
// ── Lightweight health check (before rate limiter) ──
app.get("/health", (_req, res) => {
    res.status(200).json({ ok: true });
});
// Global rate limiter: 500 requests per 15 minutes
const limiter = (0, express_rate_limit_1.default)({
    windowMs: 15 * 60 * 1000,
    max: 500,
    message: 'Too many requests from this IP, please try again later.',
});
app.use(limiter);
app.use((0, cookie_parser_1.default)());
app.use(express_1.default.json());
exports.default = app;
//# sourceMappingURL=app.js.map
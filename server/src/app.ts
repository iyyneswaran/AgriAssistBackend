import express, { Request, Response } from "express";
import cors from "cors";
import cookieParser from "cookie-parser";
import rateLimit from 'express-rate-limit';

const app = express();

// Trust one level of proxy (Railway's reverse proxy)
app.set("trust proxy", 1);

const allowedOrigins = [
  "https://agri-assist-frontend-seven.vercel.app",
  "http://localhost:5173",
  "http://localhost:5174",
  "http://localhost:3000",
];

app.use(cors({
  origin: (origin, callback) => {
    // Allow requests with no origin (mobile apps, server-to-server, curl)
    if (!origin) return callback(null, true);

    // Allow known frontend domains or any preview deployment on Vercel
    if (
      allowedOrigins.includes(origin) ||
      /^https:\/\/.*\.vercel\.app$/.test(origin)
    ) {
      return callback(null, true);
    }

    // Fallback: allow and reflect origin
    return callback(null, true);
  },
  credentials: true,
  methods: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
  allowedHeaders: ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
  optionsSuccessStatus: 200,
}));

// ── Lightweight health check (before rate limiter) ──
app.get("/health", (_req: Request, res: Response) => {
  res.status(200).json({ ok: true });
});

// Global rate limiter: 500 requests per 15 minutes
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 500,
  message: 'Too many requests from this IP, please try again later.',
});

app.use(limiter);

app.use(cookieParser());
app.use(express.json());

export default app;

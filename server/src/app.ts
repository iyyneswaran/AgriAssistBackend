import express, { Request, Response, NextFunction } from "express";
import cors from "cors";
import cookieParser from "cookie-parser";
import rateLimit from 'express-rate-limit';

const app = express();

app.use(cors({
  origin: true,
  credentials: true,
}));

// Global rate limiter: 100 requests per 15 minutes
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: 'Too many requests from this IP, please try again later.',
});

app.use(limiter);

app.use(cookieParser());
app.use(express.json());

// Error Handling Middleware (must be last)
import { errorMiddleware } from "./valid/errorMiddleware";
app.use(errorMiddleware);

export default app;
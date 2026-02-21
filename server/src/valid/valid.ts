import rateLimit from "express-rate-limit";

export const authLimiter = rateLimit({
  windowMs: 5 * 60 * 1000,
  max: 5,
  message: 'Too many attempts, please try again after 5 minutes'
});
import "dotenv/config";
import app from "./app";
import routes from "./routes/routes";
import { Request, Response } from "express";

const PORT = process.env.PORT || 5000;

app.use("/api", routes);
app.use("/", (req: Request, res: Response) => {
  res.send("Hello World!");
});

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

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
import "dotenv/config";
import { createServer } from "http";
import app from "./app";
import routes from "./routes/routes";
import voiceAgentRouter, { setupVoiceAgentWebSocket } from "./voice-agent/voiceAgentRoutes";
import { Request, Response } from "express";

const PORT = process.env.PORT || 5000;

// Mount main API routes
app.use("/api", routes);

// Mount voice agent routes under /api/voice-agent
app.use("/api/voice-agent", voiceAgentRouter);

app.use("/", (req: Request, res: Response) => {
  res.send("Hello World!");
});

// ─── Create HTTP server (required for WebSocket support) ────────────
const server = createServer(app);

// Set up Voice Agent WebSocket for Twilio media streams
setupVoiceAgentWebSocket(server);

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
"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.db = void 0;
const client_1 = require("@prisma/client");
const adapter_pg_1 = require("@prisma/adapter-pg");
const pg_1 = __importDefault(require("pg"));
// config({ path: resolve(__dirname, "../../.env") });
const pool = new pg_1.default.Pool({
    connectionString: process.env.DATABASE_URL,
    // Neon serverless: close idle connections before Neon's 5-min timeout
    idleTimeoutMillis: 30000, // Close idle connections after 30s
    connectionTimeoutMillis: 10000, // Fail fast if can't connect in 10s
    max: 10, // Max pool size
});
// CRITICAL: Handle pool errors to prevent Node.js crash
// Neon can close idle connections, emitting 'error' on the pool.
// Without this listener, Node.js crashes with "unhandled 'error' event".
pool.on('error', (err) => {
    console.error('[DB Pool] Unexpected error on idle client:', err.message);
    // Don't crash — pg.Pool will automatically remove the broken client
    // and create a new one on the next query.
});
const adapter = new adapter_pg_1.PrismaPg(pool);
exports.db = new client_1.PrismaClient({ adapter });
//# sourceMappingURL=db.js.map
import { config } from "dotenv";
import { resolve } from "path";
import { PrismaClient } from "./generated/prisma";
import { PrismaPg } from "@prisma/adapter-pg";
import pg from "pg";

// config({ path: resolve(__dirname, "../../.env") });

const pool = new pg.Pool({
    connectionString: process.env.DATABASE_URL,
    // Neon serverless: close idle connections before Neon's 5-min timeout
    idleTimeoutMillis: 30000,        // Close idle connections after 30s
    connectionTimeoutMillis: 10000,  // Fail fast if can't connect in 10s
    max: 10,                         // Max pool size
});

// CRITICAL: Handle pool errors to prevent Node.js crash
// Neon can close idle connections, emitting 'error' on the pool.
// Without this listener, Node.js crashes with "unhandled 'error' event".
pool.on('error', (err) => {
    console.error('[DB Pool] Unexpected error on idle client:', err.message);
    // Don't crash — pg.Pool will automatically remove the broken client
    // and create a new one on the next query.
});

const adapter = new PrismaPg(pool);

export const db = new PrismaClient({ adapter });

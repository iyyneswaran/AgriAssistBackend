import { createClient } from "redis";

export const redis = createClient({
    url: process.env.REDIS_URL,
});

redis.on("error", (err) => console.error("[Redis] Client Error", err));

// Only connect if URL is provided
if (process.env.REDIS_URL) {
    redis.connect().catch((err) => {
        console.error("[Redis] Failed to connect", err);
    });
} else {
    console.warn("[Redis] REDIS_URL not set in environment.");
}

import { createClient } from "redis";

const redisUrl = process.env.REDIS_URL;

export const redis = redisUrl
    ? createClient({ url: redisUrl })
    : createClient();

redis.on("error", (err) => console.error("[Redis] Client Error", err));

// Only connect if URL is provided
if (redisUrl) {
    redis.connect().catch((err) => {
        console.error("[Redis] Failed to connect", err);
    });
} else {
    console.warn("[Redis] REDIS_URL not set in environment.");
}

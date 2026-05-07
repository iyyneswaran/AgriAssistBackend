"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.redis = void 0;
const redis_1 = require("redis");
const redisUrl = process.env.REDIS_URL;
exports.redis = redisUrl
    ? (0, redis_1.createClient)({ url: redisUrl })
    : (0, redis_1.createClient)();
exports.redis.on("error", (err) => console.error("[Redis] Client Error", err));
// Only connect if URL is provided
if (redisUrl) {
    exports.redis.connect().catch((err) => {
        console.error("[Redis] Failed to connect", err);
    });
}
else {
    console.warn("[Redis] REDIS_URL not set in environment.");
}
//# sourceMappingURL=redis.js.map
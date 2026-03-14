import asyncio
import redis.asyncio as redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

redis_client: redis.Redis | None = None


async def init_pubsub():
    global redis_client
    if not settings.REDIS_URL:
        logger.warning("[Redis] REDIS_URL not set. Pub/Sub is disabled.")
        redis_client = None
        return

    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )
    try:
        await redis_client.ping()
    except Exception as exc:
        logger.warning(f"[Redis] Pub/Sub connection failed: {exc}")
        redis_client = None


async def publish_event(channel: str, message: dict):
    """
    Publishes event to Redis channel.
    """
    if redis_client is None:
        return

    await redis_client.publish(channel, str(message))


async def subscribe(channel: str, handler):
    """
    Subscribes to Redis channel and processes messages with handler coroutine.
    """
    if redis_client is None:
        raise RuntimeError("Redis Pub/Sub is not initialized. Set REDIS_URL to enable subscriptions.")

    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)

    async for message in pubsub.listen():
        if message["type"] == "message":
            await handler(message["data"])

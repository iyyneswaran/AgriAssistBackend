import asyncio
import redis.asyncio as redis
from app.core.config import settings

redis_client: redis.Redis | None = None


async def init_pubsub():
    global redis_client
    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )


async def publish_event(channel: str, message: dict):
    """
    Publishes event to Redis channel.
    """
    await redis_client.publish(channel, str(message))


async def subscribe(channel: str, handler):
    """
    Subscribes to Redis channel and processes messages with handler coroutine.
    """
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)

    async for message in pubsub.listen():
        if message["type"] == "message":
            await handler(message["data"])

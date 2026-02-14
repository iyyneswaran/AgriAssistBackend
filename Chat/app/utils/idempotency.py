import redis.asyncio as redis
from app.core.config import settings

redis_client: redis.Redis | None = None


async def init_idempotency():
    global redis_client
    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )


async def is_duplicate(message_id: str) -> bool:
    """
    Returns True if message_id already processed.
    """
    exists = await redis_client.exists(f"idempotency:{message_id}")
    return exists == 1


async def mark_processed(message_id: str, ttl_seconds: int = 3600):
    """
    Marks message as processed with TTL.
    """
    await redis_client.set(
        f"idempotency:{message_id}",
        "1",
        ex=ttl_seconds,
    )

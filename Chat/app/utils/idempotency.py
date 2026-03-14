import redis.asyncio as redis
from app.core.config import settings
import logging
import time

logger = logging.getLogger(__name__)

redis_client: redis.Redis | None = None
in_memory_processed: dict[str, float] = {}


async def init_idempotency():
    global redis_client
    if not settings.REDIS_URL:
        logger.warning("[Redis] REDIS_URL not set. Using in-memory idempotency cache.")
        redis_client = None
        return

    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )
    try:
        await redis_client.ping()
    except Exception as exc:
        logger.warning(f"[Redis] Idempotency connection failed. Using in-memory cache: {exc}")
        redis_client = None


async def is_duplicate(message_id: str) -> bool:
    """
    Returns True if message_id already processed.
    """
    if redis_client is None:
        now = time.monotonic()
        expires_at = in_memory_processed.get(message_id)
        if expires_at is None:
            return False
        if expires_at <= now:
            in_memory_processed.pop(message_id, None)
            return False
        return True

    exists = await redis_client.exists(f"idempotency:{message_id}")
    return exists == 1


async def mark_processed(message_id: str, ttl_seconds: int = 3600):
    """
    Marks message as processed with TTL.
    """
    if redis_client is None:
        in_memory_processed[message_id] = time.monotonic() + ttl_seconds
        return

    await redis_client.set(
        f"idempotency:{message_id}",
        "1",
        ex=ttl_seconds,
    )

import redis.asyncio as redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

redis_client: redis.Redis | None = None
local_sessions_by_user: dict[str, set[str]] = {}


async def init_redis():
    global redis_client
    if not settings.REDIS_URL:
        logger.warning("[Redis] REDIS_URL not set. Falling back to in-memory session tracking.")
        redis_client = None
        return

    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )
    try:
        await redis_client.ping()
    except Exception as exc:
        logger.warning(f"[Redis] Connection failed. Falling back to in-memory session tracking: {exc}")
        redis_client = None


async def set_user_online(user_id: str, session_id: str):
    """
    Stores active session for user.
    """
    if redis_client is None:
        if user_id not in local_sessions_by_user:
            local_sessions_by_user[user_id] = set()
        local_sessions_by_user[user_id].add(session_id)
        return

    await redis_client.sadd(f"user:{user_id}:sessions", session_id)
    await redis_client.set(f"session:{session_id}:user", user_id)


async def remove_user_session(user_id: str, session_id: str):
    """
    Removes session when disconnected.
    """
    if redis_client is None:
        sessions = local_sessions_by_user.get(user_id)
        if sessions:
            sessions.discard(session_id)
            if not sessions:
                local_sessions_by_user.pop(user_id, None)
        return

    await redis_client.srem(f"user:{user_id}:sessions", session_id)
    await redis_client.delete(f"session:{session_id}:user")


async def is_user_online(user_id: str) -> bool:
    if redis_client is None:
        return bool(local_sessions_by_user.get(user_id))

    sessions = await redis_client.smembers(f"user:{user_id}:sessions")
    return len(sessions) > 0


async def get_user_sessions(user_id: str):
    if redis_client is None:
        return local_sessions_by_user.get(user_id, set())

    return await redis_client.smembers(f"user:{user_id}:sessions")

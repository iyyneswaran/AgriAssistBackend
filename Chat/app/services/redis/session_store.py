import redis.asyncio as redis
from app.core.config import settings

redis_client: redis.Redis | None = None


async def init_redis():
    global redis_client
    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )


async def set_user_online(user_id: str, session_id: str):
    """
    Stores active session for user.
    """
    await redis_client.sadd(f"user:{user_id}:sessions", session_id)
    await redis_client.set(f"session:{session_id}:user", user_id)


async def remove_user_session(user_id: str, session_id: str):
    """
    Removes session when disconnected.
    """
    await redis_client.srem(f"user:{user_id}:sessions", session_id)
    await redis_client.delete(f"session:{session_id}:user")


async def is_user_online(user_id: str) -> bool:
    sessions = await redis_client.smembers(f"user:{user_id}:sessions")
    return len(sessions) > 0


async def get_user_sessions(user_id: str):
    return await redis_client.smembers(f"user:{user_id}:sessions")

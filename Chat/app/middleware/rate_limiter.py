from fastapi import Request, HTTPException
from app.services.redis import session_store
from app.core.rate_limiter import rate_limit_dependency
import logging

logger = logging.getLogger(__name__)


async def rate_limit(request: Request):
    # Proxy trust belongs in ASGI configuration, not arbitrary forwarded headers.
    rate_limit_dependency(request)
    client = session_store.redis_client
    if client is None:
        return
    ip = request.client.host if request.client else 'unknown'
    key = f'rate_limit:{ip}:{request.scope["path"]}'
    try:
        async with client.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.expire(key, 60, nx=True)
            current, _ = await pipe.execute()
        if current > 10:
            raise HTTPException(status_code=429, detail='Too many requests. Please try again later.')
    except HTTPException:
        raise
    except Exception:
        logger.warning('Redis rate limiter unavailable; local limit remains active')

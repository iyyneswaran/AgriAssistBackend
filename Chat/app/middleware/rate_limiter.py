from fastapi import Request, HTTPException
from app.services.redis.session_store import redis_client
import logging

logger = logging.getLogger(__name__)

async def rate_limit(request: Request):
    """
    Dependency for token-bucket style rate limiting per IP using Redis.
    Allows 10 requests per minute.
    """
    if redis_client is None:
        return # Skip if Redis not configured
    
    # Use x-forwarded-for if behind proxy, else client.host
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0] if forwarded else request.client.host
    
    key = f"rate_limit:{ip}:{request.url.path}"
    
    try:
        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, 60) # 1 minute window
        
        if current > 10:
            logger.warning(f"Rate limit exceeded for IP: {ip} on {request.url.path}")
            raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
            
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"[RateLimiter] Error: {e}")

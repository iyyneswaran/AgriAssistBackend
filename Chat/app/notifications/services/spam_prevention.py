"""
Spam Prevention Service
========================
Prevents notification fatigue through deduplication, cooldown periods,
priority handling, and alert grouping using Redis.
"""

import logging
from datetime import datetime
from typing import Optional

from app.notifications.models.notification_event import NotificationEvent
from app.services.redis.session_store import redis_client

logger = logging.getLogger(__name__)

# In-memory fallback when Redis is unavailable
_local_dedup_cache: dict[str, float] = {}
_local_cooldown_cache: dict[str, float] = {}

# Cooldown periods per event type (in seconds)
DEFAULT_COOLDOWNS = {
    "smart_irrigation": 3600,      # 1 hour
    "disease_warning": 7200,       # 2 hours
    "drought_intelligence": 14400, # 4 hours
    "flood_prevention": 1800,      # 30 minutes (urgent)
    "resource_optimization": 7200, # 2 hours
    "iot_offline": 900,            # 15 minutes
}

# Severity priorities — critical always gets through
SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


class SpamPreventionService:
    """Filters notification events to prevent spam and notification fatigue."""

    async def should_send(self, event: NotificationEvent) -> bool:
        """
        Determine if a notification event should be sent.

        Checks (in order):
        1. Critical severity → always send
        2. Deduplication → skip if identical event was sent recently
        3. Cooldown → skip if same event type was sent within cooldown period
        """
        # Critical events always bypass spam prevention
        if event.severity == "critical":
            await self._record_sent(event)
            return True

        # Check deduplication
        if event.dedup_hash:
            is_dup = await self._check_dedup(event.user_id, event.dedup_hash)
            if is_dup:
                logger.debug(
                    f"Suppressed duplicate notification: {event.event_type} "
                    f"for user {event.user_id}"
                )
                return False

        # Check cooldown
        is_cooled = await self._check_cooldown(event.user_id, event.event_type)
        if is_cooled:
            logger.debug(
                f"Suppressed by cooldown: {event.event_type} "
                f"for user {event.user_id}"
            )
            return False

        # Passed all checks
        await self._record_sent(event)
        return True

    async def _check_dedup(self, user_id: str, dedup_hash: str) -> bool:
        """Check if this exact event was already sent recently."""
        key = f"notif:dedup:{user_id}:{dedup_hash}"

        if redis_client is not None:
            try:
                exists = await redis_client.exists(key)
                return bool(exists)
            except Exception as e:
                logger.warning(f"Redis dedup check failed: {e}")

        # Fallback to local cache
        cached_time = _local_dedup_cache.get(key)
        if cached_time:
            elapsed = datetime.utcnow().timestamp() - cached_time
            if elapsed < 3600:  # 1 hour dedup window
                return True
            del _local_dedup_cache[key]
        return False

    async def _check_cooldown(self, user_id: str, event_type: str) -> bool:
        """Check if we're in a cooldown period for this event type."""
        key = f"notif:cooldown:{user_id}:{event_type}"
        cooldown = DEFAULT_COOLDOWNS.get(event_type, 3600)

        if redis_client is not None:
            try:
                exists = await redis_client.exists(key)
                return bool(exists)
            except Exception as e:
                logger.warning(f"Redis cooldown check failed: {e}")

        # Fallback to local cache
        cached_time = _local_cooldown_cache.get(key)
        if cached_time:
            elapsed = datetime.utcnow().timestamp() - cached_time
            if elapsed < cooldown:
                return True
            del _local_cooldown_cache[key]
        return False

    async def _record_sent(self, event: NotificationEvent) -> None:
        """Record that this event was sent for future dedup/cooldown checks."""
        cooldown = DEFAULT_COOLDOWNS.get(event.event_type, 3600)
        now = datetime.utcnow().timestamp()

        dedup_key = f"notif:dedup:{event.user_id}:{event.dedup_hash}"
        cooldown_key = f"notif:cooldown:{event.user_id}:{event.event_type}"

        if redis_client is not None:
            try:
                pipe = redis_client.pipeline()
                if event.dedup_hash:
                    pipe.setex(dedup_key, 3600, "1")  # 1 hour dedup TTL
                pipe.setex(cooldown_key, cooldown, "1")
                await pipe.execute()
                return
            except Exception as e:
                logger.warning(f"Redis record failed: {e}")

        # Fallback
        if event.dedup_hash:
            _local_dedup_cache[dedup_key] = now
        _local_cooldown_cache[cooldown_key] = now

        # Clean old entries periodically
        if len(_local_dedup_cache) > 1000:
            cutoff = now - 7200
            keys_to_remove = [
                k for k, v in _local_dedup_cache.items() if v < cutoff
            ]
            for k in keys_to_remove:
                del _local_dedup_cache[k]

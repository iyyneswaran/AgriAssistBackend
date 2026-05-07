"""
Push Subscription API Routes.

The browser owns the permission prompt and PushManager subscription. These
routes store that subscription securely against the authenticated AgriAssist
user, expose the public VAPID key, and provide diagnostics for production
support.
"""

import hashlib
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.notifications.models.delivery_status import DeliveryStatus
from app.notifications.models.notification_log import NotificationLog
from app.notifications.models.push_subscription import PushSubscription
from app.notifications.schemas.push_schemas import (
    PushDiagnosticsResponse,
    PushSubscriptionCreate,
    PushSubscriptionList,
    PushSubscriptionResponse,
    PushSubscriptionStatusResponse,
    PushSubscriptionUnsubscribe,
    VAPIDPublicKeyResponse,
)

router = APIRouter(prefix="/notifications/push", tags=["Push Notifications"])
logger = logging.getLogger(__name__)

MAX_SUBSCRIPTIONS_PER_USER = 10


def _extract_user_id(authorization: str = Header(None)) -> str:
    """Extract the authenticated user ID from a JWT Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )

    token = authorization.split(" ", 1)[1]
    user = get_current_user(token)
    user_id = user.get("id") or user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    return user_id


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _vapid_public_key_hash() -> Optional[str]:
    if not settings.VAPID_PUBLIC_KEY:
        return None
    return _hash_value(settings.VAPID_PUBLIC_KEY)


def _origin_allowed(origin: Optional[str]) -> bool:
    if not origin:
        return True

    allowed = {
        item.strip().rstrip("/")
        for item in settings.ALLOWED_ORIGINS.split(",")
        if item.strip()
    }
    if "*" in allowed:
        return True
    return origin.rstrip("/") in allowed


def _validate_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if not _origin_allowed(origin):
        logger.warning("Rejected push subscription from unexpected origin %s", origin)
        raise HTTPException(status_code=403, detail="Origin is not allowed")


def _expiration_from_browser(expiration_time: Optional[float]) -> Optional[datetime]:
    if expiration_time is None:
        return None
    try:
        return datetime.utcfromtimestamp(float(expiration_time) / 1000)
    except (TypeError, ValueError, OSError):
        return None


def _infer_device_metadata(user_agent: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if not user_agent:
        return None, None

    ua = user_agent.lower()
    if "edg/" in ua:
        browser = "Edge"
    elif "chrome/" in ua or "crios/" in ua:
        browser = "Chrome"
    elif "firefox/" in ua:
        browser = "Firefox"
    elif "safari/" in ua:
        browser = "Safari"
    else:
        browser = "Unknown"

    if "android" in ua:
        platform = "Android"
    elif "iphone" in ua or "ipad" in ua:
        platform = "iOS"
    elif "windows" in ua:
        platform = "Windows"
    elif "mac os" in ua:
        platform = "macOS"
    elif "linux" in ua:
        platform = "Linux"
    else:
        platform = "Unknown"

    return browser, platform


def _subscription_response(sub: PushSubscription) -> PushSubscriptionResponse:
    return PushSubscriptionResponse(
        id=sub.id,
        endpoint=sub.endpoint,
        device_name=sub.device_name,
        browser=sub.browser,
        platform=sub.platform,
        is_active=sub.is_active,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
        last_success_at=sub.last_success_at,
        failure_count=sub.failure_count or 0,
    )


@router.get("/vapid-key", response_model=VAPIDPublicKeyResponse)
async def get_vapid_public_key():
    """Return the server's public VAPID key for PushManager.subscribe()."""
    if not settings.VAPID_PUBLIC_KEY:
        raise HTTPException(
            status_code=503,
            detail="Push notifications are not configured on this server",
        )
    return VAPIDPublicKeyResponse(public_key=settings.VAPID_PUBLIC_KEY)


@router.get("/status", response_model=PushSubscriptionStatusResponse)
async def get_push_status(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Return active push subscription status for the current user."""
    user_id = _extract_user_id(authorization)

    result = await db.execute(
        select(PushSubscription)
        .where(
            PushSubscription.user_id == user_id,
            PushSubscription.is_active == True,
        )
        .order_by(desc(PushSubscription.updated_at))
    )
    subscriptions = result.scalars().all()

    return PushSubscriptionStatusResponse(
        vapid_configured=bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY),
        subscriptions=[_subscription_response(sub) for sub in subscriptions],
    )


@router.post("/subscribe", response_model=PushSubscriptionResponse)
async def subscribe_push(
    payload: PushSubscriptionCreate,
    request: Request,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Register or renew a push subscription for the authenticated user."""
    _validate_origin(request)
    user_id = _extract_user_id(authorization)

    if not settings.VAPID_PUBLIC_KEY or not settings.VAPID_PRIVATE_KEY:
        raise HTTPException(
            status_code=503,
            detail="Push notifications are not configured on this server",
        )

    if not payload.keys.p256dh or not payload.keys.auth:
        raise HTTPException(status_code=400, detail="Subscription keys are required")

    existing_result = await db.execute(
        select(PushSubscription).where(PushSubscription.endpoint == payload.endpoint)
    )
    existing_sub = existing_result.scalar_one_or_none()
    is_new_active_subscription = (
        existing_sub is None
        or not existing_sub.is_active
        or existing_sub.user_id != user_id
    )

    if is_new_active_subscription:
        count_result = await db.execute(
            select(func.count(PushSubscription.id)).where(
                PushSubscription.user_id == user_id,
                PushSubscription.is_active == True,
            )
        )
        count = count_result.scalar() or 0
        if count >= MAX_SUBSCRIPTIONS_PER_USER:
            raise HTTPException(
                status_code=429,
                detail=f"Maximum {MAX_SUBSCRIPTIONS_PER_USER} active devices allowed",
            )

    inferred_browser, inferred_platform = _infer_device_metadata(payload.user_agent)
    now = datetime.utcnow()

    if existing_sub:
        sub = existing_sub
        sub.user_id = user_id
        sub.p256dh_key = payload.keys.p256dh
        sub.auth_key = payload.keys.auth
        sub.content_encoding = payload.content_encoding or "aes128gcm"
        sub.vapid_public_key_hash = _vapid_public_key_hash()
        sub.user_agent = payload.user_agent
        sub.device_name = payload.device_name
        sub.browser = payload.browser or inferred_browser
        sub.platform = payload.platform or inferred_platform
        sub.expires_at = _expiration_from_browser(payload.expiration_time)
        sub.is_active = True
        sub.failure_count = 0
        sub.last_error = None
        sub.updated_at = now
    else:
        sub = PushSubscription(
            id=str(uuid.uuid4()),
            user_id=user_id,
            endpoint=payload.endpoint,
            endpoint_hash=_hash_value(payload.endpoint),
            p256dh_key=payload.keys.p256dh,
            auth_key=payload.keys.auth,
            content_encoding=payload.content_encoding or "aes128gcm",
            vapid_public_key_hash=_vapid_public_key_hash(),
            user_agent=payload.user_agent,
            device_name=payload.device_name,
            browser=payload.browser or inferred_browser,
            platform=payload.platform or inferred_platform,
            is_active=True,
            created_at=now,
            updated_at=now,
            expires_at=_expiration_from_browser(payload.expiration_time),
        )
        db.add(sub)

    await db.commit()
    await db.refresh(sub)

    logger.info(
        "push_subscription_registered user_id=%s subscription_id=%s endpoint_hash=%s",
        user_id,
        sub.id,
        sub.endpoint_hash or _hash_value(sub.endpoint),
    )
    return _subscription_response(sub)


@router.get("/subscriptions", response_model=PushSubscriptionList)
async def list_subscriptions(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """List active push subscriptions for the authenticated user."""
    user_id = _extract_user_id(authorization)

    result = await db.execute(
        select(PushSubscription)
        .where(
            PushSubscription.user_id == user_id,
            PushSubscription.is_active == True,
        )
        .order_by(desc(PushSubscription.updated_at))
    )
    subs = result.scalars().all()

    return PushSubscriptionList(
        subscriptions=[_subscription_response(sub) for sub in subs],
        count=len(subs),
    )


@router.post("/unsubscribe")
async def unsubscribe_push(
    payload: PushSubscriptionUnsubscribe,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a push subscription by endpoint or subscription ID."""
    user_id = _extract_user_id(authorization)

    if not payload.endpoint and not payload.subscription_id:
        raise HTTPException(
            status_code=400,
            detail="endpoint or subscription_id is required",
        )

    conditions = []
    if payload.endpoint:
        conditions.append(PushSubscription.endpoint == payload.endpoint)
    if payload.subscription_id:
        conditions.append(PushSubscription.id == payload.subscription_id)

    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.user_id == user_id,
            or_(*conditions),
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    sub.is_active = False
    sub.updated_at = datetime.utcnow()
    await db.commit()

    logger.info(
        "push_subscription_unsubscribed user_id=%s subscription_id=%s endpoint_hash=%s",
        user_id,
        sub.id,
        sub.endpoint_hash or _hash_value(sub.endpoint),
    )
    return {"status": "unsubscribed", "id": sub.id}


@router.delete("/unsubscribe/{subscription_id}")
async def unsubscribe_push_by_id(
    subscription_id: str,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Backward-compatible unsubscribe endpoint using a subscription ID."""
    return await unsubscribe_push(
        PushSubscriptionUnsubscribe(subscription_id=subscription_id),
        authorization=authorization,
        db=db,
    )


@router.get("/diagnostics", response_model=PushDiagnosticsResponse)
async def get_push_diagnostics(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Return server-side diagnostics for support and DevTools verification."""
    user_id = _extract_user_id(authorization)

    active_count = (
        await db.execute(
            select(func.count(PushSubscription.id)).where(
                PushSubscription.user_id == user_id,
                PushSubscription.is_active == True,
            )
        )
    ).scalar() or 0

    inactive_count = (
        await db.execute(
            select(func.count(PushSubscription.id)).where(
                PushSubscription.user_id == user_id,
                PushSubscription.is_active == False,
            )
        )
    ).scalar() or 0

    last_delivery = (
        await db.execute(
            select(DeliveryStatus)
            .join(NotificationLog, DeliveryStatus.log_id == NotificationLog.id)
            .where(NotificationLog.user_id == user_id)
            .order_by(desc(DeliveryStatus.created_at))
            .limit(1)
        )
    ).scalar_one_or_none()

    last_success = (
        await db.execute(
            select(func.max(PushSubscription.last_success_at)).where(
                PushSubscription.user_id == user_id
            )
        )
    ).scalar()

    return PushDiagnosticsResponse(
        vapid_configured=bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY),
        active_subscription_count=active_count,
        inactive_subscription_count=inactive_count,
        last_delivery_status=last_delivery.status if last_delivery else None,
        last_delivery_error=last_delivery.error_message if last_delivery else None,
        last_delivery_at=last_delivery.created_at if last_delivery else None,
        last_subscription_success_at=last_success,
        max_subscriptions_per_user=MAX_SUBSCRIPTIONS_PER_USER,
    )

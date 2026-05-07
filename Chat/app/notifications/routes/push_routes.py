"""
Push Subscription API Routes
==============================
Handles VAPID public key exchange, subscription registration,
listing, and deletion. All endpoints require JWT authentication.
"""

import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.notifications.models.push_subscription import PushSubscription
from app.notifications.schemas.push_schemas import (
    PushSubscriptionCreate,
    PushSubscriptionResponse,
    PushSubscriptionList,
    VAPIDPublicKeyResponse,
)

router = APIRouter(prefix="/notifications/push", tags=["Push Notifications"])
logger = logging.getLogger(__name__)

# Maximum subscriptions per user (prevent abuse)
MAX_SUBSCRIPTIONS_PER_USER = 10


def _extract_user_id(authorization: str = Header(None)) -> str:
    """Extract user ID from JWT token in Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    token = authorization.split(" ", 1)[1]
    user = get_current_user(token)
    user_id = user.get("id") or user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id


@router.get("/vapid-key", response_model=VAPIDPublicKeyResponse)
async def get_vapid_public_key():
    """Return the server's VAPID public key for push subscription."""
    public_key = getattr(settings, "VAPID_PUBLIC_KEY", None)
    if not public_key:
        raise HTTPException(
            status_code=503,
            detail="Push notifications not configured on server",
        )
    return VAPIDPublicKeyResponse(public_key=public_key)


@router.post("/subscribe", response_model=PushSubscriptionResponse)
async def subscribe_push(
    payload: PushSubscriptionCreate,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Register a new push subscription for the authenticated user."""
    user_id = _extract_user_id(authorization)

    # Rate limit: check existing subscription count
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
            detail=f"Maximum {MAX_SUBSCRIPTIONS_PER_USER} subscriptions allowed",
        )

    # Check if endpoint already exists (upsert)
    existing = await db.execute(
        select(PushSubscription).where(
            PushSubscription.endpoint == payload.endpoint
        )
    )
    existing_sub = existing.scalar_one_or_none()

    if existing_sub:
        # Update existing subscription
        existing_sub.p256dh_key = payload.keys.p256dh
        existing_sub.auth_key = payload.keys.auth
        existing_sub.user_id = user_id
        existing_sub.is_active = True
        existing_sub.user_agent = payload.user_agent
        existing_sub.device_name = payload.device_name
        sub = existing_sub
    else:
        # Create new subscription
        sub = PushSubscription(
            id=str(uuid.uuid4()),
            user_id=user_id,
            endpoint=payload.endpoint,
            p256dh_key=payload.keys.p256dh,
            auth_key=payload.keys.auth,
            user_agent=payload.user_agent,
            device_name=payload.device_name,
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db.add(sub)

    await db.commit()
    await db.refresh(sub)

    logger.info(f"Push subscription registered for user {user_id}")
    return PushSubscriptionResponse(
        id=sub.id,
        endpoint=sub.endpoint,
        device_name=sub.device_name,
        is_active=sub.is_active,
        created_at=sub.created_at,
    )


@router.get("/subscriptions", response_model=PushSubscriptionList)
async def list_subscriptions(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """List all push subscriptions for the authenticated user."""
    user_id = _extract_user_id(authorization)

    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.user_id == user_id,
            PushSubscription.is_active == True,
        )
    )
    subs = result.scalars().all()

    return PushSubscriptionList(
        subscriptions=[
            PushSubscriptionResponse(
                id=s.id,
                endpoint=s.endpoint,
                device_name=s.device_name,
                is_active=s.is_active,
                created_at=s.created_at,
            )
            for s in subs
        ],
        count=len(subs),
    )


@router.delete("/unsubscribe/{subscription_id}")
async def unsubscribe_push(
    subscription_id: str,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a push subscription."""
    user_id = _extract_user_id(authorization)

    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.id == subscription_id,
            PushSubscription.user_id == user_id,
        )
    )
    sub = result.scalar_one_or_none()

    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    sub.is_active = False
    await db.commit()

    return {"status": "unsubscribed", "id": subscription_id}

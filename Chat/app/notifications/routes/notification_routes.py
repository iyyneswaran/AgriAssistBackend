"""
Notification API Routes
========================
Handles notification listing, read/unread tracking, count endpoints,
pipeline triggering, and admin test endpoints.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Depends, Query, BackgroundTasks
from sqlalchemy import select, func, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.notifications.models.notification_log import NotificationLog
from app.notifications.models.notification_history import NotificationHistory
from app.notifications.schemas.notification_schemas import (
    NotificationItem,
    NotificationListResponse,
    NotificationMarkReadRequest,
    NotificationCountResponse,
    TestNotificationRequest,
)
from app.notifications.services.orchestrator import NotificationOrchestrator

router = APIRouter(prefix="/notifications", tags=["Notifications"])
logger = logging.getLogger(__name__)

orchestrator = NotificationOrchestrator()


def _extract_user_id(authorization: str = Header(None)) -> str:
    """Extract user ID from JWT Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization required")
    token = authorization.split(" ", 1)[1]
    user = get_current_user(token)
    user_id = user.get("id") or user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    unread_only: bool = Query(False),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """List notifications for the authenticated user with pagination and filters."""
    user_id = _extract_user_id(authorization)

    # Build query joining logs with history
    query = (
        select(NotificationLog, NotificationHistory)
        .join(
            NotificationHistory,
            NotificationHistory.log_id == NotificationLog.id,
        )
        .where(NotificationLog.user_id == user_id)
    )

    if severity:
        query = query.where(NotificationLog.severity == severity)
    if event_type:
        query = query.where(NotificationLog.event_type == event_type)
    if unread_only:
        query = query.where(NotificationHistory.is_read == False)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Count unread
    unread_query = (
        select(func.count())
        .select_from(
            select(NotificationHistory.id)
            .join(NotificationLog, NotificationHistory.log_id == NotificationLog.id)
            .where(
                NotificationLog.user_id == user_id,
                NotificationHistory.is_read == False,
            )
            .subquery()
        )
    )
    unread_count = (await db.execute(unread_query)).scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(desc(NotificationLog.sent_at)).offset(offset).limit(page_size)
    result = await db.execute(query)
    rows = result.all()

    notifications = []
    for log, history in rows:
        notifications.append(
            NotificationItem(
                id=history.id,
                title=log.title,
                body=log.body,
                severity=log.severity,
                event_type=log.event_type,
                is_read=history.is_read,
                is_dismissed=history.is_dismissed,
                sent_at=log.sent_at,
                read_at=history.read_at,
                payload=log.payload,
            )
        )

    return NotificationListResponse(
        notifications=notifications,
        total=total,
        page=page,
        page_size=page_size,
        unread_count=unread_count,
    )


@router.get("/count", response_model=NotificationCountResponse)
async def get_notification_count(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Get notification counts (total and unread) for the authenticated user."""
    user_id = _extract_user_id(authorization)

    total_q = select(func.count(NotificationHistory.id)).where(
        NotificationHistory.user_id == user_id
    )
    unread_q = select(func.count(NotificationHistory.id)).where(
        NotificationHistory.user_id == user_id,
        NotificationHistory.is_read == False,
    )

    total = (await db.execute(total_q)).scalar() or 0
    unread = (await db.execute(unread_q)).scalar() or 0

    return NotificationCountResponse(unread_count=unread, total_count=total)


@router.post("/mark-read")
async def mark_notifications_read(
    payload: NotificationMarkReadRequest,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Mark one or more notifications as read."""
    user_id = _extract_user_id(authorization)

    await db.execute(
        update(NotificationHistory)
        .where(
            NotificationHistory.id.in_(payload.notification_ids),
            NotificationHistory.user_id == user_id,
        )
        .values(is_read=True, read_at=datetime.utcnow())
    )
    await db.commit()

    return {"status": "ok", "marked_read": len(payload.notification_ids)}


@router.post("/mark-all-read")
async def mark_all_read(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Mark all notifications as read for the authenticated user."""
    user_id = _extract_user_id(authorization)

    result = await db.execute(
        update(NotificationHistory)
        .where(
            NotificationHistory.user_id == user_id,
            NotificationHistory.is_read == False,
        )
        .values(is_read=True, read_at=datetime.utcnow())
    )
    await db.commit()

    return {"status": "ok", "marked_read": result.rowcount}


@router.post("/dismiss/{notification_id}")
async def dismiss_notification(
    notification_id: str,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Dismiss a notification."""
    user_id = _extract_user_id(authorization)

    result = await db.execute(
        update(NotificationHistory)
        .where(
            NotificationHistory.id == notification_id,
            NotificationHistory.user_id == user_id,
        )
        .values(is_dismissed=True, dismissed_at=datetime.utcnow())
    )
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"status": "dismissed"}


@router.post("/evaluate")
async def trigger_evaluation(
    background_tasks: BackgroundTasks,
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    authorization: str = Header(None),
):
    """
    Trigger a notification pipeline evaluation for the authenticated user.
    Runs in background to avoid blocking the request.
    """
    user_id = _extract_user_id(authorization)

    background_tasks.add_task(
        orchestrator.run_pipeline,
        user_id=user_id,
        latitude=latitude,
        longitude=longitude,
    )

    return {
        "status": "evaluation_started",
        "message": "Notification pipeline evaluation triggered in background",
    }


@router.post("/test")
async def send_test_notification(
    payload: TestNotificationRequest,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Send a test notification (for development/debugging)."""
    user_id = _extract_user_id(authorization)

    from app.notifications.services.push_service import PushService
    push_svc = PushService()

    title = "🧪 Test Notification"
    body = payload.message or "This is a test notification from AgriAssist."

    log_id = await push_svc.send_notification(
        session=db,
        user_id=user_id,
        title=title,
        body=body,
        severity=payload.severity,
        event_type=payload.event_type,
    )

    return {"status": "sent", "notification_id": log_id}

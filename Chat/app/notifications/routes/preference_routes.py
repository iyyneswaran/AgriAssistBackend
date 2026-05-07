"""
Notification Preferences API Routes
=====================================
Manages per-user notification settings including category toggles,
quiet hours, severity filtering, and language preferences.
"""

import uuid
import logging
from datetime import datetime, time

from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.notifications.models.notification_preference import NotificationPreference
from app.notifications.schemas.preference_schemas import (
    NotificationPreferenceUpdate,
    NotificationPreferenceResponse,
)

router = APIRouter(prefix="/notifications/preferences", tags=["Notification Preferences"])
logger = logging.getLogger(__name__)


def _extract_user_id(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization required")
    token = authorization.split(" ", 1)[1]
    user = get_current_user(token)
    user_id = user.get("id") or user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id


@router.get("", response_model=NotificationPreferenceResponse)
async def get_preferences(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Get notification preferences for the authenticated user."""
    user_id = _extract_user_id(authorization)

    result = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        # Create default preferences
        prefs = NotificationPreference(
            id=str(uuid.uuid4()),
            user_id=user_id,
        )
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)

    return NotificationPreferenceResponse(
        enabled=prefs.enabled,
        irrigation_alerts=prefs.irrigation_alerts,
        disease_alerts=prefs.disease_alerts,
        drought_alerts=prefs.drought_alerts,
        flood_alerts=prefs.flood_alerts,
        resource_alerts=prefs.resource_alerts,
        system_alerts=prefs.system_alerts,
        quiet_hours_start=prefs.quiet_hours_start.strftime("%H:%M") if prefs.quiet_hours_start else None,
        quiet_hours_end=prefs.quiet_hours_end.strftime("%H:%M") if prefs.quiet_hours_end else None,
        min_severity=prefs.min_severity,
        language=prefs.language,
    )


@router.put("", response_model=NotificationPreferenceResponse)
async def update_preferences(
    payload: NotificationPreferenceUpdate,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Update notification preferences for the authenticated user."""
    user_id = _extract_user_id(authorization)

    result = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = NotificationPreference(
            id=str(uuid.uuid4()),
            user_id=user_id,
        )
        db.add(prefs)

    # Update only provided fields
    update_data = payload.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        if field_name in ("quiet_hours_start", "quiet_hours_end") and value:
            # Parse HH:MM string to time object
            try:
                h, m = value.split(":")
                value = time(int(h), int(m))
            except (ValueError, AttributeError):
                raise HTTPException(status_code=400, detail=f"Invalid time format: {value}")
        if field_name == "min_severity" and value not in ("info", "low", "medium", "high", "critical"):
            raise HTTPException(status_code=400, detail=f"Invalid severity: {value}")
        setattr(prefs, field_name, value)

    prefs.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(prefs)

    return NotificationPreferenceResponse(
        enabled=prefs.enabled,
        irrigation_alerts=prefs.irrigation_alerts,
        disease_alerts=prefs.disease_alerts,
        drought_alerts=prefs.drought_alerts,
        flood_alerts=prefs.flood_alerts,
        resource_alerts=prefs.resource_alerts,
        system_alerts=prefs.system_alerts,
        quiet_hours_start=prefs.quiet_hours_start.strftime("%H:%M") if prefs.quiet_hours_start else None,
        quiet_hours_end=prefs.quiet_hours_end.strftime("%H:%M") if prefs.quiet_hours_end else None,
        min_severity=prefs.min_severity,
        language=prefs.language,
    )

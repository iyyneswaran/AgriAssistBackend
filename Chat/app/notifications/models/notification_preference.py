"""Per-user notification preferences model."""

import uuid
from datetime import datetime, time
from sqlalchemy import String, DateTime, Boolean, Time, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Master toggle
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Per-category toggles
    irrigation_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    disease_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    drought_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    flood_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    resource_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    system_alerts: Mapped[bool] = mapped_column(Boolean, default=True)

    # Quiet hours (no notifications during this window)
    quiet_hours_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    quiet_hours_end: Mapped[time | None] = mapped_column(Time, nullable=True)

    # Minimum severity to receive push (info, low, medium, high, critical)
    min_severity: Mapped[str] = mapped_column(String(20), default="medium")

    # Language preference for AI-generated messages
    language: Mapped[str] = mapped_column(String(10), default="en")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

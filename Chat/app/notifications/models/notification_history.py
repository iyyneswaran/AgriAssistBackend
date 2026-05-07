"""Notification history model — user interaction tracking (read/dismiss/action)."""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class NotificationHistory(Base):
    __tablename__ = "notification_history"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    log_id: Mapped[str] = mapped_column(
        String, ForeignKey("notification_logs.id"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # User interaction state
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    clicked_action: Mapped[bool] = mapped_column(Boolean, default=False)
    action_taken_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

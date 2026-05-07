"""Delivery status model — tracks individual push delivery attempts."""

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class DeliveryStatus(Base):
    __tablename__ = "delivery_status"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    log_id: Mapped[str] = mapped_column(
        String, ForeignKey("notification_logs.id"), nullable=False, index=True
    )
    subscription_id: Mapped[str] = mapped_column(
        String, ForeignKey("push_subscriptions.id"), nullable=False
    )

    # Delivery outcome
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending, delivered, failed, expired
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

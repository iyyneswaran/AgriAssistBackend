"""General notification schemas for API responses."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NotificationItem(BaseModel):
    """A single notification in the user's notification list."""
    id: str
    title: str
    body: str
    severity: str
    event_type: str
    is_read: bool
    is_dismissed: bool
    sent_at: datetime
    read_at: Optional[datetime] = None
    payload: dict = Field(default_factory=dict)


class NotificationListResponse(BaseModel):
    """Paginated notification list response."""
    notifications: list[NotificationItem]
    total: int
    page: int
    page_size: int
    unread_count: int


class NotificationMarkReadRequest(BaseModel):
    """Request to mark notifications as read."""
    notification_ids: list[str]


class NotificationInteractionRequest(BaseModel):
    """Request to track notification click/open interactions."""
    notification_id: Optional[str] = None
    history_id: Optional[str] = None
    action: Optional[str] = None


class NotificationCountResponse(BaseModel):
    """Unread notification count."""
    unread_count: int
    total_count: int


class TestNotificationRequest(BaseModel):
    """Admin endpoint to trigger a test notification."""
    event_type: str = "smart_irrigation"
    severity: str = "medium"
    message: Optional[str] = None
    url: Optional[str] = None

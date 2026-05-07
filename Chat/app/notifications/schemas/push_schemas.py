"""Push subscription Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PushSubscriptionKeys(BaseModel):
    """Web Push subscription keys from the browser."""
    p256dh: str = Field(..., description="P-256 Diffie-Hellman public key")
    auth: str = Field(..., description="Authentication secret")


class PushSubscriptionCreate(BaseModel):
    """Request body for registering a push subscription."""
    endpoint: str = Field(..., description="Push service endpoint URL")
    keys: PushSubscriptionKeys
    device_name: Optional[str] = Field(None, max_length=100)
    user_agent: Optional[str] = None


class PushSubscriptionResponse(BaseModel):
    """Response after subscription creation."""
    id: str
    endpoint: str
    device_name: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PushSubscriptionList(BaseModel):
    """List of push subscriptions for a user."""
    subscriptions: list[PushSubscriptionResponse]
    count: int


class VAPIDPublicKeyResponse(BaseModel):
    """Response with the server's VAPID public key."""
    public_key: str

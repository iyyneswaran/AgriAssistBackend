"""Push subscription Pydantic schemas."""

from pydantic import BaseModel, Field, field_validator
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
    browser: Optional[str] = Field(None, max_length=80)
    platform: Optional[str] = Field(None, max_length=80)
    expiration_time: Optional[float] = Field(
        None, description="Browser PushSubscription.expirationTime in milliseconds"
    )
    content_encoding: str = Field("aes128gcm", max_length=30)

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("Push endpoint must use HTTPS")
        return value


class PushSubscriptionResponse(BaseModel):
    """Response after subscription creation."""
    id: str
    endpoint: str
    device_name: Optional[str]
    browser: Optional[str] = None
    platform: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    failure_count: int = 0

    class Config:
        from_attributes = True


class PushSubscriptionList(BaseModel):
    """List of push subscriptions for a user."""
    subscriptions: list[PushSubscriptionResponse]
    count: int


class VAPIDPublicKeyResponse(BaseModel):
    """Response with the server's VAPID public key."""
    public_key: str


class PushSubscriptionUnsubscribe(BaseModel):
    """Request body for removing a browser push subscription."""
    endpoint: Optional[str] = None
    subscription_id: Optional[str] = None


class PushDiagnosticsResponse(BaseModel):
    """Server-side diagnostics for the current user's push setup."""
    vapid_configured: bool
    active_subscription_count: int
    inactive_subscription_count: int
    last_delivery_status: Optional[str] = None
    last_delivery_error: Optional[str] = None
    last_delivery_at: Optional[datetime] = None
    last_subscription_success_at: Optional[datetime] = None
    max_subscriptions_per_user: int


class PushSubscriptionStatusResponse(BaseModel):
    """Current user's push subscription summary."""
    vapid_configured: bool
    subscriptions: list[PushSubscriptionResponse]

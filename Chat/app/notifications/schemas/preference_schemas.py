"""User notification preference schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import time


class NotificationPreferenceUpdate(BaseModel):
    """Request body for updating notification preferences."""
    enabled: Optional[bool] = None
    irrigation_alerts: Optional[bool] = None
    disease_alerts: Optional[bool] = None
    drought_alerts: Optional[bool] = None
    flood_alerts: Optional[bool] = None
    resource_alerts: Optional[bool] = None
    system_alerts: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, description="HH:MM format")
    quiet_hours_end: Optional[str] = Field(None, description="HH:MM format")
    min_severity: Optional[str] = Field(None, description="info, low, medium, high, critical")
    language: Optional[str] = Field(None, max_length=10)


class NotificationPreferenceResponse(BaseModel):
    """Response schema for notification preferences."""
    enabled: bool
    irrigation_alerts: bool
    disease_alerts: bool
    drought_alerts: bool
    flood_alerts: bool
    resource_alerts: bool
    system_alerts: bool
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    min_severity: str
    language: str

    class Config:
        from_attributes = True

"""Notification event Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NotificationEventCreate(BaseModel):
    """Internal schema for creating a notification event."""
    event_type: str = Field(..., description="Type: smart_irrigation, disease_warning, drought, flood, resource_opt, iot_offline")
    severity: str = Field(..., description="Severity: info, low, medium, high, critical")
    confidence: int = Field(..., ge=0, le=100, description="Confidence score 0-100")
    situation: str = Field(..., description="What is happening")
    impact: str = Field(..., description="What this means for the farmer")
    recommended_action: str = Field(..., description="What the farmer should do")
    farm_id: Optional[str] = None
    zone_id: Optional[str] = None
    risk_scores: dict = Field(default_factory=dict)
    source_data: dict = Field(default_factory=dict)
    dedup_hash: Optional[str] = None


class NotificationEventResponse(BaseModel):
    """Response schema for notification events."""
    id: str
    user_id: str
    event_type: str
    severity: str
    confidence: int
    situation: str
    impact: str
    recommended_action: str
    farm_id: Optional[str]
    zone_id: Optional[str]
    risk_scores: dict
    created_at: datetime

    class Config:
        from_attributes = True


class RiskScores(BaseModel):
    """Computed risk scores from the risk engine."""
    drought_risk: float = Field(0.0, ge=0, le=100)
    flood_risk: float = Field(0.0, ge=0, le=100)
    disease_risk: float = Field(0.0, ge=0, le=100)
    irrigation_efficiency: float = Field(0.0, ge=0, le=100)
    crop_stress: float = Field(0.0, ge=0, le=100)


class FarmContext(BaseModel):
    """Aggregated farm context for the notification pipeline."""
    user_id: str
    farm_id: Optional[str] = None
    zone_id: Optional[str] = None

    # IoT sensor data
    sensor_temperature: Optional[float] = None
    sensor_humidity: Optional[float] = None
    sensor_moisture: Optional[float] = None
    sensor_last_seen: Optional[datetime] = None

    # GEE analytics
    gee_ndvi: Optional[float] = None
    gee_temperature: Optional[float] = None
    gee_humidity: Optional[float] = None
    gee_moisture: Optional[float] = None
    gee_ph: Optional[float] = None
    gee_elevation: Optional[float] = None

    # Weather forecast
    weather_temperature: Optional[float] = None
    weather_humidity: Optional[float] = None
    weather_precipitation: Optional[float] = None
    weather_wind_speed: Optional[float] = None
    weather_rain_probability: Optional[float] = None
    weather_forecast_rain_mm: Optional[float] = None
    weather_condition_code: Optional[int] = None

    # Disease analysis
    disease_detected: bool = False
    disease_type: Optional[str] = None
    disease_confidence: Optional[float] = None

    # Farm metadata
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Timestamps
    aggregated_at: datetime = Field(default_factory=datetime.utcnow)

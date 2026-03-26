from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SensorDataSubmit(BaseModel):
    """Request body for ESP32 sensor data submission."""
    user_id: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    soil_moisture: Optional[float] = None
    raw_payload: Optional[dict] = None


class SensorDataResponse(BaseModel):
    """Response for latest sensor reading."""
    id: str
    user_id: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    soil_moisture: Optional[float] = None
    recorded_at: datetime


class AnalysisItem(BaseModel):
    """A single analysis result card."""
    id: str
    title: str
    category: str  # irrigation, disease, stress, climate, growth, detection
    severity: str  # low, medium, high, critical
    icon: str  # emoji icon for frontend
    summary: str
    recommendation: str
    score: Optional[float] = None  # 0-100 numeric score where applicable
    details: Optional[dict] = None  # extra data for frontend display


class AnalysisResponse(BaseModel):
    """Full analysis response with all prediction indices."""
    sensor: Optional[SensorDataResponse] = None
    analyses: List[AnalysisItem] = []
    computed_at: datetime
    has_sensor_data: bool = False

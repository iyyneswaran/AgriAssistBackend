"""
Pydantic schemas for the Scan Crop disease detection feature.
Strict validation for image predictions, sensor context, and remedy responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class ScanPredictResponse(BaseModel):
    """Response from the /predict endpoint."""
    disease_label: str = Field(..., description="Raw label e.g. 'tomato_early_blight'")
    crop_name: str = Field(..., description="Extracted crop name e.g. 'Tomato'")
    disease_name: str = Field(..., description="Human-readable disease e.g. 'Early Blight'")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence 0-1")
    is_healthy: bool = Field(False, description="True when prediction is a healthy class")


class SensorContext(BaseModel):
    """IoT sensor data sent from frontend or fetched from hardware."""
    soil_moisture: Optional[float] = Field(None, ge=0, le=100, description="Soil moisture %")
    temperature: Optional[float] = Field(None, ge=-10, le=60, description="Temperature °C")
    humidity: Optional[float] = Field(None, ge=0, le=100, description="Humidity %")
    ph_value: Optional[float] = Field(None, ge=0, le=14, description="Soil pH value")


class RemedyRequest(BaseModel):
    """Request body for the /remedy endpoint."""
    disease_label: str = Field(..., min_length=1, max_length=100)
    crop_type: Optional[str] = Field(None, max_length=50)
    sensor_data: Optional[SensorContext] = None


class RemedyResponse(BaseModel):
    """Structured AI-generated remedy response."""
    explanation: str = Field(..., description="Clear explanation of the disease")
    treatment_steps: List[str] = Field(default_factory=list, description="Step-by-step treatment")
    preventive_measures: List[str] = Field(default_factory=list, description="Prevention tips")
    sensor_advice: Optional[str] = Field(None, description="Personalized advice from sensor data")
    source: str = Field("ai", description="'ai' or 'fallback'")


class ScanAnalyzeResponse(BaseModel):
    """Combined response from the /analyze endpoint (predict + remedy)."""
    prediction: ScanPredictResponse
    remedy: RemedyResponse

from pydantic import BaseModel
from typing import List, Optional


class GeoAnalyzeRequest(BaseModel):
    farmer_id: Optional[str] = None
    latitude: float
    longitude: float


class GeoAnalyzeResponse(BaseModel):
    ndvi: dict
    rainfall_forecast: dict
    temperature_forecast: dict
    alerts: List[str]
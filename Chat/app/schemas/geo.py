from pydantic import BaseModel
from typing import List


class GeoAnalyzeRequest(BaseModel):
    farmer_id: str
    latitude: float
    longitude: float


class GeoAnalyzeResponse(BaseModel):
    ndvi: dict
    rainfall_forecast: dict
    temperature_forecast: dict
    alerts: List[str]
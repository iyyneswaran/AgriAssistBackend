"""
Risk Engine
============
Calculates composite risk scores from FarmContext data.
This is the third stage of the notification pipeline.
"""

import logging
from app.notifications.schemas.event_schemas import FarmContext, RiskScores

logger = logging.getLogger(__name__)


class RiskEngine:
    """Calculates drought, flood, disease, irrigation efficiency, and crop stress risk scores."""

    def calculate(self, ctx: FarmContext) -> RiskScores:
        return RiskScores(
            drought_risk=self._drought_risk(ctx),
            flood_risk=self._flood_risk(ctx),
            disease_risk=self._disease_risk(ctx),
            irrigation_efficiency=self._irrigation_efficiency(ctx),
            crop_stress=self._crop_stress(ctx),
        )

    def _drought_risk(self, ctx: FarmContext) -> float:
        score = 0.0
        if ctx.sensor_moisture is not None:
            score += max(0, (50 - ctx.sensor_moisture) * 1.5)
        if ctx.gee_ndvi is not None and ctx.gee_ndvi < 0.4:
            score += (0.4 - ctx.gee_ndvi) * 100
        if ctx.weather_forecast_rain_mm is not None and ctx.weather_forecast_rain_mm < 2:
            score += 15
        if ctx.sensor_temperature is not None and ctx.sensor_temperature > 35:
            score += min(20, (ctx.sensor_temperature - 35) * 4)
        return min(100, max(0, score))

    def _flood_risk(self, ctx: FarmContext) -> float:
        score = 0.0
        if ctx.weather_forecast_rain_mm is not None:
            score += min(40, ctx.weather_forecast_rain_mm * 0.8)
        if ctx.sensor_moisture is not None and ctx.sensor_moisture > 80:
            score += (ctx.sensor_moisture - 80) * 2
        if ctx.gee_elevation is not None and ctx.gee_elevation < 50:
            score += 15
        if ctx.weather_rain_probability is not None and ctx.weather_rain_probability > 70:
            score += 15
        return min(100, max(0, score))

    def _disease_risk(self, ctx: FarmContext) -> float:
        score = 0.0
        humidity = ctx.sensor_humidity or ctx.weather_humidity
        temp = ctx.sensor_temperature or ctx.weather_temperature
        if humidity is not None and humidity > 60:
            score += (humidity - 60) * 1.5
        if temp is not None and 20 <= temp <= 30:
            score += 20
        if ctx.disease_detected:
            score += 40
        return min(100, max(0, score))

    def _irrigation_efficiency(self, ctx: FarmContext) -> float:
        score = 80.0  # baseline good
        temp = ctx.sensor_temperature or ctx.weather_temperature
        humidity = ctx.sensor_humidity or ctx.weather_humidity
        if temp is not None and temp > 30 and humidity is not None and humidity < 50:
            score -= min(30, (temp - 30) * 3)
        if ctx.weather_wind_speed is not None and ctx.weather_wind_speed > 15:
            score -= 10
        if ctx.weather_rain_probability is not None and ctx.weather_rain_probability > 60:
            score += 10  # natural rain helps
        return min(100, max(0, score))

    def _crop_stress(self, ctx: FarmContext) -> float:
        score = 0.0
        temp = ctx.sensor_temperature or ctx.weather_temperature
        if temp is not None:
            if temp > 40: score += 40
            elif temp > 35: score += (temp - 35) * 6
        if ctx.sensor_moisture is not None and ctx.sensor_moisture < 25:
            score += (25 - ctx.sensor_moisture) * 2
        humidity = ctx.sensor_humidity or ctx.weather_humidity
        if humidity is not None and humidity > 90:
            score += 15
        if ctx.gee_ndvi is not None and ctx.gee_ndvi < 0.25:
            score += 20
        return min(100, max(0, score))

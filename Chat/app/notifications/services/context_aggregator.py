"""
Context Aggregator Service
===========================
Combines IoT sensor data, GEE analytics, weather forecasts, and disease outputs
into a unified FarmContext object for downstream notification processing.

This is the first stage of the notification pipeline.
"""

import logging
from typing import Optional
from datetime import datetime

import httpx

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.db.models.sensor_data import SensorData
from app.notifications.schemas.event_schemas import FarmContext
from sqlalchemy import select, desc

logger = logging.getLogger(__name__)

# Sensor hardware URL for live readings
SENSOR_HARDWARE_URL = settings.SENSOR_HARDWARE_URL


class ContextAggregator:
    """
    Aggregates data from all sources into a FarmContext.

    Data Sources:
    1. IoT Sensors (ESP32 via ngrok tunnel)
    2. Google Earth Engine (GEE via FarmMetricsService)
    3. Open-Meteo Weather API (current + forecast)
    4. Historical sensor data from PostgreSQL
    """

    def __init__(self) -> None:
        self._gee_service = None

    def _get_gee_service(self):
        """Lazy-load GEE service to avoid import-time initialization."""
        if self._gee_service is None:
            try:
                from app.services.geo.farm_metrics_service import FarmMetricsService
                self._gee_service = FarmMetricsService()
            except Exception as e:
                logger.warning(f"Could not initialize GEE service: {e}")
        return self._gee_service

    async def aggregate(
        self,
        user_id: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        farm_id: Optional[str] = None,
        zone_id: Optional[str] = None,
    ) -> FarmContext:
        """
        Build a complete FarmContext by fetching from all data sources.
        All fetches are fault-tolerant — partial data is still useful.
        """
        context = FarmContext(
            user_id=user_id,
            farm_id=farm_id,
            zone_id=zone_id,
            latitude=latitude,
            longitude=longitude,
        )

        # Fetch all sources concurrently where possible
        await self._fetch_sensor_data(context)
        if latitude is not None and longitude is not None:
            await self._fetch_gee_data(context, latitude, longitude)
            await self._fetch_weather_data(context, latitude, longitude)

        # Check last sensor heartbeat
        await self._check_sensor_heartbeat(context, user_id)

        context.aggregated_at = datetime.utcnow()
        return context

    async def _fetch_sensor_data(self, context: FarmContext) -> None:
        """Fetch live sensor readings from ESP32 hardware or database."""
        success = False
        if SENSOR_HARDWARE_URL:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        f"{SENSOR_HARDWARE_URL}/api/sensors",
                        headers={"ngrok-skip-browser-warning": "true"},
                        timeout=8,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        context.sensor_temperature = data.get("temperature")
                        context.sensor_humidity = data.get("humidity")
                        context.sensor_moisture = data.get("soil_moisture")
                        context.sensor_last_seen = datetime.utcnow()
                        success = True
                        logger.debug(f"Live sensor data fetched: T={context.sensor_temperature}, H={context.sensor_humidity}, M={context.sensor_moisture}")
            except Exception as e:
                logger.warning(f"Failed to fetch live sensor data: {e}")

        if not success:
            logger.debug("Falling back to latest sensor data from database")
            try:
                async with AsyncSessionLocal() as session:
                    result = await session.execute(
                        select(SensorData)
                        .where(SensorData.user_id == context.user_id)
                        .order_by(desc(SensorData.recorded_at))
                        .limit(1)
                    )
                    record = result.scalar_one_or_none()
                    if record:
                        context.sensor_temperature = record.temperature
                        context.sensor_humidity = record.humidity
                        context.sensor_moisture = record.soil_moisture
                        context.sensor_last_seen = record.recorded_at
                        logger.debug(f"DB sensor data fetched: T={context.sensor_temperature}, H={context.sensor_humidity}, M={context.sensor_moisture}")
            except Exception as e:
                logger.warning(f"Failed to fetch sensor data from DB: {e}")

    async def _fetch_gee_data(
        self, context: FarmContext, lat: float, lng: float
    ) -> None:
        """Fetch Google Earth Engine analytics."""
        service = self._get_gee_service()
        if service is None:
            return

        try:
            gee_data = service.get_metrics(lat, lng)
            context.gee_temperature = gee_data.get("temperature_celsius")
            context.gee_humidity = gee_data.get("humidity_percent")
            context.gee_moisture = gee_data.get("soil_moisture_mm")
            context.gee_ph = gee_data.get("soil_ph")
            context.gee_ndvi = gee_data.get("ndvi")
            context.gee_elevation = gee_data.get("elevation")
            logger.debug(f"GEE data fetched: NDVI={context.gee_ndvi}, pH={context.gee_ph}")
        except Exception as e:
            logger.warning(f"Failed to fetch GEE data: {e}")

    async def _fetch_weather_data(
        self, context: FarmContext, lat: float, lng: float
    ) -> None:
        """Fetch current weather and forecast from Open-Meteo."""
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lng}"
                f"&current_weather=true"
                f"&hourly=relativehumidity_2m,precipitation_probability,precipitation"
                f"&daily=precipitation_sum,precipitation_probability_max"
                f"&timezone=auto"
                f"&forecast_days=2"
            )
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    current = data.get("current_weather", {})
                    context.weather_temperature = current.get("temperature")
                    context.weather_wind_speed = current.get("windspeed")
                    context.weather_condition_code = current.get("weathercode")

                    # Extract current-hour humidity and precipitation
                    hourly = data.get("hourly", {})
                    current_time = current.get("time", "")
                    current_hour = current_time[:13] + ":00" if current_time else ""
                    times = hourly.get("time", [])
                    if current_hour in times:
                        idx = times.index(current_hour)
                        humidity_list = hourly.get("relativehumidity_2m", [])
                        if idx < len(humidity_list):
                            context.weather_humidity = humidity_list[idx]
                        precip_prob_list = hourly.get("precipitation_probability", [])
                        if idx < len(precip_prob_list):
                            context.weather_rain_probability = precip_prob_list[idx]

                    # Extract forecast rain totals (next day)
                    daily = data.get("daily", {})
                    daily_precip = daily.get("precipitation_sum", [])
                    if len(daily_precip) > 1:
                        context.weather_forecast_rain_mm = daily_precip[1]
                    elif daily_precip:
                        context.weather_forecast_rain_mm = daily_precip[0]

                    daily_precip_prob = daily.get("precipitation_probability_max", [])
                    if daily_precip_prob and context.weather_rain_probability is None:
                        context.weather_rain_probability = daily_precip_prob[0]

                    logger.debug(
                        f"Weather data fetched: T={context.weather_temperature}, "
                        f"Rain%={context.weather_rain_probability}, "
                        f"ForecastRain={context.weather_forecast_rain_mm}mm"
                    )
        except Exception as e:
            logger.warning(f"Failed to fetch weather data: {e}")

    async def _check_sensor_heartbeat(
        self, context: FarmContext, user_id: str
    ) -> None:
        """Check when the last sensor reading was recorded in the database."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(SensorData.recorded_at)
                    .where(SensorData.user_id == user_id)
                    .order_by(desc(SensorData.recorded_at))
                    .limit(1)
                )
                last_recorded = result.scalar_one_or_none()
                if last_recorded and context.sensor_last_seen is None:
                    context.sensor_last_seen = last_recorded
        except Exception as e:
            logger.warning(f"Failed to check sensor heartbeat: {e}")

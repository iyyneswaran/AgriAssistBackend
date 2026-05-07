"""
Sensor Data API — Handles IoT sensor data ingestion from ESP32,
retrieval of latest readings, and advanced analysis computation.
"""

from fastapi import APIRouter, HTTPException, Header, Query, BackgroundTasks
from app.schemas.sensor_schemas import SensorDataSubmit, SensorDataResponse, AnalysisItem, AnalysisResponse
from app.services.analysis.analysis_service import AdvancedAnalysisService
from app.db.session import AsyncSessionLocal
from app.db.models.sensor_data import SensorData
from sqlalchemy import select, desc
from datetime import datetime
import uuid
import os
import logging

router = APIRouter(prefix="/sensor-data", tags=["Sensor Data"])
logger = logging.getLogger(__name__)

SENSOR_API_KEY = os.getenv("SENSOR_API_KEY")
SENSOR_HARDWARE_URL = os.getenv("SENSOR_HARDWARE_URL")

analysis_service = AdvancedAnalysisService()


def _verify_sensor_key(x_sensor_key: str = Header(None)):
    """Validate the ESP32 sensor API key."""
    if not x_sensor_key or x_sensor_key != SENSOR_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing sensor API key")


async def _trigger_notification_pipeline(user_id: str):
    """Trigger the notification pipeline in background after sensor data ingestion."""
    try:
        from app.notifications.services.orchestrator import NotificationOrchestrator
        orchestrator = NotificationOrchestrator()
        await orchestrator.run_pipeline(user_id=user_id)
    except Exception as e:
        logger.error(f"Notification pipeline error for user {user_id}: {e}")


# ─────────────────────────────────────────────
# POST /api/sensor-data — ESP32 submits readings
# ─────────────────────────────────────────────
@router.post("")
async def submit_sensor_data(
    payload: SensorDataSubmit,
    background_tasks: BackgroundTasks,
    x_sensor_key: str = Header(None),
):
    """Receive sensor data from ESP32 device."""
    _verify_sensor_key(x_sensor_key)

    try:
        async with AsyncSessionLocal() as session:
            sensor_record = SensorData(
                id=str(uuid.uuid4()),
                user_id=payload.user_id,
                temperature=payload.temperature,
                humidity=payload.humidity,
                soil_moisture=payload.soil_moisture,
                raw_payload=payload.raw_payload or {},
                recorded_at=datetime.utcnow(),
            )
            session.add(sensor_record)
            await session.commit()

        # Trigger notification pipeline in background
        background_tasks.add_task(_trigger_notification_pipeline, payload.user_id)

        return {
            "status": "success",
            "message": "Sensor data recorded",
            "id": sensor_record.id,
            "recorded_at": sensor_record.recorded_at.isoformat(),
        }
    except Exception as e:
        logger.error(f"Error saving sensor data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save sensor data: {str(e)}")


# ─────────────────────────────────────────────
# GET /api/sensor-data/latest/{user_id}
# ─────────────────────────────────────────────
@router.get("/latest/{user_id}", response_model=SensorDataResponse)
async def get_latest_sensor_data(user_id: str):
    """Get the most recent sensor reading for a user."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(SensorData)
                .where(SensorData.user_id == user_id)
                .order_by(desc(SensorData.recorded_at))
                .limit(1)
            )
            record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=404, detail="No sensor data found for this user")

        return SensorDataResponse(
            id=record.id,
            user_id=record.user_id,
            temperature=record.temperature,
            humidity=record.humidity,
            soil_moisture=record.soil_moisture,
            recorded_at=record.recorded_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sensor data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sensor data: {str(e)}")


# ─────────────────────────────────────────────
# GET /api/sensor-data/live
# ─────────────────────────────────────────────
@router.get("/live")
async def get_live_hardware_data():
    """Fetch live sensor data directly from ESP32 hardware via ngrok tunnel (proxied to bypass CORS)."""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SENSOR_HARDWARE_URL}/api/sensors",
                headers={"ngrok-skip-browser-warning": "true"},
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code in (502, 504):
                raise HTTPException(status_code=503, detail="device_offline")
            else:
                raise HTTPException(status_code=resp.status_code, detail="Hardware API error")
    except httpx.RequestError as e:
        logger.warning(f"Could not connect to sensor hardware ngrok tunnel: {e}")
        raise HTTPException(status_code=503, detail="device_offline")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching live sensor data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch live sensor data")


# ─────────────────────────────────────────────
# GET /api/sensor-data/analysis/{user_id}
# ─────────────────────────────────────────────
@router.get("/analysis/{user_id}")
async def get_sensor_analysis(
    user_id: str,
    latitude: float = Query(None),
    longitude: float = Query(None),
):
    """
    Compute advanced analysis combining IoT sensor data with GEE regional
    and Open-Meteo weather data. Returns all 8+ analysis indices.
    """
    # 1. Fetch live sensor data from ESP32 hardware via ngrok
    sensor_temp = None
    sensor_humidity = None
    sensor_moisture = None
    hardware_data = None

    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SENSOR_HARDWARE_URL}/api/sensors",
                headers={"ngrok-skip-browser-warning": "true"},
                timeout=10,
            )
            if resp.status_code == 200:
                hardware_data = resp.json()
                sensor_temp = hardware_data.get("temperature")
                sensor_humidity = hardware_data.get("humidity")
                sensor_moisture = hardware_data.get("soil_moisture")
    except Exception as e:
        logger.warning(f"Could not fetch live sensor data from hardware: {e}")

    # 2. Fetch GEE regional data (if coordinates provided)
    gee_temp = None
    gee_humidity = None
    gee_moisture = None
    gee_ph = None

    if latitude is not None and longitude is not None:
        try:
            from app.services.geo.farm_metrics_service import FarmMetricsService
            farm_metrics_svc = FarmMetricsService()
            gee_data = farm_metrics_svc.get_metrics(latitude, longitude)
            gee_temp = gee_data.get("temperature_celsius")
            gee_humidity = gee_data.get("humidity_percent")
            gee_moisture = gee_data.get("soil_moisture_mm")
            gee_ph = gee_data.get("soil_ph")
        except Exception as e:
            logger.warning(f"Could not fetch GEE data for analysis: {e}")

    # 3. Fetch weather data from Open-Meteo (if coordinates provided)
    weather_temp = None
    weather_humidity = None

    if latitude is not None and longitude is not None:
        try:
            import httpx
            url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true&hourly=relativehumidity_2m&timezone=auto"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10)
                if resp.status_code == 200:
                    weather_json = resp.json()
                    weather_temp = weather_json.get("current_weather", {}).get("temperature")
                    # Get current hour humidity
                    hourly = weather_json.get("hourly", {})
                    current_time = weather_json.get("current_weather", {}).get("time", "")
                    current_hour = current_time[:13] + ":00" if current_time else ""
                    times = hourly.get("time", [])
                    if current_hour in times:
                        idx = times.index(current_hour)
                        humidity_list = hourly.get("relativehumidity_2m", [])
                        if idx < len(humidity_list):
                            weather_humidity = humidity_list[idx]
        except Exception as e:
            logger.warning(f"Could not fetch weather data for analysis: {e}")

    # 4. Run all analyses
    analyses_raw = analysis_service.compute_all(
        sensor_temp=sensor_temp,
        sensor_humidity=sensor_humidity,
        sensor_moisture=sensor_moisture,
        gee_temp=gee_temp,
        gee_humidity=gee_humidity,
        gee_moisture=gee_moisture,
        gee_ph=gee_ph,
        weather_temp=weather_temp,
        weather_humidity=weather_humidity,
    )

    # Build sensor response
    sensor_response = None
    if hardware_data:
        sensor_response = {
            "temperature": hardware_data.get("temperature"),
            "humidity": hardware_data.get("humidity"),
            "soil_moisture": hardware_data.get("soil_moisture"),
        }

    return {
        "sensor": sensor_response,
        "analyses": analyses_raw,
        "computed_at": datetime.utcnow().isoformat(),
        "has_sensor_data": hardware_data is not None,
    }

"""
Remedy Service — Generates contextual disease remedies using Sarvam AI.
Falls back to rule-based remedies when the API is unavailable.
"""

import httpx
import re
import logging
from typing import Optional
from app.core.config import settings
from app.schemas.scan_schemas import SensorContext
from app.services.scan.fallback_remedies import get_fallback_remedy

logger = logging.getLogger(__name__)

# Sarvam AI endpoint (same as chat_service.py)
_SARVAM_URL = "https://api.sarvam.ai/v1/chat/completions"


def _build_remedy_prompt(
    disease_label: str,
    crop_type: Optional[str],
    sensor: Optional[SensorContext],
) -> str:
    """Build a structured prompt for Sarvam AI."""
    parts = disease_label.split("_")
    crop = crop_type or parts[0].capitalize()
    disease = " ".join(p.capitalize() for p in parts[1:])

    prompt = f"""You are an expert agricultural scientist. A farmer's crop has been diagnosed with a disease.

**Crop:** {crop}
**Disease Detected:** {disease}
"""

    # Add sensor context if available
    if sensor:
        prompt += "\n**Live Farm Sensor Data:**\n"
        if sensor.temperature is not None:
            prompt += f"- Temperature: {sensor.temperature}°C\n"
        if sensor.humidity is not None:
            prompt += f"- Humidity: {sensor.humidity}%\n"
        if sensor.soil_moisture is not None:
            prompt += f"- Soil Moisture: {sensor.soil_moisture}%\n"
        if sensor.ph_value is not None:
            prompt += f"- Soil pH: {sensor.ph_value}\n"

    prompt += """
Please respond in the following EXACT format. Use simple, farmer-friendly language:

EXPLANATION:
[1-2 sentence clear explanation of what this disease is and how it affects the crop]

TREATMENT:
1. [Step 1]
2. [Step 2]
3. [Step 3]
4. [Step 4]

PREVENTION:
1. [Measure 1]
2. [Measure 2]
3. [Measure 3]
4. [Measure 4]

SENSOR_ADVICE:
[If sensor data was provided above, give 1-2 sentences of personalized advice based on the current temperature, humidity, moisture, and pH values. If no sensor data, write "No sensor data available."]
"""
    return prompt.strip()


def _parse_remedy_response(raw: str) -> dict:
    """Parse the structured AI response into sections."""
    result = {
        "explanation": "",
        "treatment_steps": [],
        "preventive_measures": [],
        "sensor_advice": None,
        "source": "ai",
    }

    # Extract sections using regex
    explanation_match = re.search(
        r"EXPLANATION:\s*\n(.*?)(?=\nTREATMENT:|\Z)", raw, re.DOTALL
    )
    treatment_match = re.search(
        r"TREATMENT:\s*\n(.*?)(?=\nPREVENTION:|\Z)", raw, re.DOTALL
    )
    prevention_match = re.search(
        r"PREVENTION:\s*\n(.*?)(?=\nSENSOR_ADVICE:|\Z)", raw, re.DOTALL
    )
    sensor_match = re.search(
        r"SENSOR_ADVICE:\s*\n(.*?)$", raw, re.DOTALL
    )

    if explanation_match:
        result["explanation"] = explanation_match.group(1).strip()

    if treatment_match:
        steps = re.findall(r"\d+\.\s*(.+)", treatment_match.group(1))
        result["treatment_steps"] = [s.strip() for s in steps if s.strip()]

    if prevention_match:
        measures = re.findall(r"\d+\.\s*(.+)", prevention_match.group(1))
        result["preventive_measures"] = [m.strip() for m in measures if m.strip()]

    if sensor_match:
        advice = sensor_match.group(1).strip()
        if advice and "no sensor data" not in advice.lower():
            result["sensor_advice"] = advice

    # Fallback if parsing failed to extract meaningful content
    if not result["explanation"] and not result["treatment_steps"]:
        result["explanation"] = raw.strip()[:500]
        result["source"] = "ai"

    return result


async def _fetch_live_sensor_data() -> Optional[SensorContext]:
    """Fetch live sensor data from ESP32 hardware endpoint."""
    hardware_url = settings.SENSOR_HARDWARE_URL if hasattr(settings, "SENSOR_HARDWARE_URL") else None
    if not hardware_url:
        # Try environment variable directly
        import os
        hardware_url = os.getenv("SENSOR_HARDWARE_URL")

    if not hardware_url:
        logger.debug("[Remedy] No SENSOR_HARDWARE_URL configured, skipping live sensor fetch.")
        return None

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{hardware_url}/api/sensors",
                headers={"ngrok-skip-browser-warning": "true"},
                timeout=5.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                return SensorContext(
                    temperature=data.get("temperature"),
                    humidity=data.get("humidity"),
                    soil_moisture=data.get("soil_moisture"),
                    ph_value=data.get("ph", data.get("ph_value")),
                )
    except Exception as e:
        logger.warning(f"[Remedy] Could not fetch live sensor data: {e}")

    return None


async def generate_remedy(
    disease_label: str,
    crop_type: Optional[str] = None,
    sensor_data: Optional[SensorContext] = None,
) -> dict:
    """
    Generate an AI-powered remedy using Sarvam AI.
    Falls back to static remedies if the API fails.
    """

    # Merge frontend sensor data with live hardware data
    live_sensor = await _fetch_live_sensor_data()
    merged_sensor = sensor_data or live_sensor
    if sensor_data and live_sensor:
        # Use frontend values as overrides, fill gaps with live data
        merged_sensor = SensorContext(
            temperature=sensor_data.temperature if sensor_data.temperature is not None else live_sensor.temperature,
            humidity=sensor_data.humidity if sensor_data.humidity is not None else live_sensor.humidity,
            soil_moisture=sensor_data.soil_moisture if sensor_data.soil_moisture is not None else live_sensor.soil_moisture,
            ph_value=sensor_data.ph_value if sensor_data.ph_value is not None else live_sensor.ph_value,
        )

    # Check for "healthy" predictions — no disease remedy needed
    if "healthy" in disease_label.lower():
        fallback = get_fallback_remedy(disease_label)
        if merged_sensor:
            fallback["sensor_advice"] = _build_sensor_summary(merged_sensor)
        return fallback

    # Check if API key is available
    api_key = settings.SARWAM_API_KEY
    if not api_key:
        logger.warning("[Remedy] SARWAM_API_KEY not configured. Using fallback remedies.")
        fallback = get_fallback_remedy(disease_label)
        if merged_sensor:
            fallback["sensor_advice"] = _build_sensor_summary(merged_sensor)
        return fallback

    # Build prompt and call Sarvam AI
    prompt = _build_remedy_prompt(disease_label, crop_type, merged_sensor)

    system_prompt = (
        "You are an expert agricultural advisor helping Indian farmers with crop disease management. "
        "Provide practical, actionable advice using locally available treatments. "
        "Be concise and use simple language. Follow the requested output format exactly."
    )

    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": api_key,
    }

    payload = {
        "model": "sarvam-m",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(_SARVAM_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            # Strip <think> blocks (Sarvam-m sometimes includes reasoning)
            content = re.sub(r"<think>.*?</think>\s*", "", content, flags=re.DOTALL)
            content = content.replace("<think>\n", "").replace("<think>", "").strip()

            result = _parse_remedy_response(content)
            return result

    except httpx.TimeoutException:
        logger.error("[Remedy] Sarvam AI request timed out. Using fallback.")
    except httpx.HTTPStatusError as e:
        logger.error(f"[Remedy] Sarvam AI HTTP error {e.response.status_code}. Using fallback.")
    except Exception as e:
        logger.error(f"[Remedy] Sarvam AI error: {type(e).__name__}: {e}. Using fallback.")

    # Fallback
    fallback = get_fallback_remedy(disease_label)
    if merged_sensor:
        fallback["sensor_advice"] = _build_sensor_summary(merged_sensor)
    return fallback


def _build_sensor_summary(sensor: SensorContext) -> str:
    """Build a simple sensor summary for fallback mode."""
    parts = []
    if sensor.temperature is not None:
        if sensor.temperature > 35:
            parts.append(f"Temperature is high ({sensor.temperature}°C). Ensure adequate watering and consider shade protection.")
        elif sensor.temperature < 15:
            parts.append(f"Temperature is low ({sensor.temperature}°C). Disease spread may slow, but monitor for cold stress.")
        else:
            parts.append(f"Temperature ({sensor.temperature}°C) is within normal range.")

    if sensor.humidity is not None:
        if sensor.humidity > 80:
            parts.append(f"High humidity ({sensor.humidity}%) favors fungal growth. Ensure good air circulation.")
        elif sensor.humidity < 30:
            parts.append(f"Low humidity ({sensor.humidity}%). Spider mites may become more active.")

    if sensor.soil_moisture is not None:
        if sensor.soil_moisture < 30:
            parts.append(f"Soil moisture is low ({sensor.soil_moisture}%). Irrigate soon.")
        elif sensor.soil_moisture > 80:
            parts.append(f"Soil moisture is high ({sensor.soil_moisture}%). Risk of root rot; reduce irrigation.")

    if sensor.ph_value is not None:
        if sensor.ph_value < 5.5:
            parts.append(f"Soil pH is acidic ({sensor.ph_value}). Consider liming to improve nutrient availability.")
        elif sensor.ph_value > 8.0:
            parts.append(f"Soil pH is alkaline ({sensor.ph_value}). Apply gypsum or sulfur to lower pH.")

    return " ".join(parts) if parts else "Sensor data received but within normal ranges."

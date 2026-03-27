from app.services.chat.context_builder import build_context
from app.core.config import settings
import httpx
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


async def call_sarvam_llm(prompt: str) -> str:
    """
    Calls Sarvam AI's standard conversational LLM (sarvam-m) for reasoning.
    """
    system_prompt = (
        "You are AgriAssist, a highly intelligent farming assistant for Indian farmers. "
        "You help with crop advice, disease diagnosis, pest management, soil health, and weather warnings. "
        "IMPORTANT RULES:\n"
        "1. DO NOT simply echo or repeat back what the user says. Give direct, actionable remedies or answers.\n"
        "2. If the user greets you (e.g., 'hello'), greet them back and ask how you can help with their farm today.\n"
        "3. You must reply in the EXACT SAME LANGUAGE as the user! If they speak Tamil, reply in conversational Tamil. If Hindi, use Hindi. "
        "4. Keep your answers brief and practical. Use bullet points for steps or tips. Integrate current sensor and weather data if relevant "
        "to the remedy (e.g., if moisture is low and weather is hot, advise irrigation).\n"
        "5. Be supportive and use friendly, natural native slang if perfectly appropriate."
    )

    api_key = settings.SARWAM_API_KEY
    if not api_key:
        logger.error("SARWAM_API_KEY is not configured.")
        return "I'm having trouble connecting to my brain because the API key is missing. Please contact support."

    url = "https://api.sarvam.ai/v1/chat/completions"
    payload = {
        "model": "sarvam-m",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
    }
    
    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": api_key
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            # Sarvam-m might return <think> blocks. Strip them out.
            cleaned_content = re.sub(r'<think>.*?</think>\s*', '', content, flags=re.DOTALL)
            # Failsafe if it didn't use a closing tag
            cleaned_content = cleaned_content.replace('<think>\n', '').replace('<think>', '').strip()
            # If the response was entirely inside quotes, strip them
            if cleaned_content.startswith('"') and cleaned_content.endswith('"'):
                cleaned_content = cleaned_content[1:-1].strip()

            return cleaned_content
    except httpx.TimeoutException:
        logger.error("Sarvam LLM timeout")
        return "Sorry, the AI is taking too long to respond. Please try again."
    except Exception as e:
        logger.error(f"Sarvam LLM error: {type(e).__name__}: {e}")
        return "Sorry, I couldn't process your request right now. Please try again in a moment."


async def generate_ai_response(
    user_id: str,
    session_id: str,
    language: str,
    content: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> str:
    """
    Generates an AI response for the user's chat message.
    """
    from app.api.http.sensor import SENSOR_HARDWARE_URL
    
    # 1. Fetch live hardware sensor data silently
    sensor_temp = "Unknown"
    sensor_humidity = "Unknown"
    sensor_moisture = "Unknown"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{SENSOR_HARDWARE_URL}/api/sensors",
                headers={"ngrok-skip-browser-warning": "true"},
                timeout=3.0,
            )
            if resp.status_code == 200:
                hw_data = resp.json()
                sensor_temp = str(hw_data.get("temperature", sensor_temp))
                sensor_humidity = str(hw_data.get("humidity", sensor_humidity))
                sensor_moisture = str(hw_data.get("soil_moisture", sensor_moisture))
    except Exception as e:
        logger.warning(f"Chat service could not fetch live sensor data: {e}")

    # 2. Fetch Open-Meteo Weather Data
    weather_summary = "Unknown"
    if latitude is not None and longitude is not None:
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true&timezone=auto"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=3.0)
                if resp.status_code == 200:
                    wdata = resp.json().get("current_weather", {})
                    w_temp = wdata.get("temperature")
                    w_wind = wdata.get("windspeed")
                    weather_summary = f"{w_temp}°C, Wind {w_wind} km/h"
        except Exception as e:
            logger.warning(f"Chat service could not fetch weather data: {e}")

    # Build context prompt with farm data
    enriched_prompt = await build_context(
        crop="Unknown", # Placeholder until DB integration
        temperature=sensor_temp,
        humidity=sensor_humidity,
        moisture=sensor_moisture,
        weather=weather_summary,
        user_question=content,
    )

    # Call Sarvam AI
    response = await call_sarvam_llm(enriched_prompt)
    return response

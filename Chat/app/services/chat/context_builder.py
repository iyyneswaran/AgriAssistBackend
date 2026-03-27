from typing import Dict, Optional

async def build_context(
    crop: str,
    temperature: str,
    humidity: str,
    moisture: str,
    weather: str,
    user_question: str,
) -> str:
    """
    Builds structured prompt for AI reasoning.
    """

    context_prompt = f"""
Current Farm Context:
- Crop: {crop}
- Sensor Temperature: {temperature}
- Sensor Humidity: {humidity}
- Soil Moisture: {moisture}
- Local Weather: {weather}

User Question:
{user_question}
"""

    return context_prompt.strip()

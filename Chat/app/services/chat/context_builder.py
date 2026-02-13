from typing import Dict


async def build_context(
    crop: str,
    temperature: float,
    moisture: str,
    weather: str,
    user_question: str,
) -> str:
    """
    Builds structured prompt for Gemini reasoning.
    """

    context_prompt = f"""
Crop: {crop}
Temperature: {temperature}°C
Soil Moisture: {moisture}
Weather Forecast: {weather}

User Question:
{user_question}

Provide diagnosis and clear recommendation.
"""

    return context_prompt.strip()

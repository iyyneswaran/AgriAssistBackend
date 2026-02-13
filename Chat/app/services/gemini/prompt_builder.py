from typing import List, Dict


def build_structured_prompt(
    crop: str,
    temperature: float,
    moisture: str,
    weather: str,
    conversation_history: List[Dict[str, str]],
    user_question: str,
) -> str:
    """
    Builds structured, context-aware prompt for Gemini.
    """

    history_text = ""
    for msg in conversation_history:
        role = msg.get("role")
        content = msg.get("content")
        history_text += f"{role.upper()}: {content}\n"

    prompt = f"""
You are an agricultural AI assistant.

Crop: {crop}
Temperature: {temperature}°C
Soil Moisture: {moisture}
Weather Forecast: {weather}

Conversation History:
{history_text}

User Question:
{user_question}

Instructions:
- Provide diagnosis if relevant.
- Give actionable recommendations.
- Keep response concise and practical.
"""

    return prompt.strip()

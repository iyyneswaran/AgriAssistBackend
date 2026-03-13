from app.services.chat.context_builder import build_context
from app.core.config import settings
import httpx
import logging

logger = logging.getLogger(__name__)


async def call_pollinations(prompt: str) -> str:
    """
    Calls Pollination AI's OpenAI-compatible endpoint for English text chat.
    """
    try:
        url = "https://text.pollinations.ai/openai"

        system_prompt = (
            "You are AgriAssist, a friendly and knowledgeable AI assistant for Indian farmers. "
            "You help with crop advice, pest management, soil health, weather guidance, and government schemes. "
            "Keep your answers clear, short, and practical — like talking to a fellow farmer. "
            "Use simple English. Use bullet points when listing steps or tips. "
            "Always be encouraging and supportive."
        )

        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "model": "openai"
        }

        headers = {}
        if settings.POLLINATION_API_KEY:
            headers["Authorization"] = f"Bearer {settings.POLLINATION_API_KEY}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    except httpx.TimeoutException:
        logger.error("Pollinations API timeout")
        return "Sorry, the AI is taking too long to respond. Please try again."
    except Exception as e:
        logger.error(f"Pollinations API error: {type(e).__name__}: {e}")
        return "Sorry, I couldn't process your request right now. Please try again in a moment."


async def generate_ai_response(
    user_id: str,
    session_id: str,
    language: str,
    content: str,
) -> str:
    """
    Generates an AI response for the user's chat message.
    """
    # Build context prompt with farm data
    enriched_prompt = await build_context(
        crop="Paddy",
        temperature=34,
        moisture="Low",
        weather="No rain forecast",
        user_question=content,
    )

    # Call Pollinations AI
    response = await call_pollinations(enriched_prompt)
    return response

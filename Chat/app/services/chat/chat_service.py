from app.services.chat.translation_service import translate_text
from app.services.chat.context_builder import build_context
from app.core.config import settings
import httpx


GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"


async def call_gemini(prompt: str) -> str:
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    params = {"key": settings.GEMINI_API_KEY}

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(GEMINI_URL, json=payload, params=params)

    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return "Sorry, I couldn't process your request."


async def generate_ai_response(
    user_id: str,
    session_id: str,
    language: str,
    content: str,
) -> str:
    # Step 1: Normalize to English
    english_text = await translate_text(content, language, "English")

    # Step 2: Context enrichment (dummy values for now)
    enriched_prompt = await build_context(
        crop="Paddy",
        temperature=34,
        moisture="Low",
        weather="No rain forecast",
        user_question=english_text,
    )

    # Step 3: Gemini reasoning
    english_response = await call_gemini(enriched_prompt)

    # Step 4: Translate back to original language
    final_response = await translate_text(
        english_response,
        "English",
        language,
    )

    return final_response

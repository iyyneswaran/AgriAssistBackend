from app.services.chat.translation_service import translate_text
from app.services.chat.context_builder import build_context
from app.core.config import settings
from google import genai
import asyncio
import logging

logger = logging.getLogger(__name__)

# Initialize the Gemini client once
gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
GEMINI_MODEL = "gemini-2.0-flash"


async def call_gemini(prompt: str) -> str:
    try:
        # google-genai SDK is sync, so run in thread to avoid blocking
        response = await asyncio.to_thread(
            gemini_client.models.generate_content,
            model=GEMINI_MODEL,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {type(e).__name__}: {e}")
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

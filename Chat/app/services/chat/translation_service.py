from app.core.config import settings
from google import genai
import asyncio
import logging

logger = logging.getLogger(__name__)

# Initialize the Gemini client once
gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
GEMINI_MODEL = settings.GEMINI_MODEL


async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    if source_lang == target_lang:
        return text

    prompt = f"Translate the following text from {source_lang} to {target_lang}. Return ONLY the translated text, nothing else:\n{text}"

    try:
        response = await asyncio.to_thread(
            gemini_client.models.generate_content,
            model=GEMINI_MODEL,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini translation error: {type(e).__name__}: {e}")
        return text

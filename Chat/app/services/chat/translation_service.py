import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translates text to the target language using Sarvam AI.
    Example target_lang from STT: 'ta-IN', 'hi-IN'.
    """
    # If the LLM already output the desired language natively, or language is English
    if target_lang.startswith("en") or source_lang == target_lang:
        return text

    if not settings.SARWAM_API_KEY:
        logger.warning("SARWAM_API_KEY missing, skipping translation.")
        return text

    # Map generic source 'en' to Sarvam's 'en-IN'
    src = "en-IN" if source_lang == "en" else source_lang
    tgt = target_lang

    url = "https://api.sarvam.ai/translate"
    headers = {
        "api-subscription-key": settings.SARWAM_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": text,
        "source_language_code": src,
        "target_language_code": tgt,
        "speaker_gender": "Female",
        "mode": "formal",
        "model": "mayura:v1",
        "enable_preprocessing": True
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            # Sarvam returns { "translated_text": "..." }
            translated = data.get("translated_text", text)
            return translated
    except httpx.HTTPError as e:
        logger.error(f"Sarvam translation HTTP error: {e}")
        if hasattr(e, 'response') and e.response is not None:
             logger.error(f"Response: {e.response.text}")
        return text
    except Exception as e:
        logger.error(f"Sarvam translation error: {type(e).__name__}: {e}")
        return text

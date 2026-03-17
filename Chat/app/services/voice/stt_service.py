"""
STT Service — Sarvam AI Speech-to-Text
Transcribes Indic speech directly into Native Text, returning the detected language.
"""

import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

async def speech_to_text(file_path: str, language: str | None = None) -> dict:
    """
    Sends audio file to Sarvam AI for transcription natively.
    Returns: { "text": "Native translation...", "language": "ta-IN" }
    """
    if not settings.SARWAM_API_KEY:
        raise RuntimeError("SARWAM_API_KEY is not configured")

    logger.info(f"[STT] Transcribing {file_path} via Sarvam AI (Native)")

    url = "https://api.sarvam.ai/speech-to-text"
    headers = {
        "api-subscription-key": settings.SARWAM_API_KEY
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(file_path, "rb") as audio_file:
                files = {"file": (file_path, audio_file, "audio/wav")}
                # Use saarika:v2.5 for native Indic text
                data = {"prompt": "", "model": "saarika:v2.5"}
                if language:
                    data["language_code"] = language if "-" in language else f"{language}-IN"

                response = await client.post(url, files=files, data=data, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                transcript = result.get("transcript", "")
                
                # saarika might not return language_code or might return "hi-IN" by default. 
                # We enforce the input language if specified.
                detected_lang = data.get("language_code", "en-IN")
                
                logger.info(f"[STT] Sarvam Result: '{transcript}' (Language: {detected_lang})")

                return {
                    "text": transcript.strip(),
                    "language": detected_lang,
                }
    except httpx.HTTPError as e:
        logger.error(f"[STT] Sarvam API HTTP error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"[STT] Response details: {e.response.text}")
        raise RuntimeError(f"STT failed: {e}")
    except Exception as e:
        logger.error(f"[STT] Unexpected error: {e}")
        raise RuntimeError(f"STT failed: {e}")

"""
TTS Service — gTTS (Google Translate Text-to-Speech)
Supports Tamil, Hindi, Malayalam, English, Telugu, Kannada, Marathi.
No API key required. Fast and reliable.
"""

import logging
import base64
import httpx
from app.core.config import settings
from app.services.voice.audio_processor import generate_tts_output_path

logger = logging.getLogger(__name__)

async def text_to_speech(text: str, language: str | None = None) -> str:
    """
    Converts text to speech using Sarvam AI.
    Expected language code format: 'hi-IN', 'ta-IN'.
    Returns file path to the generated WAV file.
    """
    lang = language if language else "en-IN"
    # Sarvam typically returns WAV audio
    output_path = generate_tts_output_path(extension="wav")

    if not settings.SARWAM_API_KEY:
        logger.warning("SARWAM_API_KEY missing, skipping TTS.")
        return output_path

    logger.info(f"[TTS] Generating speech for '{text[:50]}...' in lang={lang} via Sarvam AI")

    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "api-subscription-key": settings.SARWAM_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": [text],
        "target_language_code": lang,
        "speaker": "ritu",
        "pace": 1.0,
        "speech_sample_rate": 8000,
        "enable_preprocessing": True,
        "model": "bulbul:v3"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            audios = data.get("audios", [])
            if not audios:
                raise ValueError("No audio returned from Sarvam AI")

            audio_base64 = audios[0]
            audio_bytes = base64.b64decode(audio_base64)
            
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            logger.info(f"[TTS] Audio saved to {output_path}")
            return output_path

    except httpx.HTTPError as e:
        logger.error(f"[TTS] Sarvam TTS HTTP error: {e}")
        if hasattr(e, 'response') and e.response is not None:
             logger.error(f"[TTS] Response: {e.response.text}")
        raise RuntimeError(f"TTS failed: {e}")
    except Exception as e:
        logger.error(f"[TTS] Sarvam TTS error: {type(e).__name__}: {e}")
        raise RuntimeError(f"TTS failed: {e}")

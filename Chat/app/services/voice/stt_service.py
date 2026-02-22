"""
STT Service — openai/whisper-large-v3-turbo via huggingface_hub InferenceClient
Supports auto language detection for Tamil, Hindi, Malayalam, English, etc.
"""

import logging
import asyncio
from huggingface_hub import InferenceClient
from app.core.config import settings

logger = logging.getLogger(__name__)

# Whisper large-v3-turbo works via InferenceClient
STT_MODEL = "openai/whisper-large-v3-turbo"

# Lazy-initialized client
_client: InferenceClient | None = None


def _get_client() -> InferenceClient:
    global _client
    if _client is None:
        _client = InferenceClient(token=settings.HUGGINGFACE_API_KEY)
    return _client


async def speech_to_text(file_path: str, language: str | None = None) -> dict:
    """
    Sends audio file to HuggingFace via InferenceClient for transcription.
    Whisper auto-detects language.

    Returns: { "text": "...", "language": "ta" }
    """
    client = _get_client()

    logger.info(f"[STT] Transcribing {file_path} with {STT_MODEL}")

    # Run HF inference in a thread pool (it's synchronous)
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None,
            lambda: client.automatic_speech_recognition(
                file_path,
                model=STT_MODEL,
            )
        )
    except Exception as e:
        logger.error(f"[STT] Inference error: {e}")
        raise RuntimeError(f"STT failed: {e}")

    transcribed_text = result.text if hasattr(result, 'text') else str(result)
    logger.info(f"[STT] Result: '{transcribed_text}'")

    # Detect language from transcribed text
    detected_lang = language or detect_language(transcribed_text)

    return {
        "text": transcribed_text.strip(),
        "language": detected_lang,
    }


def detect_language(text: str) -> str:
    """
    Unicode-range heuristic to detect language from transcribed text.
    Returns ISO 639-1 code.
    """
    if not text.strip():
        return "en"

    tamil_chars = sum(1 for c in text if '\u0B80' <= c <= '\u0BFF')
    hindi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    malayalam_chars = sum(1 for c in text if '\u0D00' <= c <= '\u0D7F')
    telugu_chars = sum(1 for c in text if '\u0C00' <= c <= '\u0C7F')
    kannada_chars = sum(1 for c in text if '\u0C80' <= c <= '\u0CFF')

    counts = {
        "ta": tamil_chars,
        "hi": hindi_chars,
        "ml": malayalam_chars,
        "te": telugu_chars,
        "kn": kannada_chars,
    }

    max_lang = max(counts, key=counts.get)  # type: ignore
    if counts[max_lang] > 0:
        return max_lang

    return "en"

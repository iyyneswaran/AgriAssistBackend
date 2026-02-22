"""
TTS Service — gTTS (Google Translate Text-to-Speech)
Supports Tamil, Hindi, Malayalam, English, Telugu, Kannada, Marathi.
No API key required. Fast and reliable.
"""

import logging
import asyncio
from gtts import gTTS
from app.services.voice.audio_processor import generate_tts_output_path

logger = logging.getLogger(__name__)

# gTTS language codes (same as ISO 639-1 for most Indic languages)
SUPPORTED_LANGS = {"ta", "hi", "ml", "en", "te", "kn", "mr"}


async def text_to_speech(text: str, language: str | None = None) -> str:
    """
    Converts text to speech using gTTS (Google Translate TTS).
    Supports: Tamil (ta), Hindi (hi), Malayalam (ml), English (en),
              Telugu (te), Kannada (kn), Marathi (mr).

    Returns file path to the generated MP3 file.
    """
    lang = language if language in SUPPORTED_LANGS else "en"
    output_path = generate_tts_output_path(extension="mp3")

    logger.info(f"[TTS] Generating speech for '{text[:50]}...' in lang={lang}")

    # gTTS is synchronous — run in thread pool
    loop = asyncio.get_event_loop()

    def _generate():
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(output_path)

    try:
        await loop.run_in_executor(None, _generate)
    except Exception as e:
        logger.error(f"[TTS] gTTS error: {e}")
        raise RuntimeError(f"TTS failed: {e}")

    logger.info(f"[TTS] Audio saved to {output_path}")
    return output_path

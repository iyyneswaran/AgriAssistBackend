"""
Voice Pipeline — Orchestrates the full voice flow:
Audio Upload → STT → AI Reasoning → TTS → Audio Response
"""

import logging
from app.services.voice.audio_processor import save_uploaded_audio, convert_to_wav
from app.services.voice.stt_service import speech_to_text
from app.services.voice.tts_service import text_to_speech
from app.services.chat.chat_service import generate_ai_response
from app.core.config import settings

logger = logging.getLogger(__name__)


async def process_voice_request(
    user_id: str,
    session_id: str,
    file_bytes: bytes,
    language: str | None = None,
) -> dict:
    """
    Full Voice Flow:
    Audio → STT → AI → TTS

    Returns dict with recognized text, AI response, and audio file path.
    """
    lang = language or settings.VOICE_LANGUAGE

    # Step 1: Save uploaded audio
    audio_path = save_uploaded_audio(file_bytes)
    logger.info(f"[Voice Pipeline] Saved upload: {audio_path}")

    # Step 2: Convert to WAV if needed (browser sends webm/ogg)
    wav_path = convert_to_wav(audio_path)

    # Step 3: Speech to Text
    logger.info("[Voice Pipeline] Running STT...")
    stt_result = await speech_to_text(wav_path, language=lang)
    user_text = stt_result["text"]
    detected_lang = stt_result["language"]
    logger.info(f"[Voice Pipeline] STT result: '{user_text}' (lang={detected_lang})")

    if not user_text.strip():
        return {
            "recognized_text": "",
            "response_text": "Sorry, I couldn't understand the audio. Please try again.",
            "audio_path": None,
        }

    # Step 4: AI Reasoning (Unified Chat Brain)
    logger.info("[Voice Pipeline] Generating AI response...")
    ai_text_response = await generate_ai_response(
        user_id=user_id,
        session_id=session_id,
        language=detected_lang,
        content=user_text,
    )
    logger.info(f"[Voice Pipeline] AI response: '{ai_text_response[:80]}...'")

    # Step 5: Text to Speech
    logger.info("[Voice Pipeline] Running TTS...")
    tts_audio_path = await text_to_speech(
        text=ai_text_response,
        language=detected_lang,
    )
    logger.info(f"[Voice Pipeline] TTS output: {tts_audio_path}")

    return {
        "recognized_text": user_text,
        "response_text": ai_text_response,
        "audio_path": tts_audio_path,
    }

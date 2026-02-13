from app.services.voice.audio_processor import save_uploaded_audio
from app.services.voice.stt_service import speech_to_text
from app.services.voice.tts_service import text_to_speech
from app.services.chat.chat_service import generate_ai_response


async def process_voice_request(
    user_id: str,
    session_id: str,
    file_bytes: bytes,
) -> dict:
    """
    Full Voice Flow:
    Audio → STT → AI → TTS
    """

    # Step 1: Save audio
    audio_path = save_uploaded_audio(file_bytes)

    # Step 2: Speech to Text
    stt_result = await speech_to_text(audio_path)
    user_text = stt_result["text"]
    language = stt_result["language"]

    # Step 3: AI Reasoning (Unified Chat Brain)
    ai_text_response = await generate_ai_response(
        user_id=user_id,
        session_id=session_id,
        language=language,
        content=user_text,
    )

    # Step 4: Text to Speech
    tts_audio_path = await text_to_speech(
        text=ai_text_response,
        language=language,
    )

    return {
        "recognized_text": user_text,
        "response_text": ai_text_response,
        "audio_path": tts_audio_path
    }

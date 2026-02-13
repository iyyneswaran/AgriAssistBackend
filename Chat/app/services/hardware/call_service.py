import httpx
from app.core.config import settings
from app.services.voice.tts_service import text_to_speech


TELEPHONY_API_URL = "https://api.telephony-provider.com/v1/call"


async def initiate_ai_voice_call(
    phone_number: str,
    message_text: str,
    language: str,
) -> dict:
    """
    Generates TTS audio and initiates automated outbound call.
    """

    # Step 1: Convert AI message to speech
    audio_path = await text_to_speech(
        text=message_text,
        language=language,
    )

    # Step 2: Trigger telephony provider
    payload = {
        "to": phone_number,
        "audio_url": audio_path,
        "callback_url": f"{settings.APP_NAME}/api/admin/call-status"
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            TELEPHONY_API_URL,
            json=payload,
        )

    return {
        "status": "call_initiated",
        "provider_response": response.json(),
        "audio_path": audio_path,
    }

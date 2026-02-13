import httpx
from app.core.config import settings


WHISPER_URL = "https://api.openai.com/v1/audio/transcriptions"


async def speech_to_text(file_path: str) -> dict:
    """
    Sends audio file to Whisper API and returns:
    {
        "text": "...",
        "language": "ta"
    }
    """

    headers = {
        "Authorization": f"Bearer {settings.GEMINI_API_KEY}"
    }

    with open(file_path, "rb") as audio_file:
        files = {
            "file": audio_file,
            "model": (None, "whisper-1")
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                WHISPER_URL,
                headers=headers,
                files=files
            )

    data = response.json()

    return {
        "text": data.get("text", ""),
        "language": data.get("language", "unknown")
    }

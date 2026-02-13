import httpx
from app.services.voice.audio_processor import generate_tts_output_path


COQUI_TTS_URL = "http://localhost:5002/api/tts"


async def text_to_speech(text: str, language: str) -> str:
    """
    Calls local Coqui TTS server and stores generated audio file.
    Returns file path.
    """

    output_path = generate_tts_output_path()

    payload = {
        "text": text,
        "language": language,
        "speaker_id": "default"
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(COQUI_TTS_URL, json=payload)

    audio_bytes = response.content

    with open(output_path, "wb") as f:
        f.write(audio_bytes)

    return output_path

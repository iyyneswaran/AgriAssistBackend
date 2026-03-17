import asyncio
import os
import sys
import httpx

# Add the project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from app.core.config import settings

async def test_sarvam_native_stt():
    api_key = settings.SARWAM_API_KEY
    if not api_key:
        print("SARWAM_API_KEY not found in settings")
        return

    # Create dummy audio file for testing
    dummy_audio = b"RIFF$" + b"\x00"*20
    test_file = "test_audio.wav"
    with open(test_file, "wb") as f:
        f.write(dummy_audio)

    url = "https://api.sarvam.ai/speech-to-text"
    headers = {
        "api-subscription-key": api_key
    }
    
    print("Testing /speech-to-text...")
    async with httpx.AsyncClient() as client:
        try:
            with open(test_file, "rb") as audio_file:
                files = {"file": (test_file, audio_file, "audio/wav")}
                # Trying saarika:v2.5 which is the native STT model
                data = {"model": "saarika:v2.5"}

                response = await client.post(
                    url,
                    data=data,
                    files=files,
                    headers=headers
                )
                print("Status:", response.status_code)
                print("Body:", response.text)
        except Exception as e:
            print("Exception:", e)
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

if __name__ == "__main__":
    asyncio.run(test_sarvam_native_stt())

"""Test TTS via raw InferenceClient post and gTTS fallback."""
import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()
client = InferenceClient(token=os.environ.get("HUGGINGFACE_API_KEY"))

# Test 1: Raw post to facebook/mms-tts-eng
print("Test 1: Raw post method to MMS-TTS...")
try:
    resp = client.post(
        json={"inputs": "Hello, this is a test"},
        model="facebook/mms-tts-eng",
    )
    print(f"  MMS-TTS-ENG raw: OK -> {len(resp)} bytes, type={type(resp)}")
    # Save to verify it's audio
    with open("test_tts_output.wav", "wb") as f:
        f.write(resp)
    print("  Saved to test_tts_output.wav")
except Exception as e:
    print(f"  MMS-TTS-ENG raw: FAILED -> {type(e).__name__}: {str(e)[:150]}")

# Test 2: Try gTTS (Google Translate TTS - works offline for basic TTS)
print("\nTest 2: Testing gTTS (pip install gTTS)...")
try:
    from gtts import gTTS
    tts = gTTS("வணக்கம் நான் உங்களுக்கு உதவ தயாராக இருக்கிறேன்", lang="ta")
    tts.save("test_gtts_tamil.mp3")
    import os
    size = os.path.getsize("test_gtts_tamil.mp3")
    print(f"  gTTS Tamil: OK -> {size} bytes saved")
    os.remove("test_gtts_tamil.mp3")
except ImportError:
    print("  gTTS not installed. Install with: pip install gTTS")
except Exception as e:
    print(f"  gTTS: FAILED -> {type(e).__name__}: {str(e)[:150]}")

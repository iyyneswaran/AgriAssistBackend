import asyncio
import os
import sys

# Add the project root to sys.path so 'app.*' imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from app.services.chat.translation_service import translate_text
from app.services.voice.tts_service import text_to_speech

async def run_tests():
    print("--- Testing Sarvam Translation ---")
    
    english_text = "The weather today is sunny and good for harvesting."
    target_lang = "ta-IN" # Tamil

    print(f"Original (en-IN): {english_text}")
    translated = await translate_text(english_text, "en-IN", target_lang)
    
    with open("translate_test.txt", "w", encoding="utf-8") as f:
        f.write(f"Original: {english_text}\n")
        f.write(f"Translated: {translated}\n")
    print(f"Translation saved to translate_test.txt")

    print("\n--- Testing Sarvam TTS ---")
    tts_path = await text_to_speech(translated, language=target_lang)
    print(f"TTS generated audio saved to: {tts_path}")
    
    # Check if file exists and has size
    if os.path.exists(tts_path):
        size = os.path.getsize(tts_path)
        print(f"File size: {size} bytes")
        if size > 1000:
            print("TTS SUCCESS!")
        else:
            print("TTS FAILURE: Output file is suspiciously small.")
    else:
        print("TTS FAILURE: Output file does not exist.")

if __name__ == "__main__":
    asyncio.run(run_tests())

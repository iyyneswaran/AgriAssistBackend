import os
from dotenv import load_dotenv
import requests

load_dotenv(".env")
api_key = os.getenv("SARWAM_API_KEY")

headers = {
    "api-subscription-key": api_key
}

# 1. Test Translation
try:
    print("Testing translation...")
    url = "https://api.sarvam.ai/translate"
    payload = {
        "input": ["Hello, how are you?"],
        "source_language_code": "en-IN",
        "target_language_code": "ta-IN",
        "speaker_gender": "Female",
        "mode": "formal",
        "model": "mayura:v1"
    }
    r = requests.post(url, json=payload, headers=headers)
    print("Translation Status:", r.status_code)
    print("Translation Resp:", r.text)
except Exception as e:
    print(e)

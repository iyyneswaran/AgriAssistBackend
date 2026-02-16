"""Test Gemini with the official google-genai SDK."""
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
print(f"Using API key: {API_KEY[:10]}...{API_KEY[-4:]}")

client = genai.Client(api_key=API_KEY)

try:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Say hello in one word",
    )
    print(f"Success! Response: {response.text}")
except Exception as e:
    print(f"Error type: {type(e).__name__}")
    print(f"Error: {e}")

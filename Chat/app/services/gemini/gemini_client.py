import httpx
from app.core.config import settings


GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"


class GeminiClient:

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY

    async def generate(self, prompt: str) -> str:
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }

        params = {"key": self.api_key}

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                GEMINI_URL,
                json=payload,
                params=params,
            )

        data = response.json()

        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return "AI response generation failed."

import asyncio
import os
import sys
import httpx

# Add the project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from app.core.config import settings

async def test_sarvam_chat():
    api_key = settings.SARWAM_API_KEY
    if not api_key:
        print("SARWAM_API_KEY not found in settings")
        return

    # Using sarvam-1 or standard sarvam-multi
    payload = {
        "model": "sarvam-m",
        "messages": [
            {
                "role": "system", 
                "content": "You are a helpful assistant. You must respond in the exact same language as the user's question."
            },
            {
                "role": "user", 
                "content": "எனது நெல் வயலில் மஞ்சள் நிறப் திட்டுகள் உள்ளன. என்ன பிரச்சனை?"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 100
    }
    
    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": api_key
    }

    print("Testing /v1/chat/completions...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.sarvam.ai/v1/chat/completions",
                json=payload,
                headers=headers
            )
            print("Status:", response.status_code)
            print("Body:", response.text)
        except Exception as e:
            print("Exception:", e)

if __name__ == "__main__":
    asyncio.run(test_sarvam_chat())

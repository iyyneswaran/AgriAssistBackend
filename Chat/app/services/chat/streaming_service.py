import asyncio
from typing import AsyncGenerator


async def stream_tokens(text: str) -> AsyncGenerator[str, None]:
    """
    Simulates token streaming.
    Replace with Gemini streaming API integration later.
    """
    words = text.split(" ")
    for word in words:
        await asyncio.sleep(0.05)
        yield word + " "

# app/services/rag/embedding_service.py

import google.generativeai as genai
from app.core.config import settings


class EmbeddingService:
    """
    Handles text → vector embedding generation using Gemini.
    """

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_EMBEDDING_MODEL

    async def embed_text(self, text: str) -> list[float]:
        """
        Generate 768-dimensional embedding vector for given text.
        """
        response = genai.embed_content(
            model=self.model_name,
            content=text,
            output_dimensionality=768,
        )

        return response["embedding"]
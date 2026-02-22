from google import genai
from app.core.config import settings


class EmbeddingService:
    """
    Handles text → vector embedding generation using Gemini.
    """

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_EMBEDDING_MODEL

    async def embed_text(self, text: str) -> list[float]:
        """
        Generate 768-dimensional embedding vector for given text.
        """
        response = self.client.models.embed_content(
            model=self.model_name,
            contents=text,
            config=genai.types.EmbedContentConfig(output_dimensionality=768)
        )

        return response.embeddings[0].values
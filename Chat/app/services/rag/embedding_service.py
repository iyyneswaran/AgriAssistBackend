from sentence_transformers import SentenceTransformer
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Handles text → vector embedding generation using Sentence Transformers.
    Model: google/embeddinggemma-300m (or fallback if configured)
    """

    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, trust_remote_code=True)
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load embedding model {self.model_name}: {e}")
            raise e

    async def embed_text(self, text: str, is_query: bool = False) -> list[float]:
        """
        Generate embedding vector for given text.
        For EmbeddingGemma, document prompts differ from query prompts.
        """
        # Follow official EmbeddingGemma prompt convention
        if is_query:
            prompted_text = f"task: search result | query: {text}"
        else:
            # We assume text is already formatted as "title: ... | text: ..." or similar
            # Since the ingestion service builds: "Scheme: {title}\nDescription: {desc}..."
            # We will format it properly here if it doesn't already contain "title:"
            if "title:" not in text.lower():
                # basic formatting
                prompted_text = f"title: scheme | text: {text}"
            else:
                prompted_text = text

        try:
            embedding = self.model.encode(prompted_text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise e
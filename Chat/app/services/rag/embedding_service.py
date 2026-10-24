import threading
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Handles text → vector embedding generation using Sentence Transformers.
    Model: google/embeddinggemma-300m (or fallback if configured)
    Lazy-loaded: the heavy SentenceTransformer model is loaded on first use,
    not at import time, to avoid blocking FastAPI startup.
    """

    _instance_lock = threading.Lock()
    _shared_model = None
    _shared_model_name = None

    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self._model = None

    def _ensure_model(self):
        """Lazily load the SentenceTransformer model (thread-safe singleton)."""
        if self._model is not None:
            return

        with EmbeddingService._instance_lock:
            # If another instance already loaded the same model, reuse it
            if (EmbeddingService._shared_model is not None
                    and EmbeddingService._shared_model_name == self.model_name):
                self._model = EmbeddingService._shared_model
                return

            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {self.model_name}")
                model = SentenceTransformer(self.model_name, trust_remote_code=True)
                logger.info("Embedding model loaded successfully.")
                EmbeddingService._shared_model = model
                EmbeddingService._shared_model_name = self.model_name
                self._model = model
            except Exception as e:
                logger.error(f"Failed to load embedding model {self.model_name}: {e}")
                raise e

    async def embed_text(self, text: str, is_query: bool = False) -> list[float]:
        """
        Generate embedding vector for given text.
        For EmbeddingGemma, document prompts differ from query prompts.
        """
        self._ensure_model()

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
            embedding = self._model.encode(prompted_text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise e

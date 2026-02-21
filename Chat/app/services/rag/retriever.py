# app/services/rag/retriever.py

from app.integrations.pinecone.pinecone_store import PineconeStore


class Retriever:
    """
    Handles vector similarity search via Pinecone.
    """

    def __init__(self):
        self.store = PineconeStore()

    async def retrieve(
        self,
        embedding: list[float],
        top_k: int = 5,
    ) -> list[dict]:

        results = await self.store.query_schemes(
            embedding=embedding,
            top_k=top_k,
        )

        return results

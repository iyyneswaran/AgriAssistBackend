# app/integrations/pinecone/pinecone_store.py

from typing import List, Dict
from pinecone import Pinecone
from app.core.config import settings


class PineconeStore:
    """
    Abstraction layer over Pinecone vector operations.
    """

    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)

    async def upsert_scheme(
        self,
        vector_id: str,
        title: str,
        description: str,
        eligibility: str,
        region: str,
        crop_type: str,
        embedding: List[float],
    ):
        """
        Upsert a scheme chunk vector with metadata into Pinecone.
        """
        self.index.upsert(
            vectors=[
                {
                    "id": vector_id,
                    "values": embedding,
                    "metadata": {
                        "title": title,
                        "description": description,
                        "eligibility": eligibility,
                        "region": region,
                        "crop_type": crop_type,
                    },
                }
            ]
        )

    async def query_schemes(
        self,
        embedding: List[float],
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Query Pinecone for the most similar scheme chunks.
        """
        response = self.index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
        )

        results = []
        for match in response.get("matches", []):
            metadata = match.get("metadata", {})
            results.append({
                "id": match["id"],
                "title": metadata.get("title", ""),
                "description": metadata.get("description", ""),
                "eligibility": metadata.get("eligibility", ""),
                "region": metadata.get("region", ""),
                "crop_type": metadata.get("crop_type", ""),
                "similarity": match.get("score", 0),
            })

        return results
    async def delete_all(self):
        """
        Delete all vectors from the index.
        """
        try:
            self.index.delete(delete_all=True)
        except Exception as e:
            # If namespace is not found, it means it's already empty
            if "not found" in str(e).lower():
                print("Index already empty or namespace not found. Skipping clear.")
            else:
                raise e

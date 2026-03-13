from pinecone import Pinecone
from app.core.config import settings
from typing import List, Dict

class PineconeStore:
    """
    Handles interactions with the Pinecone Vector Database for storing and retrieving schemes.
    """
    
    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = getattr(settings, "PINECONE_INDEX_NAME", "agriassist")
        self.index = self.pc.Index(self.index_name)

    async def upsert_scheme(
        self,
        vector_id: str,
        title: str,
        description: str,
        eligibility: str,
        region: str,
        crop_type: str,
        embedding: List[float],
        benefit_amount: str = "",
        scheme_id: str = "",
    ):
        """
        Upserts a scheme chunk and its metadata into Pinecone.
        """
        metadata = {
            "title": title,
            "description": description[:950] if len(description) > 950 else description,  # Pinecone metadata size limit
            "eligibility": eligibility,
            "region": region,
            "crop_type": crop_type,
        }
        
        # Add optional fields if present
        if benefit_amount:
            metadata["benefit_amount"] = benefit_amount
        if scheme_id:
            metadata["scheme_id"] = scheme_id
        
        # Pinecone upsert format: list of tuples (id, vector, metadata)
        self.index.upsert(vectors=[(vector_id, embedding, metadata)])

    async def query_schemes(
        self,
        embedding: List[float],
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Queries Pinecone for the most similar schemes based on embedding.
        """
        response = self.index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        results = []
        for match in response.matches:
            # Reconstruct the dictionary expected by RagService
            item = dict(match.metadata) if match.metadata else {}
            item["similarity"] = match.score
            item["id"] = match.id
            results.append(item)
            
        return results

    async def delete_all(self):
        """
        Deletes all vectors in the index.
        """
        self.index.delete(delete_all=True)

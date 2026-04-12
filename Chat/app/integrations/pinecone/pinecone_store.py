from pinecone import Pinecone
from app.core.config import settings
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PineconeStore:
    """
    Handles interactions with the Pinecone Vector Database for storing and retrieving schemes.
    Supports namespace-based versioning and metadata-filtered queries.
    """

    def __init__(self, namespace: Optional[str] = None):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = getattr(settings, "PINECONE_INDEX_NAME", "agriassist")
        self.index = self.pc.Index(self.index_name)
        self.namespace = namespace or getattr(settings, "PINECONE_NAMESPACE", "tn_agri_v2")

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
        soil_type: str = "",
        season: str = "",
        land_size_range: str = "",
        scheme_category: str = "",
    ):
        """
        Upserts a scheme chunk and its metadata into Pinecone with namespace.
        """
        metadata = {
            "title": title,
            "description": description[:950] if len(description) > 950 else description,  # Pinecone metadata size limit
            "eligibility": eligibility,
            "region": region,
            "crop_type": crop_type,
        }

        # Add enriched metadata fields
        if benefit_amount:
            metadata["benefit_amount"] = benefit_amount
        if scheme_id:
            metadata["scheme_id"] = scheme_id
        if soil_type:
            metadata["soil_type"] = soil_type
        if season:
            metadata["season"] = season
        if land_size_range:
            metadata["land_size_range"] = land_size_range
        if scheme_category:
            metadata["scheme_category"] = scheme_category

        # Pinecone upsert format: list of tuples (id, vector, metadata)
        self.index.upsert(
            vectors=[(vector_id, embedding, metadata)],
            namespace=self.namespace,
        )

    async def upsert_batch(
        self,
        vectors: List[tuple],
    ):
        """
        Batch upsert for efficient bulk ingestion.
        Each vector is a tuple of (id, embedding, metadata).
        """
        if not vectors:
            return

        # Pinecone supports batches up to 100 vectors
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch, namespace=self.namespace)
            logger.info(f"Upserted batch {i // batch_size + 1} ({len(batch)} vectors) to namespace '{self.namespace}'")

    async def query_schemes(
        self,
        embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Queries Pinecone for the most similar schemes based on embedding.
        Supports optional metadata filters for personalized retrieval.
        """
        query_kwargs = {
            "vector": embedding,
            "top_k": top_k,
            "include_metadata": True,
            "namespace": self.namespace,
        }

        # Apply metadata filters if provided (Pinecone filter syntax)
        if filters:
            query_kwargs["filter"] = filters

        response = self.index.query(**query_kwargs)

        results = []
        for match in response.matches:
            # Reconstruct the dictionary expected by RagService
            item = dict(match.metadata) if match.metadata else {}
            item["similarity"] = match.score
            item["id"] = match.id
            results.append(item)

        return results

    async def delete_all(self, namespace: Optional[str] = None):
        """
        Deletes all vectors in the specified namespace.
        """
        ns = namespace or self.namespace
        self.index.delete(delete_all=True, namespace=ns)
        logger.info(f"Deleted all vectors in namespace '{ns}'")

    async def get_namespace_stats(self) -> Dict:
        """
        Returns index stats for monitoring ingestion status.
        """
        stats = self.index.describe_index_stats()
        return {
            "total_vectors": stats.total_vector_count,
            "namespaces": {k: v.vector_count for k, v in stats.namespaces.items()} if stats.namespaces else {},
        }

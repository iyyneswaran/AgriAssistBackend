from app.integrations.pinecone.pinecone_store import PineconeStore
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Retriever:
    """
    Handles vector similarity search via Pinecone with metadata-filtered retrieval.
    Uses farm_context to build Pinecone filter expressions for personalized results.
    """

    def __init__(self):
        self.store = PineconeStore()

    def _build_metadata_filter(self, farm_context: Dict[str, Any]) -> Optional[Dict]:
        """
        Constructs a Pinecone metadata filter from user's farm context.
        Uses $or/$in operators for flexible matching.
        Filters on region to ensure relevance while keeping recall high.
        """
        if not farm_context:
            return None

        conditions = []

        # Region filter: match user's state, district, or pan-india schemes
        user_state = (farm_context.get("state") or "").strip().lower()
        user_district = (farm_context.get("district") or "").strip().lower()

        if user_state or user_district:
            region_values = ["pan-india"]  # Always include pan-india schemes
            if user_state:
                region_values.append(user_state)
            if user_district:
                region_values.append(user_district)
            conditions.append({"region": {"$in": region_values}})

        # Land size filter: match user's farm size category
        user_area = farm_context.get("area_acres", 0)
        if user_area and user_area > 0:
            size_values = ["all"]
            if user_area <= 5:  # ≤2 ha ≈ 5 acres → small/marginal
                size_values.append("small_marginal")
            conditions.append({"land_size_range": {"$in": size_values}})

        # Combine conditions: all must match ($and)
        if len(conditions) == 0:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {"$and": conditions}

    async def retrieve(
        self,
        embedding: list[float],
        top_k: int = 10,
        farm_context: Dict[str, Any] = None,
    ) -> list[dict]:
        """
        Retrieves schemes from Pinecone using semantic search + metadata filters.
        Falls back to unfiltered search if filtered results are too few.
        """
        filters = self._build_metadata_filter(farm_context) if farm_context else None

        # Primary retrieval: semantic + metadata filter
        results = await self.store.query_schemes(
            embedding=embedding,
            top_k=top_k,
            filters=filters,
        )

        # Fallback: if filtered results are very few, supplement with unfiltered results
        if filters and len(results) < 3:
            logger.info(f"Filtered results too few ({len(results)}), supplementing with unfiltered search")
            unfiltered = await self.store.query_schemes(
                embedding=embedding,
                top_k=top_k,
                filters=None,
            )
            # Merge: keep filtered results first, add unfiltered results not already present
            seen_ids = {r["id"] for r in results}
            for item in unfiltered:
                if item["id"] not in seen_ids:
                    results.append(item)
                    seen_ids.add(item["id"])
                if len(results) >= top_k:
                    break

        return results
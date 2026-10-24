import logging
from typing import List, Dict, Any, Optional, Tuple
from supabase import create_client, Client
from app.core.config import settings
import json

logger = logging.getLogger(__name__)

class SupabaseStore:
    """
    Handles interactions with Supabase pgvector for vector storage and retrieval.
    Replaces PineconeStore.
    """
    def __init__(self, table_name: str = "schemes"):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_SERVICE_ROLE_KEY
        if not self.url or not self.key or self.url == "YOUR_SUPABASE_URL":
            logger.warning("Supabase URL or Key not provided. Store will not function properly.")
            self.client = None
        else:
            self.client: Client = create_client(self.url, self.key)
        self.table_name = table_name

    def _embed_metadata_in_description(self, description: str, metadata: Dict[str, Any]) -> str:
        """
        Embed extra metadata into the description field as required by the schema.
        """
        if not metadata:
            return description
            
        extra_parts = []
        for key in ["scheme_id", "benefit_amount", "scheme_category", "land_size_range", "season", "soil_type"]:
            if key in metadata:
                extra_parts.append(f"{key}: {metadata[key]}")
        
        if extra_parts:
            return description + "\n\nMetadata:\n" + "\n".join(extra_parts)
        return description

    async def upsert_scheme(
        self,
        vector_id: str,
        title: str,
        description: str,
        eligibility: str,
        region: str,
        crop_type: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Inserts a single scheme. 
        Note: The vector_id from pinecone was a string. Supabase expects id as int8,
        but since we are using supabase's auto-increment or similar, we might just omit id, 
        or we hash vector_id to int8. To keep it simple, we will omit id and let DB generate it, 
        while embedding the vector_id in metadata if needed.
        """
        if not self.client:
            return False

        full_description = self._embed_metadata_in_description(description, metadata or {})

        data = {
            "title": title,
            "description": full_description,
            "eligibility": eligibility,
            "region": region,
            "crop_type": crop_type,
            "embedding": embedding
        }

        try:
            # We don't provide id so it will auto increment
            res = self.client.table(self.table_name).insert(data).execute()
            return True
        except Exception as e:
            logger.error(f"Error upserting to Supabase: {e}")
            raise

    async def upsert_batch(self, batch_vectors: List[Tuple[str, List[float], Dict[str, Any]]]) -> bool:
        """
        Upserts a batch of vectors.
        """
        if not self.client:
            return False

        data_list = []
        for vector_id, embedding, metadata in batch_vectors:
            title = metadata.get("title", "Unknown")
            description = metadata.get("description", "")
            eligibility = metadata.get("eligibility", "")
            region = metadata.get("region", "")
            crop_type = metadata.get("crop_type", "")
            
            full_desc = self._embed_metadata_in_description(description, metadata)
            
            data_list.append({
                "title": title,
                "description": full_desc,
                "eligibility": eligibility,
                "region": region,
                "crop_type": crop_type,
                "embedding": embedding
            })

        try:
            res = self.client.table(self.table_name).insert(data_list).execute()
            return True
        except Exception as e:
            logger.error(f"Error upserting batch to Supabase: {e}")
            raise

    async def query_schemes(
        self,
        embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Query schemes using pgvector RPC match_schemes.
        The match_schemes RPC takes:
        - query_embedding (vector)
        - match_threshold (float)
        - match_count (int)
        - p_region (text) (optional filter)
        - p_land_size (text) (optional filter)
        """
        if not self.client:
            return []

        # Parse filters mapped from Pinecone's $in syntax
        p_region = None
        p_land_size = None
        
        if filters:
            if "$and" in filters:
                for cond in filters["$and"]:
                    if "region" in cond:
                        p_region = ",".join(cond["region"]["$in"])
                    if "land_size_range" in cond:
                        p_land_size = ",".join(cond["land_size_range"]["$in"])
            else:
                if "region" in filters:
                    p_region = ",".join(filters["region"]["$in"])
                if "land_size_range" in filters:
                    p_land_size = ",".join(filters["land_size_range"]["$in"])

        params = {
            "query_embedding": embedding,
            "match_threshold": 0.0,
            "match_count": top_k,
            "p_region": p_region,
            "p_land_size": p_land_size
        }

        try:
            res = self.client.rpc("match_schemes", params).execute()
            
            # Map Supabase result back to the format expected by Ranker
            # Supabase result: [{id, title, description, eligibility, region, crop_type, similarity}]
            results = []
            for row in res.data:
                # Re-extract metadata from description to fulfill ranker needs
                desc = row.get("description", "")
                
                # Default extracted
                scheme_category = "general"
                season = "all"
                land_size_range = "all"
                soil_type = "all"
                scheme_id = str(row.get("id"))
                benefit_amount = ""
                
                if "\n\nMetadata:\n" in desc:
                    desc_main, meta_str = desc.split("\n\nMetadata:\n", 1)
                    desc = desc_main
                    for line in meta_str.split("\n"):
                        if line.startswith("scheme_category: "):
                            scheme_category = line.split("scheme_category: ")[1]
                        elif line.startswith("season: "):
                            season = line.split("season: ")[1]
                        elif line.startswith("land_size_range: "):
                            land_size_range = line.split("land_size_range: ")[1]
                        elif line.startswith("soil_type: "):
                            soil_type = line.split("soil_type: ")[1]
                        elif line.startswith("scheme_id: "):
                            scheme_id = line.split("scheme_id: ")[1]
                        elif line.startswith("benefit_amount: "):
                            benefit_amount = line.split("benefit_amount: ")[1]

                results.append({
                    "id": row.get("id"),
                    "title": row.get("title"),
                    "description": desc,
                    "eligibility": row.get("eligibility"),
                    "region": row.get("region"),
                    "crop_type": row.get("crop_type"),
                    "scheme_category": scheme_category,
                    "season": season,
                    "land_size_range": land_size_range,
                    "soil_type": soil_type,
                    "scheme_id": scheme_id,
                    "benefit_amount": benefit_amount,
                    "similarity": row.get("similarity", 0)
                })
            
            return results
        except Exception as e:
            logger.error(f"Error querying Supabase: {e}")
            raise

    async def delete_all(self, namespace: str = None) -> bool:
        """
        Delete all rows from schemes table.
        """
        if not self.client:
            return False
            
        try:
            # Dangerous, only used in migration script.
            # Delete where id > 0 (all rows)
            self.client.table(self.table_name).delete().gt("id", 0).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting all in Supabase: {e}")
            raise

    async def get_namespace_stats(self) -> Dict:
        """
        Return count of rows.
        """
        if not self.client:
            return {}
            
        try:
            res = self.client.table(self.table_name).select("id", count="exact").execute()
            return {"namespaces": {settings.PINECONE_NAMESPACE: res.count}}
        except Exception as e:
            logger.error(f"Error getting stats from Supabase: {e}")
            return {}

    async def get_fallback_schemes(self, limit: int = 10, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Direct database query fallback when vector similarity search is unavailable.
        """
        if not self.client:
            return []

        try:
            query = self.client.table(self.table_name).select(
                "id, title, description, eligibility, region, crop_type"
            )
            res = query.limit(limit).execute()
            results = []
            for row in (res.data or []):
                results.append({
                    "id": row.get("id"),
                    "title": row.get("title", ""),
                    "description": row.get("description", ""),
                    "eligibility": row.get("eligibility", ""),
                    "region": row.get("region", "pan-india"),
                    "crop_type": row.get("crop_type", "all"),
                    "scheme_category": "general",
                    "season": "all",
                    "land_size_range": "all",
                    "soil_type": "all",
                    "scheme_id": str(row.get("id")),
                    "benefit_amount": "",
                    "similarity": 0.8,
                })
            return results
        except Exception as e:
            logger.error(f"Fallback schemes retrieval failed: {e}")
            return []

# app/integrations/supabase/vector_store.py

from typing import List, Dict
from app.integrations.supabase.supabase_client import SupabaseClient


class VectorStore:
    """
    Abstraction layer over pgvector operations.
    """

    def __init__(self):
        self.client = SupabaseClient.get_client()

    async def insert_scheme(
        self,
        title: str,
        description: str,
        eligibility: str,
        region: str,
        crop_type: str,
        embedding: List[float],
    ):
        """
        Insert new scheme chunk into vector table.
        """

        data = {
            "title": title,
            "description": description,
            "eligibility": eligibility,
            "region": region,
            "crop_type": crop_type,
            "embedding": embedding,
        }

        self.client.table("schemes").insert(data).execute()

    async def match_schemes(
        self,
        embedding: List[float],
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Calls Postgres RPC for similarity search.
        """

        response = (
            self.client.rpc(
                "match_schemes",
                {
                    "query_embedding": embedding,
                    "match_count": top_k,
                },
            )
            .execute()
        )

        return response.data or []
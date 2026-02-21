# app/integrations/supabase/supabase_client.py

from supabase import create_client, Client
from app.core.config import settings


class SupabaseClient:
    """
    Centralized Supabase connection.
    """

    _client: Client = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._client is None:
            cls._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,
            )
        return cls._client
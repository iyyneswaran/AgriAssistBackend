# app/integrations/supabase/storage_client.py

from app.integrations.supabase.supabase_client import SupabaseClient


class StorageClient:
    """
    Handles Supabase file storage.
    """

    def __init__(self, bucket_name: str = "scheme-documents"):
        self.client = SupabaseClient.get_client()
        self.bucket = bucket_name

    def upload_file(self, file_path: str, file_bytes: bytes):
        """
        Upload document to Supabase Storage bucket.
        """

        self.client.storage.from_(self.bucket).upload(
            path=file_path,
            file=file_bytes,
        )

    def get_public_url(self, file_path: str) -> str:
        """
        Generate public URL.
        """

        return self.client.storage.from_(self.bucket).get_public_url(file_path)
import ee
import base64
from pathlib import Path
from functools import lru_cache
from app.core.config import settings


class GEEAuth:
    def __init__(self):
        self._initialize()

    def _initialize(self):
        credentials_path = settings.GOOGLE_APPLICATION_CREDENTIALS
        service_account_email = settings.GEE_SERVICE_ACCOUNT
        credentials_json = settings.GEE_CREDENTIALS_JSON
        credentials_b64 = settings.GEE_CREDENTIALS_B64

        # Backward-compatible: allow GOOGLE_APPLICATION_CREDENTIALS to contain raw JSON.
        if credentials_path and credentials_path.strip().startswith("{"):
            credentials_json = credentials_path

        if not service_account_email:
            raise EnvironmentError(
                "GEE_SERVICE_ACCOUNT not configured in .env"
            )

        try:
            if credentials_json:
                credentials = ee.ServiceAccountCredentials(
                    service_account_email,
                    key_data=credentials_json,
                )
            elif credentials_b64:
                decoded = base64.b64decode(credentials_b64).decode("utf-8")
                credentials = ee.ServiceAccountCredentials(
                    service_account_email,
                    key_data=decoded,
                )
            elif credentials_path:
                path = Path(credentials_path)
                if not path.is_absolute():
                    path = Path.cwd() / path
                if not path.exists():
                    raise FileNotFoundError(
                        f"GEE credentials file not found at: {path}. "
                        "Use GEE_CREDENTIALS_JSON or GEE_CREDENTIALS_B64 in Railway."
                    )
                credentials = ee.ServiceAccountCredentials(
                    service_account_email,
                    str(path),
                )
            else:
                raise EnvironmentError(
                    "Provide one of GOOGLE_APPLICATION_CREDENTIALS (file path), "
                    "GEE_CREDENTIALS_JSON, or GEE_CREDENTIALS_B64."
                )

            ee.Initialize(credentials)
        except Exception as e:
            raise RuntimeError(f"GEE initialization failed: {str(e)}")

    def get_client(self):
        return ee


@lru_cache()
def get_gee():
    """
    Cached singleton instance.
    Prevents reinitialization in multi-import environments.
    """
    return GEEAuth().get_client()

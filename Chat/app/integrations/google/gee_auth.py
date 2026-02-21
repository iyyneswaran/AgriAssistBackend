import ee
from functools import lru_cache
from app.core.config import settings


class GEEAuth:
    def __init__(self):
        self._initialize()

    def _initialize(self):
        credentials_path = settings.GOOGLE_APPLICATION_CREDENTIALS
        service_account_email = settings.GEE_SERVICE_ACCOUNT

        if not credentials_path:
            raise EnvironmentError(
                "GOOGLE_APPLICATION_CREDENTIALS not configured in .env"
            )

        if not service_account_email:
            raise EnvironmentError(
                "GEE_SERVICE_ACCOUNT not configured in .env"
            )

        try:
            credentials = ee.ServiceAccountCredentials(
                service_account_email,
                credentials_path
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
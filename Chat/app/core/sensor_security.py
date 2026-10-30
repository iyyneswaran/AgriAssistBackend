from app.core.config import settings


def owns_live_sensor(user_id: str) -> bool:
    # A single configured hardware URL must never be shared across all farmers.
    return bool(settings.SENSOR_OWNER_USER_ID and user_id == settings.SENSOR_OWNER_USER_ID)

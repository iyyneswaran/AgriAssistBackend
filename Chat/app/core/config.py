from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    # App
    DEBUG: bool = False
    APP_NAME: str = "Agri AI Backend"

    # JWT
    JWT_SECRET: str = Field(..., env="JWT_SECRET")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24

    # Database (Neon PostgreSQL)
    DATABASE_URL: str = Field(..., env="DATABASE_URL")

    # Redis
    REDIS_URL: str = Field(..., env="REDIS_URL")

    # Gemini
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"

    # Allowed CORS Origins
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Google Earth Engine
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None
    GEE_SERVICE_ACCOUNT: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

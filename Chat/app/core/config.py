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
    REDIS_URL: str | None = Field(None, env="REDIS_URL")

    # Gemini
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"

    # Pollinations AI
    POLLINATION_API_KEY: str | None = Field(None, env="POLLINATION_API_KEY")

    # Allowed CORS Origins (comma separated)
    ALLOWED_ORIGINS: str = "*"

    # Google Earth Engine
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None
    GEE_SERVICE_ACCOUNT: str | None = None
    GEE_CREDENTIALS_JSON: str | None = Field(None, env="GEE_CREDENTIALS_JSON")
    GEE_CREDENTIALS_B64: str | None = Field(None, env="GEE_CREDENTIALS_B64")

    # HuggingFace (Voice AI)
    HUGGINGFACE_API_KEY: str | None = Field(None, env="HUGGINGFACE_API_KEY")
    STT_MODEL_ID: str = "ai4bharat/indic-conformer-600m-multilingual"
    TTS_MODEL_ID: str = "ai4bharat/indic-parler-tts"
    VOICE_LANGUAGE: str = "ta"
    TTS_VOICE_DESCRIPTION: str = "Jaya speaks in a clear and expressive tone with moderate speed. The recording is very clear audio."

    # Pinecone
    PINECONE_API_KEY: str | None = Field(None, env="PINECONE_API_KEY")
    PINECONE_INDEX_NAME: str | None = Field("agriassist", env="PINECONE_INDEX_NAME")

    # Supabase (Optional/Deprecated)
    SUPABASE_URL: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


settings = Settings()

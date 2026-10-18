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

    # Pollinations AI
    POLLINATION_API_KEY: str | None = Field(None, env="POLLINATION_API_KEY")

    # Sarvam AI
    SARWAM_API_KEY: str | None = Field(None, env="SARWAM_API_KEY")
    SARVAM_CHAT_MODEL: str = Field("sarvam-105b", env="SARVAM_CHAT_MODEL")
    EMBEDDING_MODEL: str = Field("google/embeddinggemma-300m", env="EMBEDDING_MODEL")

    # Sensor Hardware
    SENSOR_HARDWARE_URL: str | None = Field(None, env="SENSOR_HARDWARE_URL")

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
    PINECONE_NAMESPACE: str = Field("tn_agri_v2", env="PINECONE_NAMESPACE")

    # Supabase
    # Supabase backs the optional scheme-recommendation/RAG features.  Keep the
    # API available when it has not been configured yet; SupabaseStore will
    # disable only those features and log a warning.
    SUPABASE_URL: str | None = Field(None, env="SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY: str | None = Field(None, env="SUPABASE_SERVICE_ROLE_KEY")

    # Push Notifications (VAPID)
    VITE_VAPID_PUBLIC_KEY: str | None = Field(None, env="VITE_VAPID_PUBLIC_KEY")
    VAPID_PRIVATE_KEY: str | None = Field(None, env="VAPID_PRIVATE_KEY")
    VAPID_CONTACT_EMAIL: str = Field("admin@agriassist.app", env="VAPID_CONTACT_EMAIL")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


settings = Settings()

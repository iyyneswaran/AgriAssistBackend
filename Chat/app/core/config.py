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
    GEMINI_MODEL: str = "models/gemini-2.0-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-001"

    # Supabase (Vector DB)
    SUPABASE_URL: str = Field(default="", env="SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="", env="SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_ANON_KEY: str = Field(default="", env="SUPABASE_ANON_KEY")

    # Pinecone (Vector DB)
    PINECONE_API_KEY: str = Field(default="", env="PINECONE_API_KEY")
    PINECONE_INDEX_NAME: str = Field(default="agri-schemes", env="PINECONE_INDEX_NAME")

    # Google Cloud / Google Earth Engine
    GOOGLE_APPLICATION_CREDENTIALS: str = Field(default="", env="GOOGLE_APPLICATION_CREDENTIALS")
    GEE_SERVICE_ACCOUNT: str = Field(default="", env="GEE_SERVICE_ACCOUNT")

    # Allowed CORS Origins
    ALLOWED_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

"""
Core Application Configuration
Uses Pydantic Settings to load and validate environment variables with sensible production defaults.
"""

from typing import List, Optional
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General
    ENVIRONMENT: str = Field(default="development")
    APP_NAME: str = Field(default="RAG Voice Intelligence Platform")
    APP_HOST: str = Field(default="0.0.0.0")
    APP_PORT: int = Field(default=8000)
    DEBUG: bool = Field(default=True)

    # Database
    # Async SQLite by default for zero-friction local execution, PostgreSQL for production
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./data/rag_voice.db")

    # Redis Cache & Message Broker
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # Qdrant Vector Search
    QDRANT_URL: str = Field(default="http://localhost:6333")
    QDRANT_API_KEY: Optional[str] = Field(default=None)
    QDRANT_STORAGE_PATH: str = Field(default="./data/qdrant")

    # Object Storage
    STORAGE_BACKEND: str = Field(default="local")  # "local" or "s3"
    STORAGE_LOCAL_DIR: str = Field(default="./data/storage")
    S3_ENDPOINT: str = Field(default="http://localhost:9000")
    S3_ACCESS_KEY: str = Field(default="minioadmin")
    S3_SECRET_KEY: str = Field(default="minioadmin")
    S3_BUCKET: str = Field(default="rag-voice-intelligence")
    S3_REGION: str = Field(default="us-east-1")
    S3_SECURE: bool = Field(default=False)

    # Authentication & Security
    JWT_SECRET: str = Field(default="rag_voice_super_secret_jwt_key_at_least_32_characters_123456")
    JWT_REFRESH_SECRET: str = Field(default="rag_voice_super_secret_refresh_jwt_key_at_least_32_chars_123456")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    MFA_ENCRYPTION_KEY: str = Field(default="kZ8d9vL3a1N0qX8wY7pM5sR2tV4uB6xZ8d9vL3a1N0q=")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]
    )

    # Rate Limiting & Account Security
    MAX_LOGIN_ATTEMPTS: int = Field(default=5)
    ACCOUNT_LOCKOUT_MINUTES: int = Field(default=15)
    RATE_LIMIT_LOGIN_MAX: int = Field(default=10)
    RATE_LIMIT_LOGIN_WINDOW_SEC: int = Field(default=60)

    # AI & ML Providers (Configurable & replaceable)
    LLM_PROVIDER: str = Field(default="builtin")  # "builtin", "openai", "anthropic", "ollama"
    LLM_API_KEY: Optional[str] = Field(default=None)
    LLM_MODEL: str = Field(default="gpt-4o-mini")
    LLM_TEMPERATURE: float = Field(default=0.2)
    LLM_MAX_TOKENS: int = Field(default=1024)

    EMBEDDING_PROVIDER: str = Field(default="builtin")  # "builtin", "openai", "huggingface"
    EMBEDDING_API_KEY: Optional[str] = Field(default=None)
    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION: int = Field(default=384)

    STT_PROVIDER: str = Field(default="builtin")  # "builtin", "whisper", "deepgram"
    STT_API_KEY: Optional[str] = Field(default=None)

    TTS_PROVIDER: str = Field(default="builtin")  # "builtin", "edge-tts", "elevenlabs"
    TTS_API_KEY: Optional[str] = Field(default=None)
    TTS_VOICE: str = Field(default="en-US-JennyNeural")
    TTS_SPEED: float = Field(default=1.0)

    # RAG Settings Defaults
    DEFAULT_CHUNK_SIZE: int = Field(default=500)
    DEFAULT_CHUNK_OVERLAP: int = Field(default=80)
    DEFAULT_RETRIEVAL_K: int = Field(default=5)
    DEFAULT_RERANK_K: int = Field(default=3)
    DEFAULT_SIMILARITY_THRESHOLD: float = Field(default=0.3)
    MIN_GROUNDING_CONFIDENCE: float = Field(default=0.6)

    # Directories
    DATA_DIR: str = Field(default="./data")
    ML_ARTIFACTS_DIR: str = Field(default="./ml/artifacts")

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


settings = Settings()

# Ensure local directories exist
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.STORAGE_LOCAL_DIR, exist_ok=True)
os.makedirs(settings.QDRANT_STORAGE_PATH, exist_ok=True)
os.makedirs(settings.ML_ARTIFACTS_DIR, exist_ok=True)

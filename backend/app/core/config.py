from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    app_name: str = Field(
        default="API Context Engine",
        alias="APP_NAME",
    )

    app_version: str = Field(
        default="0.1.0",
        alias="APP_VERSION",
    )

    app_description: str = Field(
        default=(
            "AI-powered platform for understanding "
            "and interacting with API specifications"
        ),
        alias="APP_DESCRIPTION",
    )

    database_url: str = Field(
        default="sqlite:///./api_context_engine.db",
        alias="DATABASE_URL",
    )

    redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL",
    )

    redis_cache_ttl_seconds: int = Field(
        default=300,
        gt=0,
        alias="REDIS_CACHE_TTL_SECONDS",
    )

    debug: bool = Field(
        default=True,
        alias="DEBUG",
    )

    host: str = Field(
        default="127.0.0.1",
        alias="HOST",
    )

    port: int = Field(
        default=8000,
        alias="PORT",
    )

    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )

    # ------------------------------------------------------------------
    # RAG
    # ------------------------------------------------------------------

    rag_embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="RAG_EMBEDDING_MODEL",
    )

    rag_vector_store_path: str = Field(
        default="./data/faiss",
        alias="RAG_VECTOR_STORE_PATH",
    )

    rag_chunk_size: int = Field(
        default=1000,
        gt=0,
        alias="RAG_CHUNK_SIZE",
    )

    rag_retrieval_limit: int = Field(
        default=5,
        gt=0,
        alias="RAG_RETRIEVAL_LIMIT",
    )

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------

    llm_provider: str = Field(
        default="deterministic",
        alias="LLM_PROVIDER",
    )

    groq_api_key: str | None = Field(
        default=None,
        alias="GROQ_API_KEY",
    )

    groq_model: str = Field(
        default="openai/gpt-oss-20b",
        alias="GROQ_MODEL",
    )

    gemini_api_key: str | None = Field(
        default=None,
        alias="GEMINI_API_KEY",
    )

    gemini_model: str = Field(
        default="gemini-3.6-flash",
        alias="GEMINI_MODEL",
    )

    # ------------------------------------------------------------------
    # LLM fallback
    # ------------------------------------------------------------------

    llm_fallback_enabled: bool = Field(
        default=True,
        alias="LLM_FALLBACK_ENABLED",
    )

    llm_fallback_provider: str = Field(
        default="gemini",
        alias="LLM_FALLBACK_PROVIDER",
    )

    llm_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        alias="LLM_TIMEOUT_SECONDS",
    )

    llm_max_retries: int = Field(
        default=2,
        ge=0,
        alias="LLM_MAX_RETRIES",
    )

    llm_retry_backoff_seconds: float = Field(
        default=1.0,
        gt=0,
        alias="LLM_RETRY_BACKOFF_SECONDS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    """

    return Settings()


settings = get_settings()

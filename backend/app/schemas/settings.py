from typing import Literal

from pydantic import BaseModel, Field


class AISettingsResponse(BaseModel):
    """
    Public AI configuration returned to the frontend.

    Secrets such as API keys are intentionally never exposed.
    """

    provider: Literal["deterministic", "groq", "gemini"]
    model: str
    timeout_seconds: float
    max_retries: int
    retry_backoff_seconds: float

    fallback_enabled: bool
    fallback_provider: Literal["deterministic", "groq", "gemini"]


class AISettingsUpdateRequest(BaseModel):
    """
    Runtime AI configuration accepted from the frontend.

    API keys are deliberately excluded. They remain backend-only
    environment configuration.
    """

    provider: Literal["deterministic", "groq", "gemini"]

    model: str | None = Field(
        default=None,
        min_length=1,
    )

    timeout_seconds: float = Field(
        default=60.0,
        gt=0,
        le=300,
    )

    max_retries: int = Field(
        default=2,
        ge=0,
        le=10,
    )

    retry_backoff_seconds: float = Field(
        default=1.0,
        gt=0,
        le=30,
    )

    fallback_enabled: bool = True

    fallback_provider: Literal[
        "deterministic",
        "groq",
        "gemini",
    ] = "gemini"

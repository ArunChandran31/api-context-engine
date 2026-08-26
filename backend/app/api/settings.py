from typing import Literal

from fastapi import APIRouter, HTTPException

from app.ai.runtime import clear_ai_dependencies_cache
from app.core.config import get_settings
from app.core.runtime_settings import (
    get_effective_settings,
    update_runtime_ai_settings,
)
from app.schemas.settings import (
    AISettingsResponse,
    AISettingsUpdateRequest,
)

router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
)

ProviderName = Literal["deterministic", "groq", "gemini"]


def _provider_name(value: str) -> ProviderName:
    """
    Convert a configured provider string into the supported provider type.

    Settings values originate from environment configuration, so validate
    them before exposing them through the API.
    """
    if value == "deterministic":
        return "deterministic"

    if value == "groq":
        return "groq"

    if value == "gemini":
        return "gemini"

    raise RuntimeError(f"Unsupported configured LLM provider: {value}")


def _model_for_provider(
    provider: ProviderName,
    settings,
) -> str:
    if provider == "groq":
        return settings.groq_model

    if provider == "gemini":
        return settings.gemini_model

    return "deterministic"


def _build_response() -> AISettingsResponse:
    settings = get_effective_settings()

    provider = _provider_name(settings.llm_provider)
    fallback_provider = _provider_name(settings.llm_fallback_provider)

    return AISettingsResponse(
        provider=provider,
        model=_model_for_provider(
            provider,
            settings,
        ),
        timeout_seconds=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
        retry_backoff_seconds=settings.llm_retry_backoff_seconds,
        fallback_enabled=settings.llm_fallback_enabled,
        fallback_provider=fallback_provider,
    )


@router.get(
    "/ai",
    response_model=AISettingsResponse,
)
def get_ai_settings() -> AISettingsResponse:
    return _build_response()


@router.put(
    "/ai",
    response_model=AISettingsResponse,
)
def update_ai_settings(
    request: AISettingsUpdateRequest,
) -> AISettingsResponse:
    base_settings = get_settings()

    model = request.model

    if model is None:
        if request.provider == "groq":
            model = base_settings.groq_model

        elif request.provider == "gemini":
            model = base_settings.gemini_model

        else:
            model = "deterministic"

    if request.provider == "groq" and not base_settings.groq_api_key:
        raise HTTPException(
            status_code=400,
            detail="GROQ_API_KEY is not configured on the backend.",
        )

    if request.provider == "gemini" and not base_settings.gemini_api_key:
        raise HTTPException(
            status_code=400,
            detail="GEMINI_API_KEY is not configured on the backend.",
        )

    if request.fallback_enabled and request.fallback_provider == request.provider:
        raise HTTPException(
            status_code=400,
            detail="Fallback provider must differ from the primary provider.",
        )

    update_runtime_ai_settings(
        provider=request.provider,
        model=model,
        timeout_seconds=request.timeout_seconds,
        max_retries=request.max_retries,
        retry_backoff_seconds=request.retry_backoff_seconds,
        fallback_enabled=request.fallback_enabled,
        fallback_provider=request.fallback_provider,
    )

    clear_ai_dependencies_cache()

    return _build_response()

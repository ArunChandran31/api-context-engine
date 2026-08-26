from dataclasses import dataclass

from app.core.config import Settings, get_settings


@dataclass
class RuntimeAISettings:
    """
    Runtime overrides for AI configuration.

    Values not explicitly overridden continue to come from Settings/.env.
    """

    provider: str | None = None
    model: str | None = None

    timeout_seconds: float | None = None
    max_retries: int | None = None
    retry_backoff_seconds: float | None = None

    fallback_enabled: bool | None = None
    fallback_provider: str | None = None


_runtime_settings = RuntimeAISettings()


def get_runtime_ai_settings() -> RuntimeAISettings:
    return _runtime_settings


def update_runtime_ai_settings(
    *,
    provider: str,
    model: str | None,
    timeout_seconds: float,
    max_retries: int,
    retry_backoff_seconds: float,
    fallback_enabled: bool,
    fallback_provider: str,
) -> None:
    _runtime_settings.provider = provider
    _runtime_settings.model = model

    _runtime_settings.timeout_seconds = timeout_seconds
    _runtime_settings.max_retries = max_retries
    _runtime_settings.retry_backoff_seconds = retry_backoff_seconds

    _runtime_settings.fallback_enabled = fallback_enabled
    _runtime_settings.fallback_provider = fallback_provider


def clear_runtime_ai_settings() -> None:
    global _runtime_settings

    _runtime_settings = RuntimeAISettings()


def apply_runtime_ai_settings(
    settings: Settings,
) -> Settings:
    """
    Return a Settings copy containing runtime AI overrides.

    The original Settings object is never mutated.
    """

    runtime = get_runtime_ai_settings()

    updates: dict[str, object] = {}

    if runtime.provider is not None:
        updates["llm_provider"] = runtime.provider

    if runtime.timeout_seconds is not None:
        updates["llm_timeout_seconds"] = runtime.timeout_seconds

    if runtime.max_retries is not None:
        updates["llm_max_retries"] = runtime.max_retries

    if runtime.retry_backoff_seconds is not None:
        updates["llm_retry_backoff_seconds"] = runtime.retry_backoff_seconds

    if runtime.fallback_enabled is not None:
        updates["llm_fallback_enabled"] = runtime.fallback_enabled

    if runtime.fallback_provider is not None:
        updates["llm_fallback_provider"] = runtime.fallback_provider

    if runtime.model is not None:
        provider = runtime.provider or settings.llm_provider

        if provider == "groq":
            updates["groq_model"] = runtime.model

        elif provider == "gemini":
            updates["gemini_model"] = runtime.model

    if not updates:
        return settings

    return settings.model_copy(
        update=updates,
    )


def get_effective_settings() -> Settings:
    """
    Return environment settings combined with runtime overrides.
    """

    return apply_runtime_ai_settings(
        get_settings(),
    )

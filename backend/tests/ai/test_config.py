import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_expose_ai_defaults() -> None:
    settings = Settings(
        _env_file=None,  # pyright: ignore[reportCallIssue]
    )

    assert settings.llm_provider == "deterministic"
    assert settings.groq_api_key is None
    assert settings.groq_model == "openai/gpt-oss-20b"


def test_settings_accept_ai_configuration() -> None:
    settings = Settings(
        LLM_PROVIDER="groq",
        GROQ_API_KEY="test-api-key",
        GROQ_MODEL="test-model",
        _env_file=None,  # pyright: ignore[reportCallIssue]
    )

    assert settings.llm_provider == "groq"
    assert settings.groq_api_key == "test-api-key"
    assert settings.groq_model == "test-model"


def test_settings_expose_llm_reliability_defaults() -> None:
    settings = Settings(
        _env_file=None,  # pyright: ignore[reportCallIssue]
    )

    assert settings.llm_timeout_seconds == 30.0
    assert settings.llm_max_retries == 2
    assert settings.llm_retry_backoff_seconds == 1.0


def test_settings_accept_llm_reliability_configuration() -> None:
    settings = Settings(
        LLM_TIMEOUT_SECONDS=10.0,
        LLM_MAX_RETRIES=3,
        LLM_RETRY_BACKOFF_SECONDS=2.0,
        _env_file=None,  # pyright: ignore[reportCallIssue]
    )

    assert settings.llm_timeout_seconds == 10.0
    assert settings.llm_max_retries == 3
    assert settings.llm_retry_backoff_seconds == 2.0


def test_settings_reject_non_positive_llm_timeout() -> None:
    with pytest.raises(ValidationError):
        Settings(
            LLM_TIMEOUT_SECONDS=0,
            _env_file=None,  # pyright: ignore[reportCallIssue]
        )


def test_settings_reject_negative_llm_retries() -> None:
    with pytest.raises(ValidationError):
        Settings(
            LLM_MAX_RETRIES=-1,
            _env_file=None,  # pyright: ignore[reportCallIssue]
        )


def test_settings_reject_non_positive_retry_backoff() -> None:
    with pytest.raises(ValidationError):
        Settings(
            LLM_RETRY_BACKOFF_SECONDS=0,
            _env_file=None,  # pyright: ignore[reportCallIssue]
        )

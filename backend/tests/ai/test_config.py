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

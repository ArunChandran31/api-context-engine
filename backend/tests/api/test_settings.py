from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_ai_settings_returns_effective_configuration() -> None:
    response = client.get("/api/settings/ai")

    assert response.status_code == 200

    data = response.json()

    assert data["provider"] in {
        "deterministic",
        "groq",
        "gemini",
    }
    assert isinstance(data["model"], str)
    assert data["model"]
    assert isinstance(data["timeout_seconds"], (int, float))
    assert isinstance(data["max_retries"], int)
    assert isinstance(data["retry_backoff_seconds"], (int, float))
    assert isinstance(data["fallback_enabled"], bool)
    assert data["fallback_provider"] in {
        "deterministic",
        "groq",
        "gemini",
    }


def test_update_ai_settings_changes_runtime_configuration() -> None:
    payload = {
        "provider": "deterministic",
        "model": "deterministic",
        "timeout_seconds": 45,
        "max_retries": 1,
        "retry_backoff_seconds": 2,
        "fallback_enabled": False,
        "fallback_provider": "gemini",
    }

    with patch("app.api.settings.clear_ai_dependencies_cache") as clear_cache:
        response = client.put(
            "/api/settings/ai",
            json=payload,
        )

    assert response.status_code == 200
    clear_cache.assert_called_once()

    data = response.json()

    assert data["provider"] == "deterministic"
    assert data["model"] == "deterministic"
    assert data["timeout_seconds"] == 45
    assert data["max_retries"] == 1
    assert data["retry_backoff_seconds"] == 2
    assert data["fallback_enabled"] is False
    assert data["fallback_provider"] == "gemini"


def test_update_ai_settings_rejects_same_primary_and_fallback_provider() -> None:
    payload = {
        "provider": "groq",
        "model": "openai/gpt-oss-20b",
        "timeout_seconds": 60,
        "max_retries": 2,
        "retry_backoff_seconds": 1,
        "fallback_enabled": True,
        "fallback_provider": "groq",
    }

    with patch("app.api.settings.get_settings") as get_settings:
        settings = get_settings.return_value
        settings.groq_api_key = "test-groq-key"

        response = client.put(
            "/api/settings/ai",
            json=payload,
        )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Fallback provider must differ from the primary provider."
    )


def test_update_ai_settings_rejects_groq_without_api_key() -> None:
    with patch("app.api.settings.get_settings") as get_settings:
        settings = get_settings.return_value
        settings.groq_api_key = None

        response = client.put(
            "/api/settings/ai",
            json={
                "provider": "groq",
                "model": "openai/gpt-oss-20b",
                "timeout_seconds": 60,
                "max_retries": 2,
                "retry_backoff_seconds": 1,
                "fallback_enabled": False,
                "fallback_provider": "gemini",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "GROQ_API_KEY is not configured on the backend."
    )


def test_update_ai_settings_rejects_gemini_without_api_key() -> None:
    with patch("app.api.settings.get_settings") as get_settings:
        settings = get_settings.return_value
        settings.gemini_api_key = None

        response = client.put(
            "/api/settings/ai",
            json={
                "provider": "gemini",
                "model": "gemini-3.6-flash",
                "timeout_seconds": 60,
                "max_retries": 2,
                "retry_backoff_seconds": 1,
                "fallback_enabled": False,
                "fallback_provider": "groq",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "GEMINI_API_KEY is not configured on the backend."
    )


def test_update_ai_settings_validates_request_ranges() -> None:
    response = client.put(
        "/api/settings/ai",
        json={
            "provider": "deterministic",
            "model": "deterministic",
            "timeout_seconds": 0,
            "max_retries": -1,
            "retry_backoff_seconds": 1,
            "fallback_enabled": False,
            "fallback_provider": "gemini",
        },
    )

    assert response.status_code == 422

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.ai.debug_models import DebugResult
from app.api.debug import get_ai_dependencies
from app.main import app

client = TestClient(app)


def test_debug_endpoint_returns_explanation() -> None:
    dependencies = MagicMock()

    dependencies.debug_service.debug.return_value = DebugResult(
        explanation="Mock debug explanation.",
    )

    app.dependency_overrides[get_ai_dependencies] = lambda: dependencies

    response = client.post(
        "/api/ai/debug",
        json={
            "question": "Why does POST /pets return 500?",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "explanation": "Mock debug explanation.",
    }


def test_debug_endpoint_rejects_empty_question() -> None:
    response = client.post(
        "/api/ai/debug",
        json={
            "question": "",
        },
    )

    assert response.status_code == 422

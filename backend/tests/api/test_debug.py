from unittest.mock import MagicMock

from app.ai.debug_models import DebugResult
from app.api.debug import get_ai_dependencies
from app.main import app
from fastapi.testclient import TestClient

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
            "specification_id": 6,
            "endpoint": "POST /pets",
            "status_code": 500,
            "error_message": "Internal Server Error",
            "request_body": '{"name": "Buddy"}',
            "response_body": '{"message": "Internal Server Error"}',
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    assert response.json() == {
        "explanation": "Mock debug explanation.",
    }

    dependencies.debug_service.debug.assert_called_once_with(
        question="Why does POST /pets return 500?",
        specification_id=6,
        endpoint="POST /pets",
        status_code=500,
        error_message="Internal Server Error",
        request_body='{"name": "Buddy"}',
        response_body='{"message": "Internal Server Error"}',
    )


def test_debug_endpoint_rejects_empty_question() -> None:
    response = client.post(
        "/api/ai/debug",
        json={
            "question": "",
            "specification_id": 6,
            "endpoint": "POST /pets",
            "status_code": 500,
            "error_message": "Internal Server Error",
        },
    )

    assert response.status_code == 422


def test_debug_endpoint_rejects_invalid_specification_id() -> None:
    response = client.post(
        "/api/ai/debug",
        json={
            "question": "Why does POST /pets return 500?",
            "specification_id": 0,
            "endpoint": "POST /pets",
            "status_code": 500,
            "error_message": "Internal Server Error",
        },
    )

    assert response.status_code == 422


def test_debug_endpoint_rejects_invalid_status_code() -> None:
    response = client.post(
        "/api/ai/debug",
        json={
            "question": "Why does POST /pets return 500?",
            "specification_id": 6,
            "endpoint": "POST /pets",
            "status_code": 600,
            "error_message": "Internal Server Error",
        },
    )

    assert response.status_code == 422


def test_debug_endpoint_rejects_empty_endpoint() -> None:
    response = client.post(
        "/api/ai/debug",
        json={
            "question": "Why does POST /pets return 500?",
            "specification_id": 6,
            "endpoint": "",
            "status_code": 500,
            "error_message": "Internal Server Error",
        },
    )

    assert response.status_code == 422


def test_debug_endpoint_rejects_empty_error_message() -> None:
    response = client.post(
        "/api/ai/debug",
        json={
            "question": "Why does POST /pets return 500?",
            "specification_id": 6,
            "endpoint": "POST /pets",
            "status_code": 500,
            "error_message": "",
        },
    )

    assert response.status_code == 422

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.ai.debug_models import DebugResult
from app.api.debug import get_ai_dependencies
from app.core.auth import AuthenticatedUser, get_current_user
from app.database.models.api_specification import ApiSpecification
from app.main import app

TEST_USER = AuthenticatedUser(
    id="test-user-id",
    email="test@example.com",
)


client = TestClient(app)


def mock_specification(specification_id: int) -> ApiSpecification:
    return ApiSpecification(
        id=specification_id,
        title="Test API",
        version="1.0",
        description="Test API description",
        base_url="http://example.com",
        source_file="test-api.json",
        user_id=TEST_USER.id,
    )


def setup_dependencies():
    dependencies = MagicMock()

    app.dependency_overrides[get_ai_dependencies] = lambda: dependencies
    app.dependency_overrides[get_current_user] = lambda: TEST_USER

    return dependencies


def cleanup_dependencies():
    app.dependency_overrides.clear()


def test_debug_endpoint_returns_explanation() -> None:
    dependencies = setup_dependencies()

    dependencies.debug_service.debug.return_value = DebugResult(
        explanation="Mock debug explanation.",
    )

    try:
        with patch(
            "app.api.debug.specification_service.repository.get_by_id_for_user",
            return_value=mock_specification(6),
        ):
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
    finally:
        cleanup_dependencies()

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
    setup_dependencies()

    try:
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
    finally:
        cleanup_dependencies()

    assert response.status_code == 422


def test_debug_endpoint_rejects_invalid_specification_id() -> None:
    setup_dependencies()

    try:
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
    finally:
        cleanup_dependencies()

    assert response.status_code == 422


def test_debug_endpoint_rejects_invalid_status_code() -> None:
    setup_dependencies()

    try:
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
    finally:
        cleanup_dependencies()

    assert response.status_code == 422


def test_debug_endpoint_rejects_empty_endpoint() -> None:
    setup_dependencies()

    try:
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
    finally:
        cleanup_dependencies()

    assert response.status_code == 422


def test_debug_endpoint_rejects_empty_error_message() -> None:
    setup_dependencies()

    try:
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
    finally:
        cleanup_dependencies()

    assert response.status_code == 422

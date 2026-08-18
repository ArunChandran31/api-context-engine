from unittest.mock import MagicMock

from app.ai.dependencies import AIDependencies
from app.ai.test_case_models import (
    GeneratedTestCase,
    TestCaseGenerationResult,
)
from app.api.test_cases import (
    get_ai_dependencies,
    router,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient


def create_test_client(
    dependencies: AIDependencies,
) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[get_ai_dependencies] = lambda: dependencies

    return TestClient(app)


def test_generate_test_cases_returns_generated_cases() -> None:
    service = MagicMock()

    service.generate.return_value = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="Positive",
                description="Verify POST /pets succeeds.",
            )
        ]
    )

    dependencies = MagicMock(spec=AIDependencies)
    dependencies.test_case_generation_service = service

    client = create_test_client(dependencies)

    response = client.post(
        "/ai/test-cases",
        json={
            "question": "Generate test cases for POST /pets.",
            "specification_id": 3,
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "test_cases": [
            {
                "category": "Positive",
                "description": "Verify POST /pets succeeds.",
            }
        ]
    }

    service.generate.assert_called_once_with(
        endpoint="Generate test cases for POST /pets.",
        specification_id=3,
        test_style="jest",
        categories=[
            "happy",
            "validation",
            "edge",
            "auth",
            "other",
        ],
    )


def test_generate_test_cases_rejects_empty_question() -> None:
    dependencies = MagicMock(spec=AIDependencies)

    client = create_test_client(dependencies)

    response = client.post(
        "/ai/test-cases",
        json={
            "question": "",
            "specification_id": 3,
        },
    )

    assert response.status_code == 422


def test_generate_test_cases_rejects_invalid_specification_id() -> None:
    dependencies = MagicMock(spec=AIDependencies)

    client = create_test_client(dependencies)

    response = client.post(
        "/ai/test-cases",
        json={
            "question": "Generate test cases for POST /pets.",
            "specification_id": 0,
        },
    )

    assert response.status_code == 422

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
                category="Positive / Happy path",
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
                "category": "Positive / Happy path",
                "description": "Verify POST /pets succeeds.",
            }
        ],
        "skipped_categories": [],
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
            "errors",
        ],
    )


def test_generate_test_cases_accepts_errors_category() -> None:
    service = MagicMock()

    service.generate.return_value = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="Documented HTTP Errors",
                description="Verify documented HTTP 400 response.",
            )
        ]
    )

    dependencies = MagicMock(spec=AIDependencies)
    dependencies.test_case_generation_service = service

    client = create_test_client(dependencies)

    response = client.post(
        "/ai/test-cases",
        json={
            "question": (
                "Generate documented error test cases "
                "for POST /products/{product_id}."
            ),
            "specification_id": 6,
            "categories": ["errors"],
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "test_cases": [
            {
                "category": "Documented HTTP Errors",
                "description": "Verify documented HTTP 400 response.",
            }
        ],
        "skipped_categories": [],
    }

    service.generate.assert_called_once_with(
        endpoint=(
            "Generate documented error test cases " "for POST /products/{product_id}."
        ),
        specification_id=6,
        test_style="jest",
        categories=["errors"],
    )


def test_generate_test_cases_forwards_test_style_and_categories() -> None:
    service = MagicMock()

    service.generate.return_value = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="Negative / Validation",
                description="Verify missing required field.",
            )
        ]
    )

    dependencies = MagicMock(spec=AIDependencies)
    dependencies.test_case_generation_service = service

    client = create_test_client(dependencies)

    response = client.post(
        "/ai/test-cases",
        json={
            "question": "Generate validation tests for POST /products.",
            "specification_id": 6,
            "test_style": "pytest",
            "categories": ["validation"],
        },
    )

    assert response.status_code == 200

    service.generate.assert_called_once_with(
        endpoint="Generate validation tests for POST /products.",
        specification_id=6,
        test_style="pytest",
        categories=["validation"],
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


def test_generate_test_cases_rejects_invalid_category() -> None:
    dependencies = MagicMock(spec=AIDependencies)

    client = create_test_client(dependencies)

    response = client.post(
        "/ai/test-cases",
        json={
            "question": "Generate test cases for POST /pets.",
            "specification_id": 3,
            "categories": ["unknown"],
        },
    )

    assert response.status_code == 422


def test_generate_test_cases_rejects_invalid_test_style() -> None:
    dependencies = MagicMock(spec=AIDependencies)

    client = create_test_client(dependencies)

    response = client.post(
        "/ai/test-cases",
        json={
            "question": "Generate test cases for POST /pets.",
            "specification_id": 3,
            "test_style": "invalid",
        },
    )

    assert response.status_code == 422


def test_generate_test_cases_returns_422_when_grounding_validation_fails() -> None:
    service = MagicMock()

    service.generate.side_effect = ValueError(
        "Generated test case contains an undocumented "
        "concrete value for request field 'name': Test Product."
    )

    dependencies = MagicMock(spec=AIDependencies)
    dependencies.test_case_generation_service = service

    client = create_test_client(dependencies)

    response = client.post(
        "/ai/test-cases",
        json={
            "question": (
                "Generate positive test cases " "for POST /products/{product_id}."
            ),
            "specification_id": 6,
            "categories": ["happy"],
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": {
            "error": "Test case generation failed validation.",
            "message": (
                "Generated test case contains an undocumented "
                "concrete value for request field 'name': Test Product."
            ),
        }
    }

    service.generate.assert_called_once_with(
        endpoint=("Generate positive test cases " "for POST /products/{product_id}."),
        specification_id=6,
        test_style="jest",
        categories=["happy"],
    )

import pytest
from app.ai.test_case_models import GeneratedTestCase
from app.schemas.test_case import (
    TestCaseGenerationRequest,
    TestCaseGenerationResponse,
)
from pydantic import ValidationError


def test_request_schema_accepts_question() -> None:
    request = TestCaseGenerationRequest(
        question="Generate test cases for POST /pets.",
        specification_id=3,
    )

    assert request.question == "Generate test cases for POST /pets."
    assert request.specification_id == 3


def test_request_schema_rejects_empty_question() -> None:
    with pytest.raises(ValidationError):
        TestCaseGenerationRequest(
            question="",
            specification_id=3,
        )


def test_request_schema_rejects_invalid_specification_id() -> None:
    with pytest.raises(ValidationError):
        TestCaseGenerationRequest(
            question="Generate test cases for POST /pets.",
            specification_id=0,
        )


def test_response_schema() -> None:
    response = TestCaseGenerationResponse(
        test_cases=[
            GeneratedTestCase(
                category="Positive",
                description="Verify POST /pets succeeds.",
            )
        ]
    )

    assert len(response.test_cases) == 1
    assert response.test_cases[0].category == "Positive"

import pytest
from pydantic import ValidationError

from app.ai.test_case_models import GeneratedTestCase
from app.schemas.test_case import (
    TestCaseGenerationRequest,
    TestCaseGenerationResponse,
)


def test_request_schema_accepts_question() -> None:
    request = TestCaseGenerationRequest(
        question="Generate test cases for POST /pets.",
    )

    assert request.question == "Generate test cases for POST /pets."


def test_request_schema_rejects_empty_question() -> None:
    with pytest.raises(ValidationError):
        TestCaseGenerationRequest(
            question="",
        )


# def test_response_schema() -> None:
#     response = TestCaseGenerationResponse(
#         test_cases="Sample test cases",
#     )


#     assert response.test_cases == "Sample test cases"
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

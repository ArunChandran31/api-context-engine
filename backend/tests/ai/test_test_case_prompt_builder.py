import pytest

from app.ai.test_case_models import TestCaseGenerationRequest
from app.ai.test_case_prompt_builder import TestCasePromptBuilder
from app.rag.retrieval_service import RetrievalResult


def test_build_returns_generation_request() -> None:
    builder = TestCasePromptBuilder()

    result = builder.build(
        endpoint="POST /users",
        contexts=[
            RetrievalResult(
                content="POST /users creates a user.",
                score=0.95,
                metadata={},
            )
        ],
    )

    assert isinstance(result, TestCaseGenerationRequest)


def test_build_includes_endpoint() -> None:
    builder = TestCasePromptBuilder()

    request = builder.build(
        endpoint="POST /users",
        contexts=[],
    )

    assert "POST /users" in request.prompt


def test_build_includes_retrieved_context() -> None:
    builder = TestCasePromptBuilder()

    request = builder.build(
        endpoint="POST /users",
        contexts=[
            RetrievalResult(
                content="Authentication: JWT required",
                score=0.90,
                metadata={},
            ),
            RetrievalResult(
                content="Body: name, email",
                score=0.85,
                metadata={},
            ),
        ],
    )

    assert "Authentication: JWT required" in request.prompt
    assert "Body: name, email" in request.prompt


def test_build_requests_multiple_test_categories() -> None:
    builder = TestCasePromptBuilder()

    request = builder.build(
        endpoint="POST /users",
        contexts=[],
    )

    assert "positive" in request.prompt.lower()
    assert "negative" in request.prompt.lower()
    assert "edge" in request.prompt.lower()


def test_build_rejects_empty_endpoint() -> None:
    builder = TestCasePromptBuilder()

    with pytest.raises(
        ValueError,
        match="Endpoint cannot be empty.",
    ):
        builder.build(
            endpoint="   ",
            contexts=[],
        )

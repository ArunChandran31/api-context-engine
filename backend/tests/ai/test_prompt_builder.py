import pytest

from app.ai.models import GenerationRequest
from app.ai.prompt_builder import GroundedPromptBuilder
from app.rag.retrieval_service import RetrievalResult


def test_build_returns_generation_request() -> None:
    builder = GroundedPromptBuilder()

    result = builder.build(
        question="Which endpoint creates a user?",
        contexts=[
            RetrievalResult(
                content="Endpoint: POST /users\nSummary: Create user",
                score=0.95,
                metadata={"path": "/users", "method": "POST"},
            )
        ],
    )

    assert isinstance(result, GenerationRequest)


def test_build_includes_question() -> None:
    builder = GroundedPromptBuilder()

    request = builder.build(
        question="Which endpoint creates a user?",
        contexts=[],
    )

    assert "Which endpoint creates a user?" in request.prompt


def test_build_includes_retrieved_context() -> None:
    builder = GroundedPromptBuilder()

    request = builder.build(
        question="Which endpoint creates a user?",
        contexts=[
            RetrievalResult(
                content="Endpoint: POST /users\nSummary: Create user",
                score=0.95,
                metadata={},
            ),
            RetrievalResult(
                content="Endpoint: GET /users\nSummary: List users",
                score=0.80,
                metadata={},
            ),
        ],
    )

    assert "Endpoint: POST /users" in request.prompt
    assert "Endpoint: GET /users" in request.prompt


def test_build_instructs_model_to_use_only_supplied_context() -> None:
    builder = GroundedPromptBuilder()

    request = builder.build(
        question="Which endpoint creates a user?",
        contexts=[],
    )

    assert "using only the API context" in request.prompt
    assert "Do not invent endpoints" in request.prompt


def test_build_instructs_model_to_report_insufficient_context() -> None:
    builder = GroundedPromptBuilder()

    request = builder.build(
        question="Which endpoint creates a user?",
        contexts=[],
    )

    assert "available API context is insufficient" in request.prompt


def test_build_rejects_empty_question() -> None:
    builder = GroundedPromptBuilder()

    with pytest.raises(
        ValueError,
        match="Question cannot be empty.",
    ):
        builder.build(
            question="   ",
            contexts=[],
        )

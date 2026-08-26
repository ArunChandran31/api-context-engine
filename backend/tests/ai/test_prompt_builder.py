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
                metadata={
                    "path": "/users",
                    "method": "POST",
                },
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


def test_build_labels_multiple_contexts() -> None:
    builder = GroundedPromptBuilder()

    request = builder.build(
        question="Which endpoint creates a user?",
        contexts=[
            RetrievalResult(
                content="Endpoint: POST /users",
                score=0.95,
                metadata={},
            ),
            RetrievalResult(
                content="Endpoint: GET /users",
                score=0.80,
                metadata={},
            ),
        ],
    )

    assert "--- API Context 1 ---" in request.prompt
    assert "--- End API Context 1 ---" in request.prompt
    assert "--- API Context 2 ---" in request.prompt
    assert "--- End API Context 2 ---" in request.prompt


def test_build_instructs_model_to_use_only_supplied_context() -> None:
    builder = GroundedPromptBuilder()

    request = builder.build(
        question="Which endpoint creates a user?",
        contexts=[],
    )

    assert "using ONLY the API specification context" in request.prompt
    assert "Do not invent endpoints" in request.prompt
    assert "Do not use your general knowledge" in request.prompt


def test_build_instructs_model_to_report_insufficient_context() -> None:
    builder = GroundedPromptBuilder()

    request = builder.build(
        question="Which endpoint creates a user?",
        contexts=[],
    )

    assert "available API context is insufficient" in request.prompt
    assert "No API context was retrieved." in request.prompt


def test_build_includes_api_specific_grounding_rules() -> None:
    builder = GroundedPromptBuilder()

    request = builder.build(
        question="What authentication does this endpoint use?",
        contexts=[
            RetrievalResult(
                content=(
                    "Endpoint: GET /products/{product_id}\n"
                    "Security:\n"
                    '[{"bearerAuth": []}]'
                ),
                score=0.95,
                metadata={},
            )
        ],
    )

    assert "authentication requirements" in request.prompt
    assert (
        "Do not assume behavior merely because it is common practice" in request.prompt
    )
    assert "rely only on explicitly stated security information" in request.prompt


def test_build_includes_parameter_guidance() -> None:
    builder = GroundedPromptBuilder()

    request = builder.build(
        question="What parameters are required?",
        contexts=[],
    )

    assert "distinguish required and optional parameters" in request.prompt


def test_build_includes_request_body_guidance() -> None:
    builder = GroundedPromptBuilder()

    request = builder.build(
        question="What fields are required in the request body?",
        contexts=[],
    )

    assert "distinguish required and optional fields" in request.prompt


def test_build_includes_response_guidance() -> None:
    builder = GroundedPromptBuilder()

    request = builder.build(
        question="What happens when the resource is not found?",
        contexts=[],
    )

    assert "status code" in request.prompt
    assert "response information" in request.prompt


def test_build_preserves_exact_api_context() -> None:
    builder = GroundedPromptBuilder()

    context = (
        "API: Rich Products API\n"
        "Endpoint: POST /products/{product_id}\n"
        "Operation ID: replaceProduct\n"
        "Request Body:\n"
        '"required": ["name", "price"]'
    )

    request = builder.build(
        question="What fields are required?",
        contexts=[
            RetrievalResult(
                content=context,
                score=0.95,
                metadata={},
            )
        ],
    )

    assert context in request.prompt


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

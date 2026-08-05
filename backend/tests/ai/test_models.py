import pytest

from app.ai.models import GenerationRequest, GenerationResult


def test_generation_request_creation() -> None:
    request = GenerationRequest(
        prompt="Which endpoint creates a user?",
    )

    assert request.prompt == "Which endpoint creates a user?"


def test_generation_request_rejects_empty_prompt() -> None:
    with pytest.raises(
        ValueError,
        match="Generation prompt cannot be empty.",
    ):
        GenerationRequest(prompt="   ")


def test_generation_result_creation() -> None:
    result = GenerationResult(
        content="POST /users creates a user.",
    )

    assert result.content == "POST /users creates a user."


def test_generation_result_rejects_empty_content() -> None:
    with pytest.raises(
        ValueError,
        match="Generated content cannot be empty.",
    ):
        GenerationResult(content="   ")

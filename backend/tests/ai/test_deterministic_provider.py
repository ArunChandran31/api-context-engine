import pytest

from app.ai.deterministic_provider import DeterministicLLMProvider
from app.ai.models import GenerationRequest, GenerationResult
from app.ai.provider import LLMProvider


def test_deterministic_provider_implements_llm_provider() -> None:
    provider = DeterministicLLMProvider(
        response="POST /users creates a user.",
    )

    assert isinstance(provider, LLMProvider)


def test_deterministic_provider_returns_configured_response() -> None:
    provider = DeterministicLLMProvider(
        response="POST /users creates a user.",
    )

    request = GenerationRequest(
        prompt="Which endpoint creates a user?",
    )

    result = provider.generate(request)

    assert result == GenerationResult(
        content="POST /users creates a user.",
    )


def test_deterministic_provider_returns_same_response_for_different_prompts() -> None:
    provider = DeterministicLLMProvider(
        response="Configured response.",
    )

    first_result = provider.generate(
        GenerationRequest(prompt="First question"),
    )

    second_result = provider.generate(
        GenerationRequest(prompt="Second question"),
    )

    assert first_result == second_result


def test_deterministic_provider_rejects_empty_response() -> None:
    with pytest.raises(
        ValueError,
        match="Deterministic response cannot be empty.",
    ):
        DeterministicLLMProvider(response="   ")

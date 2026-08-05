import pytest

from app.ai.models import GenerationRequest, GenerationResult
from app.ai.provider import LLMProvider


def test_llm_provider_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        LLMProvider()  # pyright: ignore[reportAbstractUsage]


def test_concrete_llm_provider_implements_generate() -> None:
    class ConcreteLLMProvider(LLMProvider):
        def generate(
            self,
            request: GenerationRequest,
        ) -> GenerationResult:
            return GenerationResult(
                content=f"Generated response for: {request.prompt}",
            )

    provider = ConcreteLLMProvider()

    request = GenerationRequest(
        prompt="Which endpoint creates a user?",
    )

    result = provider.generate(request)

    assert result == GenerationResult(
        content=("Generated response for: " "Which endpoint creates a user?"),
    )

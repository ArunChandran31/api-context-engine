import pytest
from app.ai.exceptions import LLMProviderError
from app.ai.fallback_provider import FallbackLLMProvider
from app.ai.models import GenerationRequest, GenerationResult
from app.ai.provider import LLMProvider


class FakeProvider(LLMProvider):
    def __init__(
        self,
        result: GenerationResult | None = None,
        error: LLMProviderError | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.calls = 0

    def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        self.calls += 1

        if self.error is not None:
            raise self.error

        assert self.result is not None
        return self.result


def test_primary_provider_success_does_not_call_fallback() -> None:
    primary = FakeProvider(
        result=GenerationResult(
            content="primary response",
        ),
    )
    fallback = FakeProvider(
        result=GenerationResult(
            content="fallback response",
        ),
    )

    provider = FallbackLLMProvider(
        primary_provider=primary,
        fallback_provider=fallback,
    )

    result = provider.generate(
        GenerationRequest(prompt="hello"),
    )

    assert result.content == "primary response"
    assert primary.calls == 1
    assert fallback.calls == 0


@pytest.mark.parametrize(
    "status_code",
    [429, 500, 502, 503, 504],
)
def test_retryable_primary_failure_uses_fallback(
    status_code: int,
) -> None:
    primary = FakeProvider(
        error=LLMProviderError(
            "primary failed",
            status_code=status_code,
        ),
    )
    fallback = FakeProvider(
        result=GenerationResult(
            content="fallback response",
        ),
    )

    provider = FallbackLLMProvider(
        primary_provider=primary,
        fallback_provider=fallback,
    )

    result = provider.generate(
        GenerationRequest(prompt="hello"),
    )

    assert result.content == "fallback response"
    assert primary.calls == 1
    assert fallback.calls == 1


@pytest.mark.parametrize(
    "status_code",
    [400, 401, 403],
)
def test_non_retryable_primary_failure_does_not_use_fallback(
    status_code: int,
) -> None:
    primary = FakeProvider(
        error=LLMProviderError(
            "primary failed",
            status_code=status_code,
        ),
    )
    fallback = FakeProvider(
        result=GenerationResult(
            content="fallback response",
        ),
    )

    provider = FallbackLLMProvider(
        primary_provider=primary,
        fallback_provider=fallback,
    )

    with pytest.raises(
        LLMProviderError,
        match="primary failed",
    ):
        provider.generate(
            GenerationRequest(prompt="hello"),
        )

    assert primary.calls == 1
    assert fallback.calls == 0


def test_fallback_can_be_disabled() -> None:
    primary = FakeProvider(
        error=LLMProviderError(
            "primary failed",
            status_code=429,
        ),
    )
    fallback = FakeProvider(
        result=GenerationResult(
            content="fallback response",
        ),
    )

    provider = FallbackLLMProvider(
        primary_provider=primary,
        fallback_provider=fallback,
        fallback_enabled=False,
    )

    with pytest.raises(
        LLMProviderError,
        match="primary failed",
    ):
        provider.generate(
            GenerationRequest(prompt="hello"),
        )

    assert primary.calls == 1
    assert fallback.calls == 0


def test_fallback_error_is_propagated() -> None:
    primary = FakeProvider(
        error=LLMProviderError(
            "primary rate limited",
            status_code=429,
        ),
    )
    fallback = FakeProvider(
        error=LLMProviderError(
            "fallback unavailable",
            status_code=503,
        ),
    )

    provider = FallbackLLMProvider(
        primary_provider=primary,
        fallback_provider=fallback,
    )

    with pytest.raises(
        LLMProviderError,
        match="fallback unavailable",
    ):
        provider.generate(
            GenerationRequest(prompt="hello"),
        )

    assert primary.calls == 1
    assert fallback.calls == 1

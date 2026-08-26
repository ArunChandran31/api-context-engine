import logging

from app.ai.exceptions import LLMProviderError
from app.ai.models import GenerationRequest, GenerationResult
from app.ai.provider import LLMProvider

logger = logging.getLogger(__name__)


class FallbackLLMProvider(LLMProvider):
    """
    Provider that attempts generation with a primary provider and
    transparently falls back to a secondary provider when the primary
    provider is temporarily unavailable.
    """

    def __init__(
        self,
        primary_provider: LLMProvider,
        fallback_provider: LLMProvider,
        *,
        fallback_enabled: bool = True,
    ) -> None:
        self._primary_provider = primary_provider
        self._fallback_provider = fallback_provider
        self._fallback_enabled = fallback_enabled

    def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        try:
            return self._primary_provider.generate(request)

        except LLMProviderError as exc:
            if not self._fallback_enabled:
                raise

            if not self._should_fallback(exc):
                raise

            logger.warning(
                "Primary LLM provider failed with status %s. "
                "Falling back to secondary LLM provider.",
                exc.status_code,
            )

            try:
                return self._fallback_provider.generate(request)
            except LLMProviderError:
                logger.exception("Fallback LLM provider also failed.")
                raise

    @staticmethod
    def _should_fallback(
        exc: LLMProviderError,
    ) -> bool:
        return exc.status_code in {
            429,
            500,
            502,
            503,
            504,
        }

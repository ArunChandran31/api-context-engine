from abc import ABC, abstractmethod

from app.ai.models import GenerationRequest, GenerationResult


class LLMProvider(ABC):
    """
    Abstract interface for large-language-model text generation.

    Higher-level AI services depend on this contract rather than
    a specific LLM provider or SDK.
    """

    @abstractmethod
    def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        """
        Generate text for the supplied provider-independent request.
        """

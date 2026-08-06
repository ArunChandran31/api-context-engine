from app.ai.models import GenerationRequest, GenerationResult
from app.ai.provider import LLMProvider


class DeterministicLLMProvider(LLMProvider):
    """
    Deterministic LLM provider for local development and testing.

    Returns a configured response without making external network calls.
    """

    def __init__(self, response: str) -> None:
        if not response.strip():
            raise ValueError("Deterministic response cannot be empty.")

        self._response = response

    def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        return GenerationResult(
            content=self._response,
        )

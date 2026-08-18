from app.ai.debug_generator import DebugGenerator
from app.ai.debug_models import (
    DebugRequest,
    DebugResult,
)
from app.ai.models import GenerationRequest
from app.ai.provider import LLMProvider


class LLMDebugGenerator(DebugGenerator):
    """
    LLM-backed implementation of the debug generator.

    The generator converts the provider-independent DebugRequest
    into the common GenerationRequest used by the configured
    LLM provider.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
    ) -> None:
        self._llm_provider = llm_provider

    def generate(
        self,
        request: DebugRequest,
    ) -> DebugResult:
        generation_request = GenerationRequest(
            prompt=request.prompt,
        )

        result = self._llm_provider.generate(
            generation_request,
        )

        return DebugResult(
            explanation=result.content,
        )

from app.ai.debug_generator import DebugGenerator
from app.ai.debug_models import DebugResult
from app.ai.debug_prompt_builder import DebugPromptBuilder
from app.rag.retrieval_service import RAGRetrievalService


class DebugService:
    """
    Coordinates retrieval-grounded AI debugging.
    """

    def __init__(
        self,
        retrieval_service: RAGRetrievalService,
        prompt_builder: DebugPromptBuilder,
        debug_generator: DebugGenerator,
        retrieval_limit: int = 5,
    ) -> None:
        if retrieval_limit <= 0:
            raise ValueError("Retrieval limit must be greater than zero.")

        self._retrieval_service = retrieval_service
        self._prompt_builder = prompt_builder
        self._debug_generator = debug_generator
        self._retrieval_limit = retrieval_limit

    def debug(
        self,
        question: str,
    ) -> DebugResult:
        """
        Generate an AI-assisted debugging explanation.
        """

        if not question.strip():
            raise ValueError("Debug question cannot be empty.")

        results = self._retrieval_service.retrieve(
            query=question,
            limit=self._retrieval_limit,
        )

        context = "\n\n".join(result.content for result in results)

        request = self._prompt_builder.build(
            question=question,
            context=context,
        )

        return self._debug_generator.generate(
            request,
        )

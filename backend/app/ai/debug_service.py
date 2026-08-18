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
            raise ValueError(
                "Retrieval limit must be greater than zero.",
            )

        self._retrieval_service = retrieval_service
        self._prompt_builder = prompt_builder
        self._debug_generator = debug_generator
        self._retrieval_limit = retrieval_limit

    def debug(
        self,
        question: str,
        specification_id: int,
        endpoint: str,
        status_code: int,
        error_message: str,
        request_body: str = "",
        response_body: str = "",
    ) -> DebugResult:
        """
        Generate an AI-assisted debugging explanation
        using both API context and failure details.
        """

        if not question.strip():
            raise ValueError(
                "Debug question cannot be empty.",
            )

        if specification_id <= 0:
            raise ValueError(
                "Specification ID must be greater than zero.",
            )

        if not endpoint.strip():
            raise ValueError(
                "Endpoint cannot be empty.",
            )

        if status_code < 100 or status_code > 599:
            raise ValueError(
                "Status code must be between 100 and 599.",
            )

        if not error_message.strip():
            raise ValueError(
                "Error message cannot be empty.",
            )

        results = self._retrieval_service.retrieve(
            query=endpoint,
            limit=self._retrieval_limit,
            specification_id=specification_id,
        )

        context = "\n\n".join(
            result.content for result in results if result.content.strip()
        )

        request = self._prompt_builder.build(
            question=question,
            context=context,
            endpoint=endpoint,
            status_code=status_code,
            error_message=error_message,
            request_body=request_body,
            response_body=response_body,
        )

        return self._debug_generator.generate(
            request,
        )

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
        using API context together with failure details.
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

        retrieval_query = self._build_retrieval_query(
            question=question,
            endpoint=endpoint,
            status_code=status_code,
            error_message=error_message,
            request_body=request_body,
            response_body=response_body,
        )

        results = self._retrieval_service.retrieve(
            query=retrieval_query,
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

    @staticmethod
    def _build_retrieval_query(
        question: str,
        endpoint: str,
        status_code: int,
        error_message: str,
        request_body: str,
        response_body: str,
    ) -> str:
        """
        Build a diagnostic retrieval query containing the endpoint and
        observed failure information.

        The endpoint is intentionally kept at the beginning because the
        retrieval service performs explicit method/path matching when the
        query contains an HTTP endpoint reference.
        """

        parts = [
            endpoint.strip(),
            f"HTTP Status: {status_code}",
            f"Error: {error_message.strip()}",
            f"Question: {question.strip()}",
        ]

        if request_body.strip():
            parts.append(
                f"Request Body: {request_body.strip()}",
            )

        if response_body.strip():
            parts.append(
                f"Response / Stack Trace: {response_body.strip()}",
            )

        return "\n".join(parts)

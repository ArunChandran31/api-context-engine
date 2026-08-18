from dataclasses import dataclass

from app.ai.models import GenerationResult
from app.ai.prompt_builder import GroundedPromptBuilder
from app.ai.provider import LLMProvider
from app.rag.retrieval_service import RAGRetrievalService, RetrievalResult


@dataclass(frozen=True)
class QuestionAnswerResult:
    """
    AI answer together with the API context used to generate it.
    """

    answer: GenerationResult
    sources: list[RetrievalResult]


class QuestionAnsweringService:
    """
    Orchestrates retrieval-grounded API question answering.

    Retrieves relevant indexed API context, builds a grounded
    generation request, delegates text generation to the configured
    LLM provider, and preserves the retrieved context for source
    attribution.
    """

    def __init__(
        self,
        retrieval_service: RAGRetrievalService,
        prompt_builder: GroundedPromptBuilder,
        llm_provider: LLMProvider,
        retrieval_limit: int = 5,
    ) -> None:
        if retrieval_limit <= 0:
            raise ValueError("Retrieval limit must be positive.")

        self._retrieval_service = retrieval_service
        self._prompt_builder = prompt_builder
        self._llm_provider = llm_provider
        self._retrieval_limit = retrieval_limit

    def answer(
        self,
        question: str,
        specification_id: int,
    ) -> QuestionAnswerResult:
        if not question.strip():
            raise ValueError("Question cannot be empty.")

        if specification_id <= 0:
            raise ValueError("Specification ID must be greater than zero.")

        contexts = self._retrieval_service.retrieve(
            query=question,
            limit=self._retrieval_limit,
            specification_id=specification_id,
        )

        request = self._prompt_builder.build(
            question=question,
            contexts=contexts,
        )

        generation_result = self._llm_provider.generate(request)

        return QuestionAnswerResult(
            answer=generation_result,
            sources=contexts,
        )

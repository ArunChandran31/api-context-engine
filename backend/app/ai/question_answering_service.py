from app.ai.models import GenerationResult
from app.ai.prompt_builder import GroundedPromptBuilder
from app.ai.provider import LLMProvider
from app.rag.retrieval_service import RAGRetrievalService


class QuestionAnsweringService:
    """
    Orchestrates retrieval-grounded API question answering.

    Retrieves relevant API context, builds a grounded generation
    request, and delegates text generation to the configured LLM
    provider.
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
    ) -> GenerationResult:
        if not question.strip():
            raise ValueError("Question cannot be empty.")

        contexts = self._retrieval_service.retrieve(
            query=question,
            limit=self._retrieval_limit,
        )

        request = self._prompt_builder.build(
            question=question,
            contexts=contexts,
        )

        return self._llm_provider.generate(request)

from app.ai.test_case_generator import TestCaseGenerator
from app.ai.test_case_models import TestCaseGenerationResult
from app.ai.test_case_prompt_builder import TestCasePromptBuilder
from app.rag.retrieval_service import RAGRetrievalService


class TestCaseGenerationService:
    """
    Coordinates retrieval-grounded AI test case generation.

    Retrieves relevant API context, builds a grounded prompt,
    and delegates generation to the configured test case
    generator.
    """

    def __init__(
        self,
        retrieval_service: RAGRetrievalService,
        prompt_builder: TestCasePromptBuilder,
        generator: TestCaseGenerator,
        retrieval_limit: int = 5,
    ) -> None:
        if retrieval_limit <= 0:
            raise ValueError(
                "Retrieval limit must be positive.",
            )

        self._retrieval_service = retrieval_service
        self._prompt_builder = prompt_builder
        self._generator = generator
        self._retrieval_limit = retrieval_limit

    def generate(
        self,
        endpoint: str,
    ) -> TestCaseGenerationResult:
        if not endpoint.strip():
            raise ValueError(
                "Endpoint cannot be empty.",
            )

        contexts = self._retrieval_service.retrieve(
            query=endpoint,
            limit=self._retrieval_limit,
        )

        request = self._prompt_builder.build(
            endpoint=endpoint,
            contexts=contexts,
        )

        return self._generator.generate(request)

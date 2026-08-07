from unittest.mock import MagicMock

import pytest

from app.ai.test_case_generation_service import (
    TestCaseGenerationService,
)
from app.ai.test_case_generator import TestCaseGenerator
from app.ai.test_case_models import (
    GeneratedTestCase,
    TestCaseGenerationRequest,
    TestCaseGenerationResult,
)
from app.ai.test_case_prompt_builder import TestCasePromptBuilder
from app.rag.retrieval_service import (
    RAGRetrievalService,
    RetrievalResult,
)


def test_generate_retrieves_context_and_generates_test_cases() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = MagicMock(spec=TestCasePromptBuilder)
    generator = MagicMock(spec=TestCaseGenerator)

    contexts = [
        RetrievalResult(
            content="Endpoint: POST /users",
            score=0.95,
            metadata={},
        )
    ]

    request = TestCaseGenerationRequest(
        prompt="Prompt",
    )

    result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="Positive",
                description="Valid request",
            )
        ]
    )

    retrieval_service.retrieve.return_value = contexts
    prompt_builder.build.return_value = request
    generator.generate.return_value = result

    service = TestCaseGenerationService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        generator=generator,
        retrieval_limit=3,
    )

    generated = service.generate(
        "POST /users",
    )

    assert generated == result

    retrieval_service.retrieve.assert_called_once_with(
        query="POST /users",
        limit=3,
    )

    prompt_builder.build.assert_called_once_with(
        endpoint="POST /users",
        contexts=contexts,
    )

    generator.generate.assert_called_once_with(
        request,
    )


def test_generate_supports_empty_retrieval_results() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = TestCasePromptBuilder()
    generator = MagicMock(spec=TestCaseGenerator)

    retrieval_service.retrieve.return_value = []

    generator.generate.return_value = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="Negative",
                description="No context available",
            )
        ]
    )

    service = TestCaseGenerationService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        generator=generator,
    )

    result = service.generate(
        "POST /users",
    )

    assert len(result.test_cases) == 1

    request = generator.generate.call_args.args[0]

    assert "API Context:" in request.prompt


def test_generate_rejects_empty_endpoint() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = MagicMock(spec=TestCasePromptBuilder)
    generator = MagicMock(spec=TestCaseGenerator)

    service = TestCaseGenerationService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        generator=generator,
    )

    with pytest.raises(
        ValueError,
        match="Endpoint cannot be empty.",
    ):
        service.generate("   ")

    retrieval_service.retrieve.assert_not_called()
    prompt_builder.build.assert_not_called()
    generator.generate.assert_not_called()


def test_service_rejects_invalid_retrieval_limit() -> None:
    with pytest.raises(
        ValueError,
        match="Retrieval limit must be positive.",
    ):
        TestCaseGenerationService(
            retrieval_service=MagicMock(spec=RAGRetrievalService),
            prompt_builder=MagicMock(spec=TestCasePromptBuilder),
            generator=MagicMock(spec=TestCaseGenerator),
            retrieval_limit=0,
        )

from unittest.mock import MagicMock

import pytest

from app.ai.debug_generator import DebugGenerator
from app.ai.debug_models import (
    DebugResult,
)
from app.ai.debug_prompt_builder import DebugPromptBuilder
from app.ai.debug_service import DebugService
from app.rag.retrieval_service import (
    RAGRetrievalService,
    RetrievalResult,
)


def test_debug_retrieves_context_and_generates_response() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)

    retrieval_service.retrieve.return_value = [
        RetrievalResult(
            content="POST /pets returns 500.",
            score=0.95,
            metadata={},
        ),
    ]

    prompt_builder = DebugPromptBuilder()

    debug_generator = MagicMock(spec=DebugGenerator)

    debug_generator.generate.return_value = DebugResult(
        explanation="The endpoint raises a server error.",
    )

    service = DebugService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        debug_generator=debug_generator,
    )

    result = service.debug("Why does POST /pets return 500?")

    assert result.explanation == ("The endpoint raises a server error.")


def test_debug_supports_empty_retrieval_results() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)

    retrieval_service.retrieve.return_value = []

    prompt_builder = DebugPromptBuilder()

    debug_generator = MagicMock(spec=DebugGenerator)

    debug_generator.generate.return_value = DebugResult(
        explanation="Insufficient context.",
    )

    service = DebugService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        debug_generator=debug_generator,
    )

    result = service.debug("Unknown failure")

    assert result.explanation == ("Insufficient context.")


def test_debug_rejects_empty_question() -> None:
    service = DebugService(
        retrieval_service=MagicMock(
            spec=RAGRetrievalService,
        ),
        prompt_builder=DebugPromptBuilder(),
        debug_generator=MagicMock(
            spec=DebugGenerator,
        ),
    )

    with pytest.raises(
        ValueError,
        match="Debug question cannot be empty.",
    ):
        service.debug("")


def test_service_rejects_invalid_retrieval_limit() -> None:
    with pytest.raises(
        ValueError,
        match="Retrieval limit must be greater than zero.",
    ):
        DebugService(
            retrieval_service=MagicMock(
                spec=RAGRetrievalService,
            ),
            prompt_builder=DebugPromptBuilder(),
            debug_generator=MagicMock(
                spec=DebugGenerator,
            ),
            retrieval_limit=0,
        )

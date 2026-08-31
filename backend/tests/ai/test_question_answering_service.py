from unittest.mock import MagicMock

import pytest

from app.ai.models import GenerationRequest, GenerationResult
from app.ai.prompt_builder import GroundedPromptBuilder
from app.ai.provider import LLMProvider
from app.ai.question_answering_service import QuestionAnsweringService
from app.cache.service import CacheService
from app.rag.retrieval_service import RAGRetrievalService, RetrievalResult


def _build_service(
    retrieval_service: RAGRetrievalService,
    prompt_builder: GroundedPromptBuilder,
    llm_provider: LLMProvider,
    cache_service: CacheService,
    retrieval_limit: int = 5,
) -> QuestionAnsweringService:
    return QuestionAnsweringService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        llm_provider=llm_provider,
        cache_service=cache_service,
        retrieval_limit=retrieval_limit,
    )


def test_answer_cache_miss_retrieves_generates_and_caches() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = MagicMock(spec=GroundedPromptBuilder)
    llm_provider = MagicMock(spec=LLMProvider)
    cache_service = MagicMock(spec=CacheService)

    cache_service.get.return_value = None

    contexts = [
        RetrievalResult(
            content="Endpoint: POST /users",
            score=0.95,
            metadata={"path": "/users", "method": "POST"},
        )
    ]

    generation_request = GenerationRequest(
        prompt="Grounded prompt",
    )

    generation_result = GenerationResult(
        content="POST /users creates a user.",
    )

    retrieval_service.retrieve.return_value = contexts
    prompt_builder.build.return_value = generation_request
    llm_provider.generate.return_value = generation_result

    service = _build_service(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        llm_provider=llm_provider,
        cache_service=cache_service,
        retrieval_limit=3,
    )

    result = service.answer(
        "Which endpoint creates a user?",
        specification_id=3,
    )

    assert result.answer == generation_result
    assert result.sources == contexts

    cache_service.get.assert_called_once()

    retrieval_service.retrieve.assert_called_once_with(
        query="Which endpoint creates a user?",
        limit=3,
        specification_id=3,
    )

    prompt_builder.build.assert_called_once_with(
        question="Which endpoint creates a user?",
        contexts=contexts,
    )

    llm_provider.generate.assert_called_once_with(
        generation_request,
    )

    cache_service.set.assert_called_once()


def test_answer_cache_hit_skips_retrieval_and_generation() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = MagicMock(spec=GroundedPromptBuilder)
    llm_provider = MagicMock(spec=LLMProvider)
    cache_service = MagicMock(spec=CacheService)

    cached_value = {
        "answer": {
            "content": "POST /users creates a user.",
        },
        "sources": [
            {
                "content": "Endpoint: POST /users",
                "score": 0.95,
                "metadata": {
                    "path": "/users",
                    "method": "POST",
                },
            }
        ],
    }

    cache_service.get.return_value = cached_value

    service = _build_service(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        llm_provider=llm_provider,
        cache_service=cache_service,
        retrieval_limit=3,
    )

    result = service.answer(
        "Which endpoint creates a user?",
        specification_id=3,
    )

    assert result.answer.content == "POST /users creates a user."
    assert len(result.sources) == 1
    assert result.sources[0].content == "Endpoint: POST /users"
    assert result.sources[0].score == 0.95
    assert result.sources[0].metadata == {
        "path": "/users",
        "method": "POST",
    }

    cache_service.get.assert_called_once()

    retrieval_service.retrieve.assert_not_called()
    prompt_builder.build.assert_not_called()
    llm_provider.generate.assert_not_called()
    cache_service.set.assert_not_called()


def test_answer_retrieves_context_and_generates_response() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = MagicMock(spec=GroundedPromptBuilder)
    llm_provider = MagicMock(spec=LLMProvider)
    cache_service = MagicMock(spec=CacheService)

    cache_service.get.return_value = None

    contexts = [
        RetrievalResult(
            content="Endpoint: POST /users",
            score=0.95,
            metadata={"path": "/users", "method": "POST"},
        )
    ]

    generation_request = GenerationRequest(
        prompt="Grounded prompt",
    )

    generation_result = GenerationResult(
        content="POST /users creates a user.",
    )

    retrieval_service.retrieve.return_value = contexts
    prompt_builder.build.return_value = generation_request
    llm_provider.generate.return_value = generation_result

    service = _build_service(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        llm_provider=llm_provider,
        cache_service=cache_service,
        retrieval_limit=3,
    )

    result = service.answer(
        "Which endpoint creates a user?",
        specification_id=3,
    )

    assert result.answer == generation_result
    assert result.sources == contexts


def test_answer_supports_empty_retrieval_results() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = GroundedPromptBuilder()
    llm_provider = MagicMock(spec=LLMProvider)
    cache_service = MagicMock(spec=CacheService)

    cache_service.get.return_value = None
    retrieval_service.retrieve.return_value = []

    llm_provider.generate.return_value = GenerationResult(
        content="The available API context is insufficient.",
    )

    service = _build_service(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        llm_provider=llm_provider,
        cache_service=cache_service,
    )

    result = service.answer(
        "Which endpoint deletes an account?",
        specification_id=3,
    )

    assert result.answer.content == "The available API context is insufficient."
    assert result.sources == []

    generation_request = llm_provider.generate.call_args.args[0]

    assert "API Context:" in generation_request.prompt
    assert "available API context is insufficient" in generation_request.prompt


def test_answer_rejects_empty_question() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = MagicMock(spec=GroundedPromptBuilder)
    llm_provider = MagicMock(spec=LLMProvider)
    cache_service = MagicMock(spec=CacheService)

    service = _build_service(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        llm_provider=llm_provider,
        cache_service=cache_service,
    )

    with pytest.raises(
        ValueError,
        match="Question cannot be empty.",
    ):
        service.answer(
            "   ",
            specification_id=3,
        )

    cache_service.get.assert_not_called()
    retrieval_service.retrieve.assert_not_called()
    prompt_builder.build.assert_not_called()
    llm_provider.generate.assert_not_called()


def test_service_rejects_invalid_retrieval_limit() -> None:
    with pytest.raises(
        ValueError,
        match="Retrieval limit must be positive.",
    ):
        QuestionAnsweringService(
            retrieval_service=MagicMock(spec=RAGRetrievalService),
            prompt_builder=MagicMock(spec=GroundedPromptBuilder),
            llm_provider=MagicMock(spec=LLMProvider),
            cache_service=MagicMock(spec=CacheService),
            retrieval_limit=0,
        )

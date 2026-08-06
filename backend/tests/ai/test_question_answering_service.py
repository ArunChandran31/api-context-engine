from unittest.mock import MagicMock

import pytest

from app.ai.models import GenerationRequest, GenerationResult
from app.ai.prompt_builder import GroundedPromptBuilder
from app.ai.provider import LLMProvider
from app.ai.question_answering_service import QuestionAnsweringService
from app.rag.retrieval_service import RAGRetrievalService, RetrievalResult


def test_answer_retrieves_context_and_generates_response() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = MagicMock(spec=GroundedPromptBuilder)
    llm_provider = MagicMock(spec=LLMProvider)

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

    service = QuestionAnsweringService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        llm_provider=llm_provider,
        retrieval_limit=3,
    )

    result = service.answer(
        "Which endpoint creates a user?",
    )

    assert result == generation_result

    retrieval_service.retrieve.assert_called_once_with(
        query="Which endpoint creates a user?",
        limit=3,
    )

    prompt_builder.build.assert_called_once_with(
        question="Which endpoint creates a user?",
        contexts=contexts,
    )

    llm_provider.generate.assert_called_once_with(
        generation_request,
    )


def test_answer_supports_empty_retrieval_results() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = GroundedPromptBuilder()
    llm_provider = MagicMock(spec=LLMProvider)

    retrieval_service.retrieve.return_value = []

    llm_provider.generate.return_value = GenerationResult(
        content="The available API context is insufficient.",
    )

    service = QuestionAnsweringService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        llm_provider=llm_provider,
    )

    result = service.answer(
        "Which endpoint deletes an account?",
    )

    assert result.content == "The available API context is insufficient."

    generation_request = llm_provider.generate.call_args.args[0]

    assert "API Context:" in generation_request.prompt
    assert "available API context is insufficient" in generation_request.prompt


def test_answer_rejects_empty_question() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = MagicMock(spec=GroundedPromptBuilder)
    llm_provider = MagicMock(spec=LLMProvider)

    service = QuestionAnsweringService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        llm_provider=llm_provider,
    )

    with pytest.raises(
        ValueError,
        match="Question cannot be empty.",
    ):
        service.answer("   ")

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
            retrieval_limit=0,
        )

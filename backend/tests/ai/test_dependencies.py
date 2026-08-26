from unittest.mock import MagicMock

import pytest
from app.ai.dependencies import AIDependencies, build_ai_dependencies
from app.ai.deterministic_provider import DeterministicLLMProvider
from app.ai.fallback_provider import FallbackLLMProvider
from app.ai.gemini_provider import GeminiLLMProvider
from app.ai.groq_provider import GroqLLMProvider
from app.ai.llm_test_case_generator import LLMTestCaseGenerator
from app.ai.prompt_builder import GroundedPromptBuilder
from app.ai.question_answering_service import QuestionAnsweringService
from app.core.config import Settings
from app.rag.dependencies import RAGDependencies
from app.rag.retrieval_service import RAGRetrievalService


def test_build_ai_dependencies_returns_dependency_graph() -> None:
    settings = Settings(
        _env_file=None,  # pyright: ignore[reportCallIssue]
    )

    retrieval_service = MagicMock(spec=RAGRetrievalService)

    rag_dependencies = MagicMock(spec=RAGDependencies)
    rag_dependencies.retrieval_service = retrieval_service

    dependencies = build_ai_dependencies(
        settings=settings,
        rag_dependencies=rag_dependencies,
    )

    assert isinstance(dependencies, AIDependencies)
    assert isinstance(
        dependencies.llm_provider,
        DeterministicLLMProvider,
    )
    assert isinstance(
        dependencies.prompt_builder,
        GroundedPromptBuilder,
    )
    assert isinstance(
        dependencies.question_answering_service,
        QuestionAnsweringService,
    )


def test_question_answering_service_uses_rag_retrieval_service() -> None:
    settings = Settings()

    retrieval_service = MagicMock(spec=RAGRetrievalService)
    retrieval_service.retrieve.return_value = []

    rag_dependencies = MagicMock(spec=RAGDependencies)
    rag_dependencies.retrieval_service = retrieval_service

    dependencies = build_ai_dependencies(
        settings=settings,
        rag_dependencies=rag_dependencies,
    )

    result = dependencies.question_answering_service.answer(
        "Which endpoint creates a user?",
        specification_id=3,
    )

    retrieval_service.retrieve.assert_called_once_with(
        query="Which endpoint creates a user?",
        limit=settings.rag_retrieval_limit,
        specification_id=3,
    )

    assert result.answer.content
    assert result.sources == []


def test_build_ai_dependencies_uses_deterministic_provider_by_default() -> None:
    settings = Settings(
        _env_file=None,  # pyright: ignore[reportCallIssue]
    )

    retrieval_service = MagicMock(spec=RAGRetrievalService)

    rag_dependencies = MagicMock()
    rag_dependencies.retrieval_service = retrieval_service

    dependencies = build_ai_dependencies(
        settings=settings,
        rag_dependencies=rag_dependencies,
    )

    assert isinstance(
        dependencies.llm_provider,
        DeterministicLLMProvider,
    )


def test_build_ai_dependencies_uses_groq_provider() -> None:
    settings = Settings(
        LLM_PROVIDER="groq",
        GROQ_API_KEY="test-api-key",
        GROQ_MODEL="test-model",
        LLM_FALLBACK_ENABLED=False,
        _env_file=None,  # pyright: ignore[reportCallIssue]
    )

    retrieval_service = MagicMock(spec=RAGRetrievalService)

    rag_dependencies = MagicMock()
    rag_dependencies.retrieval_service = retrieval_service

    dependencies = build_ai_dependencies(
        settings=settings,
        rag_dependencies=rag_dependencies,
    )

    assert isinstance(
        dependencies.llm_provider,
        GroqLLMProvider,
    )


def test_build_ai_dependencies_passes_llm_timeout_to_groq_provider() -> None:
    settings = Settings(
        LLM_PROVIDER="groq",
        GROQ_API_KEY="test-api-key",
        GROQ_MODEL="test-model",
        LLM_TIMEOUT_SECONDS=10.0,
        LLM_FALLBACK_ENABLED=False,
        _env_file=None,  # pyright: ignore[reportCallIssue]
    )

    retrieval_service = MagicMock(spec=RAGRetrievalService)

    rag_dependencies = MagicMock()
    rag_dependencies.retrieval_service = retrieval_service

    dependencies = build_ai_dependencies(
        settings=settings,
        rag_dependencies=rag_dependencies,
    )

    assert isinstance(
        dependencies.llm_provider,
        GroqLLMProvider,
    )

    assert dependencies.llm_provider._client.timeout == 10.0


def test_build_ai_dependencies_uses_llm_test_case_generator_for_groq() -> None:
    settings = Settings(
        LLM_PROVIDER="groq",
        GROQ_API_KEY="test-api-key",
        GROQ_MODEL="test-model",
        LLM_FALLBACK_ENABLED=False,
        _env_file=None,  # pyright: ignore[reportCallIssue]
    )

    retrieval_service = MagicMock(spec=RAGRetrievalService)

    rag_dependencies = MagicMock()
    rag_dependencies.retrieval_service = retrieval_service

    dependencies = build_ai_dependencies(
        settings=settings,
        rag_dependencies=rag_dependencies,
    )

    assert isinstance(
        dependencies.test_case_generation_service._generator,
        LLMTestCaseGenerator,
    )


def test_build_ai_dependencies_requires_groq_api_key() -> None:
    settings = Settings(
        LLM_PROVIDER="groq",
        GROQ_API_KEY=None,
        _env_file=None,  # pyright: ignore[reportCallIssue]
    )

    rag_dependencies = MagicMock(spec=RAGDependencies)

    with pytest.raises(
        ValueError,
        match="GROQ_API_KEY is required",
    ):
        build_ai_dependencies(
            settings=settings,
            rag_dependencies=rag_dependencies,
        )


def test_build_ai_dependencies_rejects_unsupported_provider() -> None:
    settings = Settings(
        LLM_PROVIDER="unsupported",
        _env_file=None,  # pyright: ignore[reportCallIssue]
    )

    rag_dependencies = MagicMock(spec=RAGDependencies)

    with pytest.raises(
        ValueError,
        match="Unsupported LLM provider: unsupported",
    ):
        build_ai_dependencies(
            settings=settings,
            rag_dependencies=rag_dependencies,
        )


def test_build_ai_dependencies_wraps_groq_with_gemini_fallback() -> None:
    settings = Settings(
        LLM_PROVIDER="groq",
        GROQ_API_KEY="test-groq-api-key",
        GROQ_MODEL="test-groq-model",
        GEMINI_API_KEY="test-gemini-api-key",
        GEMINI_MODEL="test-gemini-model",
        LLM_FALLBACK_ENABLED=True,
        LLM_FALLBACK_PROVIDER="gemini",
        _env_file=None,  # pyright: ignore[reportCallIssue]
    )

    retrieval_service = MagicMock(spec=RAGRetrievalService)

    rag_dependencies = MagicMock(spec=RAGDependencies)
    rag_dependencies.retrieval_service = retrieval_service

    dependencies = build_ai_dependencies(
        settings=settings,
        rag_dependencies=rag_dependencies,
    )

    assert isinstance(
        dependencies.llm_provider,
        FallbackLLMProvider,
    )

    assert isinstance(
        dependencies.llm_provider._primary_provider,
        GroqLLMProvider,
    )

    assert isinstance(
        dependencies.llm_provider._fallback_provider,
        GeminiLLMProvider,
    )


def test_build_ai_dependencies_disables_primary_groq_retries_when_fallback_enabled() -> (
    None
):
    settings = Settings(
        LLM_PROVIDER="groq",
        GROQ_API_KEY="test-groq-api-key",
        GROQ_MODEL="test-groq-model",
        GEMINI_API_KEY="test-gemini-api-key",
        GEMINI_MODEL="test-gemini-model",
        LLM_MAX_RETRIES=2,
        LLM_RETRY_BACKOFF_SECONDS=1.0,
        LLM_FALLBACK_ENABLED=True,
        LLM_FALLBACK_PROVIDER="gemini",
        _env_file=None,  # pyright: ignore[reportCallIssue]
    )

    retrieval_service = MagicMock(spec=RAGRetrievalService)

    rag_dependencies = MagicMock(spec=RAGDependencies)
    rag_dependencies.retrieval_service = retrieval_service

    dependencies = build_ai_dependencies(
        settings=settings,
        rag_dependencies=rag_dependencies,
    )

    assert isinstance(
        dependencies.llm_provider,
        FallbackLLMProvider,
    )

    primary_provider = dependencies.llm_provider._primary_provider

    assert isinstance(
        primary_provider,
        GroqLLMProvider,
    )

    assert primary_provider._max_retries == 0


def test_build_ai_dependencies_preserves_groq_retries_when_fallback_disabled() -> None:
    settings = Settings(
        LLM_PROVIDER="groq",
        GROQ_API_KEY="test-groq-api-key",
        GROQ_MODEL="test-groq-model",
        LLM_MAX_RETRIES=2,
        LLM_RETRY_BACKOFF_SECONDS=1.0,
        LLM_FALLBACK_ENABLED=False,
        _env_file=None,  # pyright: ignore[reportCallIssue]
    )

    retrieval_service = MagicMock(spec=RAGRetrievalService)

    rag_dependencies = MagicMock(spec=RAGDependencies)
    rag_dependencies.retrieval_service = retrieval_service

    dependencies = build_ai_dependencies(
        settings=settings,
        rag_dependencies=rag_dependencies,
    )

    assert isinstance(
        dependencies.llm_provider,
        GroqLLMProvider,
    )

    assert dependencies.llm_provider._max_retries == 2

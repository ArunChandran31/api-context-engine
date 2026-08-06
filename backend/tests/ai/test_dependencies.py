from unittest.mock import MagicMock

from app.ai.dependencies import AIDependencies, build_ai_dependencies
from app.ai.deterministic_provider import DeterministicLLMProvider
from app.ai.prompt_builder import GroundedPromptBuilder
from app.ai.question_answering_service import QuestionAnsweringService
from app.core.config import Settings
from app.rag.dependencies import RAGDependencies
from app.rag.retrieval_service import RAGRetrievalService


def test_build_ai_dependencies_returns_dependency_graph() -> None:
    settings = Settings()

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
        "Which endpoint creates a user?"
    )

    retrieval_service.retrieve.assert_called_once_with(
        query="Which endpoint creates a user?",
        limit=settings.rag_retrieval_limit,
    )

    assert result.content

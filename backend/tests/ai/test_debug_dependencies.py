from unittest.mock import MagicMock

from app.ai.debug_generator import DebugGenerator
from app.ai.debug_prompt_builder import DebugPromptBuilder
from app.ai.debug_service import DebugService
from app.ai.dependencies import (
    AIDependencies,
    build_ai_dependencies,
)
from app.core.config import Settings
from app.rag.dependencies import RAGDependencies


def test_build_ai_dependencies_contains_debug_components() -> None:
    settings = Settings(
        _env_file=None,  # pyright: ignore[reportCallIssue]
    )

    rag_dependencies = MagicMock(spec=RAGDependencies)
    rag_dependencies.retrieval_service = MagicMock()

    dependencies = build_ai_dependencies(
        settings=settings,
        rag_dependencies=rag_dependencies,
    )

    assert isinstance(
        dependencies,
        AIDependencies,
    )

    assert isinstance(
        dependencies.debug_prompt_builder,
        DebugPromptBuilder,
    )

    assert isinstance(
        dependencies.debug_generator,
        DebugGenerator,
    )

    assert isinstance(
        dependencies.debug_service,
        DebugService,
    )


def test_debug_service_uses_rag_retrieval_service() -> None:
    settings = Settings(
        _env_file=None,  # pyright: ignore[reportCallIssue]
    )

    rag_dependencies = MagicMock(spec=RAGDependencies)
    rag_dependencies.retrieval_service = MagicMock()

    dependencies = build_ai_dependencies(
        settings=settings,
        rag_dependencies=rag_dependencies,
    )

    assert (
        dependencies.debug_service._retrieval_service
        is rag_dependencies.retrieval_service
    )

from functools import lru_cache

from app.ai.dependencies import AIDependencies, build_ai_dependencies
from app.core.runtime_settings import get_effective_settings
from app.rag.dependencies import get_rag_dependencies


@lru_cache
def get_ai_dependencies() -> AIDependencies:
    """
    Return the cached application AI dependency graph.

    The AI dependency graph reuses the shared RAG dependency graph so
    the embedding provider and vector store are not duplicated.
    """
    return build_ai_dependencies(
        settings=get_effective_settings(),
        rag_dependencies=get_rag_dependencies(),
    )


def clear_ai_dependencies_cache() -> None:
    """
    Clear the cached AI dependency graph.

    This must be called whenever runtime AI configuration changes so that
    subsequent requests construct providers using the new configuration.
    """
    get_ai_dependencies.cache_clear()

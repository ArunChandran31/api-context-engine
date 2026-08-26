from functools import lru_cache

from app.ai.dependencies import AIDependencies, build_ai_dependencies
from app.core.runtime_settings import get_effective_settings


@lru_cache
def get_ai_dependencies() -> AIDependencies:
    """
    Return the cached application AI dependency graph.

    The dependency graph is built from the effective settings, which
    combine environment configuration with any runtime AI overrides.
    """
    return build_ai_dependencies(
        settings=get_effective_settings(),
    )


def clear_ai_dependencies_cache() -> None:
    """
    Clear the cached AI dependency graph.

    This must be called whenever runtime AI configuration changes so that
    subsequent requests construct providers using the new configuration.
    """
    get_ai_dependencies.cache_clear()

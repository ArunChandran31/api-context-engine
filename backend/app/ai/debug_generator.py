from abc import ABC, abstractmethod

from app.ai.debug_models import (
    DebugRequest,
    DebugResult,
)


class DebugGenerator(ABC):
    """
    Provider-independent interface for AI debugging.
    """

    @abstractmethod
    def generate(
        self,
        request: DebugRequest,
    ) -> DebugResult:
        """
        Generate a debugging explanation.
        """

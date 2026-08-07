from app.ai.debug_generator import DebugGenerator
from app.ai.debug_models import (
    DebugRequest,
    DebugResult,
)


class DeterministicDebugGenerator(DebugGenerator):
    """
    Deterministic implementation used for testing.
    """

    def __init__(
        self,
        explanation: str,
    ) -> None:
        self._explanation = explanation

    def generate(
        self,
        request: DebugRequest,
    ) -> DebugResult:
        return DebugResult(
            explanation=self._explanation,
        )

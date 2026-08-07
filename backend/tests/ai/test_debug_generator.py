import pytest

from app.ai.debug_generator import DebugGenerator
from app.ai.debug_models import (
    DebugRequest,
    DebugResult,
)


def test_debug_generator_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        DebugGenerator()


def test_concrete_debug_generator_implements_generate() -> None:
    class ConcreteDebugGenerator(DebugGenerator):
        def generate(
            self,
            request: DebugRequest,
        ) -> DebugResult:
            return DebugResult(
                explanation="Debug explanation.",
            )

    generator = ConcreteDebugGenerator()

    result = generator.generate(
        DebugRequest(
            prompt="Explain this traceback.",
        )
    )

    assert result == DebugResult(
        explanation="Debug explanation.",
    )

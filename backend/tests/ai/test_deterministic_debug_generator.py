import pytest

from app.ai.debug_generator import DebugGenerator
from app.ai.debug_models import (
    DebugRequest,
    DebugResult,
)
from app.ai.deterministic_debug_generator import (
    DeterministicDebugGenerator,
)


def test_generator_implements_interface() -> None:
    generator = DeterministicDebugGenerator(
        explanation="Deterministic explanation.",
    )

    assert isinstance(
        generator,
        DebugGenerator,
    )


def test_generator_returns_configured_result() -> None:
    generator = DeterministicDebugGenerator(
        explanation="Configured explanation.",
    )

    result = generator.generate(
        DebugRequest(
            prompt="Explain this error.",
        )
    )

    assert result == DebugResult(
        explanation="Configured explanation.",
    )


def test_generator_returns_same_result_for_different_requests() -> None:
    generator = DeterministicDebugGenerator(
        explanation="Always identical.",
    )

    first = generator.generate(
        DebugRequest(
            prompt="First prompt",
        )
    )

    second = generator.generate(
        DebugRequest(
            prompt="Second prompt",
        )
    )

    assert first == second


def test_generator_rejects_empty_explanation() -> None:
    generator = DeterministicDebugGenerator(
        explanation="",
    )

    with pytest.raises(
        ValueError,
        match="Debug explanation cannot be empty.",
    ):
        generator.generate(
            DebugRequest(
                prompt="Explain",
            )
        )

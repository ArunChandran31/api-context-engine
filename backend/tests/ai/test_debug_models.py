import pytest

from app.ai.debug_models import (
    DebugRequest,
    DebugResult,
)


def test_debug_request_creation() -> None:
    request = DebugRequest(prompt="Explain this traceback.")

    assert request.prompt == "Explain this traceback."


def test_debug_request_rejects_empty_prompt() -> None:
    with pytest.raises(
        ValueError,
        match="Debug prompt cannot be empty.",
    ):
        DebugRequest(prompt="")


def test_debug_result_creation() -> None:
    result = DebugResult(explanation="The endpoint raises an exception.")

    assert result.explanation == ("The endpoint raises an exception.")


def test_debug_result_rejects_empty_explanation() -> None:
    with pytest.raises(
        ValueError,
        match="Debug explanation cannot be empty.",
    ):
        DebugResult(explanation="")

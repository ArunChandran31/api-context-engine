from app.ai.debug_models import DebugRequest
from app.ai.debug_prompt_builder import DebugPromptBuilder


def test_prompt_builder_returns_debug_request() -> None:
    builder = DebugPromptBuilder()

    request = builder.build(
        question="Why does POST /pets return 500?",
        context="Stack trace: KeyError",
    )

    assert isinstance(request, DebugRequest)


def test_prompt_contains_question() -> None:
    builder = DebugPromptBuilder()

    request = builder.build(
        question="Why does POST /pets return 500?",
        context="Stack trace",
    )

    assert "Why does POST /pets return 500?" in request.prompt


def test_prompt_contains_context() -> None:
    builder = DebugPromptBuilder()

    request = builder.build(
        question="Question",
        context="NullPointerException",
    )

    assert "NullPointerException" in request.prompt


def test_prompt_instructs_model_to_use_context() -> None:
    builder = DebugPromptBuilder()

    request = builder.build(
        question="Question",
        context="Context",
    )

    assert "Use ONLY the provided context." in request.prompt

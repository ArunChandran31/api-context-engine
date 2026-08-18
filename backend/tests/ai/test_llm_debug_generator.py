from unittest.mock import MagicMock

from app.ai.debug_models import (
    DebugRequest,
    DebugResult,
)
from app.ai.llm_debug_generator import LLMDebugGenerator
from app.ai.models import GenerationResult
from app.ai.provider import LLMProvider


def test_generate_delegates_to_llm_provider() -> None:
    llm_provider = MagicMock(spec=LLMProvider)

    llm_provider.generate.return_value = GenerationResult(
        content="The request is missing a required field.",
    )

    generator = LLMDebugGenerator(
        llm_provider=llm_provider,
    )

    request = DebugRequest(
        prompt="Explain why POST /pets returns 400.",
    )

    result = generator.generate(request)

    assert isinstance(result, DebugResult)

    assert result.explanation == ("The request is missing a required field.")

    llm_provider.generate.assert_called_once()

    generation_request = llm_provider.generate.call_args.args[0]

    assert generation_request.prompt == ("Explain why POST /pets returns 400.")


def test_generate_preserves_debug_prompt() -> None:
    llm_provider = MagicMock(spec=LLMProvider)

    llm_provider.generate.return_value = GenerationResult(
        content="Insufficient context.",
    )

    generator = LLMDebugGenerator(
        llm_provider=llm_provider,
    )

    prompt = (
        "You are an API debugging assistant.\n" "Use only the supplied API context."
    )

    request = DebugRequest(
        prompt=prompt,
    )

    result = generator.generate(request)

    assert result.explanation == "Insufficient context."

    generation_request = llm_provider.generate.call_args.args[0]

    assert generation_request.prompt == prompt

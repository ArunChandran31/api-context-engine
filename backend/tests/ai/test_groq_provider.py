from unittest.mock import MagicMock, patch

import pytest

from app.ai.groq_provider import GroqLLMProvider
from app.ai.models import GenerationRequest, GenerationResult
from app.ai.provider import LLMProvider


def test_groq_provider_implements_llm_provider() -> None:
    with patch("app.ai.groq_provider.Groq"):
        provider = GroqLLMProvider(
            api_key="test-api-key",
            model="test-model",
        )

    assert isinstance(provider, LLMProvider)


def test_groq_provider_rejects_empty_api_key() -> None:
    with pytest.raises(
        ValueError,
        match="Groq API key cannot be empty.",
    ):
        GroqLLMProvider(
            api_key="   ",
            model="test-model",
        )


def test_groq_provider_rejects_empty_model() -> None:
    with pytest.raises(
        ValueError,
        match="Groq model cannot be empty.",
    ):
        GroqLLMProvider(
            api_key="test-api-key",
            model="   ",
        )


def test_groq_provider_generates_response() -> None:
    with patch("app.ai.groq_provider.Groq") as groq_class:
        client = MagicMock()
        groq_class.return_value = client

        completion = MagicMock()
        completion.choices[0].message.content = "POST /users creates a user."

        client.chat.completions.create.return_value = completion

        provider = GroqLLMProvider(
            api_key="test-api-key",
            model="test-model",
        )

        request = GenerationRequest(
            prompt="Which endpoint creates a user?",
        )

        result = provider.generate(request)

    assert result == GenerationResult(
        content="POST /users creates a user.",
    )

    groq_class.assert_called_once_with(
        api_key="test-api-key",
    )

    client.chat.completions.create.assert_called_once_with(
        model="test-model",
        messages=[
            {
                "role": "user",
                "content": "Which endpoint creates a user?",
            }
        ],
    )


def test_groq_provider_rejects_empty_response() -> None:
    with patch("app.ai.groq_provider.Groq") as groq_class:
        client = MagicMock()
        groq_class.return_value = client

        completion = MagicMock()
        completion.choices[0].message.content = "   "

        client.chat.completions.create.return_value = completion

        provider = GroqLLMProvider(
            api_key="test-api-key",
            model="test-model",
        )

        with pytest.raises(
            ValueError,
            match="Groq returned an empty response.",
        ):
            provider.generate(
                GenerationRequest(
                    prompt="Which endpoint creates a user?",
                )
            )

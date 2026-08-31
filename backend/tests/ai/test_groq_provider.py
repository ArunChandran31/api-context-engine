from unittest.mock import MagicMock, patch

import pytest
from app.ai.exceptions import LLMProviderError
from app.ai.groq_provider import GroqLLMProvider
from app.ai.models import GenerationRequest, GenerationResult
from app.ai.provider import LLMProvider
from groq import (
    APIConnectionError,
    APITimeoutError,
    BadRequestError,
    InternalServerError,
    RateLimitError,
)


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
        timeout=30.0,
        max_retries=0,
    )

    client.chat.completions.create.assert_called_once_with(
        model="test-model",
        messages=[
            {
                "role": "user",
                "content": "Which endpoint creates a user?",
            }
        ],
        max_tokens=None,
        temperature=None,
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


def test_groq_provider_accepts_custom_timeout() -> None:
    with patch("app.ai.groq_provider.Groq") as groq_class:
        GroqLLMProvider(
            api_key="test-api-key",
            model="test-model",
            timeout_seconds=10.0,
        )

    groq_class.assert_called_once_with(
        api_key="test-api-key",
        timeout=10.0,
        max_retries=0,
    )


def test_groq_provider_rejects_non_positive_timeout() -> None:
    with pytest.raises(
        ValueError,
        match="Groq timeout must be greater than zero.",
    ):
        GroqLLMProvider(
            api_key="test-api-key",
            model="test-model",
            timeout_seconds=0,
        )


def _build_request() -> GenerationRequest:
    return GenerationRequest(
        prompt="Which endpoint creates a user?",
    )


def _build_structured_json_request() -> GenerationRequest:
    return GenerationRequest(
        prompt="Generate API test cases.",
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "api_test_cases",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "test_cases": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "category": {
                                        "type": "string",
                                    },
                                    "description": {
                                        "type": "string",
                                    },
                                },
                                "required": [
                                    "category",
                                    "description",
                                ],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["test_cases"],
                    "additionalProperties": False,
                },
            },
        },
    )


def _build_successful_completion() -> MagicMock:
    completion = MagicMock()
    completion.choices[0].message.content = "POST /users creates a user."
    return completion


def test_groq_provider_retries_on_connection_error() -> None:
    with patch("app.ai.groq_provider.Groq") as groq_class:
        client = MagicMock()
        groq_class.return_value = client

        request = MagicMock()

        client.chat.completions.create.side_effect = [
            APIConnectionError(
                request=request,
            ),
            _build_successful_completion(),
        ]

        provider = GroqLLMProvider(
            api_key="test-api-key",
            model="test-model",
            max_retries=1,
            retry_backoff_seconds=1.0,
        )

        with patch("app.ai.groq_provider.sleep") as sleep:
            result = provider.generate(_build_request())

        assert result == GenerationResult(
            content="POST /users creates a user.",
        )

        assert client.chat.completions.create.call_count == 2
        sleep.assert_called_once_with(1.0)


def test_groq_provider_uses_exponential_backoff() -> None:
    with patch("app.ai.groq_provider.Groq") as groq_class:
        client = MagicMock()
        groq_class.return_value = client

        request = MagicMock()

        client.chat.completions.create.side_effect = [
            APIConnectionError(request=request),
            APIConnectionError(request=request),
            _build_successful_completion(),
        ]

        provider = GroqLLMProvider(
            api_key="test-api-key",
            model="test-model",
            max_retries=2,
            retry_backoff_seconds=1.0,
        )

        with patch("app.ai.groq_provider.sleep") as sleep:
            result = provider.generate(_build_request())

        assert result == GenerationResult(
            content="POST /users creates a user.",
        )

        assert client.chat.completions.create.call_count == 3
        assert sleep.call_args_list == [
            ((1.0,),),
            ((2.0,),),
        ]


def test_groq_provider_stops_after_max_retries() -> None:
    with patch("app.ai.groq_provider.Groq") as groq_class:
        client = MagicMock()
        groq_class.return_value = client

        request = MagicMock()
        error = APIConnectionError(request=request)

        client.chat.completions.create.side_effect = error

        provider = GroqLLMProvider(
            api_key="test-api-key",
            model="test-model",
            max_retries=2,
            retry_backoff_seconds=1.0,
        )

        with patch("app.ai.groq_provider.sleep") as sleep, pytest.raises(
            LLMProviderError,
            match="LLM provider is temporarily unavailable.",
        ):
            provider.generate(_build_request())

        assert client.chat.completions.create.call_count == 3
        assert sleep.call_args_list == [
            ((1.0,),),
            ((2.0,),),
        ]


def test_groq_provider_does_not_retry_when_max_retries_is_zero() -> None:
    with patch("app.ai.groq_provider.Groq") as groq_class:
        client = MagicMock()
        groq_class.return_value = client

        request = MagicMock()
        error = APIConnectionError(request=request)

        client.chat.completions.create.side_effect = error

        provider = GroqLLMProvider(
            api_key="test-api-key",
            model="test-model",
            max_retries=0,
        )

        with patch("app.ai.groq_provider.sleep") as sleep, pytest.raises(
            LLMProviderError,
            match="LLM provider is temporarily unavailable.",
        ):
            provider.generate(_build_request())

        assert client.chat.completions.create.call_count == 1
        sleep.assert_not_called()


def test_groq_provider_does_not_retry_non_retryable_errors() -> None:
    with patch("app.ai.groq_provider.Groq") as groq_class:
        client = MagicMock()
        groq_class.return_value = client

        error = ValueError("Invalid request")
        client.chat.completions.create.side_effect = error

        provider = GroqLLMProvider(
            api_key="test-api-key",
            model="test-model",
            max_retries=3,
            retry_backoff_seconds=1.0,
        )

        with patch("app.ai.groq_provider.sleep") as sleep, pytest.raises(
            ValueError, match="Invalid request"
        ):
            provider.generate(_build_request())

        assert client.chat.completions.create.call_count == 1
        sleep.assert_not_called()


def test_groq_provider_retries_on_timeout() -> None:
    with patch("app.ai.groq_provider.Groq") as groq_class:
        client = MagicMock()
        groq_class.return_value = client

        completion = MagicMock()
        completion.choices[0].message.content = "POST /users creates a user."

        client.chat.completions.create.side_effect = [
            APITimeoutError(request=MagicMock()),
            completion,
        ]

        provider = GroqLLMProvider(
            api_key="test-api-key",
            model="test-model",
            max_retries=1,
            retry_backoff_seconds=0.001,
        )

        with patch("app.ai.groq_provider.sleep"):
            result = provider.generate(
                GenerationRequest(
                    prompt="Which endpoint creates a user?",
                )
            )

        assert result == GenerationResult(
            content="POST /users creates a user.",
        )

        assert client.chat.completions.create.call_count == 2


def test_groq_provider_retries_on_rate_limit() -> None:
    with patch("app.ai.groq_provider.Groq") as groq_class:
        client = MagicMock()
        groq_class.return_value = client

        completion = MagicMock()
        completion.choices[0].message.content = "POST /users creates a user."

        rate_limit_error = RateLimitError(
            "Rate limit exceeded",
            response=MagicMock(),
            body=None,
        )

        client.chat.completions.create.side_effect = [
            rate_limit_error,
            completion,
        ]

        provider = GroqLLMProvider(
            api_key="test-api-key",
            model="test-model",
            max_retries=1,
            retry_backoff_seconds=0.001,
        )

        with patch("app.ai.groq_provider.sleep"):
            result = provider.generate(
                GenerationRequest(
                    prompt="Which endpoint creates a user?",
                )
            )

        assert result == GenerationResult(
            content="POST /users creates a user.",
        )

        assert client.chat.completions.create.call_count == 2


def test_groq_provider_retries_on_internal_server_error() -> None:
    with patch("app.ai.groq_provider.Groq") as groq_class:
        client = MagicMock()
        groq_class.return_value = client

        completion = MagicMock()
        completion.choices[0].message.content = "POST /users creates a user."

        internal_server_error = InternalServerError(
            "Internal server error",
            response=MagicMock(),
            body=None,
        )

        client.chat.completions.create.side_effect = [
            internal_server_error,
            completion,
        ]

        provider = GroqLLMProvider(
            api_key="test-api-key",
            model="test-model",
            max_retries=1,
            retry_backoff_seconds=0.001,
        )

        with patch("app.ai.groq_provider.sleep"):
            result = provider.generate(
                GenerationRequest(
                    prompt="Which endpoint creates a user?",
                )
            )

        assert result == GenerationResult(
            content="POST /users creates a user.",
        )

        assert client.chat.completions.create.call_count == 2


def test_groq_provider_retries_on_json_validation_error() -> None:
    with patch("app.ai.groq_provider.Groq") as groq_class:
        client = MagicMock()
        groq_class.return_value = client

        error_response = MagicMock()
        error_response.json.return_value = {
            "error": {
                "code": "json_validate_failed",
                "message": "Failed to validate JSON. Please adjust your prompt.",
            }
        }

        error = BadRequestError(
            "Failed to validate JSON. Please adjust your prompt.",
            response=error_response,
            body={
                "error": {
                    "code": "json_validate_failed",
                }
            },
        )

        client.chat.completions.create.side_effect = [
            error,
            _build_successful_completion(),
        ]

        provider = GroqLLMProvider(
            api_key="test-api-key",
            model="test-model",
            max_retries=1,
            retry_backoff_seconds=1.0,
        )

        with patch("app.ai.groq_provider.sleep") as sleep:
            result = provider.generate(_build_request())

        assert result == GenerationResult(
            content="POST /users creates a user.",
        )

        assert client.chat.completions.create.call_count == 2
        sleep.assert_called_once_with(1.0)


def test_groq_provider_falls_back_to_json_object_on_json_validation_error() -> None:
    with patch("app.ai.groq_provider.Groq") as groq_class:
        client = MagicMock()
        groq_class.return_value = client

        error_response = MagicMock()
        error_response.json.return_value = {
            "error": {
                "code": "json_validate_failed",
                "message": "Failed to validate JSON. Please adjust your prompt.",
            }
        }

        error = BadRequestError(
            "Failed to validate JSON. Please adjust your prompt.",
            response=error_response,
            body={
                "error": {
                    "code": "json_validate_failed",
                }
            },
        )

        client.chat.completions.create.side_effect = [
            error,
            _build_successful_completion(),
        ]

        provider = GroqLLMProvider(
            api_key="test-api-key",
            model="test-model",
            max_retries=1,
            retry_backoff_seconds=1.0,
        )

        with patch("app.ai.groq_provider.sleep") as sleep:
            result = provider.generate(_build_structured_json_request())

        assert result == GenerationResult(
            content="POST /users creates a user.",
        )

        assert client.chat.completions.create.call_count == 2

        first_call = client.chat.completions.create.call_args_list[0]
        second_call = client.chat.completions.create.call_args_list[1]

        assert first_call.kwargs["response_format"]["type"] == "json_schema"
        assert second_call.kwargs["response_format"] == {
            "type": "json_object",
        }

        sleep.assert_called_once_with(1.0)


def test_groq_provider_returns_502_after_json_validation_retries_exhausted() -> None:
    with patch("app.ai.groq_provider.Groq") as groq_class:
        client = MagicMock()
        groq_class.return_value = client

        error_response = MagicMock()
        error_response.json.return_value = {
            "error": {
                "code": "json_validate_failed",
                "message": "Failed to validate JSON. Please adjust your prompt.",
            }
        }

        error = BadRequestError(
            "Failed to validate JSON. Please adjust your prompt.",
            response=error_response,
            body={
                "error": {
                    "code": "json_validate_failed",
                }
            },
        )

        client.chat.completions.create.side_effect = error

        provider = GroqLLMProvider(
            api_key="test-api-key",
            model="test-model",
            max_retries=2,
            retry_backoff_seconds=1.0,
        )

        with patch("app.ai.groq_provider.sleep") as sleep, pytest.raises(
            LLMProviderError,
            match=(
                "LLM provider failed to generate valid structured "
                "JSON after multiple attempts."
            ),
        ) as exc_info:
            provider.generate(_build_structured_json_request())

        assert exc_info.value.status_code == 502

        assert client.chat.completions.create.call_count == 3

        first_call = client.chat.completions.create.call_args_list[0]
        second_call = client.chat.completions.create.call_args_list[1]
        third_call = client.chat.completions.create.call_args_list[2]

        assert first_call.kwargs["response_format"]["type"] == "json_schema"

        assert second_call.kwargs["response_format"] == {
            "type": "json_object",
        }

        assert third_call.kwargs["response_format"] == {
            "type": "json_object",
        }

        assert sleep.call_args_list == [
            ((1.0,),),
            ((2.0,),),
        ]


def test_groq_provider_does_not_retry_unrelated_bad_request() -> None:
    with patch("app.ai.groq_provider.Groq") as groq_class:
        client = MagicMock()
        groq_class.return_value = client

        error_response = MagicMock()
        error_response.json.return_value = {
            "error": {
                "code": "invalid_request_error",
                "message": "Invalid request.",
            }
        }

        error = BadRequestError(
            "Invalid request.",
            response=error_response,
            body={
                "error": {
                    "code": "invalid_request_error",
                }
            },
        )

        client.chat.completions.create.side_effect = error

        provider = GroqLLMProvider(
            api_key="test-api-key",
            model="test-model",
            max_retries=3,
            retry_backoff_seconds=1.0,
        )

        with patch("app.ai.groq_provider.sleep") as sleep, pytest.raises(
            LLMProviderError,
            match="LLM provider rejected the generation request.",
        ) as exc_info:
            provider.generate(_build_request())

        assert exc_info.value.status_code == 400

        assert client.chat.completions.create.call_count == 1
        sleep.assert_not_called()

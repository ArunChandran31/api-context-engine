import logging
from time import sleep
from typing import cast

from groq import (
    APIConnectionError,
    APITimeoutError,
    BadRequestError,
    Groq,
    InternalServerError,
    RateLimitError,
)
from groq.types.chat import ChatCompletionMessageParam
from groq.types.chat.completion_create_params import ResponseFormat

from app.ai.exceptions import LLMProviderError
from app.ai.models import GenerationRequest, GenerationResult
from app.ai.provider import LLMProvider

logger = logging.getLogger(__name__)


class GroqLLMProvider(LLMProvider):
    """
    Groq-backed implementation of the LLM provider contract.

    Converts provider-independent generation requests into Groq
    chat-completion requests and returns provider-independent results.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
        retry_backoff_seconds: float = 1.0,
    ) -> None:
        if not api_key.strip():
            raise ValueError("Groq API key cannot be empty.")

        if not model.strip():
            raise ValueError("Groq model cannot be empty.")

        if timeout_seconds <= 0:
            raise ValueError("Groq timeout must be greater than zero.")

        if max_retries < 0:
            raise ValueError("Groq max retries cannot be negative.")

        if retry_backoff_seconds <= 0:
            raise ValueError("Groq retry backoff must be greater than zero.")

        self._model = model
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds

        self._client = Groq(
            api_key=api_key,
            timeout=timeout_seconds,
            max_retries=0,
        )

    def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        messages: list[ChatCompletionMessageParam] = [
            {
                "role": "user",
                "content": request.prompt,
            }
        ]

        response_format = (
            cast(ResponseFormat, request.response_format)
            if request.response_format is not None
            else None
        )

        # Keep the original requested format for the first attempt.
        current_response_format = response_format
        json_schema_fallback_used = False

        for attempt in range(self._max_retries + 1):
            try:
                if current_response_format is None:
                    completion = self._client.chat.completions.create(
                        model=self._model,
                        messages=messages,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                    )
                else:
                    completion = self._client.chat.completions.create(
                        model=self._model,
                        messages=messages,
                        response_format=current_response_format,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature,
                    )

                content = completion.choices[0].message.content

                if content is None or not content.strip():
                    raise ValueError("Groq returned an empty response.")

                return GenerationResult(
                    content=content,
                )

            except APITimeoutError as exc:
                if attempt >= self._max_retries:
                    raise LLMProviderError(
                        "LLM provider request timed out.",
                        status_code=504,
                    ) from exc

                self._sleep_before_retry(attempt)

            except RateLimitError as exc:
                if attempt >= self._max_retries:
                    raise LLMProviderError(
                        "LLM provider rate limit exceeded.",
                        status_code=429,
                    ) from exc

                self._sleep_before_retry(attempt)

            except (APIConnectionError, InternalServerError) as exc:
                if attempt >= self._max_retries:
                    raise LLMProviderError(
                        "LLM provider is temporarily unavailable.",
                        status_code=503,
                    ) from exc

                self._sleep_before_retry(attempt)

            except BadRequestError as exc:
                logger.error(
                    "Groq BadRequestError: %s",
                    self._extract_error_payload(exc),
                )

                if self._is_json_validation_error(exc):
                    if attempt >= self._max_retries:
                        raise LLMProviderError(
                            (
                                "LLM provider failed to generate valid structured "
                                "JSON after multiple attempts."
                            ),
                            status_code=502,
                        ) from exc

                    # Groq can reject a strict JSON schema even when the model
                    # can produce valid JSON. On the first validation failure,
                    # retry once using the simpler JSON-object format.
                    if (
                        response_format is not None
                        and response_format.get("type") == "json_schema"
                        and not json_schema_fallback_used
                    ):
                        current_response_format = cast(
                            ResponseFormat,
                            {
                                "type": "json_object",
                            },
                        )
                        json_schema_fallback_used = True

                    self._sleep_before_retry(attempt)
                    continue

                raise LLMProviderError(
                    "LLM provider rejected the generation request.",
                    status_code=400,
                ) from exc

        raise RuntimeError("Groq generation failed unexpectedly.")

    def _sleep_before_retry(
        self,
        attempt: int,
    ) -> None:
        delay = self._retry_backoff_seconds * (2**attempt)
        sleep(delay)

    @staticmethod
    def _is_json_validation_error(
        exc: BadRequestError,
    ) -> bool:
        """
        Return True when Groq rejected the generated output because
        it failed structured JSON validation.
        """

        response = getattr(exc, "response", None)

        if response is None:
            return False

        try:
            payload = response.json()
        except (AttributeError, TypeError, ValueError):
            return False

        if not isinstance(payload, dict):
            return False

        error = payload.get("error")

        if not isinstance(error, dict):
            return False

        return error.get("code") == "json_validate_failed"

    @staticmethod
    def _extract_error_payload(
        exc: BadRequestError,
    ) -> object:
        """
        Extract the provider error payload for diagnostic logging.
        """

        response = getattr(exc, "response", None)

        if response is None:
            return str(exc)

        try:
            return response.json()
        except (AttributeError, TypeError, ValueError):
            return str(exc)

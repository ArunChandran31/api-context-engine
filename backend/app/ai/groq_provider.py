from time import sleep
from typing import cast

from groq import (
    APIConnectionError,
    APITimeoutError,
    Groq,
    InternalServerError,
    RateLimitError,
)
from groq.types.chat import ChatCompletionMessageParam
from groq.types.chat.completion_create_params import ResponseFormat

from app.ai.exceptions import LLMProviderError
from app.ai.models import GenerationRequest, GenerationResult
from app.ai.provider import LLMProvider


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

        for attempt in range(self._max_retries + 1):
            try:
                if response_format is None:
                    completion = self._client.chat.completions.create(
                        model=self._model,
                        messages=messages,
                    )
                else:
                    completion = self._client.chat.completions.create(
                        model=self._model,
                        messages=messages,
                        response_format=response_format,
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

                delay = self._retry_backoff_seconds * (2**attempt)
                sleep(delay)

            except RateLimitError as exc:
                if attempt >= self._max_retries:
                    raise LLMProviderError(
                        "LLM provider rate limit exceeded.",
                        status_code=429,
                    ) from exc

                delay = self._retry_backoff_seconds * (2**attempt)
                sleep(delay)

            except (APIConnectionError, InternalServerError) as exc:
                if attempt >= self._max_retries:
                    raise LLMProviderError(
                        "LLM provider is temporarily unavailable.",
                        status_code=503,
                    ) from exc

                delay = self._retry_backoff_seconds * (2**attempt)
                sleep(delay)

        raise RuntimeError("Groq generation failed unexpectedly.")

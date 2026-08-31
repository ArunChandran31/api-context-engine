from typing import Any

import httpx
from google import genai
from google.genai import types

from app.ai.exceptions import LLMProviderError
from app.ai.models import GenerationRequest, GenerationResult
from app.ai.provider import LLMProvider


class GeminiLLMProvider(LLMProvider):
    """
    Google Gemini implementation of the provider-independent LLM interface.

    This provider translates the application's GenerationRequest into a
    Google GenAI request and returns a provider-independent GenerationResult.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not api_key.strip():
            raise ValueError("Gemini API key cannot be empty.")

        if not model.strip():
            raise ValueError("Gemini model cannot be empty.")

        if timeout_seconds <= 0:
            raise ValueError("Gemini timeout must be greater than zero.")

        self._model = model
        self._timeout_seconds = timeout_seconds
        self._http_client: httpx.Client | None = None

        try:
            # Use an explicit HTTPX client rather than allowing the Google
            # GenAI SDK to construct its own internal HTTP client.
            #
            # This is important for environments such as WSL where the
            # SDK-created transport can fail with:
            # [Errno 101] Network is unreachable
            #
            # A direct httpx.Client has been verified to successfully reach
            # the Gemini API from the current runtime environment.
            self._http_client = httpx.Client(
                timeout=timeout_seconds,
            )

            self._client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(
                    timeout=int(timeout_seconds * 1000),
                    httpx_client=self._http_client,
                ),
            )

        except Exception as exc:
            if self._http_client is not None:
                self._http_client.close()
                self._http_client = None

            raise LLMProviderError(
                message=f"Failed to initialize Gemini client: {exc}",
                status_code=503,
            ) from exc

    def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        """
        Generate content using Google Gemini.
        """

        config_kwargs: dict[str, Any] = {}

        response_format = request.response_format

        if response_format is not None:
            response_type = response_format.get("type")

            if response_type == "json_object":
                config_kwargs["response_mime_type"] = "application/json"

            elif response_type == "json_schema":
                config_kwargs["response_mime_type"] = "application/json"

                json_schema = response_format.get("json_schema")

                if isinstance(json_schema, dict):
                    schema = json_schema.get("schema")

                    if isinstance(schema, dict):
                        config_kwargs["response_schema"] = (
                            self._convert_json_schema_for_gemini(schema)
                        )

            else:
                raise ValueError(f"Unsupported Gemini response format: {response_type}")

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=request.prompt,
                config=types.GenerateContentConfig(
                    **config_kwargs,
                ),
            )

        except Exception as exc:
            raise self._translate_exception(exc) from exc

        content = response.text

        if content is None or not content.strip():
            raise LLMProviderError(
                message="Gemini returned an empty response.",
                status_code=502,
            )

        return GenerationResult(
            content=content,
        )

    def close(self) -> None:
        """
        Close the explicitly managed HTTPX client.
        """
        if self._http_client is not None:
            self._http_client.close()
            self._http_client = None

    @classmethod
    def _convert_json_schema_for_gemini(
        cls,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Convert the application's JSON Schema into the subset supported by
        the Google Gemini response_schema format.

        The application uses JSON Schema conventions such as
        `additional_properties`, while Gemini's schema representation
        does not accept that field.

        This conversion is intentionally recursive so nested objects and
        arrays are handled correctly.
        """

        converted: dict[str, Any] = {}

        for key, value in schema.items():
            if key == "additional_properties":
                continue

            if key == "additionalProperties":
                continue

            if key == "properties":
                if isinstance(value, dict):
                    converted["properties"] = {
                        property_name: cls._convert_json_schema_for_gemini(
                            property_schema
                        )
                        for property_name, property_schema in value.items()
                        if isinstance(property_schema, dict)
                    }
                continue

            if key == "items":
                if isinstance(value, dict):
                    converted["items"] = cls._convert_json_schema_for_gemini(value)
                elif isinstance(value, list):
                    converted["items"] = [
                        (
                            cls._convert_json_schema_for_gemini(item)
                            if isinstance(item, dict)
                            else item
                        )
                        for item in value
                    ]
                continue

            if key == "anyOf":
                if isinstance(value, list):
                    converted["anyOf"] = [
                        (
                            cls._convert_json_schema_for_gemini(item)
                            if isinstance(item, dict)
                            else item
                        )
                        for item in value
                    ]
                continue

            if key == "oneOf":
                if isinstance(value, list):
                    converted["oneOf"] = [
                        (
                            cls._convert_json_schema_for_gemini(item)
                            if isinstance(item, dict)
                            else item
                        )
                        for item in value
                    ]
                continue

            if key == "allOf":
                if isinstance(value, list):
                    converted["allOf"] = [
                        (
                            cls._convert_json_schema_for_gemini(item)
                            if isinstance(item, dict)
                            else item
                        )
                        for item in value
                    ]
                continue

            converted[key] = value

        return converted

    @staticmethod
    def _translate_exception(
        exc: Exception,
    ) -> LLMProviderError:
        """
        Translate Google GenAI exceptions into the application's
        provider-independent error type.
        """

        message = str(exc)
        normalized_message = message.lower()

        if (
            "429" in normalized_message
            or "resource exhausted" in normalized_message
            or "rate limit" in normalized_message
            or "quota" in normalized_message
        ):
            return LLMProviderError(
                message="Gemini rate limit exceeded.",
                status_code=429,
            )

        if (
            "timeout" in normalized_message
            or "timed out" in normalized_message
            or "deadline_exceeded" in normalized_message
            or "deadline expired" in normalized_message
        ):
            return LLMProviderError(
                message="Gemini request timed out.",
                status_code=504,
            )

        if (
            "401" in normalized_message
            or "403" in normalized_message
            or "api key" in normalized_message
            or "permission denied" in normalized_message
        ):
            return LLMProviderError(
                message="Gemini authentication or authorization failed.",
                status_code=401,
            )

        if (
            "400" in normalized_message
            or "invalid argument" in normalized_message
            or "invalid request" in normalized_message
        ):
            return LLMProviderError(
                message=f"Gemini rejected the request: {message}",
                status_code=400,
            )

        if "404" in normalized_message:
            return LLMProviderError(
                message=f"Gemini model or endpoint not found: {message}",
                status_code=404,
            )

        return LLMProviderError(
            message=f"Gemini provider request failed: {message}",
            status_code=502,
        )

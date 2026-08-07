from groq import Groq

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
    ) -> None:
        if not api_key.strip():
            raise ValueError("Groq API key cannot be empty.")

        if not model.strip():
            raise ValueError("Groq model cannot be empty.")

        self._model = model
        self._client = Groq(api_key=api_key)

    def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResult:
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "user",
                    "content": request.prompt,
                }
            ],
        )

        content = completion.choices[0].message.content

        if content is None or not content.strip():
            raise ValueError("Groq returned an empty response.")

        return GenerationResult(
            content=content,
        )

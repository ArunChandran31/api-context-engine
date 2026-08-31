from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GenerationRequest:
    """
    Provider-independent request for text generation.

    The AI layer uses this model so higher-level services do not depend
    directly on a specific LLM provider or SDK.
    """

    prompt: str
    response_format: dict[str, Any] | None = None
    max_tokens: int | None = None
    temperature: float | None = None

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("Generation prompt cannot be empty.")

        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("Max tokens must be greater than zero.")

        if self.temperature is not None and self.temperature < 0:
            raise ValueError("Temperature cannot be negative.")


@dataclass(frozen=True)
class GenerationResult:
    """
    Provider-independent result returned by a text-generation provider.
    """

    content: str

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError("Generated content cannot be empty.")

class LLMProviderError(Exception):
    """Base exception for expected LLM provider failures."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 503,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code

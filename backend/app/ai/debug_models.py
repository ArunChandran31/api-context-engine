from dataclasses import dataclass


@dataclass(frozen=True)
class DebugRequest:
    """
    Provider-independent debugging request.
    """

    prompt: str

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("Debug prompt cannot be empty.")


@dataclass(frozen=True)
class DebugResult:
    """
    Provider-independent debugging result.
    """

    explanation: str

    def __post_init__(self) -> None:
        if not self.explanation.strip():
            raise ValueError("Debug explanation cannot be empty.")

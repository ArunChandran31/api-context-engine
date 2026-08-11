from dataclasses import dataclass


@dataclass(frozen=True)
class TestCaseGenerationRequest:
    __test__ = False
    prompt: str

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("Test case generation prompt cannot be empty.")


@dataclass(frozen=True)
class GeneratedTestCase:
    category: str
    description: str

    def __post_init__(self) -> None:
        if not self.category.strip():
            raise ValueError("Test case category cannot be empty.")

        if not self.description.strip():
            raise ValueError("Test case description cannot be empty.")


@dataclass(frozen=True)
class TestCaseGenerationResult:
    __test__ = False
    test_cases: list[GeneratedTestCase]

    def __post_init__(self) -> None:
        if not self.test_cases:
            raise ValueError("Generated test cases cannot be empty.")

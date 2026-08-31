from dataclasses import dataclass, field
from typing import Literal

TestStyle = Literal[
    "jest",
    "pytest",
    "postman",
    "curl",
]


TestCategory = Literal[
    "happy",
    "validation",
    "edge",
    "auth",
    "errors",
]


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
class SkippedTestCategory:
    category: TestCategory
    reason: str

    def __post_init__(self) -> None:
        if not self.category.strip():
            raise ValueError("Skipped test category cannot be empty.")

        if not self.reason.strip():
            raise ValueError("Skipped test category reason cannot be empty.")


@dataclass(frozen=True)
class TestCaseGenerationResult:
    __test__ = False

    test_cases: list[GeneratedTestCase]
    skipped_categories: list[SkippedTestCategory] = field(
        default_factory=list,
    )

    def __post_init__(self) -> None:
        if not self.test_cases:
            raise ValueError("Generated test cases cannot be empty.")

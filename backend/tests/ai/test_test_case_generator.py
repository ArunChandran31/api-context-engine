import pytest

from app.ai.test_case_generator import TestCaseGenerator
from app.ai.test_case_models import (
    GeneratedTestCase,
    TestCaseGenerationRequest,
    TestCaseGenerationResult,
)


def test_generator_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        TestCaseGenerator()  # pyright: ignore[reportAbstractUsage]


def test_concrete_generator_implements_generate() -> None:
    class ConcreteTestCaseGenerator(TestCaseGenerator):
        def generate(
            self,
            request: TestCaseGenerationRequest,
        ) -> TestCaseGenerationResult:
            return TestCaseGenerationResult(
                test_cases=[
                    GeneratedTestCase(
                        category="Positive",
                        description=(f"Generated test for: {request.prompt}"),
                    )
                ]
            )

    generator = ConcreteTestCaseGenerator()

    request = TestCaseGenerationRequest(
        prompt="Generate test cases for POST /users.",
    )

    result = generator.generate(request)

    assert result == TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="Positive",
                description=(
                    "Generated test for: " "Generate test cases for POST /users."
                ),
            )
        ]
    )

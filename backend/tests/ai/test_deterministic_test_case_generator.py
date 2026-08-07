import pytest

from app.ai.deterministic_test_case_generator import (
    DeterministicTestCaseGenerator,
)
from app.ai.test_case_generator import TestCaseGenerator
from app.ai.test_case_models import (
    GeneratedTestCase,
    TestCaseGenerationRequest,
    TestCaseGenerationResult,
)


def test_generator_implements_interface() -> None:
    generator = DeterministicTestCaseGenerator(
        result=TestCaseGenerationResult(
            test_cases=[
                GeneratedTestCase(
                    category="Positive",
                    description="Create a valid user.",
                )
            ]
        )
    )

    assert isinstance(generator, TestCaseGenerator)


def test_generator_returns_configured_result() -> None:
    expected = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="Positive",
                description="Create a valid user.",
            )
        ]
    )

    generator = DeterministicTestCaseGenerator(
        result=expected,
    )

    request = TestCaseGenerationRequest(
        prompt="Generate tests",
    )

    result = generator.generate(request)

    assert result == expected


def test_generator_returns_same_result_for_different_requests() -> None:
    expected = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="Negative",
                description="Missing email",
            )
        ]
    )

    generator = DeterministicTestCaseGenerator(
        result=expected,
    )

    first = generator.generate(
        TestCaseGenerationRequest(
            prompt="Prompt 1",
        )
    )

    second = generator.generate(
        TestCaseGenerationRequest(
            prompt="Prompt 2",
        )
    )

    assert first == second


def test_generator_rejects_empty_collection() -> None:
    with pytest.raises(
        ValueError,
        match="Generated test cases cannot be empty.",
    ):
        DeterministicTestCaseGenerator(
            result=TestCaseGenerationResult(
                test_cases=[],
            )
        )

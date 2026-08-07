import pytest

from app.ai.test_case_models import (
    GeneratedTestCase,
    TestCaseGenerationRequest,
    TestCaseGenerationResult,
)


def test_request_creation() -> None:
    request = TestCaseGenerationRequest(
        prompt="Generate test cases for POST /users.",
    )

    assert request.prompt == "Generate test cases for POST /users."


def test_request_rejects_empty_prompt() -> None:
    with pytest.raises(
        ValueError,
        match="Test case generation prompt cannot be empty.",
    ):
        TestCaseGenerationRequest(
            prompt="   ",
        )


def test_generated_test_case_creation() -> None:
    test_case = GeneratedTestCase(
        category="Positive",
        description="Create a user with valid data.",
    )

    assert test_case.category == "Positive"
    assert test_case.description == "Create a user with valid data."


def test_generated_test_case_rejects_empty_category() -> None:
    with pytest.raises(
        ValueError,
        match="Test case category cannot be empty.",
    ):
        GeneratedTestCase(
            category="",
            description="Example",
        )


def test_generated_test_case_rejects_empty_description() -> None:
    with pytest.raises(
        ValueError,
        match="Test case description cannot be empty.",
    ):
        GeneratedTestCase(
            category="Positive",
            description="   ",
        )


def test_generation_result_creation() -> None:
    result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="Positive",
                description="Create user.",
            )
        ],
    )

    assert len(result.test_cases) == 1


def test_generation_result_rejects_empty_collection() -> None:
    with pytest.raises(
        ValueError,
        match="Generated test cases cannot be empty.",
    ):
        TestCaseGenerationResult(
            test_cases=[],
        )

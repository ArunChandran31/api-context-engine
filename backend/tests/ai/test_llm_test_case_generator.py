from app.ai.llm_test_case_generator import LLMTestCaseGenerator
from app.ai.models import GenerationRequest, GenerationResult
from app.ai.provider import LLMProvider
from app.ai.test_case_models import TestCaseGenerationRequest


class FakeLLMProvider(LLMProvider):
    def __init__(self, response: str) -> None:
        self.response = response
        self.last_prompt: str | None = None
        self.last_request: GenerationRequest | None = None

    def generate(self, request: GenerationRequest) -> GenerationResult:
        self.last_prompt = request.prompt
        self.last_request = request
        return GenerationResult(content=self.response)


def test_generates_test_cases_from_valid_llm_response() -> None:
    provider = FakeLLMProvider(
        response=(
            '{"test_cases": ['
            '{"category": "Positive", '
            '"description": "Create a pet with valid data."},'
            '{"category": "Negative", '
            '"description": "Reject a pet with missing required fields."}'
            "]}"
        )
    )

    generator = LLMTestCaseGenerator(provider)

    result = generator.generate(
        TestCaseGenerationRequest(
            prompt="Generate test cases for POST /pets.",
        )
    )

    assert len(result.test_cases) == 2
    assert result.test_cases[0].category == "Positive"
    assert result.test_cases[0].description == "Create a pet with valid data."
    assert result.test_cases[1].category == "Negative"
    assert (
        result.test_cases[1].description == "Reject a pet with missing required fields."
    )


def test_passes_prompt_to_llm_provider() -> None:
    provider = FakeLLMProvider(
        response=(
            '{"test_cases": ['
            '{"category": "Positive", '
            '"description": "Create a pet."}'
            "]}"
        )
    )

    generator = LLMTestCaseGenerator(provider)

    generator.generate(
        TestCaseGenerationRequest(
            prompt="Generate tests for POST /pets.",
        )
    )

    assert provider.last_prompt == "Generate tests for POST /pets."


def test_requests_structured_json_response_format() -> None:
    provider = FakeLLMProvider(
        response=(
            '{"test_cases": ['
            '{"category": "Positive", '
            '"description": "Create a pet."}'
            "]}"
        )
    )

    generator = LLMTestCaseGenerator(provider)

    generator.generate(
        TestCaseGenerationRequest(
            prompt="Generate tests for POST /pets.",
        )
    )

    assert provider.last_request is not None
    assert provider.last_request.response_format is not None
    assert provider.last_request.response_format["type"] == "json_schema"

    response_format = provider.last_request.response_format

    assert response_format["type"] == "json_schema"

    json_schema = response_format["json_schema"]

    assert json_schema["name"] == "api_test_cases"
    assert json_schema["strict"] is True

    schema = json_schema["schema"]

    assert schema["type"] == "object"
    assert schema["required"] == ["test_cases"]
    assert schema["additionalProperties"] is False

    test_cases_schema = schema["properties"]["test_cases"]

    assert test_cases_schema["type"] == "array"

    item_schema = test_cases_schema["items"]

    assert item_schema["type"] == "object"
    assert item_schema["required"] == [
        "category",
        "description",
    ]
    assert item_schema["additionalProperties"] is False


def test_rejects_empty_prompt() -> None:
    provider = FakeLLMProvider(
        response=(
            '{"test_cases": ['
            '{"category": "Positive", '
            '"description": "Create a pet."}'
            "]}"
        )
    )

    generator = LLMTestCaseGenerator(provider)

    try:
        generator.generate(
            TestCaseGenerationRequest(
                prompt="   ",
            )
        )
    except ValueError as exc:
        assert str(exc) == "Test case generation prompt cannot be empty."
    else:
        raise AssertionError("Expected ValueError")


def test_rejects_invalid_json() -> None:
    provider = FakeLLMProvider(
        response="not valid json",
    )

    generator = LLMTestCaseGenerator(provider)

    try:
        generator.generate(
            TestCaseGenerationRequest(
                prompt="Generate tests for POST /pets.",
            )
        )
    except ValueError as exc:
        assert str(exc) == "LLM returned invalid JSON for test case generation."
    else:
        raise AssertionError("Expected ValueError")


def test_rejects_empty_test_cases() -> None:
    provider = FakeLLMProvider(
        response='{"test_cases": []}',
    )

    generator = LLMTestCaseGenerator(provider)

    try:
        generator.generate(
            TestCaseGenerationRequest(
                prompt="Generate tests for POST /pets.",
            )
        )
    except ValueError as exc:
        assert (
            str(exc)
            == "LLM test case response must contain a non-empty 'test_cases' list."
        )
    else:
        raise AssertionError("Expected ValueError")


def test_rejects_non_object_llm_response() -> None:
    provider = FakeLLMProvider(
        response='["invalid"]',
    )

    generator = LLMTestCaseGenerator(provider)

    try:
        generator.generate(
            TestCaseGenerationRequest(
                prompt="Generate tests for POST /pets.",
            )
        )
    except TypeError as exc:
        assert str(exc) == "LLM test case response must be a JSON object."
    else:
        raise AssertionError("Expected TypeError")


def test_rejects_non_list_test_cases() -> None:
    provider = FakeLLMProvider(
        response='{"test_cases": {}}',
    )

    generator = LLMTestCaseGenerator(provider)

    try:
        generator.generate(
            TestCaseGenerationRequest(
                prompt="Generate tests for POST /pets.",
            )
        )
    except ValueError as exc:
        assert (
            str(exc)
            == "LLM test case response must contain a non-empty 'test_cases' list."
        )
    else:
        raise AssertionError("Expected ValueError")


def test_rejects_non_object_test_case() -> None:
    provider = FakeLLMProvider(
        response='{"test_cases": ["invalid"]}',
    )

    generator = LLMTestCaseGenerator(provider)

    try:
        generator.generate(
            TestCaseGenerationRequest(
                prompt="Generate tests for POST /pets.",
            )
        )
    except TypeError as exc:
        assert str(exc) == "Each generated test case must be a JSON object."
    else:
        raise AssertionError("Expected TypeError")


def test_rejects_invalid_test_case_field_types() -> None:
    provider = FakeLLMProvider(
        response=(
            '{"test_cases": ['
            '{"category": 123, '
            '"description": "Create a pet."}'
            "]}"
        )
    )

    generator = LLMTestCaseGenerator(provider)

    try:
        generator.generate(
            TestCaseGenerationRequest(
                prompt="Generate tests for POST /pets.",
            )
        )
    except TypeError as exc:
        assert str(exc) == "Generated test case category must be a string."
    else:
        raise AssertionError("Expected TypeError")

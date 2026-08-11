import json

from app.ai.models import GenerationRequest
from app.ai.provider import LLMProvider
from app.ai.test_case_generator import TestCaseGenerator
from app.ai.test_case_models import (
    GeneratedTestCase,
    TestCaseGenerationRequest,
    TestCaseGenerationResult,
)


class LLMTestCaseGenerator(TestCaseGenerator):
    """
    Generates structured API test cases using an LLM provider.
    """

    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm_provider = llm_provider

    def generate(
        self,
        request: TestCaseGenerationRequest,
    ) -> TestCaseGenerationResult:
        if not request.prompt.strip():
            raise ValueError("Test case generation prompt cannot be empty.")

        generation_request = GenerationRequest(
            prompt=request.prompt,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "api_test_cases",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "test_cases": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "category": {
                                            "type": "string",
                                        },
                                        "description": {
                                            "type": "string",
                                        },
                                    },
                                    "required": [
                                        "category",
                                        "description",
                                    ],
                                    "additionalProperties": False,
                                },
                            },
                        },
                        "required": ["test_cases"],
                        "additionalProperties": False,
                    },
                },
            },
        )

        result = self._llm_provider.generate(generation_request)

        return self._parse_result(result.content)

    def _parse_result(self, content: str) -> TestCaseGenerationResult:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "LLM returned invalid JSON for test case generation."
            ) from exc

        if not isinstance(payload, dict):
            raise TypeError("LLM test case response must be a JSON object.")

        raw_test_cases = payload.get("test_cases")

        if not isinstance(raw_test_cases, list) or not raw_test_cases:
            raise ValueError(
                "LLM test case response must contain a non-empty 'test_cases' list."
            )

        test_cases: list[GeneratedTestCase] = []

        for item in raw_test_cases:
            if not isinstance(item, dict):
                raise TypeError("Each generated test case must be a JSON object.")

            category = item.get("category")
            description = item.get("description")

            if not isinstance(category, str):
                raise TypeError("Generated test case category must be a string.")

            if not isinstance(description, str):
                raise TypeError("Generated test case description must be a string.")

            test_cases.append(
                GeneratedTestCase(
                    category=category,
                    description=description,
                )
            )

        return TestCaseGenerationResult(
            test_cases=test_cases,
        )

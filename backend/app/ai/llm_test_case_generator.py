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
                        "required": [
                            "test_cases",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
        )

        result = self._llm_provider.generate(generation_request)

        print("\n===== RAW LLM TEST CASE RESPONSE =====")
        print(result.content)
        print("===== END RAW LLM TEST CASE RESPONSE =====\n")

        return self._parse_result(result.content)

    def _parse_result(
        self,
        content: str,
    ) -> TestCaseGenerationResult:
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
                "LLM test case response must contain a non-empty " "'test_cases' list."
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

            normalized_description = self._normalize_description(
                description,
            )

            test_cases.append(
                GeneratedTestCase(
                    category=category,
                    description=normalized_description,
                )
            )

        return TestCaseGenerationResult(
            test_cases=test_cases,
        )

    @staticmethod
    def _normalize_description(
        description: str,
    ) -> str:
        """
        Normalize line-break escape sequences that an LLM may return
        literally inside the JSON string.

        Valid JSON decoding normally converts escaped newlines into
        actual newline characters. Some providers can nevertheless
        return double-escaped sequences such as '\\n'. Those sequences
        are converted here so downstream AST validation receives real
        source code.
        """

        normalized = description.replace("\\r\\n", "\n")
        normalized = normalized.replace("\\n", "\n")
        normalized = normalized.replace("\\r", "\n")

        return normalized

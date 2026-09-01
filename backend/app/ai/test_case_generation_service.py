import re
from typing import ClassVar

from app.ai.test_case_artifact_validator import TestCaseArtifactValidator
from app.ai.test_case_generator import TestCaseGenerator
from app.ai.test_case_models import (
    SkippedTestCategory,
    TestCaseGenerationRequest,
    TestCaseGenerationResult,
    TestCategory,
    TestStyle,
)
from app.ai.test_case_prompt_builder import TestCasePromptBuilder
from app.ai.test_case_validator import TestCaseGroundingValidator
from app.ai.test_plan_builder import TestPlanBuilder
from app.ai.test_plan_models import TestPlan, TestPlanCategory
from app.rag.retrieval_service import RAGRetrievalService


class TestCaseGenerationService:
    __test__ = False

    """
    Coordinates retrieval-grounded AI test case generation.

    Retrieves relevant API context, builds a grounded test plan,
    determines which requested categories are actually supported by
    the API documentation, builds the final generation prompt using
    only supported categories, delegates generation to the configured
    test case generator, and validates the generated result.

    Unsupported requested categories are returned explicitly as
    skipped_categories rather than being sent to the LLM.

    If grounding, artifact, or category-coverage validation fails,
    the service performs one bounded regeneration attempt using the
    validation error as correction feedback.
    """

    MAX_GENERATION_ATTEMPTS = 2

    _CANONICAL_CATEGORIES: tuple[TestCategory, ...] = (
        "happy",
        "validation",
        "edge",
        "auth",
        "errors",
    )

    _CATEGORY_ALIASES: ClassVar[dict[TestCategory, set[str]]] = {
        "happy": {
            "happy",
            "happy path",
            "positive",
            "positive happy path",
            "positive / happy path",
        },
        "validation": {
            "validation",
            "negative",
            "negative validation",
            "negative / validation",
        },
        "edge": {
            "edge",
            "edge case",
        },
        "auth": {
            "auth",
            "authentication",
            "authorization",
            "authentication authorization",
            "authentication / authorization",
        },
        "errors": {
            "error",
            "errors",
            "http error",
            "http errors",
            "documented http error",
            "documented http errors",
        },
    }

    def __init__(
        self,
        retrieval_service: RAGRetrievalService,
        prompt_builder: TestCasePromptBuilder,
        generator: TestCaseGenerator,
        validator: TestCaseGroundingValidator | None = None,
        artifact_validator: TestCaseArtifactValidator | None = None,
        test_plan_builder: TestPlanBuilder | None = None,
        retrieval_limit: int = 5,
    ) -> None:
        if retrieval_limit <= 0:
            raise ValueError(
                "Retrieval limit must be positive.",
            )

        self._retrieval_service = retrieval_service
        self._prompt_builder = prompt_builder
        self._generator = generator
        self._validator = validator or TestCaseGroundingValidator()
        self._artifact_validator = artifact_validator or TestCaseArtifactValidator()
        self._test_plan_builder = test_plan_builder or TestPlanBuilder()
        self._retrieval_limit = retrieval_limit

    def generate(
        self,
        endpoint: str,
        specification_id: int,
        test_style: TestStyle = "jest",
        categories: list[TestCategory] | None = None,
    ) -> TestCaseGenerationResult:
        if not endpoint.strip():
            raise ValueError(
                "Endpoint cannot be empty.",
            )

        if specification_id <= 0:
            raise ValueError(
                "Specification ID must be greater than zero.",
            )

        contexts = self._retrieval_service.retrieve(
            query=endpoint,
            limit=self._retrieval_limit,
            specification_id=specification_id,
        )

        plan_categories = self._map_categories_to_plan_categories(
            categories,
        )

        test_plan = self._test_plan_builder.build(
            endpoint=endpoint,
            contexts=contexts,
            categories=plan_categories,
        )

        supported_categories = self._build_supported_categories(
            categories=categories,
            test_plan=test_plan,
        )

        skipped_categories = self._build_skipped_categories(
            categories=categories,
            supported_categories=supported_categories,
        )

        request = self._prompt_builder.build(
            endpoint=endpoint,
            contexts=contexts,
            test_style=test_style,
            categories=supported_categories,
            test_plan=test_plan,
        )

        # No retrieved context means there is nothing to validate
        # the generated result against.
        if not contexts:
            result = self._generator.generate(request)

            validated_result = self._artifact_validator.validate(
                result=result,
                test_style=test_style,
            )

            return self._attach_skipped_categories(
                result=validated_result,
                skipped_categories=skipped_categories,
            )

        context_text = "\n\n".join(
            context.content.strip() for context in contexts if context.content.strip()
        )

        # Protect against RetrievalResult objects containing only
        # whitespace/empty content.
        if not context_text:
            result = self._generator.generate(request)

            validated_result = self._artifact_validator.validate(
                result=result,
                test_style=test_style,
            )

            return self._attach_skipped_categories(
                result=validated_result,
                skipped_categories=skipped_categories,
            )

        current_request = request
        last_validation_error: ValueError | None = None

        for attempt in range(self.MAX_GENERATION_ATTEMPTS):
            result = self._generator.generate(current_request)

            try:
                validated_result = self._validator.validate(
                    result=result,
                    context=context_text,
                )

                validated_result = self._artifact_validator.validate(
                    result=validated_result,
                    test_style=test_style,
                )

                self._validate_category_coverage(
                    result=validated_result,
                    required_categories=supported_categories,
                )

                return self._attach_skipped_categories(
                    result=validated_result,
                    skipped_categories=skipped_categories,
                )

            except ValueError as exc:
                last_validation_error = exc

                # No more attempts remain.
                if attempt >= self.MAX_GENERATION_ATTEMPTS - 1:
                    raise

                current_request = self._build_regeneration_request(
                    original_request=request,
                    validation_error=exc,
                )

        # Defensive guard. The loop should always either return a
        # validated result or raise the final validation error.
        if last_validation_error is not None:
            raise last_validation_error

        raise RuntimeError(
            "Test case generation failed unexpectedly.",
        )

    @staticmethod
    def _attach_skipped_categories(
        result: TestCaseGenerationResult,
        skipped_categories: list[SkippedTestCategory],
    ) -> TestCaseGenerationResult:
        """
        Attach categories that were intentionally excluded from
        generation because the API context could not support them.
        """

        return TestCaseGenerationResult(
            test_cases=result.test_cases,
            skipped_categories=skipped_categories,
        )

    @classmethod
    def _build_supported_categories(
        cls,
        categories: list[TestCategory] | None,
        test_plan: TestPlan,
    ) -> list[TestCategory]:
        """
        Return categories that are supported by the grounded test plan.

        When the caller does not explicitly select categories, use the
        categories actually represented by the grounded plan instead of
        asking the LLM to generate every possible category blindly.
        """

        supported_plan_categories = {
            item.category
            for item in test_plan.items
            if item.category in cls._CANONICAL_CATEGORIES
        }

        if categories is None:
            return [
                category
                for category in cls._CANONICAL_CATEGORIES
                if category in supported_plan_categories
            ]

        return list(
            dict.fromkeys(
                category
                for category in categories
                if category in supported_plan_categories
            )
        )

    @staticmethod
    def _build_skipped_categories(
        categories: list[TestCategory] | None,
        supported_categories: list[TestCategory],
    ) -> list[SkippedTestCategory]:
        """
        Identify requested categories that are not supported by the
        grounded test plan.
        """

        if categories is None:
            return []

        supported = set(supported_categories)

        reasons = {
            "happy": (
                "No documented successful HTTP 200 response was found "
                "for this endpoint."
            ),
            "validation": (
                "No documented required-field or request-body validation "
                "constraint was found for this endpoint."
            ),
            "edge": (
                "No explicit edge-case constraint such as minimum, "
                "maximum, length, pattern, or collection boundary was "
                "found for this endpoint."
            ),
            "auth": (
                "No documented authentication or security requirement "
                "was found for this endpoint."
            ),
            "errors": (
                "No documented HTTP error response was found for this endpoint."
            ),
        }

        skipped: list[SkippedTestCategory] = []

        for category in categories:
            if category not in supported:
                skipped.append(
                    SkippedTestCategory(
                        category=category,
                        reason=reasons[category],
                    )
                )

        return skipped

    @classmethod
    def _canonicalize_category(
        cls,
        category: str,
    ) -> TestCategory:
        """
        Normalize common LLM category labels to canonical API categories.
        """

        normalized = re.sub(
            r"[^a-z0-9]+",
            " ",
            category.strip().lower(),
        ).strip()

        for canonical, aliases in cls._CATEGORY_ALIASES.items():
            normalized_aliases = {
                re.sub(
                    r"[^a-z0-9]+",
                    " ",
                    alias.strip().lower(),
                ).strip()
                for alias in aliases
            }

            if normalized in normalized_aliases:
                return canonical

        raise ValueError(
            "Generated test case contains an unsupported category: "
            f"{category.strip()}.",
        )

    @classmethod
    def _validate_category_coverage(
        cls,
        result: TestCaseGenerationResult,
        required_categories: list[TestCategory],
    ) -> None:
        """
        Ensure the LLM returned at least one test case for every
        grounded-supported category requested for this generation.

        Also reject categories that were not part of the grounded request.
        """

        if not required_categories:
            return

        required = set(required_categories)
        generated: set[TestCategory] = set()
        unexpected: list[str] = []

        for test_case in result.test_cases:
            try:
                canonical = cls._canonicalize_category(
                    test_case.category,
                )
            except ValueError:
                unexpected.append(
                    test_case.category.strip(),
                )
                continue

            if canonical not in required:
                unexpected.append(
                    test_case.category.strip(),
                )
                continue

            generated.add(canonical)

        if unexpected:
            unexpected_text = ", ".join(
                dict.fromkeys(unexpected),
            )

            raise ValueError(
                "Generated test cases contain unsupported generated "
                f"categories: {unexpected_text}.",
            )

        missing = [
            category for category in required_categories if category not in generated
        ]

        if missing:
            missing_text = ", ".join(missing)

            raise ValueError(
                "Generated test cases are missing requested categories: "
                f"{missing_text}.",
            )

    @staticmethod
    def _build_regeneration_request(
        original_request: TestCaseGenerationRequest,
        validation_error: ValueError,
    ) -> TestCaseGenerationRequest:
        error_message = str(validation_error)

        artifact_feedback = (
            "\n\n"
            "TEST CASE VALIDATION FEEDBACK:\n"
            "The previous generated test cases failed validation.\n\n"
            "Validation error:\n"
            f"{error_message}\n\n"
            "REGENERATION REQUIREMENTS:\n"
            "1. Regenerate the test cases from scratch.\n"
            "2. Fix the exact validation problem described above.\n"
            "3. Preserve all grounding requirements from the original prompt.\n"
            "4. Do not introduce new undocumented API behavior.\n"
            "5. Do not invent API-specific values, statuses, fields, "
            "headers, authentication requirements, or response properties.\n"
        )

        if (
            "missing requested categories" in error_message
            or "unsupported generated categories" in error_message
        ):
            artifact_feedback += (
                "\nCATEGORY COVERAGE REQUIREMENTS:\n"
                "- Every requested and grounded-supported category MUST "
                "have at least one generated test case.\n"
                "- Do not omit a requested supported category.\n"
                "- Do not generate categories that were not requested "
                "or grounded as supported.\n"
                "- Use canonical category values in the JSON response: "
                "`happy`, `validation`, `edge`, `auth`, or `errors`.\n"
                "- Generate a distinct scenario for each category rather "
                "than collapsing multiple categories into one test.\n"
            )

        elif "invalid Python syntax" in error_message:
            artifact_feedback += (
                "\nPYTHON SYNTAX REQUIREMENTS:\n"
                "- Return syntactically valid Python.\n"
                "- Ensure every function, conditional, loop, and block "
                "has valid indentation.\n"
                "- Ensure all strings, parentheses, brackets, and braces "
                "are properly closed.\n"
                "- The generated artifact must successfully parse with "
                "Python's AST parser.\n"
            )

        elif "must contain an assertion" in error_message:
            artifact_feedback += (
                "\nPYTEST ASSERTION REQUIREMENTS:\n"
                "- The generated pytest test MUST contain at least one "
                "real Python assert statement.\n"
                "- The assertion must verify behavior supported by the "
                "API Context.\n"
                "- Do not add a meaningless assertion such as "
                "`assert True` merely to satisfy validation.\n"
            )

        elif "relative HTTP URL" in error_message:
            artifact_feedback += (
                "\nPYTEST URL REQUIREMENTS:\n"
                "- Do not pass a relative URL directly to requests.\n"
                "- If no base URL is documented, define:\n"
                '  base_url = "<base_url>"\n'
                "- Construct the endpoint URL from that runtime base URL.\n"
                '- Example: f"{base_url}/products/{product_id}"\n'
                "- Never invent a real API hostname.\n"
            )

        elif "does not import the requests module" in error_message:
            artifact_feedback += (
                "\nPYTEST IMPORT REQUIREMENTS:\n"
                "- If the generated test uses requests, include "
                "`import requests`.\n"
            )

        elif "does not import the pytest module" in error_message:
            artifact_feedback += (
                "\nPYTEST IMPORT REQUIREMENTS:\n"
                "- If the generated test uses pytest APIs, include "
                "`import pytest`.\n"
            )

        elif "must contain a Jest test block" in error_message:
            artifact_feedback += (
                "\nJEST TEST STRUCTURE REQUIREMENTS:\n"
                "- The generated Jest test case MUST contain at least "
                "one real Jest test block.\n"
                "- Use `test(...)` or `it(...)` for the test block.\n"
                "- A `describe(...)` block alone is not sufficient unless "
                "it contains a nested `test(...)` or `it(...)` block.\n"
                "- The test block MUST contain a real `expect(...)` assertion.\n"
                "- Return executable JavaScript or TypeScript test code, "
                "not prose describing a test.\n"
            )

        elif "must contain a Jest assertion" in error_message:
            artifact_feedback += (
                "\nJEST ASSERTION REQUIREMENTS:\n"
                "- The generated Jest test case MUST contain at least "
                "one real `expect(...)` assertion.\n"
                "- The assertion must verify behavior supported by the "
                "API documentation.\n"
                "- Do not use a meaningless assertion merely to satisfy "
                "validation.\n"
            )

        artifact_feedback += (
            "\nIMPORTANT:\n"
            "Return ONLY the JSON structure requested by the original "
            "prompt. Do not return explanations outside the JSON object.\n"
        )

        return TestCaseGenerationRequest(
            prompt=original_request.prompt + artifact_feedback,
        )

    @staticmethod
    def _map_categories_to_plan_categories(
        categories: list[TestCategory] | None,
    ) -> list[TestPlanCategory] | None:
        """
        Map the public test-case categories to internal test-plan
        categories.
        """

        if categories is None:
            return None

        mapped: list[TestPlanCategory] = []

        for category in categories:
            if category == "happy":
                mapped.append("happy")
            elif category == "validation":
                mapped.append("validation")
            elif category == "edge":
                mapped.append("edge")
            elif category == "auth":
                mapped.append("auth")
            elif category == "errors":
                mapped.append("errors")

        return list(dict.fromkeys(mapped))

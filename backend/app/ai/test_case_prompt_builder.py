from app.ai.test_case_models import (
    TestCaseGenerationRequest,
    TestCategory,
    TestStyle,
)
from app.rag.retrieval_service import RetrievalResult


class TestCasePromptBuilder:
    """
    Builds prompts for AI-powered API test case generation.

    The generated tests must be strictly grounded in the
    retrieved API specification context.
    """

    def build(
        self,
        endpoint: str,
        contexts: list[RetrievalResult],
        test_style: TestStyle = "jest",
        categories: list[TestCategory] | None = None,
    ) -> TestCaseGenerationRequest:
        if not endpoint.strip():
            raise ValueError("Endpoint cannot be empty.")

        context_sections = [
            result.content.strip() for result in contexts if result.content.strip()
        ]

        context_text = "\n\n".join(context_sections)

        if not context_text:
            context_text = (
                "NO API CONTEXT WAS RETRIEVED. "
                "Do not assume or invent any API behavior."
            )

        selected_categories = categories or [
            "happy",
            "validation",
            "edge",
            "auth",
            "other",
        ]

        category_labels = {
            "happy": "Positive / Happy path",
            "validation": "Negative / Validation",
            "edge": "Edge case",
            "auth": "Authentication / Authorization",
            "other": "Other",
        }

        category_instructions = "\n".join(
            f"- {category_labels.get(category, category)}"
            for category in selected_categories
        )

        style_instructions = {
            "jest": (
                "Generate Jest-compatible JavaScript or TypeScript "
                "test cases. Use describe/it or test blocks where "
                "appropriate."
            ),
            "pytest": (
                "Generate pytest-compatible Python test cases. "
                "Use pytest conventions and assertions."
            ),
            "postman": (
                "Generate Postman-compatible requests and test "
                "scripts. Include request configuration and "
                "Postman test assertions where appropriate."
            ),
            "curl": (
                "Generate executable cURL commands. Include HTTP "
                "method, URL structure, headers, path parameters, "
                "query parameters, and request body only when "
                "explicitly supported by the API context."
            ),
        }

        style_instruction = style_instructions.get(
            test_style,
            style_instructions["jest"],
        )

        prompt = (
            "You are an expert API testing engineer.\n\n"
            "Your task is to generate API test cases for the "
            "specified endpoint using ONLY the supplied API "
            "specification context.\n\n"
            "STRICT GROUNDING RULES:\n"
            "1. Treat the API Context as the only source of truth.\n"
            "2. Never invent API behavior, parameters, schemas, "
            "headers, authentication requirements, response "
            "statuses, response bodies, request bodies, field "
            "names, field values, enums, or validation rules.\n"
            "3. Never assume that a successful request returns "
            "HTTP 200 unless HTTP 200 is explicitly documented "
            "in the API Context.\n"
            "4. Never assume a response is an array, object, "
            "string, or any other type unless the response schema "
            "explicitly documents that type.\n"
            "5. Never create authentication tests unless the API "
            "Context explicitly documents authentication or "
            "authorization requirements.\n"
            "6. Never create query-parameter tests unless query "
            "parameters are explicitly documented.\n"
            "7. Never create request-body tests unless a request "
            "body schema is explicitly documented.\n"
            "8. Never create required-field, type, enum, boundary, "
            "or validation tests unless the corresponding "
            "constraint is explicitly documented.\n"
            "9. Never assume behavior for empty collections, "
            "missing resources, malformed requests, rate limits, "
            "timeouts, or server errors unless that behavior is "
            "supported by the API Context.\n"
            "10. Do not convert general API testing knowledge into "
            "API-specific facts.\n\n"
            "IMPORTANT:\n"
            "A test is allowed to contain an assertion or API "
            "detail ONLY when that detail is supported by the "
            "provided API Context.\n\n"
            "If a requested category cannot be implemented "
            "without making an unsupported assumption, do NOT "
            "invent a pseudo-test.\n"
            "Instead, return a concise limitation explaining "
            "exactly which API information is missing.\n\n"
            "For example, if the context does not document a "
            "response status, do NOT generate:\n"
            "assert response.status_code == 200\n"
            "Instead, state that the documented success status "
            "is unavailable.\n\n"
            "If the context does not document authentication, do "
            "NOT generate a hypothetical 401/403 test.\n"
            "Instead, state that authentication requirements are "
            "not documented.\n\n"
            "If the context does not document query parameters, "
            "do NOT invent invalid query parameters.\n\n"
            f"Target test style: {test_style}\n"
            f"{style_instruction}\n\n"
            "Target endpoint:\n"
            f"{endpoint.strip()}\n\n"
            "API Context:\n"
            f"{context_text}\n\n"
            "Generate test cases ONLY for these categories:\n"
            f"{category_instructions}\n\n"
            "OUTPUT REQUIREMENTS:\n"
            "Each generated test case must contain:\n"
            "- Category\n"
            "- Description containing the actual test "
            "implementation, request, command, assertions, or "
            "limitation appropriate for the selected style.\n\n"
            "For executable tests, every API-specific value must "
            "be traceable to the API Context.\n\n"
            "Do not explain your reasoning outside the generated "
            "test cases.\n\n"
            "Answer:"
        )

        return TestCaseGenerationRequest(
            prompt=prompt,
        )

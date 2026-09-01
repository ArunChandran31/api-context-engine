from app.ai.test_case_models import (
    TestCaseGenerationRequest,
    TestCategory,
    TestStyle,
)
from app.ai.test_plan_models import TestPlan
from app.rag.retrieval_service import RetrievalResult


class TestCasePromptBuilder:
    """
    Builds prompts for AI-powered API test case generation.

    The generated tests must be strictly grounded in the
    retrieved API specification context and the derived
    test plan.
    """

    def build(
        self,
        endpoint: str,
        contexts: list[RetrievalResult],
        test_style: TestStyle = "jest",
        categories: list[TestCategory] | None = None,
        test_plan: TestPlan | None = None,
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

        selected_categories = (
            categories
            if categories is not None
            else [
                "happy",
                "validation",
                "edge",
                "auth",
                "errors",
            ]
        )

        category_labels = {
            "happy": "Positive / Happy path",
            "validation": "Negative / Validation",
            "edge": "Edge case",
            "auth": "Authentication / Authorization",
            "errors": "Documented HTTP Errors",
        }

        category_instructions = "\n".join(
            f"- {category_labels.get(category, category)}"
            for category in selected_categories
        )

        style_instructions = {
            "jest": (
                "Generate executable Jest-compatible JavaScript or TypeScript "
                "test cases. Every generated test case description MUST contain "
                "actual Jest code, not a prose-only explanation. Every Jest test "
                "case MUST contain at least one `test(...)` or `it(...)` block "
                "and at least one `expect(...)` assertion. A `describe(...)` "
                "block may be used to group tests but does not replace the "
                "required test/it block. Keep all API-specific values grounded "
                "in the supplied API Context and Test Plan."
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
                "Generate executable cURL-based API tests. "
                "Each test must contain an actual cURL command and, when a "
                "response status is documented, a shell assertion that verifies "
                "the expected HTTP status code. "
                "Do not merely print the status code with -w. "
                "The generated command must fail when the expected status "
                "is not received. "
                "For every cURL test that asserts an HTTP status, capture the "
                "status code returned by curl and compare it explicitly against "
                "the expected status. Prefer this pattern: "
                '`status=$(curl -s -o /dev/null -w "%{http_code}" ...); '
                '[ "$status" = "400" ] || exit 1`. '
                "The expected status must be the documented status for that "
                "test case. "
                "Do not use `grep` against the raw curl output to determine "
                "whether a status passed. "
                "Do not use a pipeline such as `curl ... | grep -q 400` or "
                "`curl ... | grep -q 404` as the primary HTTP status assertion. "
                "Do not treat the presence of a status string in the response "
                "body as proof of the HTTP status. "
                "Use curl's `%{http_code}` output with `-o /dev/null` when "
                "the response body itself is not required. "
                "The shell assertion must return a non-zero exit status when "
                "the actual HTTP status differs from the documented expected "
                "status. "
                "Use the documented HTTP method, URL path, path parameters, "
                "query parameters, headers, authentication requirements, and "
                "request body only when explicitly supported by the API context. "
                "Use documented example values when available. Otherwise use "
                "placeholders for values that cannot be concretely grounded. "
                "If a base URL is explicitly documented, use it. "
                "If no base URL is documented, use the placeholder "
                "'<base_url>' rather than inventing one. "
                "Do not assert response-body properties unless they are explicitly "
                "documented in the corresponding response schema. "
                "If the API context does not contain enough information to produce "
                "a grounded executable test, return a concise limitation instead."
            ),
        }

        style_instruction = style_instructions.get(
            test_style,
            style_instructions["jest"],
        )

        test_plan_text = self._format_test_plan(test_plan)

        prompt = (
            "You are an expert API testing engineer.\n\n"
            "Your task is to generate API test cases for the "
            "specified endpoint using ONLY the supplied API "
            "specification context and grounded test plan.\n\n"
            "STRICT GROUNDING RULES:\n"
            "1. Treat the API Context as the only source of truth.\n"
            "2. Treat the Test Plan as a list of permitted "
            "test scenarios, not as an additional source of "
            "undocumented API facts.\n"
            "3. Never invent API behavior, parameters, schemas, "
            "headers, authentication requirements, response "
            "statuses, response bodies, request bodies, field "
            "names, field values, enums, or validation rules.\n"
            "4. Never assume that a successful request returns "
            "HTTP 200 unless HTTP 200 is explicitly documented "
            "in the API Context.\n"
            "5. Never assume a response is an array, object, "
            "string, or any other type unless the response schema "
            "explicitly documents that type.\n"
            "6. Never create authentication tests unless the API "
            "Context explicitly documents authentication or "
            "authorization requirements.\n"
            "7. Never create query-parameter tests unless query "
            "parameters are explicitly documented.\n"
            "8. Never create request-body tests unless a request "
            "body schema is explicitly documented.\n"
            "9. Never create required-field, type, enum, boundary, "
            "or validation tests unless the corresponding "
            "constraint is explicitly documented.\n"
            "10. Never assume behavior for empty collections, "
            "missing resources, malformed requests, rate limits, "
            "timeouts, or server errors unless that behavior is "
            "supported by the API Context.\n"
            "11. Do not convert general API testing knowledge into "
            "API-specific facts.\n\n"
            "CATEGORY COVERAGE RULES:\n"
            "12. Generate at least one test case for every requested "
            "category that appears in the supplied Grounded Test Plan.\n"
            "13. Do not omit a requested supported category merely because "
            "another category has more obvious scenarios.\n"
            "14. Do not generate test cases for categories that are not "
            "requested or not supported by the Grounded Test Plan.\n"
            "15. Use exactly one of these canonical category values in the "
            "JSON category field: happy, validation, edge, auth, errors.\n"
            "16. Each generated category must contain a scenario appropriate "
            "to that category rather than reusing an unrelated scenario.\n\n"
            "RESPONSE-BODY GROUNDING RULES:\n"
            "12. A documented HTTP response description is NOT a "
            "response schema.\n"
            "13. A documented HTTP response status does NOT imply "
            "a documented response body.\n"
            "14. Never infer response-body fields, response-body "
            "types, or response-body structure from a response "
            "description.\n"
            "15. Never invent response properties, response "
            "fields, response values, or response types that are "
            "not explicitly documented in the corresponding "
            "response schema.\n"
            "16. A description such as 'Product replaced successfully' "
            "does not document response properties such as id, name, "
            "price, in_stock, or product_id.\n"
            "17. Never infer response fields from request-body fields.\n"
            "18. The presence of a request-body property does not "
            "authorize an assertion about the response body.\n"
            "19. if HTTP 200 is documented but no response schema is "
            "documented, verify only the documented HTTP 200 response "
            "and do not assert response-body properties.\n"
            "20. If any other HTTP response status is documented but "
            "no response schema is documented, verify only the "
            "documented HTTP status and do not assert response-body "
            "properties.\n"
            "21. Never call response.json(), response.json, "
            "response.body, response.data, or equivalent response-body "
            "accessors merely to inspect an undocumented response body.\n"
            "22. Never assert response.body.id, response.body.name, "
            "response.body.price, response.body.in_stock, or any "
            "other response property unless that property is explicitly "
            "documented in the response schema.\n"
            "23. Never assert a response property type unless that "
            "property and its type are explicitly documented in the "
            "response schema.\n"
            "24. Only assert response-body properties when the API "
            "Context explicitly documents those properties and their "
            "types in the corresponding response schema.\n"
            "25. Do not infer that a response contains the same fields "
            "as the request body.\n\n"
            "EXECUTABLE URL RULES:\n"
            "39. For executable HTTP tests, construct request URLs from "
            "a runtime base URL placeholder when no base URL is explicitly "
            "documented in the API Context.\n"
            "40. Never send a relative API path directly to an HTTP client "
            "such as requests, fetch, axios, or curl when the client requires "
            "a complete URL.\n"
            "41. For pytest requests-based tests, use a pattern such as "
            "'base_url = \"<base_url>\"' followed by "
            "'f\"{base_url}/products/{product_id}\"' when no base URL is "
            "documented.\n"
            "42. If a base URL is explicitly documented in the API Context, "
            "that documented base URL may be used.\n"
            "43. Never invent a real API host such as "
            "'https://api.example.com' or 'http://localhost:8000'.\n"
            "44. A placeholder such as '<base_url>' represents a runtime "
            "configuration value and is permitted when the API Context does "
            "not provide a base URL.\n\n"
            "AUTHENTICATION-SPECIFIC GROUNDING RULES:\n"
            "26. Security schemes in the API Context describe authentication "
            "requirements for the endpoint. Treat documented security requirements "
            "as applicable request requirements when the selected test exercises "
            "the endpoint normally.\n"
            "27. If the endpoint is documented as requiring authentication, "
            "non-authentication categories such as happy, validation, edge, and "
            "errors MUST include the documented authentication mechanism when it "
            "is required to construct the request.\n"
            "28. For bearer authentication, generate the Authorization header using "
            "a clearly marked runtime placeholder such as '<token>' when no "
            "concrete credential is provided by the API Context.\n"
            "29. Never invent concrete authentication credentials or token values "
            "such as 'test-token', 'dummy-token', 'valid-token', or "
            "'testBearerToken'.\n"
            "30. If an endpoint is NOT documented as requiring authentication, "
            "do not invent Authorization headers, bearer tokens, API keys, "
            "credentials, or other authentication values.\n"
            "31. The selected authentication mechanism MUST match the documented "
            "security scheme. Do not convert unrelated security metadata into an "
            "undocumented header or credential.\n"
            "32. Authentication-specific tests may focus specifically on the "
            "documented authentication requirement, but they must not invent "
            "undocumented failure behavior or undocumented credential semantics.\n"
            "33. If an authentication-specific test requires a credential but the "
            "API Context does not provide a concrete credential, use a clearly "
            "marked runtime placeholder such as '<token>' when that value is "
            "necessary for the test implementation.\n"
            "34. For a documented HTTP 404 error test, a synthetic resource "
            "identifier may be used when necessary to exercise the explicitly "
            "documented 'not found' behavior. Clearly mark the identifier as "
            "synthetic or nonexistent, for example '<nonexistent_product_id>'. "
            "Do not claim that a specific undocumented identifier is actually "
            "known to exist or not exist. This exception applies only to a "
            "documented 404 error test; for all other tests, do not invent "
            "concrete path parameter values.\n"
            "35. Never invent concrete request-body values such as product names, "
            "prices, IDs, or boolean values unless those values are explicitly "
            "documented in the API Context.\n"
            "36. Never invent an API base URL such as "
            "'https://api.example.com' or 'http://localhost:3000'.\n"
            "37. Never invent authentication behavior for missing, invalid, "
            "expired, or malformed credentials unless the corresponding behavior "
            "is explicitly documented.\n"
            "38. If the API Context documents authentication but does not provide "
            "enough information to construct a grounded authentication request, "
            "do not invent missing authentication details. Use a clearly marked "
            "runtime placeholder only when the documented authentication scheme "
            "makes that placeholder sufficient to construct the request.\n"
            "39. Security schemes must be interpreted together with the selected "
            "endpoint and test category. Do not add authentication to an "
            "unsecured endpoint, and do not omit documented authentication from a "
            "secured endpoint when the test is intended to exercise that endpoint.\n\n"
            "EXAMPLE VALUE VS RUNTIME VALUE RULES:\n"
            "40. A value marked as 'example' in the API Context is an "
            "illustrative example only.\n"
            "41. An example value does NOT prove that the corresponding "
            "resource, identifier, account, record, or state exists at "
            "runtime.\n"
            "42. Never describe an example identifier as an existing "
            "resource unless the API Context explicitly states that the "
            "resource exists.\n"
            "43. For endpoints that require an existing resource, use a "
            "runtime placeholder such as '<existing_product_id>' when the "
            "API Context does not explicitly document an existing runtime "
            "resource.\n"
            "44. A documented example value may be used directly only when "
            "doing so does not imply that the example resource actually "
            "exists or that a particular runtime state is guaranteed.\n"
            "45. Never assert that a request succeeded because an example "
            "identifier happened to be documented.\n"
            "46. Distinguish documented example values from documented "
            "runtime guarantees. The existence of an example value is not "
            "evidence that the referenced resource exists.\n"
            "47. When a documented example value would cause the generated "
            "test to make an unsupported runtime assumption, replace it "
            "with an appropriate clearly marked placeholder.\n\n"
            "CURL-SPECIFIC ASSERTION RULES:\n"
            "48. When test_style is curl and an HTTP status is documented, "
            "the test MUST explicitly capture the HTTP status returned by "
            "curl using `%{http_code}`.\n"
            '49. Use `-s -o /dev/null -w "%{http_code}"` when the response '
            "body is not needed for the assertion.\n"
            "50. Store the returned status in a shell variable, for example:\n"
            '    status=$(curl -s -o /dev/null -w "%{http_code}" ...)\n'
            "51. Compare the captured status against the documented expected "
            "status using a shell assertion, for example:\n"
            '    [ "$status" = "400" ] || exit 1\n'
            "52. The test MUST fail with a non-zero exit status when the "
            "actual HTTP status differs from the expected documented status.\n"
            "53. Do NOT use `grep` on curl output as the HTTP status assertion.\n"
            "54. Do NOT generate patterns such as `curl ... | grep -q 400`, "
            '`curl ... | grep -q 404`, or `curl ... | grep -q "200"`.\n'
            "55. Do NOT infer an HTTP status from the response body.\n"
            "56. Do NOT merely print `%{http_code}` without comparing it "
            "against the expected status.\n"
            "57. For documented 400 and 404 tests, assert exactly 400 and "
            "404 respectively. Do not substitute another status.\n"
            "58. For a documented success status, assert exactly that "
            "documented success status. Do not assume 200.\n"
            "59. Keep the status assertion separate from response-body "
            "assertions unless a response schema explicitly documents "
            "response properties.\n\n"
            "IMPORTANT:\n"
            "A test is allowed to contain an assertion or API "
            "detail ONLY when that detail is supported by the "
            "provided API Context.\n\n"
            "For response-body assertions, the corresponding response "
            "schema must explicitly document the asserted property. "
            "A response description alone is insufficient.\n\n"
            "If a requested category cannot be implemented "
            "without making an unsupported assumption, do NOT "
            "invent a pseudo-test.\n"
            "Instead, return a concise limitation explaining "
            "exactly which API information is missing.\n\n"
            "For executable tests, every API-specific value must "
            "be traceable to the API Context, except for the explicitly "
            "permitted synthetic resource identifier in a documented "
            "404 error test and clearly marked runtime placeholders "
            "required when the API Context does not establish a concrete "
            "runtime value.\n\n"
            f"Target test style: {test_style}\n"
            f"{style_instruction}\n\n"
            "Target endpoint:\n"
            f"{endpoint.strip()}\n\n"
            "Grounded Test Plan:\n"
            f"{test_plan_text}\n\n"
            "API Context:\n"
            f"{context_text}\n\n"
            "Generate test cases ONLY for these categories:\n"
            f"{category_instructions}\n\n"
            "OUTPUT REQUIREMENTS:\n"
            "Return ONLY one valid JSON object.\n\n"
            "The JSON object MUST have exactly this structure:\n"
            "{\n"
            '  "test_cases": [\n'
            "    {\n"
            '      "category": "string",\n'
            '      "description": "string"\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "OUTPUT FORMAT RULES:\n"
            "- The root value MUST be a JSON object.\n"
            '- The root object MUST contain a non-empty "test_cases" array.\n'
            "- Every item in the test_cases array MUST contain "
            '"category" and "description" string fields.\n'
            "- Do NOT return a JSON array as the root value.\n"
            "- Do NOT return Markdown.\n"
            "- Do NOT wrap the JSON in ```json fences.\n"
            "- Do NOT include explanatory text before or after the JSON.\n"
            "- Do NOT add fields other than category and description "
            "inside each test case.\n"
            "- Do not explain your reasoning outside the JSON object.\n\n"
            "CATEGORY OUTPUT RULES:\n"
            "- The category field MUST use only these canonical values: "
            "`happy`, `validation`, `edge`, `auth`, or `errors`.\n"
            "- Do not use display labels such as `Positive / Happy path`, "
            "`Negative / Validation`, `Edge case`, "
            "`Authentication / Authorization`, or "
            "`Documented HTTP Errors` in the category field.\n"
            "- Every requested and grounded-supported category MUST appear "
            "at least once in the generated test_cases array.\n\n"
            "ARTIFACT OUTPUT RULES:\n"
            "- The description field must contain only the requested "
            "test implementation, request, command, assertion, or concise "
            "limitation.\n"
            "- Do not prefix the description with a test-case title, "
            "category heading, Markdown fence, or explanatory prose.\n\n"
            "Each generated test case's description must contain the "
            "actual test implementation, request, command, assertions, "
            "or limitation appropriate for the selected style.\n\n"
            "Answer:"
        )

        return TestCaseGenerationRequest(
            prompt=prompt,
        )

    @staticmethod
    def _format_test_plan(
        test_plan: TestPlan | None,
    ) -> str:
        if test_plan is None:
            return "NO TEST PLAN WAS PROVIDED. " "Rely only on the API Context."

        if not test_plan.items:
            return "NO TEST PLAN ITEMS WERE DERIVED. " "Do not invent test scenarios."

        sections: list[str] = []

        for index, item in enumerate(
            test_plan.items,
            start=1,
        ):
            facts = "; ".join(item.grounded_facts)

            sections.append(
                f"{index}. Category: {item.category}\n"
                f"   Scenario: {item.description}\n"
                f"   Grounded facts: {facts}"
            )

        return "\n".join(sections)

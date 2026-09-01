from app.ai.test_case_models import TestCaseGenerationRequest
from app.ai.test_case_prompt_builder import TestCasePromptBuilder
from app.ai.test_plan_models import TestPlan, TestPlanItem
from app.rag.retrieval_service import RetrievalResult


def create_context(
    content: str = (
        "Endpoint: POST /products/{product_id}\n"
        "Request Body:\n"
        "{\n"
        '  "properties": {\n'
        '    "name": {"type": "string"},\n'
        '    "price": {"type": "number"},\n'
        '    "in_stock": {"type": "boolean"}\n'
        "  },\n"
        '  "required": ["name", "price"]\n'
        "}\n"
        "Responses:\n"
        "{\n"
        '  "200": {\n'
        '    "description": "Product replaced successfully"\n'
        "  },\n"
        '  "400": {\n'
        '    "description": "Invalid product data"\n'
        "  },\n"
        '  "404": {\n'
        '    "description": "Product not found"\n'
        "  }\n"
        "}\n"
        "Security:\n"
        '[{"bearerAuth": []}]'
    ),
) -> RetrievalResult:
    return RetrievalResult(
        content=content,
        score=0.95,
        metadata={},
    )


def test_build_returns_generation_request() -> None:
    builder = TestCasePromptBuilder()

    request = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
    )

    assert isinstance(request, TestCaseGenerationRequest)
    assert request.prompt


def test_build_includes_endpoint() -> None:
    builder = TestCasePromptBuilder()

    request = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
    )

    assert "POST /products/{product_id}" in request.prompt


def test_build_includes_api_context() -> None:
    builder = TestCasePromptBuilder()

    request = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
    )

    assert "Product replaced successfully" in request.prompt
    assert '"name"' in request.prompt
    assert '"price"' in request.prompt


def test_build_uses_default_categories() -> None:
    builder = TestCasePromptBuilder()

    request = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
    )

    assert "Positive / Happy path" in request.prompt
    assert "Negative / Validation" in request.prompt
    assert "Edge case" in request.prompt
    assert "Authentication / Authorization" in request.prompt
    assert "Documented HTTP Errors" in request.prompt


def test_build_uses_selected_categories() -> None:
    builder = TestCasePromptBuilder()

    request = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
        categories=["auth"],
    )

    assert "Authentication / Authorization" in request.prompt


def test_build_includes_style_instruction() -> None:
    builder = TestCasePromptBuilder()

    request = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
        test_style="pytest",
    )

    assert "pytest-compatible Python test cases" in request.prompt


def test_build_includes_curl_assertion_requirements() -> None:
    builder = TestCasePromptBuilder()

    request = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
        test_style="curl",
        categories=["happy"],
    )

    prompt = request.prompt

    assert "Generate executable cURL-based API tests" in prompt
    assert "shell assertion" in prompt
    assert "expected HTTP status code" in prompt
    assert "must fail when the expected status is not received" in prompt
    assert "Do not merely print the status code with -w" in prompt
    assert "If a base URL is explicitly documented, use it." in prompt
    assert (
        "If no base URL is documented, use the placeholder '<base_url>' rather than inventing one."
        in prompt
    )


def test_build_handles_empty_context() -> None:
    builder = TestCasePromptBuilder()

    request = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[],
    )

    assert "NO API CONTEXT WAS RETRIEVED" in request.prompt
    assert "Do not assume or invent any API behavior" in request.prompt


def test_build_rejects_empty_endpoint() -> None:
    builder = TestCasePromptBuilder()

    try:
        builder.build(
            endpoint="   ",
            contexts=[create_context()],
        )
    except ValueError as exc:
        assert str(exc) == "Endpoint cannot be empty."
    else:
        raise AssertionError("Expected ValueError")


def test_build_includes_test_plan() -> None:
    builder = TestCasePromptBuilder()

    plan = TestPlan(
        endpoint="POST /products/{product_id}",
        items=[
            TestPlanItem(
                category="happy",
                description="Verify successful product replacement.",
                grounded_facts=(
                    "HTTP 200 response is documented.",
                    "Documented request fields: name, price, in_stock.",
                ),
            )
        ],
    )

    request = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
        categories=["happy"],
        test_plan=plan,
    )

    assert "Verify successful product replacement." in request.prompt
    assert "HTTP 200 response is documented." in request.prompt


def test_build_includes_authentication_specific_grounding_rules() -> None:
    builder = TestCasePromptBuilder()

    request = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[
            RetrievalResult(
                content=(
                    "Endpoint: POST /products/{product_id}\n"
                    "Authentication: bearerAuth"
                ),
                score=0.95,
                metadata={},
            )
        ],
        categories=["auth"],
    )

    prompt = request.prompt

    assert "Security schemes in the API Context describe authentication" in prompt
    assert "documented security requirements" in prompt
    assert (
        "non-authentication categories such as happy, validation, edge, and errors"
        in prompt
    )
    assert "Authorization header" in prompt
    assert "Bearer" in prompt
    assert "'<token>'" in prompt
    assert "Never invent concrete authentication credentials" in prompt
    assert "Never invent authentication behavior" in prompt


def test_build_requires_documented_auth_for_secured_non_auth_categories() -> None:
    builder = TestCasePromptBuilder()

    request = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[
            RetrievalResult(
                content=(
                    "Endpoint: POST /products/{product_id}\n"
                    "HTTP 200 is documented.\n"
                    "Security: bearerAuth\n"
                    "Request Body: name, price, in_stock"
                ),
                score=0.95,
                metadata={},
            )
        ],
        categories=["happy"],
    )

    prompt = request.prompt

    assert (
        "non-authentication categories such as happy, validation, edge, and errors "
        "MUST include the documented authentication mechanism"
    ) in prompt
    assert ("For bearer authentication, generate the Authorization header") in prompt
    assert "'<token>'" in prompt


def test_build_does_not_invent_authentication_for_unsecured_endpoint() -> None:
    builder = TestCasePromptBuilder()

    request = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[
            RetrievalResult(
                content=(
                    "Endpoint: POST /products/{product_id}\n"
                    "HTTP 200 is documented.\n"
                    "No security requirement is documented."
                ),
                score=0.95,
                metadata={},
            )
        ],
        categories=["happy"],
    )

    prompt = request.prompt

    assert "If an endpoint is NOT documented as requiring authentication" in prompt
    assert "do not invent Authorization headers" in prompt
    assert "bearer tokens" in prompt


def test_build_includes_response_body_grounding_rules() -> None:
    builder = TestCasePromptBuilder()

    request = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
        categories=["happy"],
    )

    prompt = request.prompt

    assert "A documented HTTP response status does NOT imply" in prompt
    assert "Never infer response fields from request-body fields" in prompt
    assert "Never invent response properties" in prompt
    assert "Only assert response-body properties when the API" in prompt
    assert "response schema" in prompt


def test_build_prevents_request_to_response_field_inference() -> None:
    builder = TestCasePromptBuilder()

    request = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
        categories=["happy"],
    )

    prompt = request.prompt

    assert (
        "The presence of a request-body property does not "
        "authorize an assertion about the response body."
    ) in prompt


def test_build_prevents_response_assertions_without_schema() -> None:
    builder = TestCasePromptBuilder()

    request = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[
            create_context(
                content=(
                    "Endpoint: POST /products/{product_id}\n"
                    "Request Body:\n"
                    '{ "properties": {'
                    '"name": {"type": "string"},'
                    '"price": {"type": "number"}'
                    "} }\n"
                    "Responses:\n"
                    '{ "200": {'
                    '"description": "Product replaced successfully"'
                    "} }"
                )
            )
        ],
        categories=["happy"],
    )

    prompt = request.prompt

    assert (
        "if HTTP 200 is documented but no response schema is "
        "documented, verify only the documented HTTP 200 response"
    ) in prompt


def test_build_formats_missing_test_plan() -> None:
    builder = TestCasePromptBuilder()

    request = builder.build(
        endpoint="POST /products/{product_id}",
        contexts=[create_context()],
        test_plan=None,
    )

    assert "NO TEST PLAN WAS PROVIDED" in request.prompt


def test_format_test_plan_with_valid_plan() -> None:
    plan = TestPlan(
        endpoint="POST /products/{product_id}",
        items=[
            TestPlanItem(
                category="happy",
                description="Verify successful product replacement.",
                grounded_facts=("HTTP 200 response is documented.",),
            )
        ],
    )

    formatted = TestCasePromptBuilder._format_test_plan(plan)

    assert "1. Category: happy" in formatted
    assert "Verify successful product replacement." in formatted
    assert "HTTP 200 response is documented." in formatted

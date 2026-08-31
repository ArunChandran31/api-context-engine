from unittest.mock import MagicMock

import pytest

from app.ai.test_case_artifact_validator import (
    TestCaseArtifactValidator,
)
from app.ai.test_case_generation_service import (
    TestCaseGenerationService,
)
from app.ai.test_case_generator import TestCaseGenerator
from app.ai.test_case_models import (
    GeneratedTestCase,
    TestCaseGenerationRequest,
    TestCaseGenerationResult,
)
from app.ai.test_case_prompt_builder import TestCasePromptBuilder
from app.ai.test_plan_builder import TestPlanBuilder
from app.ai.test_plan_models import (
    TestPlan,
    TestPlanItem,
)
from app.rag.retrieval_service import (
    RAGRetrievalService,
    RetrievalResult,
)


def test_generate_retrieves_context_and_generates_test_cases() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = MagicMock(spec=TestCasePromptBuilder)
    generator = MagicMock(spec=TestCaseGenerator)
    test_plan_builder = MagicMock(spec=TestPlanBuilder)

    contexts = [
        RetrievalResult(
            content="Endpoint: POST /users",
            score=0.95,
            metadata={},
        )
    ]

    request = TestCaseGenerationRequest(
        prompt="Prompt",
    )

    test_plan = TestPlan(
        endpoint="POST /users",
        items=[
            TestPlanItem(
                category="happy",
                description="Generate a successful request.",
                grounded_facts=("HTTP 200 is documented.",),
            )
        ],
    )

    result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="Positive",
                description=(
                    "test('valid request', async () => {\n"
                    "    expect(true).toBe(true);\n"
                    "});"
                ),
            )
        ]
    )

    retrieval_service.retrieve.return_value = contexts
    test_plan_builder.build.return_value = test_plan
    prompt_builder.build.return_value = request
    generator.generate.return_value = result

    service = TestCaseGenerationService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        generator=generator,
        test_plan_builder=test_plan_builder,
        retrieval_limit=3,
    )

    generated = service.generate(
        "POST /users",
        specification_id=3,
    )

    assert generated == result

    retrieval_service.retrieve.assert_called_once_with(
        query="POST /users",
        limit=3,
        specification_id=3,
    )

    test_plan_builder.build.assert_called_once_with(
        endpoint="POST /users",
        contexts=contexts,
        categories=None,
    )

    prompt_builder.build.assert_called_once_with(
        endpoint="POST /users",
        contexts=contexts,
        test_style="jest",
        categories=None,
        test_plan=test_plan,
    )

    generator.generate.assert_called_once_with(
        request,
    )


def test_generate_supports_empty_retrieval_results() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = TestCasePromptBuilder()
    generator = MagicMock(spec=TestCaseGenerator)
    test_plan_builder = TestPlanBuilder()

    retrieval_service.retrieve.return_value = []

    generator.generate.return_value = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="Negative",
                description=(
                    "test('no context available', async () => {\n"
                    "    expect(true).toBe(true);\n"
                    "});"
                ),
            )
        ]
    )

    service = TestCaseGenerationService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        generator=generator,
        test_plan_builder=test_plan_builder,
    )

    result = service.generate(
        "POST /users",
        specification_id=3,
    )

    assert len(result.test_cases) == 1

    request = generator.generate.call_args.args[0]

    assert "API Context:" in request.prompt
    assert "NO API CONTEXT WAS RETRIEVED" in request.prompt

    generator.generate.assert_called_once()


def test_generate_retries_when_grounding_validation_fails() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = MagicMock(spec=TestCasePromptBuilder)
    generator = MagicMock(spec=TestCaseGenerator)
    validator = MagicMock()
    test_plan_builder = MagicMock(spec=TestPlanBuilder)

    contexts = [
        RetrievalResult(
            content=(
                "Endpoint: POST /products/{product_id}\n"
                "HTTP 200 is documented.\n"
                "Request field name has type string."
            ),
            score=0.95,
            metadata={},
        )
    ]

    request = TestCaseGenerationRequest(
        prompt="Original grounded prompt",
    )

    test_plan = TestPlan(
        endpoint="POST /products/{product_id}",
        items=[
            TestPlanItem(
                category="happy",
                description="Replace a product successfully.",
                grounded_facts=("HTTP 200 is documented.",),
            )
        ],
    )

    first_result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="Positive",
                description=(
                    "test('uses unsupported value', async () => {\n"
                    "    expect(true).toBe(true);\n"
                    "});"
                ),
            )
        ]
    )

    second_result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="Positive",
                description=(
                    "test('uses grounded API values', async () => {\n"
                    "    expect(true).toBe(true);\n"
                    "});"
                ),
            )
        ]
    )

    retrieval_service.retrieve.return_value = contexts
    test_plan_builder.build.return_value = test_plan
    prompt_builder.build.return_value = request

    generator.generate.side_effect = [
        first_result,
        second_result,
    ]

    validation_error = ValueError(
        "Generated test case contains an undocumented "
        "concrete value for request field 'name': Test Product."
    )

    validator.validate.side_effect = [
        validation_error,
        second_result,
    ]

    service = TestCaseGenerationService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        generator=generator,
        validator=validator,
        test_plan_builder=test_plan_builder,
    )

    result = service.generate(
        endpoint="POST /products/{product_id}",
        specification_id=6,
        categories=["happy"],
    )

    assert result == second_result

    assert generator.generate.call_count == 2
    assert validator.validate.call_count == 2

    first_request = generator.generate.call_args_list[0].args[0]
    second_request = generator.generate.call_args_list[1].args[0]

    assert first_request.prompt == "Original grounded prompt"

    assert "TEST CASE VALIDATION FEEDBACK:" in second_request.prompt
    assert str(validation_error) in second_request.prompt
    assert "Regenerate the test cases from scratch." in second_request.prompt
    assert "Return ONLY the JSON structure requested by the original prompt." in (
        second_request.prompt
    )


def test_generate_raises_after_grounding_validation_retry_fails() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = MagicMock(spec=TestCasePromptBuilder)
    generator = MagicMock(spec=TestCaseGenerator)
    validator = MagicMock()
    test_plan_builder = MagicMock(spec=TestPlanBuilder)

    contexts = [
        RetrievalResult(
            content=(
                "Endpoint: POST /products/{product_id}\n" "HTTP 200 is documented."
            ),
            score=0.95,
            metadata={},
        )
    ]

    request = TestCaseGenerationRequest(
        prompt="Original grounded prompt",
    )

    test_plan = TestPlan(
        endpoint="POST /products/{product_id}",
        items=[
            TestPlanItem(
                category="happy",
                description="Replace a product successfully.",
                grounded_facts=("HTTP 200 is documented.",),
            )
        ],
    )

    result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="Positive",
                description="Unsupported test",
            )
        ]
    )

    retrieval_service.retrieve.return_value = contexts
    test_plan_builder.build.return_value = test_plan
    prompt_builder.build.return_value = request
    generator.generate.return_value = result

    validation_error = ValueError(
        "Generated test case contains an undocumented HTTP status code 201."
    )

    validator.validate.side_effect = validation_error

    service = TestCaseGenerationService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        generator=generator,
        validator=validator,
        test_plan_builder=test_plan_builder,
    )

    with pytest.raises(
        ValueError,
        match="undocumented HTTP status code 201",
    ):
        service.generate(
            endpoint="POST /products/{product_id}",
            specification_id=6,
            categories=["happy"],
        )

    assert generator.generate.call_count == 2
    assert validator.validate.call_count == 2

    second_request = generator.generate.call_args_list[1].args[0]

    assert "TEST CASE VALIDATION FEEDBACK:" in second_request.prompt
    assert str(validation_error) in second_request.prompt


def test_generate_rejects_empty_endpoint() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = MagicMock(spec=TestCasePromptBuilder)
    generator = MagicMock(spec=TestCaseGenerator)
    test_plan_builder = MagicMock(spec=TestPlanBuilder)

    service = TestCaseGenerationService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        generator=generator,
        test_plan_builder=test_plan_builder,
    )

    with pytest.raises(
        ValueError,
        match="Endpoint cannot be empty.",
    ):
        service.generate(
            "   ",
            specification_id=3,
        )

    retrieval_service.retrieve.assert_not_called()
    test_plan_builder.build.assert_not_called()
    prompt_builder.build.assert_not_called()
    generator.generate.assert_not_called()


def test_generate_rejects_invalid_specification_id() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = MagicMock(spec=TestCasePromptBuilder)
    generator = MagicMock(spec=TestCaseGenerator)
    test_plan_builder = MagicMock(spec=TestPlanBuilder)

    service = TestCaseGenerationService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        generator=generator,
        test_plan_builder=test_plan_builder,
    )

    with pytest.raises(
        ValueError,
        match="Specification ID must be greater than zero.",
    ):
        service.generate(
            "POST /users",
            specification_id=0,
        )

    retrieval_service.retrieve.assert_not_called()
    test_plan_builder.build.assert_not_called()
    prompt_builder.build.assert_not_called()
    generator.generate.assert_not_called()


def test_service_rejects_invalid_retrieval_limit() -> None:
    with pytest.raises(
        ValueError,
        match="Retrieval limit must be positive.",
    ):
        TestCaseGenerationService(
            retrieval_service=MagicMock(
                spec=RAGRetrievalService,
            ),
            prompt_builder=MagicMock(
                spec=TestCasePromptBuilder,
            ),
            generator=MagicMock(
                spec=TestCaseGenerator,
            ),
            test_plan_builder=MagicMock(
                spec=TestPlanBuilder,
            ),
            retrieval_limit=0,
        )


def test_generate_validates_generated_pytest_artifact() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = MagicMock(spec=TestCasePromptBuilder)
    generator = MagicMock(spec=TestCaseGenerator)
    validator = MagicMock()
    artifact_validator = MagicMock(
        spec=TestCaseArtifactValidator,
    )
    test_plan_builder = MagicMock(spec=TestPlanBuilder)

    contexts = [
        RetrievalResult(
            content="Endpoint: POST /users\nHTTP 200 is documented.",
            score=0.95,
            metadata={},
        )
    ]

    request = TestCaseGenerationRequest(
        prompt="Generate pytest tests.",
    )

    test_plan = TestPlan(
        endpoint="POST /users",
        items=[
            TestPlanItem(
                category="happy",
                description="Generate a successful request.",
                grounded_facts=("HTTP 200 is documented.",),
            )
        ],
    )

    result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="happy",
                description=(
                    "def test_create_user():\n"
                    "    response = None\n"
                    "    assert response is None\n"
                ),
            )
        ]
    )

    retrieval_service.retrieve.return_value = contexts
    test_plan_builder.build.return_value = test_plan
    prompt_builder.build.return_value = request
    generator.generate.return_value = result
    validator.validate.return_value = result
    artifact_validator.validate.return_value = result

    service = TestCaseGenerationService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        generator=generator,
        validator=validator,
        artifact_validator=artifact_validator,
        test_plan_builder=test_plan_builder,
    )

    generated = service.generate(
        endpoint="POST /users",
        specification_id=3,
        test_style="pytest",
    )

    assert generated == result

    validator.validate.assert_called_once_with(
        result=result,
        context="Endpoint: POST /users\nHTTP 200 is documented.",
    )

    artifact_validator.validate.assert_called_once_with(
        result=result,
        test_style="pytest",
    )


def test_generate_retries_when_artifact_syntax_validation_fails() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = MagicMock(spec=TestCasePromptBuilder)
    generator = MagicMock(spec=TestCaseGenerator)
    validator = MagicMock()
    artifact_validator = MagicMock(
        spec=TestCaseArtifactValidator,
    )
    test_plan_builder = MagicMock(spec=TestPlanBuilder)

    contexts = [
        RetrievalResult(
            content="Endpoint: POST /users\nHTTP 200 is documented.",
            score=0.95,
            metadata={},
        )
    ]

    request = TestCaseGenerationRequest(
        prompt="Original pytest prompt",
    )

    test_plan = TestPlan(
        endpoint="POST /users",
        items=[
            TestPlanItem(
                category="happy",
                description="Generate a successful request.",
                grounded_facts=("HTTP 200 is documented.",),
            )
        ],
    )

    first_result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="happy",
                description="def broken(:\n    assert True",
            )
        ]
    )

    second_result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="happy",
                description=("def test_valid():\n" "    assert True\n"),
            )
        ]
    )

    retrieval_service.retrieve.return_value = contexts
    test_plan_builder.build.return_value = test_plan
    prompt_builder.build.return_value = request

    generator.generate.side_effect = [
        first_result,
        second_result,
    ]

    validator.validate.side_effect = [
        first_result,
        second_result,
    ]

    artifact_error = ValueError(
        "Generated pytest test case contains invalid Python syntax."
    )

    artifact_validator.validate.side_effect = [
        artifact_error,
        second_result,
    ]

    service = TestCaseGenerationService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        generator=generator,
        validator=validator,
        artifact_validator=artifact_validator,
        test_plan_builder=test_plan_builder,
    )

    result = service.generate(
        endpoint="POST /users",
        specification_id=3,
        test_style="pytest",
    )

    assert result == second_result

    assert generator.generate.call_count == 2
    assert validator.validate.call_count == 2
    assert artifact_validator.validate.call_count == 2

    first_request = generator.generate.call_args_list[0].args[0]
    second_request = generator.generate.call_args_list[1].args[0]

    assert first_request.prompt == "Original pytest prompt"

    assert "TEST CASE VALIDATION FEEDBACK:" in second_request.prompt
    assert str(artifact_error) in second_request.prompt
    assert "PYTHON SYNTAX REQUIREMENTS:" in second_request.prompt
    assert "Return syntactically valid Python." in second_request.prompt


def test_generate_retries_when_artifact_url_validation_fails() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = MagicMock(spec=TestCasePromptBuilder)
    generator = MagicMock(spec=TestCaseGenerator)
    validator = MagicMock()
    artifact_validator = MagicMock(
        spec=TestCaseArtifactValidator,
    )
    test_plan_builder = MagicMock(spec=TestPlanBuilder)

    contexts = [
        RetrievalResult(
            content=(
                "Endpoint: GET /products/{product_id}\n" "HTTP 200 is documented."
            ),
            score=0.95,
            metadata={},
        )
    ]

    request = TestCaseGenerationRequest(
        prompt="Original grounded prompt",
    )

    test_plan = TestPlan(
        endpoint="GET /products/{product_id}",
        items=[
            TestPlanItem(
                category="happy",
                description="Retrieve a product successfully.",
                grounded_facts=("HTTP 200 is documented.",),
            )
        ],
    )

    first_result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="happy",
                description="invalid generated test",
            )
        ]
    )

    second_result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="happy",
                description="valid generated test",
            )
        ]
    )

    retrieval_service.retrieve.return_value = contexts
    test_plan_builder.build.return_value = test_plan
    prompt_builder.build.return_value = request

    generator.generate.side_effect = [
        first_result,
        second_result,
    ]

    validator.validate.side_effect = [
        first_result,
        second_result,
    ]

    artifact_error = ValueError(
        "Generated pytest test case uses a relative HTTP URL " "with requests."
    )

    artifact_validator.validate.side_effect = [
        artifact_error,
        second_result,
    ]

    service = TestCaseGenerationService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        generator=generator,
        validator=validator,
        artifact_validator=artifact_validator,
        test_plan_builder=test_plan_builder,
    )

    result = service.generate(
        endpoint="GET /products/{product_id}",
        specification_id=6,
        test_style="pytest",
        categories=["happy"],
    )

    assert result == second_result

    assert generator.generate.call_count == 2
    assert validator.validate.call_count == 2
    assert artifact_validator.validate.call_count == 2

    first_request = generator.generate.call_args_list[0].args[0]
    second_request = generator.generate.call_args_list[1].args[0]

    assert first_request.prompt == "Original grounded prompt"

    assert "TEST CASE VALIDATION FEEDBACK:" in second_request.prompt
    assert str(artifact_error) in second_request.prompt
    assert "PYTEST URL REQUIREMENTS:" in second_request.prompt
    assert 'base_url = "<base_url>"' in second_request.prompt
    assert "Do not pass a relative URL directly to requests." in second_request.prompt


def test_generate_retries_when_artifact_assertion_validation_fails() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)
    prompt_builder = MagicMock(spec=TestCasePromptBuilder)
    generator = MagicMock(spec=TestCaseGenerator)
    validator = MagicMock()
    artifact_validator = MagicMock(
        spec=TestCaseArtifactValidator,
    )
    test_plan_builder = MagicMock(spec=TestPlanBuilder)

    contexts = [
        RetrievalResult(
            content=(
                "Endpoint: GET /products/{product_id}\n" "HTTP 200 is documented."
            ),
            score=0.95,
            metadata={},
        )
    ]

    request = TestCaseGenerationRequest(
        prompt="Original grounded prompt",
    )

    test_plan = TestPlan(
        endpoint="GET /products/{product_id}",
        items=[
            TestPlanItem(
                category="happy",
                description="Retrieve a product successfully.",
                grounded_facts=("HTTP 200 is documented.",),
            )
        ],
    )

    first_result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="happy",
                description="response = requests.get(url)",
            )
        ]
    )

    second_result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="happy",
                description=(
                    "def test_product():\n" "    assert response.status_code == 200\n"
                ),
            )
        ]
    )

    retrieval_service.retrieve.return_value = contexts
    test_plan_builder.build.return_value = test_plan
    prompt_builder.build.return_value = request

    generator.generate.side_effect = [
        first_result,
        second_result,
    ]

    validator.validate.side_effect = [
        first_result,
        second_result,
    ]

    artifact_error = ValueError("Generated pytest test case must contain an assertion.")

    artifact_validator.validate.side_effect = [
        artifact_error,
        second_result,
    ]

    service = TestCaseGenerationService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        generator=generator,
        validator=validator,
        artifact_validator=artifact_validator,
        test_plan_builder=test_plan_builder,
    )

    result = service.generate(
        endpoint="GET /products/{product_id}",
        specification_id=6,
        test_style="pytest",
        categories=["happy"],
    )

    assert result == second_result

    assert generator.generate.call_count == 2
    assert validator.validate.call_count == 2
    assert artifact_validator.validate.call_count == 2

    second_request = generator.generate.call_args_list[1].args[0]

    assert "TEST CASE VALIDATION FEEDBACK:" in second_request.prompt
    assert str(artifact_error) in second_request.prompt
    assert "PYTEST ASSERTION REQUIREMENTS:" in second_request.prompt
    assert (
        "MUST contain at least one real Python assert statement"
        in second_request.prompt
    )
    assert "assert True" in second_request.prompt

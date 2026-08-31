import pytest

from app.ai.test_case_artifact_validator import (
    TestCaseArtifactValidator,
)
from app.ai.test_case_models import (
    GeneratedTestCase,
    TestCaseGenerationResult,
)


def test_validator_accepts_valid_pytest_artifact() -> None:
    validator = TestCaseArtifactValidator()

    result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="happy",
                description=(
                    "def test_create_product():\n"
                    "    response = None\n"
                    "    assert response is None\n"
                ),
            )
        ]
    )

    validated = validator.validate(
        result=result,
        test_style="pytest",
    )

    assert validated == result


def test_validator_rejects_invalid_pytest_syntax() -> None:
    validator = TestCaseArtifactValidator()

    result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="validation",
                description=(
                    "def test_missing_name():\n"
                    "    response = None\n"
                    "  assert response is None\n"
                ),
            )
        ]
    )

    with pytest.raises(
        ValueError,
        match="Generated pytest test case contains invalid Python syntax.",
    ):
        validator.validate(
            result=result,
            test_style="pytest",
        )


def test_validator_rejects_pytest_without_test_function() -> None:
    validator = TestCaseArtifactValidator()

    result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="happy",
                description=(
                    "def create_product():\n"
                    "    response = None\n"
                    "    assert response is None\n"
                ),
            )
        ]
    )

    with pytest.raises(
        ValueError,
        match="Generated pytest test case must contain a pytest test function.",
    ):
        validator.validate(
            result=result,
            test_style="pytest",
        )


def test_validator_rejects_pytest_without_assertion() -> None:
    validator = TestCaseArtifactValidator()

    result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="happy",
                description=("def test_create_product():\n" "    response = None\n"),
            )
        ]
    )

    with pytest.raises(
        ValueError,
        match="Generated pytest test case must contain an assertion.",
    ):
        validator.validate(
            result=result,
            test_style="pytest",
        )


def test_validator_rejects_requests_usage_without_import() -> None:
    validator = TestCaseArtifactValidator()

    result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="happy",
                description=(
                    "def test_create_product():\n"
                    "    response = requests.post('/products')\n"
                    "    assert response.status_code == 200\n"
                ),
            )
        ]
    )

    with pytest.raises(
        ValueError,
        match=(
            "Generated pytest test case uses 'requests' "
            "but does not import the requests module."
        ),
    ):
        validator.validate(
            result=result,
            test_style="pytest",
        )


def test_validator_accepts_requests_import() -> None:
    validator = TestCaseArtifactValidator()

    result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="happy",
                description=(
                    "import requests\n"
                    "\n"
                    "def test_create_product():\n"
                    '    base_url = "<base_url>"\n'
                    '    response = requests.post(f"{base_url}/products")\n'
                    "    assert response.status_code == 200\n"
                ),
            )
        ]
    )

    validated = validator.validate(
        result=result,
        test_style="pytest",
    )

    assert validated == result


def test_validator_accepts_valid_jest_artifact() -> None:
    validator = TestCaseArtifactValidator()

    result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="happy",
                description=(
                    "test('create product', async () => {\n"
                    "    const response = await request.post('/products/123');\n"
                    "    expect(response.status).toBe(200);\n"
                    "});"
                ),
            )
        ]
    )

    validated = validator.validate(
        result=result,
        test_style="jest",
    )

    assert validated == result


def test_validator_rejects_jest_artifact_without_test_block() -> None:
    validator = TestCaseArtifactValidator()

    result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="happy",
                description=(
                    "const response = await request.post('/products/123');\n"
                    "expect(response.status).toBe(200);"
                ),
            )
        ]
    )

    with pytest.raises(
        ValueError,
        match="Generated Jest test case must contain a Jest test block.",
    ):
        validator.validate(
            result=result,
            test_style="jest",
        )


def test_validator_rejects_jest_artifact_without_assertion() -> None:
    validator = TestCaseArtifactValidator()

    result = TestCaseGenerationResult(
        test_cases=[
            GeneratedTestCase(
                category="happy",
                description=(
                    "test('create product', async () => {\n"
                    "    const response = await request.post('/products/123');\n"
                    "});"
                ),
            )
        ]
    )

    with pytest.raises(
        ValueError,
        match="Generated Jest test case must contain a Jest assertion.",
    ):
        validator.validate(
            result=result,
            test_style="jest",
        )

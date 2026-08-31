import ast
import re
from typing import ClassVar

from app.ai.test_case_models import (
    TestCaseGenerationResult,
    TestStyle,
)


class TestCaseArtifactValidator:
    """
    Validates generated test artifacts for their requested test style.

    This validator is intentionally separate from
    TestCaseGroundingValidator. Grounding validation determines whether
    generated API behavior is supported by the API context, while this
    validator checks whether the generated artifact is structurally valid
    for its selected implementation style.
    """

    _HTTP_METHODS: ClassVar[set[str]] = {
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "head",
        "options",
    }

    _ABSOLUTE_URL_PATTERN = re.compile(
        r"^(?:https?|ftp)://",
        re.IGNORECASE,
    )

    @staticmethod
    def validate(
        result: TestCaseGenerationResult,
        test_style: TestStyle,
    ) -> TestCaseGenerationResult:
        if test_style == "pytest":
            TestCaseArtifactValidator._validate_pytest_artifacts(result)

        elif test_style == "jest":
            TestCaseArtifactValidator._validate_jest_artifacts(result)

        return result

    @classmethod
    def _validate_pytest_artifacts(
        cls,
        result: TestCaseGenerationResult,
    ) -> None:
        for test_case in result.test_cases:
            description = test_case.description.strip()

            if not description:
                raise ValueError("Generated pytest test case contains empty Python.")

            try:
                tree = ast.parse(description)
            except SyntaxError as exc:
                raise ValueError(
                    "Generated pytest test case contains invalid Python syntax."
                ) from exc

            cls._validate_pytest_test_function(tree)
            cls._validate_pytest_assertion(tree)
            cls._validate_pytest_imports(tree, description)
            cls._validate_pytest_requests_urls(tree)

    @staticmethod
    def _validate_pytest_test_function(
        tree: ast.AST,
    ) -> None:
        test_functions = [
            node
            for node in ast.walk(tree)
            if isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            )
            and node.name.startswith("test_")
        ]

        if not test_functions:
            raise ValueError(
                "Generated pytest test case must contain a pytest test function."
            )

    @staticmethod
    def _validate_pytest_assertion(
        tree: ast.AST,
    ) -> None:
        assertions = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]

        if not assertions:
            raise ValueError("Generated pytest test case must contain an assertion.")

    @staticmethod
    def _validate_pytest_imports(
        tree: ast.AST,
        description: str,
    ) -> None:
        imported_modules: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split(".")[0])

            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module.split(".")[0])

        if (
            re.search(r"\brequests\s*\.", description)
            and "requests" not in imported_modules
        ):
            raise ValueError(
                "Generated pytest test case uses 'requests' "
                "but does not import the requests module."
            )

        if (
            re.search(r"\bpytest\s*\.", description)
            and "pytest" not in imported_modules
        ):
            raise ValueError(
                "Generated pytest test case uses 'pytest' "
                "but does not import the pytest module."
            )

    @classmethod
    def _validate_pytest_requests_urls(
        cls,
        tree: ast.AST,
    ) -> None:
        """
        Reject relative URLs passed directly to requests.

        A generated test such as:

            requests.get(f"/products/{product_id}")

        is syntactically valid Python but is not an executable HTTP
        request. The generated test must use a runtime base URL, for
        example:

            base_url = "<base_url>"
            requests.get(f"{base_url}/products/{product_id}")
        """

        assignments: dict[str, ast.AST] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assignments[target.id] = node.value

            elif (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.value is not None
            ):
                assignments[node.target.id] = node.value

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            if not isinstance(node.func, ast.Attribute):
                continue

            if not isinstance(node.func.value, ast.Name):
                continue

            if node.func.value.id != "requests":
                continue

            if node.func.attr.lower() not in cls._HTTP_METHODS:
                continue

            if not node.args:
                continue

            url_expression = node.args[0]

            if cls._is_relative_url_expression(
                url_expression,
                assignments,
            ):
                raise ValueError(
                    "Generated pytest test case uses a relative HTTP URL "
                    "with requests. Use a runtime base URL placeholder such "
                    "as '<base_url>' and construct the endpoint URL from it."
                )

    @classmethod
    def _is_relative_url_expression(
        cls,
        expression: ast.AST,
        assignments: dict[str, ast.AST],
        *,
        visited: set[str] | None = None,
    ) -> bool:
        """
        Determine whether an AST expression represents a relative URL.

        Examples rejected:

            "/products/1"
            f"/products/{product_id}"
            url = f"/products/{product_id}"
            requests.get(url)

        Examples accepted:

            "<base_url>/products/1"
            f"{base_url}/products/{product_id}"
            base_url = "<base_url>"
            url = f"{base_url}/products/{product_id}"
        """

        if visited is None:
            visited = set()

        if isinstance(expression, ast.Constant):
            if isinstance(expression.value, str):
                return cls._string_is_relative_url(
                    expression.value,
                )

            return False

        if isinstance(expression, ast.JoinedStr):
            if not expression.values:
                return False

            first_text = ""

            for value in expression.values:
                if isinstance(value, ast.Constant):
                    if isinstance(value.value, str):
                        first_text += value.value
                    else:
                        break
                else:
                    break

            return cls._string_is_relative_url(first_text)

        if isinstance(expression, ast.Name):
            name = expression.id

            if name in visited:
                return False

            assigned_expression = assignments.get(name)

            if assigned_expression is None:
                return False

            visited.add(name)

            return cls._is_relative_url_expression(
                assigned_expression,
                assignments,
                visited=visited,
            )

        return False

    @classmethod
    def _string_is_relative_url(
        cls,
        value: str,
    ) -> bool:
        stripped = value.strip()

        if not stripped:
            return False

        if stripped.startswith("/"):
            return True

        if cls._ABSOLUTE_URL_PATTERN.match(stripped):
            return False

        if stripped.startswith("<base_url>"):
            return False

        if stripped.startswith("{base_url}"):
            return False

        return False

    @staticmethod
    def _validate_jest_artifacts(
        result: TestCaseGenerationResult,
    ) -> None:
        for test_case in result.test_cases:
            description = test_case.description.strip()

            if not description:
                raise ValueError(
                    "Generated Jest test case contains empty " "JavaScript/TypeScript."
                )

            if not re.search(
                r"\b(?:test|it|describe)\s*\(",
                description,
            ):
                raise ValueError(
                    "Generated Jest test case must contain a Jest test block."
                )

            if not re.search(
                r"\bexpect\s*\(",
                description,
            ):
                raise ValueError(
                    "Generated Jest test case must contain a Jest assertion."
                )

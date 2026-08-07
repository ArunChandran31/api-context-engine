from app.ai.test_case_generator import TestCaseGenerator
from app.ai.test_case_models import (
    TestCaseGenerationRequest,
    TestCaseGenerationResult,
)


class DeterministicTestCaseGenerator(TestCaseGenerator):
    """
    Deterministic generator used for local development
    and unit testing.
    """

    def __init__(
        self,
        result: TestCaseGenerationResult,
    ) -> None:
        self._result = result

    def generate(
        self,
        request: TestCaseGenerationRequest,
    ) -> TestCaseGenerationResult:
        return self._result

from abc import ABC, abstractmethod

from app.ai.test_case_models import (
    TestCaseGenerationRequest,
    TestCaseGenerationResult,
)


class TestCaseGenerator(ABC):
    """
    Abstract interface for AI-powered API test case generation.

    Higher-level services depend on this contract rather than
    a specific LLM provider or SDK.
    """

    @abstractmethod
    def generate(
        self,
        request: TestCaseGenerationRequest,
    ) -> TestCaseGenerationResult:
        """
        Generate API test cases for the supplied request.
        """

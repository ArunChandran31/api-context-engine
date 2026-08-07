from app.ai.test_case_models import TestCaseGenerationRequest
from app.rag.retrieval_service import RetrievalResult


class TestCasePromptBuilder:
    """
    Builds prompts for AI-powered API test case generation.

    The generated prompt instructs the language model to create
    positive, negative, and edge-case test cases using only the
    supplied API context.
    """

    def build(
        self,
        endpoint: str,
        contexts: list[RetrievalResult],
    ) -> TestCaseGenerationRequest:
        if not endpoint.strip():
            raise ValueError("Endpoint cannot be empty.")

        context_sections = [
            result.content.strip() for result in contexts if result.content.strip()
        ]

        context_text = "\n\n".join(context_sections)

        prompt = (
            "You are an API testing assistant.\n"
            "Generate comprehensive API test cases using only the "
            "API context below.\n"
            "Do not invent endpoints, request bodies, "
            "authentication requirements, or response fields.\n\n"
            f"Endpoint:\n{endpoint.strip()}\n\n"
            f"API Context:\n{context_text}\n\n"
            "Generate:\n"
            "- Positive test cases\n"
            "- Negative test cases\n"
            "- Edge-case test cases\n\n"
            "For each test case include:\n"
            "- Category\n"
            "- Description\n\n"
            "Answer:"
        )

        return TestCaseGenerationRequest(
            prompt=prompt,
        )

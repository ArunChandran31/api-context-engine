from app.ai.models import GenerationRequest
from app.rag.retrieval_service import RetrievalResult


class GroundedPromptBuilder:
    """
    Builds generation requests grounded in retrieved API context.

    The generated prompt instructs the language model to answer only
    from the supplied retrieval results and avoid unsupported claims.
    """

    def build(
        self,
        question: str,
        contexts: list[RetrievalResult],
    ) -> GenerationRequest:
        if not question.strip():
            raise ValueError("Question cannot be empty.")

        context_sections = [
            result.content.strip() for result in contexts if result.content.strip()
        ]

        context_text = "\n\n".join(context_sections)

        prompt = (
            "You are an API documentation assistant.\n"
            "Answer the user's question using only the API context "
            "provided below.\n"
            "Do not invent endpoints, parameters, authentication "
            "requirements, or behavior that is not present in the context.\n"
            "If the context does not contain enough information to answer "
            "the question, state that the available API context is "
            "insufficient.\n\n"
            f"API Context:\n{context_text}\n\n"
            f"Question:\n{question.strip()}\n\n"
            "Answer:"
        )

        return GenerationRequest(prompt=prompt)

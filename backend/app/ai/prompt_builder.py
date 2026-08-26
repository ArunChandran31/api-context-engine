from app.ai.models import GenerationRequest
from app.rag.retrieval_service import RetrievalResult


class GroundedPromptBuilder:
    """
    Builds generation requests grounded in retrieved API context.

    The prompt is intentionally strict: the model must reason only from
    the supplied API specification context and must explicitly identify
    missing information instead of inventing API behavior.
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

        if context_sections:
            formatted_context = []

            for index, context in enumerate(context_sections, start=1):
                formatted_context.append(
                    f"--- API Context {index} ---\n"
                    f"{context}\n"
                    f"--- End API Context {index} ---"
                )

            context_text = "\n\n".join(formatted_context)
        else:
            context_text = "No API context was retrieved."

        prompt = (
            "You are an API documentation assistant.\n\n"
            "Your task is to answer the user's question using ONLY "
            "the API specification context provided below.\n\n"
            "GROUNDING RULES:\n"
            "1. Use only facts explicitly present in the supplied API context.\n"
            "2. Do not invent endpoints, parameters, request fields, "
            "response fields, status codes, authentication requirements, "
            "default values, validation rules, or API behavior.\n"
            "3. Do not assume behavior merely because it is common practice "
            "for REST APIs.\n"
            "4. If multiple API contexts are provided, combine them only "
            "when they describe relevant parts of the same API behavior.\n"
            "5. Prefer the most relevant endpoint context when answering "
            "endpoint-specific questions.\n"
            "6. If the requested information is missing from the context, "
            "explicitly say that the available API context is insufficient.\n"
            "7. Do not use your general knowledge to fill missing API details.\n"
            "8. When the context contains exact parameter names, field names, "
            "paths, methods, status codes, or operation IDs, preserve them "
            "exactly.\n"
            "9. If the question cannot be answered from the supplied context, "
            "do not guess.\n\n"
            "ANSWERING GUIDELINES:\n"
            "- For parameter questions, distinguish required and optional "
            "parameters when the context provides that information.\n"
            "- For request-body questions, distinguish required and optional "
            "fields when the context provides that information.\n"
            "- For response questions, mention the relevant status code and "
            "response information when available.\n"
            "- For authentication questions, rely only on explicitly stated "
            "security information.\n"
            "- For endpoint questions, include the HTTP method and path when "
            "available.\n"
            "- Keep the answer concise and directly answer the question.\n\n"
            f"API Context:\n{context_text}\n\n"
            f"USER QUESTION:\n{question.strip()}\n\n"
            "ANSWER:"
        )

        return GenerationRequest(prompt=prompt)

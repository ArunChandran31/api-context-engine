from app.ai.debug_models import DebugRequest


class DebugPromptBuilder:
    """
    Builds prompts for AI-assisted debugging.
    """

    def build(
        self,
        question: str,
        context: str,
    ) -> DebugRequest:
        prompt = (
            "You are an expert software engineer.\n\n"
            "Use ONLY the provided context.\n"
            "If the context does not contain enough information, "
            'reply with "I do not know based on the provided context."\n\n'
            f"Debug Question:\n{question}\n\n"
            f"Context:\n{context}"
        )

        return DebugRequest(prompt=prompt)

from app.ai.debug_models import DebugRequest


class DebugPromptBuilder:
    """
    Builds prompts for AI-assisted API debugging.
    """

    def build(
        self,
        question: str,
        endpoint: str,
        status_code: int,
        error_message: str,
        request_body: str,
        response_body: str,
        context: str,
    ) -> DebugRequest:
        request_body_text = request_body.strip() or "(empty)"
        response_body_text = response_body.strip() or "(empty)"
        context_text = context.strip() or "(empty)"

        prompt = (
            "You are an expert software engineer specializing in "
            "API debugging.\n\n"
            "Use ONLY the API context provided below together with "
            "the supplied failure details.\n"
            "Do not invent endpoints, request bodies, response fields, "
            "authentication requirements, or API behavior.\n"
            "If the provided API context does not contain enough "
            "information to determine the cause, clearly state that "
            "the available context is insufficient.\n\n"
            f"Debug Question:\n{question.strip()}\n\n"
            f"Endpoint:\n{endpoint.strip()}\n\n"
            f"HTTP Status Code:\n{status_code}\n\n"
            f"Error Message:\n{error_message.strip()}\n\n"
            f"Request Body:\n{request_body_text}\n\n"
            f"Response / Stack Trace:\n{response_body_text}\n\n"
            f"API Context:\n{context_text}\n\n"
            "Analyze the failure and provide:\n"
            "1. Likely cause of the failure\n"
            "2. Suggested fix\n"
            "3. Relevant supporting details from the provided context\n"
            "4. Corrected request example if the available context "
            "supports one\n\n"
            "Answer:"
        )

        return DebugRequest(
            prompt=prompt,
        )

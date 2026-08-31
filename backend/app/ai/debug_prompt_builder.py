from app.ai.debug_models import DebugRequest


class DebugPromptBuilder:
    """
    Builds grounded prompts for AI-assisted API debugging.

    The prompt explicitly separates:
    - documented API facts,
    - observed failure details,
    - reasonable inferences,
    - and information that cannot be determined.

    This helps reduce hallucinations when the API specification does not
    document the exact cause of a failure.
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
            "Your job is to diagnose the reported API failure using "
            "ONLY the API context together with the supplied failure details.\n\n"
            "GROUNDING RULES:\n"
            "- Do not invent endpoints, URLs, parameters, parameter values, "
            "request bodies, response fields, authentication flows, "
            "credentials, headers, scopes, permissions, or API behavior.\n"
            "- Treat the supplied API context as the authoritative source "
            "for documented API behavior.\n"
            "- Treat the supplied status code, error message, request body, "
            "and response body as observed failure information.\n"
            "- Clearly distinguish documented facts from reasonable "
            "inferences about the failure.\n"
            "- Do not present an inference as an explicitly documented fact.\n"
            "- If the API context documents authentication but does not "
            "document the exact authentication failure behavior, do not "
            "claim that a particular authentication condition caused "
            "the failure.\n"
            "- If a 401, 403, 400, or other status code is observed, use "
            "the supplied error details as evidence, but do not invent "
            "undocumented semantics for that status code.\n"
            "- Do not infer that a request was successfully authenticated "
            "merely because the response status is 403.\n"
            "- Do not infer that a token is missing, expired, revoked, "
            "malformed, or insufficiently privileged unless the supplied "
            "failure details or API context explicitly support that "
            "conclusion.\n"
            "- Do not treat an observed error message such as "
            '"Insufficient permissions" as proof of a specific underlying '
            "authentication state. It may indicate an authorization-related "
            "failure, but do not claim that the request was successfully "
            "authenticated or that a token was supplied unless that is "
            "explicitly established by the failure details or API context.\n"
            "- If scopes or permissions are not explicitly documented, "
            "do not invent scope names, permission names, or required "
            "privilege levels.\n"
            "- Do not invent OAuth scope names such as `products:read` "
            "or similar permission names when they are not documented.\n"
            "- Do not recommend obtaining a new token, changing token "
            "scopes, or changing permissions unless the available "
            "information supports that recommendation.\n"
            "- Do not invent example resource IDs. Use placeholders such "
            "as <PRODUCT_ID> when an ID was not supplied.\n"
            "- If the exact cause cannot be determined from the supplied "
            "information, explicitly say that the available context is "
            "insufficient to determine the exact cause.\n\n"
            "CORRECTED REQUEST RULES:\n"
            "- If a corrected request example is appropriate, use only "
            "values explicitly provided in the failure details or API "
            "context.\n"
            "- Use placeholders such as <API_HOST>, <PRODUCT_ID>, "
            "<TOKEN>, or <PARAMETER_VALUE> when required values are "
            "not available.\n"
            "- Never replace placeholders with invented example values. "
            "Every concrete value in a corrected request must come from "
            "the failure details or API context.\n"
            "- Never invent a base URL, resource ID, token, credential, "
            "scope, permission, or authentication flow.\n\n"
            f"Debug Question:\n{question.strip()}\n\n"
            f"Endpoint:\n{endpoint.strip()}\n\n"
            f"HTTP Status Code:\n{status_code}\n\n"
            f"Error Message:\n{error_message.strip()}\n\n"
            f"Request Body:\n{request_body_text}\n\n"
            f"Response / Stack Trace:\n{response_body_text}\n\n"
            f"API Context:\n{context_text}\n\n"
            "ANALYSIS REQUIREMENTS:\n"
            "Provide the following sections:\n\n"
            "1. Likely cause of the failure\n"
            "- Explain what can reasonably be concluded from the supplied "
            "failure details and API context.\n"
            "- Separate documented facts from inference.\n"
            "- If the exact cause is unknown, explicitly state that it "
            "cannot be determined from the available context.\n\n"
            "2. Suggested fix\n"
            "- Recommend only fixes supported by the available information.\n"
            "- If the exact fix cannot be determined, state what should be "
            "verified instead of inventing a solution.\n"
            "- Recommend verifying authorization requirements and credentials "
            "only when the available context supports doing so.\n"
            "- Do not assume whether an Authorization header was present in "
            "the original request unless that information was supplied.\n\n"
            "3. Relevant supporting details from the provided context\n"
            "- Cite the specific API behavior, parameter, security "
            "requirement, schema, response definition, or other context "
            "that supports the diagnosis.\n"
            "- Do not add undocumented API behavior.\n\n"
            "4. Corrected request example\n"
            "- Include this only when the available information supports "
            "a useful example.\n"
            "- Use placeholders for values that are not explicitly supplied.\n"
            "- Do not invent hostnames, IDs, tokens, credentials, scopes, "
            "permissions, headers, or parameter values.\n\n"
            "IMPORTANT:\n"
            "A documented security requirement such as bearerAuth only "
            "establishes that the endpoint uses that authentication scheme. "
            "It does not by itself establish which OAuth scopes or "
            "permissions are required, nor does it establish the exact "
            "reason for a 403 response.\n\n"
            "A 403 response combined with an error such as "
            '"Insufficient permissions" may indicate an authorization '
            "problem, but do not claim exactly why authorization failed "
            "unless that cause is explicitly supported by the supplied "
            "failure details or API context.\n\n"
            "A 403 response with an error such as "
            '"Insufficient permissions" supports describing the failure '
            "as authorization-related, but it does not prove that "
            "authentication succeeded, that a bearer token was present, "
            "or that a particular permission or scope was missing.\n\n"
            "Do not invent missing information merely to provide a more "
            "specific answer.\n\n"
            "If the available context does not contain enough information "
            "to determine the exact cause, say so clearly rather than "
            "guessing.\n\n"
            "Answer:"
        )

        return DebugRequest(
            prompt=prompt,
        )

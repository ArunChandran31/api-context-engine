from pydantic import BaseModel, Field


class DebugRequest(BaseModel):
    """
    Request payload for AI-assisted API debugging.
    """

    question: str = Field(
        min_length=1,
        description="Natural-language description of the API failure.",
    )

    specification_id: int = Field(
        gt=0,
        description="ID of the API specification to use as debugging context.",
    )

    endpoint: str = Field(
        min_length=1,
        description="API endpoint that failed.",
    )

    status_code: int = Field(
        ge=100,
        le=599,
        description="HTTP status code returned by the failed request.",
    )

    error_message: str = Field(
        min_length=1,
        description="Error message returned by the API.",
    )

    request_body: str = Field(
        default="",
        description="Request body sent to the API.",
    )

    response_body: str = Field(
        default="",
        description="Response body or stack trace returned by the API.",
    )


class DebugResponse(BaseModel):
    """
    Response returned by the AI debugging endpoint.
    """

    explanation: str = Field(
        description="AI-generated explanation of the API failure.",
    )

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    """
    Request payload for API question answering.
    """

    question: str = Field(
        min_length=1,
        description="Natural-language question about an indexed API.",
    )

    specification_id: int = Field(
        gt=0,
        description="ID of the API specification to use as AI context.",
    )


class QuestionSource(BaseModel):
    """
    Source endpoint used as context for an AI answer.
    """

    specification_id: int
    endpoint_id: int
    method: str
    path: str
    operation_id: str | None = None


class QuestionResponse(BaseModel):
    """
    Response returned by the AI question-answering endpoint.
    """

    answer: str = Field(
        description="Answer generated from retrieved API context.",
    )

    sources: list[QuestionSource] = Field(
        default_factory=list,
        description="API endpoints used as context for the answer.",
    )

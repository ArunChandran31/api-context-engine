from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    """
    Request payload for API question answering.
    """

    question: str = Field(
        min_length=1,
        description="Natural-language question about an indexed API.",
    )


class QuestionResponse(BaseModel):
    """
    Response returned by the AI question-answering endpoint.
    """

    answer: str = Field(
        description="Answer generated from retrieved API context.",
    )

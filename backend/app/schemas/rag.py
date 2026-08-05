from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema


class RAGQueryRequest(BaseSchema):
    query: str = Field(..., min_length=1)

    limit: int | None = Field(
        default=None,
        gt=0,
    )


class RAGRetrievalResultResponse(BaseSchema):
    content: str

    score: float

    metadata: dict[str, Any]


class RAGQueryResponse(BaseSchema):
    query: str

    results: list[RAGRetrievalResultResponse]


class RAGIndexResponse(BaseSchema):
    specification_id: int

    documents_indexed: int

    chunks_indexed: int

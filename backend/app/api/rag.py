from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends

from app.rag.dependencies import RAGDependencies, build_rag_dependencies
from app.schemas.rag import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGRetrievalResultResponse,
)

router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
)


@lru_cache
def get_rag_dependencies() -> RAGDependencies:
    return build_rag_dependencies()


@router.post(
    "/query",
    response_model=RAGQueryResponse,
)
def query_rag(
    request: RAGQueryRequest,
    dependencies: Annotated[
        RAGDependencies,
        Depends(get_rag_dependencies),
    ],
) -> RAGQueryResponse:
    limit = request.limit if request.limit is not None else dependencies.retrieval_limit

    results = dependencies.retrieval_service.retrieve(
        query=request.query,
        limit=limit,
    )

    return RAGQueryResponse(
        query=request.query,
        results=[
            RAGRetrievalResultResponse(
                content=result.content,
                score=result.score,
                metadata=result.metadata,
            )
            for result in results
        ],
    )

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.rag.context_generator import ContextGenerator
from app.rag.dependencies import RAGDependencies, build_rag_dependencies
from app.schemas.rag import (
    RAGIndexResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGRetrievalResultResponse,
)
from app.services.api_specification_service import ApiSpecificationService

router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
)

specification_service = ApiSpecificationService()
context_generator = ContextGenerator()


@lru_cache
def get_rag_dependencies() -> RAGDependencies:
    return build_rag_dependencies()


@router.post(
    "/index/{specification_id}",
    response_model=RAGIndexResponse,
    status_code=status.HTTP_200_OK,
)
def index_specification(
    specification_id: int,
    db: Annotated[Session, Depends(get_db)],
    dependencies: Annotated[
        RAGDependencies,
        Depends(get_rag_dependencies),
    ],
) -> RAGIndexResponse:
    specification = specification_service.get(
        db,
        specification_id,
    )

    if specification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API specification with ID {specification_id} was not found.",
        )

    documents = context_generator.generate(specification)

    chunks_indexed = sum(
        dependencies.indexing_service.index_document(document) for document in documents
    )

    dependencies.persistence.save()

    return RAGIndexResponse(
        specification_id=specification_id,
        documents_indexed=len(documents),
        chunks_indexed=chunks_indexed,
    )


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

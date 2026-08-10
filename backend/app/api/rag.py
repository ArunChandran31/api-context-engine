import logging
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.cache.dependencies import get_cache_service
from app.cache.keys import build_rag_query_cache_key
from app.cache.service import CacheService
from app.core.config import settings
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

logger = logging.getLogger(__name__)

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
    cache: Annotated[
        CacheService,
        Depends(get_cache_service),
    ],
) -> RAGQueryResponse:
    limit = request.limit if request.limit is not None else dependencies.retrieval_limit

    cache_key = build_rag_query_cache_key(
        query=request.query,
        limit=limit,
    )

    cached_results = cache.get(cache_key)

    if cached_results is not None:
        logger.info(
            "RAG cache HIT",
            extra={
                "cache_key": cache_key,
                "query": request.query,
                "limit": limit,
            },
        )

        return RAGQueryResponse(
            query=request.query,
            results=[RAGRetrievalResultResponse(**result) for result in cached_results],
        )

    logger.info(
        "RAG cache MISS",
        extra={
            "cache_key": cache_key,
            "query": request.query,
            "limit": limit,
        },
    )

    results = dependencies.retrieval_service.retrieve(
        query=request.query,
        limit=limit,
    )

    response_results = [
        RAGRetrievalResultResponse(
            content=result.content,
            score=result.score,
            metadata=result.metadata,
        )
        for result in results
    ]

    cache.set(
        cache_key,
        [result.model_dump() for result in response_results],
        ttl_seconds=settings.redis_cache_ttl_seconds,
    )

    return RAGQueryResponse(
        query=request.query,
        results=response_results,
    )

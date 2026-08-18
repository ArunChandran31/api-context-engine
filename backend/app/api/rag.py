import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.cache.dependencies import get_cache_service
from app.cache.keys import (
    build_rag_query_cache_key,
    build_rag_query_cache_pattern,
)
from app.cache.service import CacheService
from app.core.config import settings
from app.database.session import get_db
from app.rag.context_generator import ContextGenerator
from app.rag.dependencies import RAGDependencies, get_rag_dependencies
from app.schemas.rag import (
    RAGIndexResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGRetrievalResultResponse,
)
from app.services.api_specification_service import ApiSpecificationService
from app.utils.timing import Timer

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
)

specification_service = ApiSpecificationService()
context_generator = ContextGenerator()


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
    cache: Annotated[
        CacheService,
        Depends(get_cache_service),
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

    # Invalidate cached RAG queries for this specification.
    cache_pattern = build_rag_query_cache_pattern(
        specification_id=specification_id,
    )

    deleted_cache_entries = cache.delete_pattern(
        cache_pattern,
    )

    logger.info(
        "RAG specification indexed",
        extra={
            "specification_id": specification_id,
            "documents_indexed": len(documents),
            "chunks_indexed": chunks_indexed,
            "cache_entries_invalidated": deleted_cache_entries,
        },
    )

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
    total_timer = Timer()
    total_timer.start()

    limit = request.limit if request.limit is not None else dependencies.retrieval_limit

    cache_key = build_rag_query_cache_key(
        query=request.query,
        limit=limit,
        specification_id=request.specification_id,
    )

    cache_get_timer = Timer()
    cache_get_timer.start()

    cached_results = cache.get(cache_key)

    cache_get_ms = cache_get_timer.stop()

    if cached_results is not None:
        response = RAGQueryResponse(
            query=request.query,
            results=[RAGRetrievalResultResponse(**result) for result in cached_results],
        )

        total_ms = total_timer.stop()

        logger.info(
            "RAG query completed",
            extra={
                "cache_hit": True,
                "cache_get_ms": round(cache_get_ms, 2),
                "retrieval_ms": 0.0,
                "cache_set_ms": 0.0,
                "total_ms": round(total_ms, 2),
                "result_count": len(response.results),
            },
        )

        return response

    logger.info(
        "RAG cache MISS",
        extra={
            "cache_key": cache_key,
        },
    )

    retrieval_timer = Timer()
    retrieval_timer.start()

    results = dependencies.retrieval_service.retrieve(
        query=request.query,
        limit=limit,
        specification_id=request.specification_id,
    )

    retrieval_ms = retrieval_timer.stop()

    response_results = [
        RAGRetrievalResultResponse(
            content=result.content,
            score=result.score,
            metadata=result.metadata,
        )
        for result in results
    ]

    cache_set_timer = Timer()
    cache_set_timer.start()

    cache.set(
        cache_key,
        [result.model_dump() for result in response_results],
        ttl_seconds=settings.redis_cache_ttl_seconds,
    )

    cache_set_ms = cache_set_timer.stop()
    total_ms = total_timer.stop()

    logger.info(
        "RAG query completed",
        extra={
            "cache_hit": False,
            "cache_get_ms": round(cache_get_ms, 2),
            "retrieval_ms": round(retrieval_ms, 2),
            "cache_set_ms": round(cache_set_ms, 2),
            "total_ms": round(total_ms, 2),
            "result_count": len(response_results),
        },
    )

    return RAGQueryResponse(
        query=request.query,
        results=response_results,
    )

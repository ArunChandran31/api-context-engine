import logging
from dataclasses import dataclass
from typing import Protocol

from app.cache.keys import build_rag_query_cache_pattern
from app.database.models.api_specification import ApiSpecification
from app.rag.context_generator import ContextGenerator
from app.rag.indexing_service import RAGIndexingService
from app.rag.persistence import VectorStorePersistence

logger = logging.getLogger(__name__)


class CacheInvalidationService(Protocol):
    """
    Minimal cache interface required by the RAG indexing orchestrator.
    """

    def delete_pattern(self, pattern: str) -> int: ...


@dataclass(frozen=True)
class RAGIndexingResult:
    """
    Result of indexing an API specification.
    """

    specification_id: int
    documents_indexed: int
    chunks_indexed: int
    cache_entries_invalidated: int


class RAGIndexingOrchestrator:
    """
    Coordinates specification-level RAG indexing.

    This service owns the workflow around:
    - generating semantic RAG documents,
    - replacing previously indexed vectors,
    - persisting the vector store,
    - and invalidating specification-scoped RAG caches.

    The underlying indexing and storage implementations remain
    encapsulated behind their existing interfaces.
    """

    def __init__(
        self,
        context_generator: ContextGenerator,
        indexing_service: RAGIndexingService,
        persistence: VectorStorePersistence,
        cache_service: CacheInvalidationService,
    ) -> None:
        self._context_generator = context_generator
        self._indexing_service = indexing_service
        self._persistence = persistence
        self._cache_service = cache_service

    def index_specification(
        self,
        specification: ApiSpecification,
    ) -> RAGIndexingResult:
        """
        Replace the existing RAG index for a specification.

        Returns detailed statistics describing the indexing operation.
        """

        if specification.id is None or specification.id <= 0:
            raise ValueError("Specification ID must be greater than zero.")

        documents = self._context_generator.generate(
            specification,
        )

        # Remove stale vectors before indexing the current
        # representation of the specification.
        self._indexing_service.delete_specification(
            specification.id,
        )

        chunks_indexed = 0

        for document in documents:
            chunks_indexed += self._indexing_service.index_document(
                document,
            )

        # Persist the updated FAISS index and records.
        self._persistence.save()

        # Any cached query result for this specification is now stale.
        cache_pattern = build_rag_query_cache_pattern(
            specification.id,
        )

        deleted_cache_entries = self._cache_service.delete_pattern(
            cache_pattern,
        )

        result = RAGIndexingResult(
            specification_id=specification.id,
            documents_indexed=len(documents),
            chunks_indexed=chunks_indexed,
            cache_entries_invalidated=deleted_cache_entries,
        )

        logger.info(
            "RAG specification indexed",
            extra={
                "specification_id": result.specification_id,
                "documents_indexed": result.documents_indexed,
                "chunks_indexed": result.chunks_indexed,
                "cache_entries_invalidated": (result.cache_entries_invalidated),
            },
        )

        return result

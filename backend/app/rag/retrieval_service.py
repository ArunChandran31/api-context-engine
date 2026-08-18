from dataclasses import dataclass
from typing import Any

from app.rag.embeddings import EmbeddingProvider
from app.rag.vector_store import VectorSearchResult, VectorStore


@dataclass(frozen=True)
class RetrievalResult:
    """
    Application-level result returned by RAG retrieval.
    """

    content: str
    score: float
    metadata: dict[str, Any]


class RAGRetrievalService:
    """
    Retrieves relevant indexed API context for natural-language queries.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        if embedding_provider.dimension != vector_store.dimension:
            raise ValueError(
                "Embedding provider dimension must match vector store dimension."
            )

        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        specification_id: int | None = None,
    ) -> list[RetrievalResult]:
        """
        Retrieve the most relevant indexed context for a query.

        When specification_id is provided, only records belonging to
        that API specification are returned.
        """

        if not query.strip():
            raise ValueError("Query cannot be empty.")

        if limit <= 0:
            raise ValueError("Retrieval limit must be greater than zero.")

        if specification_id is not None and specification_id <= 0:
            raise ValueError("Specification ID must be greater than zero.")

        query_vector = self._embedding_provider.embed(query)

        # Retrieve a larger candidate pool when filtering by specification.
        # This prevents unrelated APIs from occupying the top `limit` slots.
        search_limit = limit

        if specification_id is not None:
            search_limit = max(limit * 10, 50)

        search_results = self._vector_store.search(
            query_vector=query_vector,
            limit=search_limit,
        )

        results = [
            self._to_retrieval_result(result)
            for result in search_results
            if (
                specification_id is None
                or result.record.metadata.get("specification_id") == specification_id
            )
        ]

        return results[:limit]

    @staticmethod
    def _to_retrieval_result(
        result: VectorSearchResult,
    ) -> RetrievalResult:
        return RetrievalResult(
            content=result.record.content,
            score=result.score,
            metadata=dict(result.record.metadata),
        )

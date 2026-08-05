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
    ) -> list[RetrievalResult]:
        """
        Retrieve the most relevant indexed context for a query.
        """

        if not query.strip():
            raise ValueError("Query cannot be empty.")

        if limit <= 0:
            raise ValueError("Retrieval limit must be greater than zero.")

        query_vector = self._embedding_provider.embed(query)

        search_results = self._vector_store.search(
            query_vector=query_vector,
            limit=limit,
        )

        return [self._to_retrieval_result(result) for result in search_results]

    @staticmethod
    def _to_retrieval_result(
        result: VectorSearchResult,
    ) -> RetrievalResult:
        return RetrievalResult(
            content=result.record.content,
            score=result.score,
            metadata=dict(result.record.metadata),
        )

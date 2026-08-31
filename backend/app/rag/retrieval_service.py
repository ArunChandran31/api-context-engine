import re
from dataclasses import dataclass
from typing import Any

from app.rag.embeddings import EmbeddingProvider
from app.rag.vector_store import VectorSearchResult, VectorStore
from app.utils.timing import Timer


@dataclass(frozen=True)
class RetrievalResult:
    """
    Application-level result returned by RAG retrieval.
    """

    content: str
    score: float
    metadata: dict[str, Any]


@dataclass(frozen=True)
class EndpointIntent:
    """
    Explicit endpoint references detected in a natural-language query.
    """

    method: str | None = None
    path: str | None = None


class RAGRetrievalService:
    """
    Retrieves relevant indexed API context for natural-language queries.

    Retrieval operates in three stages:

    1. Retrieve a larger candidate pool from the vector store.
    2. Prefer candidates matching explicitly referenced HTTP
       method/path combinations.
    3. Group matching chunks by endpoint and reconstruct the complete
       endpoint context before returning the final results.

    This prevents a single highly relevant chunk from hiding other
    chunks belonging to the same API endpoint while also improving
    precision when a user explicitly references an endpoint.
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

        self.last_timing = {
            "embedding_ms": 0.0,
            "search_ms": 0.0,
            "reconstruction_ms": 0.0,
        }

    def retrieve(
        self,
        query: str,
        limit: int = 5,
        specification_id: int | None = None,
    ) -> list[RetrievalResult]:
        """
        Retrieve the most relevant endpoint contexts for a query.

        When specification_id is provided, only records belonging to
        that API specification are considered.

        Multiple chunks belonging to the same endpoint are reconstructed
        into a single RetrievalResult.

        When the query explicitly references one or more HTTP
        method/path combinations, matching endpoints are preferred.
        """

        if not query.strip():
            raise ValueError("Query cannot be empty.")

        if limit <= 0:
            raise ValueError("Retrieval limit must be greater than zero.")

        if specification_id is not None and specification_id <= 0:
            raise ValueError("Specification ID must be greater than zero.")

        embedding_timer = Timer()
        embedding_timer.start()

        query_vector = self._embedding_provider.embed(query)

        embedding_ms = embedding_timer.stop()

        # Retrieve a larger candidate pool than the requested result count.
        #
        # This gives us enough candidates to discover multiple chunks
        # belonging to the same endpoint.
        search_limit = max(limit * 10, 50)

        search_timer = Timer()
        search_timer.start()

        search_results = self._vector_store.search(
            query_vector=query_vector,
            limit=search_limit,
        )

        search_ms = search_timer.stop()

        filtered_results = [
            result
            for result in search_results
            if (
                specification_id is None
                or result.record.metadata.get("specification_id") == specification_id
            )
        ]

        endpoint_intents = self._extract_endpoint_intents(query)

        if endpoint_intents:
            filtered_results = self._apply_endpoint_intent_filter(
                search_results=filtered_results,
                intents=endpoint_intents,
            )

        reconstruction_timer = Timer()
        reconstruction_timer.start()

        results = self._reconstruct_endpoint_results(
            filtered_results,
            limit=limit,
        )

        reconstruction_ms = reconstruction_timer.stop()

        self.last_timing = {
            "embedding_ms": round(embedding_ms, 2),
            "search_ms": round(search_ms, 2),
            "reconstruction_ms": round(reconstruction_ms, 2),
        }

        return results

    @staticmethod
    def _extract_endpoint_intents(
        query: str,
    ) -> list[EndpointIntent]:
        """
        Extract explicit HTTP method/path references from a query.

        Examples:

            "What does GET /users require?"
            ->
            [EndpointIntent(method="GET", path="/users")]

            "Compare GET /users and POST /users."
            ->
            [
                EndpointIntent(method="GET", path="/users"),
                EndpointIntent(method="POST", path="/users"),
            ]

        Trailing natural-language punctuation such as '.', ',', ';',
        ':', '!', and '?' is removed from the extracted path.

        Queries without an explicit method/path return an empty list.
        """

        pattern = re.compile(
            r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+" r"(/[A-Za-z0-9_./{}:-]+)",
            re.IGNORECASE,
        )

        intents: list[EndpointIntent] = []

        for match in pattern.finditer(query):
            method = match.group(1).upper()

            path = match.group(2).rstrip(".,;:!?")

            if not path:
                continue

            intent = EndpointIntent(
                method=method,
                path=path,
            )

            if intent not in intents:
                intents.append(intent)

        return intents

    @staticmethod
    def _apply_endpoint_intent_filter(
        search_results: list[VectorSearchResult],
        intents: list[EndpointIntent],
    ) -> list[VectorSearchResult]:
        """
        Prefer vector results matching explicitly referenced endpoints.

        When the query explicitly references an endpoint, only exact
        method/path matches are considered valid context.

        If no vector result matches an explicit endpoint reference,
        return an empty result instead of falling back to semantically
        similar but unrelated endpoints.
        """

        matching_results = [
            result
            for result in search_results
            if any(
                (
                    str(result.record.metadata.get("method", "")).upper()
                    == intent.method
                    and result.record.metadata.get("path") == intent.path
                )
                for intent in intents
            )
        ]

        return matching_results

    def _reconstruct_endpoint_results(
        self,
        search_results: list[VectorSearchResult],
        limit: int,
    ) -> list[RetrievalResult]:
        """
        Group retrieved chunks by endpoint and reconstruct endpoint context.

        The highest-scoring chunk determines the endpoint's ranking score.
        Chunks are ordered by chunk_index before their content is joined.
        """

        grouped: dict[tuple[Any, Any], list[VectorSearchResult]] = {}

        for result in search_results:
            metadata = result.record.metadata

            specification_id = metadata.get("specification_id")
            endpoint_id = metadata.get("endpoint_id")

            # Endpoint-aware reconstruction requires an endpoint ID.
            # Records without one remain individually retrievable.
            if endpoint_id is None:
                key = (
                    specification_id,
                    result.record.id,
                )
            else:
                key = (
                    specification_id,
                    endpoint_id,
                )

            grouped.setdefault(key, []).append(result)

        ranked_groups = sorted(
            grouped.values(),
            key=self._group_score,
            reverse=True,
        )

        results: list[RetrievalResult] = []

        for group in ranked_groups[:limit]:
            results.append(self._build_retrieval_result(group))

        return results

    @staticmethod
    def _group_score(
        group: list[VectorSearchResult],
    ) -> float:
        """
        Return the strongest similarity score within an endpoint group.
        """

        return max(result.score for result in group)

    @staticmethod
    def _build_retrieval_result(
        group: list[VectorSearchResult],
    ) -> RetrievalResult:
        """
        Reconstruct one endpoint from its retrieved chunks.
        """

        ordered_group = sorted(
            group,
            key=lambda result: result.record.metadata.get(
                "chunk_index",
                0,
            ),
        )

        first = ordered_group[0]

        content = "\n".join(result.record.content for result in ordered_group)

        metadata = dict(first.record.metadata)

        return RetrievalResult(
            content=content,
            score=RAGRetrievalService._group_score(group),
            metadata=metadata,
        )

    @staticmethod
    def _to_retrieval_result(
        result: VectorSearchResult,
    ) -> RetrievalResult:
        """
        Convert a vector-store result into an application-level result.

        Kept as a dedicated helper for compatibility with existing
        retrieval-service behavior and tests.
        """

        return RetrievalResult(
            content=result.record.content,
            score=result.score,
            metadata=dict(result.record.metadata),
        )

import pytest

from app.rag.embeddings import EmbeddingProvider
from app.rag.in_memory_vector_store import InMemoryVectorStore
from app.rag.retrieval_service import RAGRetrievalService
from app.rag.vector_store import VectorRecord


class FakeEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimension: int = 3) -> None:
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> list[float]:
        normalized = text.strip().lower()

        if not normalized:
            raise ValueError("Text cannot be empty.")

        if "user" in normalized:
            return [1.0, 0.0, 0.0]

        if "order" in normalized:
            return [0.0, 1.0, 0.0]

        return [0.0, 0.0, 1.0]

    def embed_batch(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return [self.embed(text) for text in texts]


def create_store() -> InMemoryVectorStore:
    store = InMemoryVectorStore(dimension=3)

    store.add_batch(
        [
            VectorRecord(
                id="users",
                vector=[1.0, 0.0, 0.0],
                content="POST /users creates a new user.",
                metadata={
                    "specification_id": 1,
                    "endpoint_id": 10,
                    "path": "/users",
                    "method": "POST",
                },
            ),
            VectorRecord(
                id="orders",
                vector=[0.0, 1.0, 0.0],
                content="GET /orders returns orders.",
                metadata={
                    "specification_id": 1,
                    "endpoint_id": 20,
                    "path": "/orders",
                    "method": "GET",
                },
            ),
            VectorRecord(
                id="products",
                vector=[0.0, 0.0, 1.0],
                content="GET /products returns products.",
                metadata={
                    "specification_id": 1,
                    "endpoint_id": 30,
                    "path": "/products",
                    "method": "GET",
                },
            ),
        ]
    )

    return store


def test_retrieve_returns_most_relevant_context() -> None:
    provider = FakeEmbeddingProvider()
    store = create_store()

    service = RAGRetrievalService(
        embedding_provider=provider,
        vector_store=store,
    )

    results = service.retrieve(
        "How do I create a user?",
        limit=1,
    )

    assert len(results) == 1
    assert results[0].content == "POST /users creates a new user."
    assert results[0].metadata["path"] == "/users"
    assert results[0].metadata["method"] == "POST"
    assert results[0].score == pytest.approx(1.0)


def test_retrieve_returns_results_in_similarity_order() -> None:
    provider = FakeEmbeddingProvider()
    store = create_store()

    service = RAGRetrievalService(
        embedding_provider=provider,
        vector_store=store,
    )

    results = service.retrieve(
        "Show me the user endpoint.",
        limit=3,
    )

    assert len(results) == 3
    assert results[0].metadata["endpoint_id"] == 10
    assert results[0].score >= results[1].score
    assert results[1].score >= results[2].score


def test_retrieve_respects_limit() -> None:
    provider = FakeEmbeddingProvider()
    store = create_store()

    service = RAGRetrievalService(
        embedding_provider=provider,
        vector_store=store,
    )

    results = service.retrieve(
        "user",
        limit=2,
    )

    assert len(results) == 2


def test_retrieve_from_empty_store_returns_empty_list() -> None:
    provider = FakeEmbeddingProvider()
    store = InMemoryVectorStore(dimension=3)

    service = RAGRetrievalService(
        embedding_provider=provider,
        vector_store=store,
    )

    results = service.retrieve("user")

    assert results == []


def test_retrieve_rejects_empty_query() -> None:
    provider = FakeEmbeddingProvider()
    store = create_store()

    service = RAGRetrievalService(
        embedding_provider=provider,
        vector_store=store,
    )

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        service.retrieve("   ")


def test_retrieve_rejects_invalid_limit() -> None:
    provider = FakeEmbeddingProvider()
    store = create_store()

    service = RAGRetrievalService(
        embedding_provider=provider,
        vector_store=store,
    )

    with pytest.raises(
        ValueError,
        match="Retrieval limit must be greater than zero",
    ):
        service.retrieve(
            "user",
            limit=0,
        )


def test_retrieval_service_rejects_dimension_mismatch() -> None:
    provider = FakeEmbeddingProvider(dimension=3)
    store = InMemoryVectorStore(dimension=4)

    with pytest.raises(
        ValueError,
        match="Embedding provider dimension must match vector store dimension",
    ):
        RAGRetrievalService(
            embedding_provider=provider,
            vector_store=store,
        )


def test_retrieval_result_metadata_is_copied() -> None:
    provider = FakeEmbeddingProvider()
    store = create_store()

    service = RAGRetrievalService(
        embedding_provider=provider,
        vector_store=store,
    )

    results = service.retrieve(
        "user",
        limit=1,
    )

    results[0].metadata["path"] = "/changed"

    second_results = service.retrieve(
        "user",
        limit=1,
    )

    assert second_results[0].metadata["path"] == "/users"

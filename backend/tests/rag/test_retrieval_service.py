import pytest
from app.rag.embeddings import EmbeddingProvider
from app.rag.in_memory_vector_store import InMemoryVectorStore
from app.rag.retrieval_service import (
    EndpointIntent,
    RAGRetrievalService,
)
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


def test_retrieve_reconstructs_multiple_chunks_for_same_endpoint() -> None:
    provider = FakeEmbeddingProvider()
    store = InMemoryVectorStore(dimension=3)

    store.add_batch(
        [
            VectorRecord(
                id="users-0",
                vector=[1.0, 0.0, 0.0],
                content="API: User API\nEndpoint: GET /users",
                metadata={
                    "specification_id": 1,
                    "endpoint_id": 10,
                    "chunk_index": 0,
                    "path": "/users",
                    "method": "GET",
                    "operation_id": "listUsers",
                },
            ),
            VectorRecord(
                id="users-1",
                vector=[1.0, 0.0, 0.0],
                content="Parameters:\npage: integer",
                metadata={
                    "specification_id": 1,
                    "endpoint_id": 10,
                    "chunk_index": 1,
                    "path": "/users",
                    "method": "GET",
                    "operation_id": "listUsers",
                },
            ),
            VectorRecord(
                id="users-2",
                vector=[1.0, 0.0, 0.0],
                content="Responses:\n200: Users returned",
                metadata={
                    "specification_id": 1,
                    "endpoint_id": 10,
                    "chunk_index": 2,
                    "path": "/users",
                    "method": "GET",
                    "operation_id": "listUsers",
                },
            ),
        ]
    )

    service = RAGRetrievalService(
        embedding_provider=provider,
        vector_store=store,
    )

    results = service.retrieve(
        "How do I get users?",
        limit=1,
    )

    assert len(results) == 1

    result = results[0]

    assert result.content == (
        "API: User API\n"
        "Endpoint: GET /users\n"
        "Parameters:\n"
        "page: integer\n"
        "Responses:\n"
        "200: Users returned"
    )

    assert result.metadata["endpoint_id"] == 10
    assert result.metadata["path"] == "/users"
    assert result.metadata["method"] == "GET"
    assert result.metadata["operation_id"] == "listUsers"


def test_retrieve_keeps_different_endpoints_separate() -> None:
    provider = FakeEmbeddingProvider()
    store = InMemoryVectorStore(dimension=3)

    store.add_batch(
        [
            VectorRecord(
                id="users-0",
                vector=[1.0, 0.0, 0.0],
                content="GET /users",
                metadata={
                    "specification_id": 1,
                    "endpoint_id": 10,
                    "chunk_index": 0,
                    "path": "/users",
                    "method": "GET",
                },
            ),
            VectorRecord(
                id="orders-0",
                vector=[0.0, 1.0, 0.0],
                content="GET /orders",
                metadata={
                    "specification_id": 1,
                    "endpoint_id": 20,
                    "chunk_index": 0,
                    "path": "/orders",
                    "method": "GET",
                },
            ),
        ]
    )

    service = RAGRetrievalService(
        embedding_provider=provider,
        vector_store=store,
    )

    results = service.retrieve(
        "user",
        limit=2,
    )

    assert len(results) == 2

    assert results[0].metadata["endpoint_id"] == 10
    assert results[1].metadata["endpoint_id"] == 20

    assert results[0].content == "GET /users"
    assert results[1].content == "GET /orders"


def test_extract_endpoint_intents_returns_single_endpoint() -> None:
    intents = RAGRetrievalService._extract_endpoint_intents(
        "What parameters does GET /products/{product_id} require?"
    )

    assert intents == [
        EndpointIntent(
            method="GET",
            path="/products/{product_id}",
        )
    ]


def test_extract_endpoint_intents_returns_multiple_endpoints() -> None:
    intents = RAGRetrievalService._extract_endpoint_intents(
        "What is the difference between GET /products/{product_id} "
        "and POST /products/{product_id}?"
    )

    assert intents == [
        EndpointIntent(
            method="GET",
            path="/products/{product_id}",
        ),
        EndpointIntent(
            method="POST",
            path="/products/{product_id}",
        ),
    ]


def test_extract_endpoint_intents_is_case_insensitive() -> None:
    intents = RAGRetrievalService._extract_endpoint_intents(
        "Does get /users require authentication?"
    )

    assert intents == [
        EndpointIntent(
            method="GET",
            path="/users",
        )
    ]


def test_extract_endpoint_intents_returns_empty_for_generic_query() -> None:
    intents = RAGRetrievalService._extract_endpoint_intents("How do I create a user?")

    assert intents == []


def test_extract_endpoint_intents_removes_trailing_sentence_punctuation() -> None:
    intents = RAGRetrievalService._extract_endpoint_intents(
        "Generate positive test cases for POST /products/{product_id}."
    )

    assert intents == [
        EndpointIntent(
            method="POST",
            path="/products/{product_id}",
        )
    ]


def test_retrieve_prefers_explicit_http_method_and_path() -> None:
    provider = FakeEmbeddingProvider()
    store = InMemoryVectorStore(dimension=3)

    store.add_batch(
        [
            VectorRecord(
                id="get-products",
                vector=[0.0, 0.0, 1.0],
                content="GET /products/{product_id}",
                metadata={
                    "specification_id": 1,
                    "endpoint_id": 10,
                    "path": "/products/{product_id}",
                    "method": "GET",
                },
            ),
            VectorRecord(
                id="post-products",
                vector=[0.0, 0.0, 1.0],
                content="POST /products/{product_id}",
                metadata={
                    "specification_id": 1,
                    "endpoint_id": 11,
                    "path": "/products/{product_id}",
                    "method": "POST",
                },
            ),
        ]
    )

    service = RAGRetrievalService(
        embedding_provider=provider,
        vector_store=store,
    )

    results = service.retrieve(
        "What parameters does GET /products/{product_id} require?",
        limit=5,
    )

    assert len(results) == 1
    assert results[0].metadata["method"] == "GET"
    assert results[0].metadata["path"] == "/products/{product_id}"


def test_retrieve_keeps_multiple_explicit_endpoints() -> None:
    provider = FakeEmbeddingProvider()
    store = InMemoryVectorStore(dimension=3)

    store.add_batch(
        [
            VectorRecord(
                id="get-products",
                vector=[0.0, 0.0, 1.0],
                content="GET /products/{product_id}",
                metadata={
                    "specification_id": 1,
                    "endpoint_id": 10,
                    "path": "/products/{product_id}",
                    "method": "GET",
                },
            ),
            VectorRecord(
                id="post-products",
                vector=[0.0, 0.0, 1.0],
                content="POST /products/{product_id}",
                metadata={
                    "specification_id": 1,
                    "endpoint_id": 11,
                    "path": "/products/{product_id}",
                    "method": "POST",
                },
            ),
        ]
    )

    service = RAGRetrievalService(
        embedding_provider=provider,
        vector_store=store,
    )

    results = service.retrieve(
        "What is the difference between GET /products/{product_id} "
        "and POST /products/{product_id}?",
        limit=5,
    )

    assert len(results) == 2

    methods = {result.metadata["method"] for result in results}

    assert methods == {"GET", "POST"}


def test_retrieve_returns_empty_when_explicit_endpoint_does_not_match() -> None:
    provider = FakeEmbeddingProvider()
    store = create_store()

    service = RAGRetrievalService(
        embedding_provider=provider,
        vector_store=store,
    )

    results = service.retrieve(
        "What does GET /missing-endpoint do?",
        limit=1,
    )

    assert results == []


def test_retrieve_returns_empty_for_explicit_nonexistent_endpoint() -> None:
    provider = FakeEmbeddingProvider()
    store = create_store()

    service = RAGRetrievalService(
        embedding_provider=provider,
        vector_store=store,
    )

    results = service.retrieve(
        "What parameters does DELETE /products/{product_id} require?",
        limit=5,
        specification_id=1,
    )

    assert results == []

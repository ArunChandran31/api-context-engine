import pytest

from app.rag.chunker import DocumentChunker
from app.rag.embeddings import EmbeddingProvider
from app.rag.in_memory_vector_store import InMemoryVectorStore
from app.rag.indexing_service import RAGIndexingService
from app.rag.models import RAGDocument


class FakeEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dimension: int = 3) -> None:
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("Text cannot be empty.")

        return [1.0] * self._dimension

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]


class BrokenBatchEmbeddingProvider(FakeEmbeddingProvider):
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        return [[1.0] * self.dimension]


def test_index_document_stores_chunks() -> None:
    chunker = DocumentChunker(max_chunk_size=20)
    embedding_provider = FakeEmbeddingProvider(dimension=3)
    vector_store = InMemoryVectorStore(dimension=3)

    service = RAGIndexingService(
        chunker=chunker,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    document = RAGDocument(
        content="API: User API\nEndpoint: POST /users\nSummary: Create user",
        specification_id=1,
        endpoint_id=10,
        path="/users",
        method="POST",
        operation_id="createUser",
        metadata={"api_title": "User API"},
    )

    indexed_count = service.index_document(document)

    assert indexed_count > 0
    assert len(vector_store) == indexed_count


def test_index_document_preserves_metadata() -> None:
    chunker = DocumentChunker(max_chunk_size=1000)
    embedding_provider = FakeEmbeddingProvider(dimension=3)
    vector_store = InMemoryVectorStore(dimension=3)

    service = RAGIndexingService(
        chunker=chunker,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    document = RAGDocument(
        content="Create a new user.",
        specification_id=1,
        endpoint_id=10,
        path="/users",
        method="POST",
        operation_id="createUser",
        metadata={"api_title": "User API"},
    )

    service.index_document(document)

    results = vector_store.search(
        query_vector=[1.0, 1.0, 1.0],
        limit=1,
    )

    record = results[0].record

    assert record.metadata["specification_id"] == 1
    assert record.metadata["endpoint_id"] == 10
    assert record.metadata["chunk_index"] == 0
    assert record.metadata["path"] == "/users"
    assert record.metadata["method"] == "POST"
    assert record.metadata["operation_id"] == "createUser"
    assert record.metadata["api_title"] == "User API"


def test_index_document_generates_deterministic_record_id() -> None:
    chunker = DocumentChunker(max_chunk_size=1000)
    embedding_provider = FakeEmbeddingProvider(dimension=3)
    vector_store = InMemoryVectorStore(dimension=3)

    service = RAGIndexingService(
        chunker=chunker,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    document = RAGDocument(
        content="Create a new user.",
        specification_id=5,
        endpoint_id=12,
    )

    service.index_document(document)

    results = vector_store.search(
        query_vector=[1.0, 1.0, 1.0],
        limit=1,
    )

    assert results[0].record.id == "spec:5:endpoint:12:chunk:0"


def test_index_document_handles_specification_level_document() -> None:
    chunker = DocumentChunker()
    embedding_provider = FakeEmbeddingProvider(dimension=3)
    vector_store = InMemoryVectorStore(dimension=3)

    service = RAGIndexingService(
        chunker=chunker,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    document = RAGDocument(
        content="General API documentation.",
        specification_id=5,
    )

    service.index_document(document)

    results = vector_store.search(
        query_vector=[1.0, 1.0, 1.0],
        limit=1,
    )

    assert results[0].record.id == "spec:5:endpoint:specification:chunk:0"


def test_indexing_service_rejects_dimension_mismatch() -> None:
    chunker = DocumentChunker()
    embedding_provider = FakeEmbeddingProvider(dimension=3)
    vector_store = InMemoryVectorStore(dimension=4)

    with pytest.raises(
        ValueError,
        match="Embedding provider dimension must match vector store dimension",
    ):
        RAGIndexingService(
            chunker=chunker,
            embedding_provider=embedding_provider,
            vector_store=vector_store,
        )


def test_index_document_rejects_embedding_count_mismatch() -> None:
    chunker = DocumentChunker(max_chunk_size=10)
    embedding_provider = BrokenBatchEmbeddingProvider(dimension=3)
    vector_store = InMemoryVectorStore(dimension=3)

    service = RAGIndexingService(
        chunker=chunker,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    document = RAGDocument(
        content="First section\nSecond section\nThird section",
        specification_id=1,
    )

    with pytest.raises(
        ValueError,
        match="unexpected number of embeddings",
    ):
        service.index_document(document)

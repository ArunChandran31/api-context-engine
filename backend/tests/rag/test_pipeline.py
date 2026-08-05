from app.rag.chunker import DocumentChunker
from app.rag.embeddings import EmbeddingProvider
from app.rag.in_memory_vector_store import InMemoryVectorStore
from app.rag.indexing_service import RAGIndexingService
from app.rag.models import RAGDocument
from app.rag.pipeline import RAGPipeline
from app.rag.retrieval_service import RAGRetrievalService


class SemanticFakeEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic embedding provider used for end-to-end RAG tests.

    Each API domain maps to a separate vector direction.
    """

    def __init__(self) -> None:
        self._dimension = 3

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

        if "product" in normalized:
            return [0.0, 0.0, 1.0]

        return [0.33, 0.33, 0.33]

    def embed_batch(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return [self.embed(text) for text in texts]


def create_pipeline() -> tuple[
    RAGPipeline,
    InMemoryVectorStore,
]:
    embedding_provider = SemanticFakeEmbeddingProvider()

    vector_store = InMemoryVectorStore(dimension=embedding_provider.dimension)

    chunker = DocumentChunker(max_chunk_size=1000)

    indexing_service = RAGIndexingService(
        chunker=chunker,
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    retrieval_service = RAGRetrievalService(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    pipeline = RAGPipeline(
        indexing_service=indexing_service,
        retrieval_service=retrieval_service,
    )

    return pipeline, vector_store


def create_documents() -> list[RAGDocument]:
    return [
        RAGDocument(
            content=(
                "POST /users creates a new user account. "
                "Use this endpoint to register a user."
            ),
            specification_id=1,
            endpoint_id=10,
            path="/users",
            method="POST",
            operation_id="createUser",
            metadata={
                "api_title": "Example API",
            },
        ),
        RAGDocument(
            content=(
                "GET /orders returns customer orders. "
                "Use this endpoint to retrieve order information."
            ),
            specification_id=1,
            endpoint_id=20,
            path="/orders",
            method="GET",
            operation_id="listOrders",
            metadata={
                "api_title": "Example API",
            },
        ),
        RAGDocument(
            content=(
                "GET /products returns available products. "
                "Use this endpoint to browse the product catalog."
            ),
            specification_id=1,
            endpoint_id=30,
            path="/products",
            method="GET",
            operation_id="listProducts",
            metadata={
                "api_title": "Example API",
            },
        ),
    ]


def test_pipeline_indexes_multiple_documents() -> None:
    pipeline, vector_store = create_pipeline()

    indexed_count = pipeline.index_documents(create_documents())

    assert indexed_count == 3
    assert len(vector_store) == 3


def test_pipeline_retrieves_user_endpoint() -> None:
    pipeline, _ = create_pipeline()

    pipeline.index_documents(create_documents())

    results = pipeline.retrieve(
        "How can I create a user?",
        limit=1,
    )

    assert len(results) == 1
    assert results[0].metadata["path"] == "/users"
    assert results[0].metadata["method"] == "POST"
    assert results[0].metadata["operation_id"] == "createUser"


def test_pipeline_retrieves_order_endpoint() -> None:
    pipeline, _ = create_pipeline()

    pipeline.index_documents(create_documents())

    results = pipeline.retrieve(
        "How do I retrieve my orders?",
        limit=1,
    )

    assert len(results) == 1
    assert results[0].metadata["path"] == "/orders"
    assert results[0].metadata["method"] == "GET"


def test_pipeline_retrieves_product_endpoint() -> None:
    pipeline, _ = create_pipeline()

    pipeline.index_documents(create_documents())

    results = pipeline.retrieve(
        "Show me the product catalog.",
        limit=1,
    )

    assert len(results) == 1
    assert results[0].metadata["path"] == "/products"


def test_pipeline_preserves_original_content() -> None:
    pipeline, _ = create_pipeline()

    documents = create_documents()

    pipeline.index_documents(documents)

    results = pipeline.retrieve(
        "create user",
        limit=1,
    )

    assert results[0].content == documents[0].content


def test_pipeline_returns_ranked_results() -> None:
    pipeline, _ = create_pipeline()

    pipeline.index_documents(create_documents())

    results = pipeline.retrieve(
        "user",
        limit=3,
    )

    assert len(results) == 3
    assert results[0].metadata["path"] == "/users"

    assert results[0].score >= results[1].score
    assert results[1].score >= results[2].score


def test_pipeline_can_index_single_document() -> None:
    pipeline, vector_store = create_pipeline()

    document = create_documents()[0]

    indexed_count = pipeline.index_document(document)

    assert indexed_count == 1
    assert len(vector_store) == 1


def test_pipeline_retrieval_before_indexing_returns_empty_list() -> None:
    pipeline, _ = create_pipeline()

    results = pipeline.retrieve("How do I create a user?")

    assert results == []

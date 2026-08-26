from unittest.mock import MagicMock

from app.api.rag import get_rag_dependencies
from app.cache.dependencies import get_cache_service
from app.database.models.api_specification import ApiSpecification
from app.database.models.endpoint import Endpoint
from app.main import app
from app.rag.chunker import DocumentChunker
from app.rag.context_generator import ContextGenerator
from app.rag.dependencies import RAGDependencies
from app.rag.embeddings import EmbeddingProvider
from app.rag.in_memory_vector_store import InMemoryVectorStore
from app.rag.indexing_orchestrator import RAGIndexingOrchestrator
from app.rag.indexing_service import RAGIndexingService
from app.rag.persistence import VectorStorePersistence
from app.rag.pipeline import RAGPipeline
from app.rag.retrieval_service import RAGRetrievalService, RetrievalResult
from fastapi.testclient import TestClient


class KeywordEmbeddingProvider(EmbeddingProvider):
    @property
    def dimension(self) -> int:
        return 3

    def embed(self, text: str) -> list[float]:
        normalized = text.lower()

        return [
            float("user" in normalized),
            float("order" in normalized),
            float("product" in normalized),
        ]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]


class FakeVectorStorePersistence(VectorStorePersistence):
    def __init__(self) -> None:
        self.save_count = 0

    def save(self) -> None:
        self.save_count += 1


class FakeCacheService:
    def __init__(self) -> None:
        self._values: dict[str, object] = {}
        self.set_calls: list[tuple[str, object, int]] = []

    def get(self, key: str):
        return self._values.get(key)

    def set(
        self,
        key: str,
        value: object,
        ttl_seconds: int,
    ) -> None:
        self._values[key] = value
        self.set_calls.append(
            (key, value, ttl_seconds),
        )

    def delete(self, key: str) -> bool:
        return self._values.pop(key, None) is not None

    def delete_pattern(self, pattern: str) -> int:
        import fnmatch

        matching_keys = [key for key in self._values if fnmatch.fnmatch(key, pattern)]

        for key in matching_keys:
            del self._values[key]

        return len(matching_keys)


def test_query_rag_returns_retrieved_results() -> None:
    retrieval_service = MagicMock()

    retrieval_service.retrieve.return_value = [
        RetrievalResult(
            content="Endpoint: POST /users",
            score=0.95,
            metadata={
                "path": "/users",
                "method": "POST",
            },
        )
    ]

    dependencies = MagicMock(spec=RAGDependencies)
    dependencies.retrieval_service = retrieval_service
    dependencies.retrieval_limit = 5

    cache = FakeCacheService()

    app.dependency_overrides[get_rag_dependencies] = lambda: dependencies
    app.dependency_overrides[get_cache_service] = lambda: cache

    try:
        client = TestClient(app)

        response = client.post(
            "/api/rag/query",
            json={
                "query": "How do I create a user?",
                "limit": 3,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    assert response.json() == {
        "query": "How do I create a user?",
        "results": [
            {
                "content": "Endpoint: POST /users",
                "score": 0.95,
                "metadata": {
                    "path": "/users",
                    "method": "POST",
                },
            }
        ],
    }

    retrieval_service.retrieve.assert_called_once_with(
        query="How do I create a user?",
        limit=3,
        specification_id=None,
    )


def test_query_rag_returns_cached_results_without_retrieval() -> None:
    retrieval_service = MagicMock()

    cached_results = [
        {
            "content": "Endpoint: POST /users",
            "score": 0.95,
            "metadata": {
                "path": "/users",
                "method": "POST",
            },
        }
    ]

    cache = MagicMock()
    cache.get.return_value = cached_results

    dependencies = MagicMock(spec=RAGDependencies)
    dependencies.retrieval_service = retrieval_service
    dependencies.retrieval_limit = 5

    app.dependency_overrides[get_rag_dependencies] = lambda: dependencies
    app.dependency_overrides[get_cache_service] = lambda: cache

    try:
        client = TestClient(app)

        response = client.post(
            "/api/rag/query",
            json={
                "query": "How do I create a user?",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    assert response.json() == {
        "query": "How do I create a user?",
        "results": cached_results,
    }

    retrieval_service.retrieve.assert_not_called()
    cache.get.assert_called_once()


def test_query_rag_uses_configured_default_limit() -> None:
    retrieval_service = MagicMock()
    retrieval_service.retrieve.return_value = []

    dependencies = MagicMock(spec=RAGDependencies)
    dependencies.retrieval_service = retrieval_service
    dependencies.retrieval_limit = 7

    cache = FakeCacheService()

    app.dependency_overrides[get_rag_dependencies] = lambda: dependencies
    app.dependency_overrides[get_cache_service] = lambda: cache

    try:
        client = TestClient(app)

        response = client.post(
            "/api/rag/query",
            json={
                "query": "How do I list users?",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    retrieval_service.retrieve.assert_called_once_with(
        query="How do I list users?",
        limit=7,
        specification_id=None,
    )


def test_query_rag_rejects_empty_query() -> None:
    dependencies = MagicMock(spec=RAGDependencies)

    cache = FakeCacheService()

    app.dependency_overrides[get_rag_dependencies] = lambda: dependencies
    app.dependency_overrides[get_cache_service] = lambda: cache

    try:
        client = TestClient(app)

        response = client.post(
            "/api/rag/query",
            json={
                "query": "",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_query_rag_rejects_invalid_limit() -> None:
    dependencies = MagicMock(spec=RAGDependencies)

    cache = FakeCacheService()

    app.dependency_overrides[get_rag_dependencies] = lambda: dependencies
    app.dependency_overrides[get_cache_service] = lambda: cache

    try:
        client = TestClient(app)

        response = client.post(
            "/api/rag/query",
            json={
                "query": "How do I create a user?",
                "limit": 0,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_query_rag_returns_empty_results_when_no_context_matches() -> None:
    retrieval_service = MagicMock()
    retrieval_service.retrieve.return_value = []

    dependencies = MagicMock(spec=RAGDependencies)
    dependencies.retrieval_service = retrieval_service
    dependencies.retrieval_limit = 5

    cache = FakeCacheService()

    app.dependency_overrides[get_rag_dependencies] = lambda: dependencies
    app.dependency_overrides[get_cache_service] = lambda: cache

    try:
        client = TestClient(app)

        response = client.post(
            "/api/rag/query",
            json={
                "query": "Unknown API operation",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    assert response.json() == {
        "query": "Unknown API operation",
        "results": [],
    }


def test_index_specification_indexes_generated_documents(
    monkeypatch,
) -> None:
    specification = ApiSpecification(
        id=1,
        title="Users API",
        version="1.0.0",
        description="User management API",
        source_file="users.yaml",
    )

    specification.endpoints = [
        Endpoint(
            id=10,
            api_specification_id=1,
            path="/users",
            method="POST",
            summary="Create user",
            description="Creates a new user.",
            operation_id="createUser",
        ),
        Endpoint(
            id=11,
            api_specification_id=1,
            path="/users/{id}",
            method="GET",
            summary="Get user",
            description="Returns a user.",
            operation_id="getUser",
        ),
    ]

    indexing_service = MagicMock()
    indexing_service.index_document.side_effect = [2, 1]

    persistence = MagicMock()
    cache = FakeCacheService()

    orchestrator = RAGIndexingOrchestrator(
        context_generator=ContextGenerator(),
        indexing_service=indexing_service,
        persistence=persistence,
        cache_service=cache,
    )

    dependencies = MagicMock(spec=RAGDependencies)
    dependencies.indexing_orchestrator = orchestrator

    monkeypatch.setattr(
        "app.api.rag.specification_service.get",
        lambda db, specification_id: specification,
    )

    app.dependency_overrides[get_rag_dependencies] = lambda: dependencies
    app.dependency_overrides[get_cache_service] = lambda: cache

    try:
        client = TestClient(app)

        response = client.post(
            "/api/rag/index/1",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    assert response.json() == {
        "specification_id": 1,
        "documents_indexed": 2,
        "chunks_indexed": 3,
    }

    assert indexing_service.index_document.call_count == 2
    persistence.save.assert_called_once_with()


def test_index_specification_returns_404_when_specification_missing(
    monkeypatch,
) -> None:
    dependencies = MagicMock(spec=RAGDependencies)

    monkeypatch.setattr(
        "app.api.rag.specification_service.get",
        lambda db, specification_id: None,
    )

    cache = FakeCacheService()

    app.dependency_overrides[get_rag_dependencies] = lambda: dependencies
    app.dependency_overrides[get_cache_service] = lambda: cache

    try:
        client = TestClient(app)

        response = client.post(
            "/api/rag/index/999",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404

    assert response.json() == {
        "detail": "API specification with ID 999 was not found.",
    }


def test_index_specification_handles_specification_without_endpoints(
    monkeypatch,
) -> None:
    specification = ApiSpecification(
        id=1,
        title="Empty API",
        version="1.0.0",
        description=None,
        source_file="empty.yaml",
    )

    specification.endpoints = []

    indexing_service = MagicMock()
    persistence = MagicMock()
    cache = FakeCacheService()

    orchestrator = RAGIndexingOrchestrator(
        context_generator=ContextGenerator(),
        indexing_service=indexing_service,
        persistence=persistence,
        cache_service=cache,
    )

    dependencies = MagicMock(spec=RAGDependencies)
    dependencies.indexing_orchestrator = orchestrator

    monkeypatch.setattr(
        "app.api.rag.specification_service.get",
        lambda db, specification_id: specification,
    )

    app.dependency_overrides[get_rag_dependencies] = lambda: dependencies
    app.dependency_overrides[get_cache_service] = lambda: cache

    try:
        client = TestClient(app)

        response = client.post(
            "/api/rag/index/1",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    assert response.json() == {
        "specification_id": 1,
        "documents_indexed": 0,
        "chunks_indexed": 0,
    }

    indexing_service.index_document.assert_not_called()
    persistence.save.assert_called_once_with()


def test_indexed_specification_can_be_queried_through_shared_vector_store(
    monkeypatch,
) -> None:
    specification = ApiSpecification(
        id=1,
        title="Users API",
        version="1.0.0",
        description="User management API",
        source_file="users.yaml",
    )

    specification.endpoints = [
        Endpoint(
            id=10,
            api_specification_id=1,
            path="/users",
            method="POST",
            summary="Create user",
            description="Creates a new user account.",
            operation_id="createUser",
        ),
        Endpoint(
            id=11,
            api_specification_id=1,
            path="/orders",
            method="GET",
            summary="List orders",
            description="Returns customer orders.",
            operation_id="listOrders",
        ),
    ]

    embedding_provider = KeywordEmbeddingProvider()

    vector_store = InMemoryVectorStore(
        dimension=embedding_provider.dimension,
    )

    chunker = DocumentChunker()

    indexing_service = RAGIndexingService(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        chunker=chunker,
    )

    retrieval_service = RAGRetrievalService(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
    )

    persistence = FakeVectorStorePersistence()

    pipeline = RAGPipeline(
        indexing_service=indexing_service,
        retrieval_service=retrieval_service,
    )

    cache = FakeCacheService()

    context_generator = ContextGenerator()

    indexing_orchestrator = RAGIndexingOrchestrator(
        context_generator=context_generator,
        indexing_service=indexing_service,
        persistence=persistence,
        cache_service=cache,
    )

    dependencies = RAGDependencies(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        persistence=persistence,
        chunker=chunker,
        indexing_service=indexing_service,
        retrieval_service=retrieval_service,
        pipeline=pipeline,
        context_generator=context_generator,
        indexing_orchestrator=indexing_orchestrator,
        retrieval_limit=5,
    )

    monkeypatch.setattr(
        "app.api.rag.specification_service.get",
        lambda db, specification_id: specification,
    )

    app.dependency_overrides[get_rag_dependencies] = lambda: dependencies
    app.dependency_overrides[get_cache_service] = lambda: cache

    try:
        client = TestClient(app)

        index_response = client.post(
            "/api/rag/index/1",
        )

        query_response = client.post(
            "/api/rag/query",
            json={
                "query": "How do I create a user?",
                "limit": 1,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert index_response.status_code == 200

    assert index_response.json()["specification_id"] == 1
    assert index_response.json()["documents_indexed"] == 2
    assert index_response.json()["chunks_indexed"] > 0
    assert persistence.save_count == 1

    assert query_response.status_code == 200

    response_body = query_response.json()

    assert response_body["query"] == "How do I create a user?"
    assert len(response_body["results"]) == 1

    result = response_body["results"][0]

    assert result["metadata"]["path"] == "/users"
    assert result["metadata"]["method"] == "POST"
    assert "user" in result["content"].lower()


def test_index_specification_persists_after_success(
    monkeypatch,
) -> None:
    specification = MagicMock()
    specification.id = 1
    specification.title = "Test API"
    specification.version = "1.0"
    specification.description = "Test API description"
    specification.endpoints = []

    indexing_service = MagicMock()
    persistence = MagicMock(spec=VectorStorePersistence)
    cache = FakeCacheService()

    orchestrator = RAGIndexingOrchestrator(
        context_generator=ContextGenerator(),
        indexing_service=indexing_service,
        persistence=persistence,
        cache_service=cache,
    )

    dependencies = MagicMock(spec=RAGDependencies)
    dependencies.indexing_orchestrator = orchestrator

    monkeypatch.setattr(
        "app.api.rag.specification_service.get",
        lambda db, specification_id: specification,
    )

    app.dependency_overrides[get_rag_dependencies] = lambda: dependencies
    app.dependency_overrides[get_cache_service] = lambda: cache

    try:
        client = TestClient(app)

        response = client.post(
            "/api/rag/index/1",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    persistence.save.assert_called_once_with()


def test_index_specification_propagates_persistence_failure(
    monkeypatch,
) -> None:
    specification = MagicMock()
    specification.id = 1
    specification.title = "Test API"
    specification.version = "1.0"
    specification.description = "Test API description"
    specification.endpoints = []

    indexing_service = MagicMock()

    persistence = MagicMock(spec=VectorStorePersistence)
    persistence.save.side_effect = OSError("Unable to persist vector store.")

    cache = FakeCacheService()

    orchestrator = RAGIndexingOrchestrator(
        context_generator=ContextGenerator(),
        indexing_service=indexing_service,
        persistence=persistence,
        cache_service=cache,
    )

    dependencies = MagicMock(spec=RAGDependencies)
    dependencies.indexing_orchestrator = orchestrator

    monkeypatch.setattr(
        "app.api.rag.specification_service.get",
        lambda db, specification_id: specification,
    )

    app.dependency_overrides[get_rag_dependencies] = lambda: dependencies
    app.dependency_overrides[get_cache_service] = lambda: cache

    try:
        client = TestClient(
            app,
            raise_server_exceptions=False,
        )

        response = client.post(
            "/api/rag/index/1",
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    persistence.save.assert_called_once_with()

from dataclasses import dataclass

import pytest

from app.database.models.api_specification import ApiSpecification
from app.database.models.endpoint import Endpoint
from app.rag.context_generator import ContextGenerator
from app.rag.indexing_orchestrator import (
    RAGIndexingOrchestrator,
    RAGIndexingResult,
)
from app.rag.indexing_service import RAGIndexingService
from app.rag.models import RAGDocument
from app.rag.persistence import VectorStorePersistence


@dataclass
class FakeDocument:
    content: str
    specification_id: int
    endpoint_id: int


class FakeContextGenerator(ContextGenerator):
    def __init__(
        self,
        documents: list[RAGDocument] | None = None,
    ) -> None:
        self.documents = documents or []
        self.generated_specification: ApiSpecification | None = None

    def generate(
        self,
        specification: ApiSpecification,
    ) -> list[RAGDocument]:
        self.generated_specification = specification
        return self.documents


class FakeIndexingService(RAGIndexingService):
    def __init__(
        self,
        chunks_by_document: list[int] | None = None,
        deleted_count: int = 0,
    ) -> None:
        self.chunks_by_document = chunks_by_document or []
        self.deleted_count = deleted_count

        self.deleted_specification_ids: list[int] = []
        self.indexed_documents: list[RAGDocument] = []

    def delete_specification(
        self,
        specification_id: int,
    ) -> int:
        self.deleted_specification_ids.append(
            specification_id,
        )

        return self.deleted_count

    def index_document(
        self,
        document: RAGDocument,
    ) -> int:
        self.indexed_documents.append(
            document,
        )

        index = len(self.indexed_documents) - 1

        if index < len(self.chunks_by_document):
            return self.chunks_by_document[index]

        return 0


class FakePersistence(VectorStorePersistence):
    def __init__(self) -> None:
        self.save_calls = 0

    def save(self) -> None:
        self.save_calls += 1


class FakeCacheService:
    def __init__(
        self,
        rag_deleted_count: int = 0,
        ai_deleted_count: int = 0,
    ) -> None:
        self.rag_deleted_count = rag_deleted_count
        self.ai_deleted_count = ai_deleted_count
        self.deleted_patterns: list[str] = []

    def delete_pattern(
        self,
        pattern: str,
    ) -> int:
        self.deleted_patterns.append(pattern)

        if ":rag:query:" in pattern:
            return self.rag_deleted_count

        if ":ai:question:" in pattern:
            return self.ai_deleted_count

        return 0


def build_specification(
    specification_id: int = 1,
    endpoint_count: int = 2,
) -> ApiSpecification:
    specification = ApiSpecification(
        id=specification_id,
        title="Test API",
        version="1.0.0",
        description="Test API specification.",
        source_file="test.yaml",
    )

    specification.endpoints = [
        Endpoint(
            id=index + 10,
            api_specification_id=specification_id,
            path=f"/items/{index}",
            method="get",
            summary=f"Get item {index}",
            description=f"Returns item {index}.",
            operation_id=f"getItem{index}",
        )
        for index in range(endpoint_count)
    ]

    return specification


def build_documents(
    specification_id: int,
    count: int,
) -> list[RAGDocument]:
    return [
        RAGDocument(
            content=f"Document {index}",
            specification_id=specification_id,
            endpoint_id=index + 10,
        )
        for index in range(count)
    ]


def build_orchestrator(
    context_generator: ContextGenerator,
    indexing_service: RAGIndexingService,
    persistence: VectorStorePersistence,
    cache_service: FakeCacheService,
) -> RAGIndexingOrchestrator:
    return RAGIndexingOrchestrator(
        context_generator=context_generator,
        indexing_service=indexing_service,
        persistence=persistence,
        cache_service=cache_service,
    )


def test_index_specification_returns_indexing_result() -> None:
    specification = build_specification(
        specification_id=5,
        endpoint_count=2,
    )

    documents = build_documents(
        specification_id=5,
        count=2,
    )

    context_generator = FakeContextGenerator(
        documents,
    )

    indexing_service = FakeIndexingService(
        chunks_by_document=[2, 3],
    )

    persistence = FakePersistence()

    cache_service = FakeCacheService(
        rag_deleted_count=4,
        ai_deleted_count=0,
    )

    orchestrator = build_orchestrator(
        context_generator=context_generator,
        indexing_service=indexing_service,
        persistence=persistence,
        cache_service=cache_service,
    )

    result = orchestrator.index_specification(
        specification,
    )

    assert isinstance(
        result,
        RAGIndexingResult,
    )

    assert result.specification_id == 5
    assert result.documents_indexed == 2
    assert result.chunks_indexed == 5
    assert result.cache_entries_invalidated == 4

    assert cache_service.deleted_patterns == [
        "api-context-engine:v1:rag:query:*:limit:*:specification:5",
        "api-context-engine:v1:ai:question:*:specification:5:provider:*:model:*",
    ]


def test_index_specification_generates_and_indexes_all_documents() -> None:
    specification = build_specification(
        specification_id=7,
        endpoint_count=3,
    )

    documents = build_documents(
        specification_id=7,
        count=3,
    )

    context_generator = FakeContextGenerator(
        documents,
    )

    indexing_service = FakeIndexingService(
        chunks_by_document=[1, 2, 1],
    )

    persistence = FakePersistence()
    cache_service = FakeCacheService()

    orchestrator = build_orchestrator(
        context_generator=context_generator,
        indexing_service=indexing_service,
        persistence=persistence,
        cache_service=cache_service,
    )

    result = orchestrator.index_specification(
        specification,
    )

    assert context_generator.generated_specification is specification

    assert indexing_service.indexed_documents == documents

    assert result.documents_indexed == 3
    assert result.chunks_indexed == 4


def test_index_specification_deletes_existing_vectors_before_indexing() -> None:
    specification = build_specification(
        specification_id=8,
        endpoint_count=1,
    )

    documents = build_documents(
        specification_id=8,
        count=1,
    )

    context_generator = FakeContextGenerator(
        documents,
    )

    indexing_service = FakeIndexingService(
        chunks_by_document=[2],
        deleted_count=6,
    )

    persistence = FakePersistence()
    cache_service = FakeCacheService()

    orchestrator = build_orchestrator(
        context_generator=context_generator,
        indexing_service=indexing_service,
        persistence=persistence,
        cache_service=cache_service,
    )

    result = orchestrator.index_specification(
        specification,
    )

    assert result.chunks_indexed == 2

    assert indexing_service.deleted_specification_ids == [
        8,
    ]

    assert indexing_service.indexed_documents == documents


def test_index_specification_persists_after_indexing() -> None:
    specification = build_specification(
        specification_id=9,
        endpoint_count=1,
    )

    documents = build_documents(
        specification_id=9,
        count=1,
    )

    context_generator = FakeContextGenerator(
        documents,
    )

    indexing_service = FakeIndexingService(
        chunks_by_document=[1],
    )

    persistence = FakePersistence()
    cache_service = FakeCacheService()

    orchestrator = build_orchestrator(
        context_generator=context_generator,
        indexing_service=indexing_service,
        persistence=persistence,
        cache_service=cache_service,
    )

    orchestrator.index_specification(
        specification,
    )

    assert persistence.save_calls == 1


def test_index_specification_invalidates_specification_cache() -> None:
    specification = build_specification(
        specification_id=10,
        endpoint_count=1,
    )

    documents = build_documents(
        specification_id=10,
        count=1,
    )

    context_generator = FakeContextGenerator(
        documents,
    )

    indexing_service = FakeIndexingService(
        chunks_by_document=[1],
    )

    persistence = FakePersistence()

    cache_service = FakeCacheService(
        rag_deleted_count=3,
        ai_deleted_count=0,
    )

    orchestrator = build_orchestrator(
        context_generator=context_generator,
        indexing_service=indexing_service,
        persistence=persistence,
        cache_service=cache_service,
    )

    result = orchestrator.index_specification(
        specification,
    )

    assert result.cache_entries_invalidated == 3

    assert cache_service.deleted_patterns == [
        "api-context-engine:v1:rag:query:*:limit:*:specification:10",
        "api-context-engine:v1:ai:question:*:specification:10:provider:*:model:*",
    ]


def test_index_specification_handles_empty_specification() -> None:
    specification = build_specification(
        specification_id=11,
        endpoint_count=0,
    )

    context_generator = FakeContextGenerator(
        documents=[],
    )

    indexing_service = FakeIndexingService()

    persistence = FakePersistence()

    cache_service = FakeCacheService(
        rag_deleted_count=2,
        ai_deleted_count=0,
    )

    orchestrator = build_orchestrator(
        context_generator=context_generator,
        indexing_service=indexing_service,
        persistence=persistence,
        cache_service=cache_service,
    )

    result = orchestrator.index_specification(
        specification,
    )

    assert result.specification_id == 11
    assert result.documents_indexed == 0
    assert result.chunks_indexed == 0
    assert result.cache_entries_invalidated == 2

    assert cache_service.deleted_patterns == [
        "api-context-engine:v1:rag:query:*:limit:*:specification:11",
        "api-context-engine:v1:ai:question:*:specification:11:provider:*:model:*",
    ]

    assert indexing_service.deleted_specification_ids == [
        11,
    ]

    assert indexing_service.indexed_documents == []

    assert persistence.save_calls == 1


@pytest.mark.parametrize(
    "specification_id",
    [0, -1],
)
def test_index_specification_rejects_invalid_specification_id(
    specification_id: int,
) -> None:
    specification = build_specification(
        specification_id=specification_id,
        endpoint_count=0,
    )

    context_generator = FakeContextGenerator()

    indexing_service = FakeIndexingService()

    persistence = FakePersistence()

    cache_service = FakeCacheService()

    orchestrator = build_orchestrator(
        context_generator=context_generator,
        indexing_service=indexing_service,
        persistence=persistence,
        cache_service=cache_service,
    )

    with pytest.raises(
        ValueError,
        match="Specification ID must be greater than zero",
    ):
        orchestrator.index_specification(
            specification,
        )

    assert context_generator.generated_specification is None

    assert indexing_service.deleted_specification_ids == []

    assert persistence.save_calls == 0

    assert cache_service.deleted_patterns == []


def test_index_specification_propagates_persistence_failure() -> None:
    specification = build_specification(
        specification_id=12,
        endpoint_count=1,
    )

    documents = build_documents(
        specification_id=12,
        count=1,
    )

    context_generator = FakeContextGenerator(
        documents,
    )

    indexing_service = FakeIndexingService(
        chunks_by_document=[1],
    )

    class BrokenPersistence(VectorStorePersistence):
        def __init__(self) -> None:
            self.save_calls = 0

        def save(self) -> None:
            self.save_calls += 1
            raise RuntimeError(
                "Simulated persistence failure",
            )

    persistence = BrokenPersistence()

    cache_service = FakeCacheService()

    orchestrator = build_orchestrator(
        context_generator=context_generator,
        indexing_service=indexing_service,
        persistence=persistence,
        cache_service=cache_service,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated persistence failure",
    ):
        orchestrator.index_specification(
            specification,
        )

    assert persistence.save_calls == 1

    assert cache_service.deleted_patterns == []

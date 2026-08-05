from pathlib import Path

from app.core.config import Settings
from app.rag.dependencies import (
    RAGDependencies,
    build_rag_dependencies,
)
from app.rag.faiss_vector_store import FAISSVectorStore
from app.rag.pipeline import RAGPipeline
from app.rag.sentence_transformer_provider import (
    SentenceTransformerEmbeddingProvider,
)
from app.rag.vector_store import VectorRecord


def create_settings(
    tmp_path: Path,
) -> Settings:
    return Settings(
        RAG_EMBEDDING_MODEL=("sentence-transformers/all-MiniLM-L6-v2"),
        RAG_VECTOR_STORE_PATH=str(tmp_path),
        RAG_CHUNK_SIZE=750,
        RAG_RETRIEVAL_LIMIT=7,
    )


def test_settings_expose_rag_defaults() -> None:
    settings = Settings()

    assert settings.rag_embedding_model == ("sentence-transformers/all-MiniLM-L6-v2")
    assert settings.rag_vector_store_path == "./data/faiss"
    assert settings.rag_chunk_size == 1000
    assert settings.rag_retrieval_limit == 5


def test_build_returns_rag_dependencies(
    tmp_path: Path,
) -> None:
    dependencies = build_rag_dependencies(create_settings(tmp_path))

    assert isinstance(
        dependencies,
        RAGDependencies,
    )

    assert isinstance(
        dependencies.pipeline,
        RAGPipeline,
    )


def test_build_configures_embedding_provider(
    tmp_path: Path,
) -> None:
    dependencies = build_rag_dependencies(create_settings(tmp_path))

    assert isinstance(
        dependencies.embedding_provider,
        SentenceTransformerEmbeddingProvider,
    )

    assert dependencies.embedding_provider.model_name == (
        "sentence-transformers/all-MiniLM-L6-v2"
    )


def test_build_configures_faiss_store(
    tmp_path: Path,
) -> None:
    dependencies = build_rag_dependencies(create_settings(tmp_path))

    assert isinstance(
        dependencies.vector_store,
        FAISSVectorStore,
    )

    assert (
        dependencies.vector_store.dimension == dependencies.embedding_provider.dimension
    )


def test_build_configures_chunk_size(
    tmp_path: Path,
) -> None:
    dependencies = build_rag_dependencies(create_settings(tmp_path))

    assert dependencies.chunker.max_chunk_size == 750


def test_build_configures_retrieval_limit(
    tmp_path: Path,
) -> None:
    dependencies = build_rag_dependencies(create_settings(tmp_path))

    assert dependencies.retrieval_limit == 7


def test_indexing_and_retrieval_share_embedding_provider(
    tmp_path: Path,
) -> None:
    dependencies = build_rag_dependencies(create_settings(tmp_path))

    assert (
        dependencies.indexing_service._embedding_provider
        is dependencies.embedding_provider
    )

    assert (
        dependencies.retrieval_service._embedding_provider
        is dependencies.embedding_provider
    )


def test_indexing_and_retrieval_share_vector_store(
    tmp_path: Path,
) -> None:
    dependencies = build_rag_dependencies(create_settings(tmp_path))

    assert dependencies.indexing_service._vector_store is dependencies.vector_store

    assert dependencies.retrieval_service._vector_store is dependencies.vector_store


def test_build_loads_existing_persisted_vector_store(
    tmp_path: Path,
) -> None:
    settings = create_settings(tmp_path)

    initial_store = FAISSVectorStore(
        dimension=384,
        storage_path=tmp_path,
    )

    initial_store.add(
        VectorRecord(
            id="persisted-record",
            vector=[1.0] + [0.0] * 383,
            content="Persisted API context",
            metadata={
                "path": "/users",
                "method": "GET",
            },
        )
    )

    initial_store.save()

    dependencies = build_rag_dependencies(settings)

    assert len(dependencies.vector_store) == 1

    results = dependencies.vector_store.search(
        [1.0] + [0.0] * 383,
        limit=1,
    )

    assert results[0].record.id == "persisted-record"
    assert results[0].record.content == "Persisted API context"


def test_build_creates_new_vector_store_when_persistence_is_missing(
    tmp_path: Path,
) -> None:
    dependencies = build_rag_dependencies(create_settings(tmp_path))

    assert isinstance(
        dependencies.vector_store,
        FAISSVectorStore,
    )

    assert len(dependencies.vector_store) == 0

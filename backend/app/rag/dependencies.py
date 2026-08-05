from dataclasses import dataclass

from app.core.config import Settings, get_settings
from app.rag.chunker import DocumentChunker
from app.rag.embeddings import EmbeddingProvider
from app.rag.faiss_vector_store import FAISSVectorStore
from app.rag.indexing_service import RAGIndexingService
from app.rag.pipeline import RAGPipeline
from app.rag.retrieval_service import RAGRetrievalService
from app.rag.sentence_transformer_provider import (
    SentenceTransformerEmbeddingProvider,
)
from app.rag.vector_store import VectorStore


@dataclass(frozen=True)
class RAGDependencies:
    """
    Container for the application's configured RAG components.
    """

    embedding_provider: EmbeddingProvider
    vector_store: VectorStore
    chunker: DocumentChunker
    indexing_service: RAGIndexingService
    retrieval_service: RAGRetrievalService
    pipeline: RAGPipeline
    retrieval_limit: int


def build_rag_dependencies(
    settings: Settings | None = None,
) -> RAGDependencies:
    """
    Build the application's RAG dependency graph.

    A Settings instance may be supplied explicitly for tests or
    alternate runtime configurations.
    """

    application_settings = settings or get_settings()

    embedding_provider = SentenceTransformerEmbeddingProvider(
        model_name=application_settings.rag_embedding_model,
    )

    vector_store = FAISSVectorStore(
        dimension=embedding_provider.dimension,
        storage_path=application_settings.rag_vector_store_path,
    )

    chunker = DocumentChunker(
        max_chunk_size=application_settings.rag_chunk_size,
    )

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

    return RAGDependencies(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        chunker=chunker,
        indexing_service=indexing_service,
        retrieval_service=retrieval_service,
        pipeline=pipeline,
        retrieval_limit=application_settings.rag_retrieval_limit,
    )

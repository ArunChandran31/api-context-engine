from app.rag.chunker import DocumentChunker
from app.rag.embeddings import EmbeddingProvider
from app.rag.models import RAGChunk, RAGDocument
from app.rag.vector_store import VectorRecord, VectorStore


class RAGIndexingService:
    """
    Coordinates document chunking, embedding generation,
    and vector storage.
    """

    def __init__(
        self,
        chunker: DocumentChunker,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        if embedding_provider.dimension != vector_store.dimension:
            raise ValueError(
                "Embedding provider dimension must match vector store dimension."
            )

        self._chunker = chunker
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    def index_document(
        self,
        document: RAGDocument,
    ) -> int:
        """
        Chunk, embed, and store a RAG document.

        Returns the number of chunks indexed.
        """

        chunks = self._chunker.chunk(document)

        if not chunks:
            return 0

        embeddings = self._embedding_provider.embed_batch(
            [chunk.content for chunk in chunks]
        )

        if len(embeddings) != len(chunks):
            raise ValueError(
                "Embedding provider returned an unexpected number of embeddings."
            )

        records = [
            self._create_record(chunk, embedding)
            for chunk, embedding in zip(
                chunks,
                embeddings,
                strict=True,
            )
        ]

        self._vector_store.add_batch(records)

        return len(records)

    @staticmethod
    def _create_record(
        chunk: RAGChunk,
        embedding: list[float],
    ) -> VectorRecord:
        metadata = {
            **chunk.metadata,
            "specification_id": chunk.specification_id,
            "endpoint_id": chunk.endpoint_id,
            "chunk_index": chunk.chunk_index,
            "path": chunk.path,
            "method": chunk.method,
            "operation_id": chunk.operation_id,
        }

        return VectorRecord(
            id=RAGIndexingService._build_record_id(chunk),
            vector=embedding,
            content=chunk.content,
            metadata=metadata,
        )

    @staticmethod
    def _build_record_id(
        chunk: RAGChunk,
    ) -> str:
        endpoint_part = (
            str(chunk.endpoint_id) if chunk.endpoint_id is not None else "specification"
        )

        return (
            f"spec:{chunk.specification_id}:"
            f"endpoint:{endpoint_part}:"
            f"chunk:{chunk.chunk_index}"
        )

    def delete_specification(
        self,
        specification_id: int,
    ) -> int:
        """
        Delete all indexed chunks belonging to a specification.

        Returns the number of deleted chunks.
        """

        if specification_id <= 0:
            raise ValueError("Specification ID must be greater than zero.")

        return self._vector_store.delete_by_specification_id(
            specification_id,
        )

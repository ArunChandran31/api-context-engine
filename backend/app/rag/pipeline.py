from app.rag.indexing_service import RAGIndexingService
from app.rag.models import RAGDocument
from app.rag.retrieval_service import (
    RAGRetrievalService,
    RetrievalResult,
)


class RAGPipeline:
    """
    High-level facade for RAG indexing and retrieval.

    Coordinates the indexing and retrieval services without exposing
    their underlying embedding or vector-store implementations.
    """

    def __init__(
        self,
        indexing_service: RAGIndexingService,
        retrieval_service: RAGRetrievalService,
    ) -> None:
        self._indexing_service = indexing_service
        self._retrieval_service = retrieval_service

    def index_document(
        self,
        document: RAGDocument,
    ) -> int:
        """
        Index a single RAG document.

        Returns the number of generated and stored chunks.
        """

        return self._indexing_service.index_document(document)

    def index_documents(
        self,
        documents: list[RAGDocument],
    ) -> int:
        """
        Index multiple RAG documents.

        Returns the total number of generated and stored chunks.
        """

        return sum(
            self._indexing_service.index_document(document) for document in documents
        )

    def retrieve(
        self,
        query: str,
        limit: int = 5,
    ) -> list[RetrievalResult]:
        """
        Retrieve the most relevant indexed API context.
        """

        return self._retrieval_service.retrieve(
            query=query,
            limit=limit,
        )

from pydantic import BaseModel


class UploadRAGResponse(BaseModel):
    """
    RAG indexing statistics returned after successfully
    indexing an uploaded OpenAPI specification.
    """

    documents_indexed: int
    chunks_indexed: int
    cache_entries_invalidated: int


class UploadResponse(BaseModel):
    """
    Response returned after successfully ingesting
    and indexing an OpenAPI specification.
    """

    specification_id: int
    title: str
    version: str | None = None
    endpoints_created: int
    filename: str
    rag: UploadRAGResponse

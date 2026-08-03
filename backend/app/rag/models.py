from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RAGDocument:
    """
    Semantic representation of API information before chunking.

    A document contains human-readable content together with metadata
    identifying the API specification and endpoint it originated from.
    """

    content: str
    specification_id: int
    endpoint_id: int | None = None
    path: str | None = None
    method: str | None = None
    operation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError("RAG document content cannot be empty.")

        if self.specification_id <= 0:
            raise ValueError("Specification ID must be positive.")

        if self.endpoint_id is not None and self.endpoint_id <= 0:
            raise ValueError("Endpoint ID must be positive when provided.")


@dataclass(frozen=True)
class RAGChunk:
    """
    Chunk of a RAG document suitable for embedding and retrieval.
    """

    content: str
    specification_id: int
    chunk_index: int
    endpoint_id: int | None = None
    path: str | None = None
    method: str | None = None
    operation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError("RAG chunk content cannot be empty.")

        if self.specification_id <= 0:
            raise ValueError("Specification ID must be positive.")

        if self.endpoint_id is not None and self.endpoint_id <= 0:
            raise ValueError("Endpoint ID must be positive when provided.")

        if self.chunk_index < 0:
            raise ValueError("Chunk index cannot be negative.")

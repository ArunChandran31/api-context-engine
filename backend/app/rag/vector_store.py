from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VectorRecord:
    """
    A vector and its associated retrieval metadata.
    """

    id: str
    vector: list[float]
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Vector record ID cannot be empty.")

        if not self.vector:
            raise ValueError("Vector cannot be empty.")

        if not self.content.strip():
            raise ValueError("Vector record content cannot be empty.")


@dataclass(frozen=True)
class VectorSearchResult:
    """
    A single result returned by vector similarity search.
    """

    record: VectorRecord
    score: float


class VectorStore(ABC):
    """
    Abstract storage interface for vector embeddings.

    RAG services depend on this contract rather than a specific
    vector database or indexing implementation.
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        Return the dimensionality expected by the vector store.
        """

    @abstractmethod
    def add(self, record: VectorRecord) -> None:
        """
        Add a single vector record.
        """

    @abstractmethod
    def add_batch(self, records: list[VectorRecord]) -> None:
        """
        Add multiple vector records.
        """

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        limit: int = 5,
    ) -> list[VectorSearchResult]:
        """
        Return the most similar vector records.
        """

    @abstractmethod
    def delete(self, record_id: str) -> bool:
        """
        Delete a vector record.

        Returns True when a record was deleted and False when the
        requested record did not exist.
        """

    @abstractmethod
    def delete_by_specification_id(
        self,
        specification_id: int,
    ) -> int:
        """
        Delete all vector records belonging to a specification.

        Returns the number of deleted records.
        """

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all records from the store.
        """

    @abstractmethod
    def __len__(self) -> int:
        """
        Return the number of records currently stored.
        """

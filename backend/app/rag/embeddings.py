from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """
    Abstract interface for converting text into vector embeddings.

    RAG components depend on this abstraction rather than a specific
    embedding model or external provider.
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        Return the dimensionality of vectors produced by this provider.
        """

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """
        Generate an embedding for a single text input.
        """

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple text inputs.
        """

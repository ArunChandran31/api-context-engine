from abc import ABC, abstractmethod


class VectorStorePersistence(ABC):
    """
    Abstract persistence contract for vector stores that support
    durable storage.
    """

    @abstractmethod
    def save(self) -> None:
        """
        Persist the current vector-store state.
        """

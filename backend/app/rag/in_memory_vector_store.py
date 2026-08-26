import math

from app.rag.vector_store import (
    VectorRecord,
    VectorSearchResult,
    VectorStore,
)


class InMemoryVectorStore(VectorStore):
    """
    In-memory vector store using cosine similarity.

    Intended for testing, local development, and small datasets.
    """

    def __init__(self, dimension: int) -> None:
        if dimension <= 0:
            raise ValueError("Vector dimension must be greater than zero.")

        self._dimension = dimension
        self._records: dict[str, VectorRecord] = {}

    @property
    def dimension(self) -> int:
        return self._dimension

    def add(self, record: VectorRecord) -> None:
        self._validate_vector(record.vector)
        self._records[record.id] = record

    def add_batch(self, records: list[VectorRecord]) -> None:
        for record in records:
            self.add(record)

    def search(
        self,
        query_vector: list[float],
        limit: int = 5,
    ) -> list[VectorSearchResult]:
        self._validate_vector(query_vector)

        if limit <= 0:
            raise ValueError("Search limit must be greater than zero.")

        results = [
            VectorSearchResult(
                record=record,
                score=self._cosine_similarity(
                    query_vector,
                    record.vector,
                ),
            )
            for record in self._records.values()
        ]

        results.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return results[:limit]

    def delete(self, record_id: str) -> bool:
        if record_id not in self._records:
            return False

        del self._records[record_id]
        return True

    def delete_by_specification_id(
        self,
        specification_id: int,
    ) -> int:
        """
        Delete all vector records belonging to a specification.

        Returns the number of deleted records.
        """

        if specification_id <= 0:
            raise ValueError("Specification ID must be greater than zero.")

        records_to_delete = [
            record_id
            for record_id, record in self._records.items()
            if record.metadata.get("specification_id") == specification_id
        ]

        for record_id in records_to_delete:
            del self._records[record_id]

        return len(records_to_delete)

    def clear(self) -> None:
        self._records.clear()

    def __len__(self) -> int:
        return len(self._records)

    def _validate_vector(self, vector: list[float]) -> None:
        if len(vector) != self._dimension:
            raise ValueError(
                f"Expected vector dimension {self._dimension}, "
                f"received {len(vector)}."
            )

    @staticmethod
    def _cosine_similarity(
        first: list[float],
        second: list[float],
    ) -> float:
        dot_product = sum(
            first_value * second_value
            for first_value, second_value in zip(
                first,
                second,
                strict=True,
            )
        )

        first_norm = math.sqrt(sum(value * value for value in first))

        second_norm = math.sqrt(sum(value * value for value in second))

        if first_norm == 0.0 or second_norm == 0.0:
            return 0.0

        return dot_product / (first_norm * second_norm)

import pickle
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from app.rag.persistence import VectorStorePersistence
from app.rag.vector_store import (
    VectorRecord,
    VectorSearchResult,
    VectorStore,
)


class FAISSVectorStore(VectorStore, VectorStorePersistence):
    """
    FAISS-backed vector store using cosine similarity.

    Vectors are normalized before being stored and searched using
    inner-product similarity, which is equivalent to cosine similarity
    for normalized vectors.
    """

    INDEX_FILENAME = "vectors.faiss"
    RECORDS_FILENAME = "records.pkl"

    def __init__(
        self,
        dimension: int,
        storage_path: str | Path,
    ) -> None:
        if dimension <= 0:
            raise ValueError("Dimension must be greater than zero.")

        self._dimension = dimension
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._index = faiss.IndexFlatIP(dimension)
        self._records: list[VectorRecord] = []

    @property
    def dimension(self) -> int:
        return self._dimension

    def __len__(self) -> int:
        return len(self._records)

    def add(self, record: VectorRecord) -> None:
        self._validate_vector(record.vector)

        existing_index = self._find_record_index(record.id)

        if existing_index is not None:
            self._records[existing_index] = record
            self._rebuild_index()
            return

        vector = self._prepare_vector(record.vector)

        self._index.add(vector)
        self._records.append(record)

    def add_batch(
        self,
        records: list[VectorRecord],
    ) -> None:
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

        if not self._records:
            return []

        query = self._prepare_vector(query_vector)

        result_count = min(
            limit,
            len(self._records),
        )

        scores, indices = self._index.search(
            query,
            result_count,
        )

        results: list[VectorSearchResult] = []

        for score, index in zip(
            scores[0],
            indices[0],
            strict=True,
        ):
            if index < 0:
                continue

            results.append(
                VectorSearchResult(
                    record=self._records[int(index)],
                    score=float(score),
                )
            )

        return results

    def delete(self, record_id: str) -> bool:
        existing_index = self._find_record_index(record_id)

        if existing_index is None:
            return False

        del self._records[existing_index]
        self._rebuild_index()

        return True

    def clear(self) -> None:
        self._records.clear()
        self._index = faiss.IndexFlatIP(self._dimension)

    def save(self) -> None:
        """
        Persist the FAISS index and associated records to disk.
        """

        faiss.write_index(
            self._index,
            str(self._storage_path / self.INDEX_FILENAME),
        )

        with (self._storage_path / self.RECORDS_FILENAME).open("wb") as file:
            pickle.dump(
                {
                    "dimension": self._dimension,
                    "records": self._records,
                },
                file,
            )

    @classmethod
    def load(
        cls,
        storage_path: str | Path,
    ) -> "FAISSVectorStore":
        """
        Load a previously persisted vector store.
        """

        path = Path(storage_path)

        index_path = path / cls.INDEX_FILENAME
        records_path = path / cls.RECORDS_FILENAME

        if not index_path.exists() or not records_path.exists():
            raise FileNotFoundError("Persisted FAISS vector store was not found.")

        with records_path.open("rb") as file:
            data: dict[str, Any] = pickle.load(file)

        dimension = data["dimension"]

        store = cls(
            dimension=dimension,
            storage_path=path,
        )

        store._index = faiss.read_index(str(index_path))
        store._records = data["records"]

        if store._index.d != dimension:
            raise ValueError("Persisted FAISS index dimension does not match metadata.")

        if store._index.ntotal != len(store._records):
            raise ValueError("Persisted FAISS index and records are inconsistent.")

        return store

    def _validate_vector(
        self,
        vector: list[float],
    ) -> None:
        if len(vector) != self._dimension:
            raise ValueError("Vector dimension does not match vector store dimension.")

    def _prepare_vector(
        self,
        vector: list[float],
    ) -> np.ndarray:
        array = np.asarray(
            [vector],
            dtype=np.float32,
        )

        faiss.normalize_L2(array)

        return array

    def _find_record_index(
        self,
        record_id: str,
    ) -> int | None:
        for index, record in enumerate(self._records):
            if record.id == record_id:
                return index

        return None

    def _rebuild_index(self) -> None:
        self._index = faiss.IndexFlatIP(self._dimension)

        if not self._records:
            return

        vectors = np.asarray(
            [record.vector for record in self._records],
            dtype=np.float32,
        )

        faiss.normalize_L2(vectors)

        self._index.add(vectors)

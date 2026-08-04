from pathlib import Path

import pytest

from app.rag.faiss_vector_store import FAISSVectorStore
from app.rag.vector_store import VectorRecord


def create_record(
    record_id: str,
    vector: list[float],
    content: str,
) -> VectorRecord:
    return VectorRecord(
        id=record_id,
        vector=vector,
        content=content,
        metadata={
            "record_id": record_id,
        },
    )


def test_store_exposes_dimension(
    tmp_path: Path,
) -> None:
    store = FAISSVectorStore(
        dimension=3,
        storage_path=tmp_path,
    )

    assert store.dimension == 3


def test_store_rejects_invalid_dimension(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="Dimension must be greater than zero",
    ):
        FAISSVectorStore(
            dimension=0,
            storage_path=tmp_path,
        )


def test_add_and_search(
    tmp_path: Path,
) -> None:
    store = FAISSVectorStore(
        dimension=3,
        storage_path=tmp_path,
    )

    store.add(
        create_record(
            "users",
            [1.0, 0.0, 0.0],
            "User endpoint",
        )
    )

    store.add(
        create_record(
            "orders",
            [0.0, 1.0, 0.0],
            "Order endpoint",
        )
    )

    results = store.search(
        [1.0, 0.0, 0.0],
        limit=1,
    )

    assert len(results) == 1
    assert results[0].record.id == "users"
    assert results[0].score == pytest.approx(1.0)


def test_search_returns_ranked_results(
    tmp_path: Path,
) -> None:
    store = FAISSVectorStore(
        dimension=3,
        storage_path=tmp_path,
    )

    store.add_batch(
        [
            create_record(
                "first",
                [1.0, 0.0, 0.0],
                "First",
            ),
            create_record(
                "second",
                [0.8, 0.2, 0.0],
                "Second",
            ),
            create_record(
                "third",
                [0.0, 1.0, 0.0],
                "Third",
            ),
        ]
    )

    results = store.search(
        [1.0, 0.0, 0.0],
        limit=3,
    )

    assert [result.record.id for result in results] == [
        "first",
        "second",
        "third",
    ]

    assert results[0].score >= results[1].score
    assert results[1].score >= results[2].score


def test_search_empty_store_returns_empty_list(
    tmp_path: Path,
) -> None:
    store = FAISSVectorStore(
        dimension=3,
        storage_path=tmp_path,
    )

    assert store.search([1.0, 0.0, 0.0]) == []


def test_search_rejects_wrong_dimension(
    tmp_path: Path,
) -> None:
    store = FAISSVectorStore(
        dimension=3,
        storage_path=tmp_path,
    )

    with pytest.raises(
        ValueError,
        match="Vector dimension does not match",
    ):
        store.search(
            [1.0, 0.0],
        )


def test_add_replaces_existing_record(
    tmp_path: Path,
) -> None:
    store = FAISSVectorStore(
        dimension=3,
        storage_path=tmp_path,
    )

    store.add(
        create_record(
            "users",
            [1.0, 0.0, 0.0],
            "Old content",
        )
    )

    store.add(
        create_record(
            "users",
            [0.0, 1.0, 0.0],
            "New content",
        )
    )

    assert len(store) == 1

    results = store.search(
        [0.0, 1.0, 0.0],
        limit=1,
    )

    assert results[0].record.content == "New content"


def test_delete_existing_record(
    tmp_path: Path,
) -> None:
    store = FAISSVectorStore(
        dimension=3,
        storage_path=tmp_path,
    )

    store.add(
        create_record(
            "users",
            [1.0, 0.0, 0.0],
            "User endpoint",
        )
    )

    assert store.delete("users") is True
    assert len(store) == 0


def test_delete_missing_record_returns_false(
    tmp_path: Path,
) -> None:
    store = FAISSVectorStore(
        dimension=3,
        storage_path=tmp_path,
    )

    assert store.delete("missing") is False


def test_clear_removes_records(
    tmp_path: Path,
) -> None:
    store = FAISSVectorStore(
        dimension=3,
        storage_path=tmp_path,
    )

    store.add(
        create_record(
            "users",
            [1.0, 0.0, 0.0],
            "User endpoint",
        )
    )

    store.clear()

    assert len(store) == 0
    assert store.search([1.0, 0.0, 0.0]) == []


def test_save_and_load_preserves_records(
    tmp_path: Path,
) -> None:
    store = FAISSVectorStore(
        dimension=3,
        storage_path=tmp_path,
    )

    store.add_batch(
        [
            create_record(
                "users",
                [1.0, 0.0, 0.0],
                "User endpoint",
            ),
            create_record(
                "orders",
                [0.0, 1.0, 0.0],
                "Order endpoint",
            ),
        ]
    )

    store.save()

    loaded_store = FAISSVectorStore.load(tmp_path)

    assert loaded_store.dimension == 3
    assert len(loaded_store) == 2

    results = loaded_store.search(
        [1.0, 0.0, 0.0],
        limit=1,
    )

    assert results[0].record.id == "users"
    assert results[0].record.content == "User endpoint"


def test_save_creates_persistence_files(
    tmp_path: Path,
) -> None:
    store = FAISSVectorStore(
        dimension=3,
        storage_path=tmp_path,
    )

    store.save()

    assert (tmp_path / FAISSVectorStore.INDEX_FILENAME).exists()

    assert (tmp_path / FAISSVectorStore.RECORDS_FILENAME).exists()


def test_load_missing_store_raises_error(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        FileNotFoundError,
        match="Persisted FAISS vector store was not found",
    ):
        FAISSVectorStore.load(tmp_path)

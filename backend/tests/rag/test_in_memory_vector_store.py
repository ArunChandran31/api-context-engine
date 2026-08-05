import pytest

from app.rag.in_memory_vector_store import InMemoryVectorStore
from app.rag.vector_store import VectorRecord


def make_record(
    record_id: str,
    vector: list[float],
    content: str = "Example content",
) -> VectorRecord:
    return VectorRecord(
        id=record_id,
        vector=vector,
        content=content,
    )


def test_store_exposes_dimension() -> None:
    store = InMemoryVectorStore(dimension=3)

    assert store.dimension == 3


def test_store_rejects_invalid_dimension() -> None:
    with pytest.raises(
        ValueError,
        match="Vector dimension must be greater than zero",
    ):
        InMemoryVectorStore(dimension=0)


def test_add_stores_record() -> None:
    store = InMemoryVectorStore(dimension=3)

    store.add(
        make_record(
            "record-1",
            [1.0, 0.0, 0.0],
        )
    )

    assert len(store) == 1


def test_add_rejects_wrong_vector_dimension() -> None:
    store = InMemoryVectorStore(dimension=3)

    with pytest.raises(
        ValueError,
        match="Expected vector dimension 3, received 2",
    ):
        store.add(
            make_record(
                "record-1",
                [1.0, 0.0],
            )
        )


def test_add_batch_stores_multiple_records() -> None:
    store = InMemoryVectorStore(dimension=3)

    store.add_batch(
        [
            make_record("record-1", [1.0, 0.0, 0.0]),
            make_record("record-2", [0.0, 1.0, 0.0]),
        ]
    )

    assert len(store) == 2


def test_add_replaces_record_with_same_id() -> None:
    store = InMemoryVectorStore(dimension=3)

    store.add(
        make_record(
            "record-1",
            [1.0, 0.0, 0.0],
            "Original content",
        )
    )

    store.add(
        make_record(
            "record-1",
            [0.0, 1.0, 0.0],
            "Updated content",
        )
    )

    results = store.search(
        [0.0, 1.0, 0.0],
        limit=1,
    )

    assert len(store) == 1
    assert results[0].record.content == "Updated content"


def test_search_returns_most_similar_record_first() -> None:
    store = InMemoryVectorStore(dimension=3)

    store.add_batch(
        [
            make_record("users", [1.0, 0.0, 0.0]),
            make_record("orders", [0.0, 1.0, 0.0]),
            make_record("products", [0.0, 0.0, 1.0]),
        ]
    )

    results = store.search(
        [0.9, 0.1, 0.0],
        limit=2,
    )

    assert len(results) == 2
    assert results[0].record.id == "users"
    assert results[0].score > results[1].score


def test_search_respects_limit() -> None:
    store = InMemoryVectorStore(dimension=2)

    store.add_batch(
        [
            make_record("record-1", [1.0, 0.0]),
            make_record("record-2", [0.8, 0.2]),
            make_record("record-3", [0.0, 1.0]),
        ]
    )

    results = store.search(
        [1.0, 0.0],
        limit=2,
    )

    assert len(results) == 2


def test_search_empty_store_returns_empty_list() -> None:
    store = InMemoryVectorStore(dimension=3)

    assert store.search([1.0, 0.0, 0.0]) == []


def test_search_rejects_wrong_query_dimension() -> None:
    store = InMemoryVectorStore(dimension=3)

    with pytest.raises(
        ValueError,
        match="Expected vector dimension 3, received 2",
    ):
        store.search([1.0, 0.0])


def test_search_rejects_invalid_limit() -> None:
    store = InMemoryVectorStore(dimension=3)

    with pytest.raises(
        ValueError,
        match="Search limit must be greater than zero",
    ):
        store.search(
            [1.0, 0.0, 0.0],
            limit=0,
        )


def test_zero_vector_similarity_is_zero() -> None:
    store = InMemoryVectorStore(dimension=3)

    store.add(
        make_record(
            "zero",
            [0.0, 0.0, 0.0],
        )
    )

    results = store.search(
        [1.0, 0.0, 0.0],
        limit=1,
    )

    assert results[0].score == 0.0


def test_delete_existing_record() -> None:
    store = InMemoryVectorStore(dimension=2)
    store.add(
        make_record(
            "record-1",
            [1.0, 0.0],
        )
    )

    deleted = store.delete("record-1")

    assert deleted is True
    assert len(store) == 0


def test_delete_missing_record_returns_false() -> None:
    store = InMemoryVectorStore(dimension=2)

    assert store.delete("missing") is False


def test_clear_removes_all_records() -> None:
    store = InMemoryVectorStore(dimension=2)

    store.add_batch(
        [
            make_record("record-1", [1.0, 0.0]),
            make_record("record-2", [0.0, 1.0]),
        ]
    )

    store.clear()

    assert len(store) == 0

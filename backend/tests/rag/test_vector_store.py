import pytest

from app.rag.vector_store import (
    VectorRecord,
    VectorSearchResult,
    VectorStore,
)


def test_vector_record_creation() -> None:
    record = VectorRecord(
        id="endpoint-1-chunk-0",
        vector=[0.1, 0.2, 0.3],
        content="GET /users returns all users.",
        metadata={
            "specification_id": 1,
            "endpoint_id": 10,
        },
    )

    assert record.id == "endpoint-1-chunk-0"
    assert record.vector == [0.1, 0.2, 0.3]
    assert record.content == "GET /users returns all users."
    assert record.metadata["specification_id"] == 1
    assert record.metadata["endpoint_id"] == 10


def test_vector_record_rejects_empty_id() -> None:
    with pytest.raises(
        ValueError,
        match="Vector record ID cannot be empty",
    ):
        VectorRecord(
            id="",
            vector=[0.1, 0.2],
            content="Example content",
        )


def test_vector_record_rejects_empty_vector() -> None:
    with pytest.raises(
        ValueError,
        match="Vector cannot be empty",
    ):
        VectorRecord(
            id="record-1",
            vector=[],
            content="Example content",
        )


def test_vector_record_rejects_empty_content() -> None:
    with pytest.raises(
        ValueError,
        match="Vector record content cannot be empty",
    ):
        VectorRecord(
            id="record-1",
            vector=[0.1, 0.2],
            content="",
        )


def test_vector_search_result_creation() -> None:
    record = VectorRecord(
        id="record-1",
        vector=[0.1, 0.2],
        content="Example content",
    )

    result = VectorSearchResult(
        record=record,
        score=0.95,
    )

    assert result.record is record
    assert result.score == 0.95


def test_vector_store_cannot_be_instantiated() -> None:
    assert VectorStore.__abstractmethods__

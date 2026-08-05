import pytest

from app.rag.models import RAGChunk, RAGDocument


def test_rag_document_creation() -> None:
    document = RAGDocument(
        content="POST /users creates a new user.",
        specification_id=1,
        endpoint_id=10,
        path="/users",
        method="POST",
        operation_id="createUser",
        metadata={"api_title": "User API"},
    )

    assert document.content == "POST /users creates a new user."
    assert document.specification_id == 1
    assert document.endpoint_id == 10
    assert document.path == "/users"
    assert document.method == "POST"
    assert document.operation_id == "createUser"
    assert document.metadata["api_title"] == "User API"


def test_rag_document_rejects_empty_content() -> None:
    with pytest.raises(
        ValueError,
        match="RAG document content cannot be empty",
    ):
        RAGDocument(
            content="   ",
            specification_id=1,
        )


def test_rag_document_rejects_invalid_specification_id() -> None:
    with pytest.raises(
        ValueError,
        match="Specification ID must be positive",
    ):
        RAGDocument(
            content="API documentation",
            specification_id=0,
        )


def test_rag_document_rejects_invalid_endpoint_id() -> None:
    with pytest.raises(
        ValueError,
        match="Endpoint ID must be positive",
    ):
        RAGDocument(
            content="API documentation",
            specification_id=1,
            endpoint_id=0,
        )


def test_rag_chunk_creation() -> None:
    chunk = RAGChunk(
        content="Creates a new user.",
        specification_id=1,
        endpoint_id=10,
        chunk_index=0,
        path="/users",
        method="POST",
        operation_id="createUser",
    )

    assert chunk.content == "Creates a new user."
    assert chunk.specification_id == 1
    assert chunk.endpoint_id == 10
    assert chunk.chunk_index == 0


def test_rag_chunk_rejects_negative_index() -> None:
    with pytest.raises(
        ValueError,
        match="Chunk index cannot be negative",
    ):
        RAGChunk(
            content="Creates a new user.",
            specification_id=1,
            chunk_index=-1,
        )


def test_rag_chunk_rejects_empty_content() -> None:
    with pytest.raises(
        ValueError,
        match="RAG chunk content cannot be empty",
    ):
        RAGChunk(
            content="",
            specification_id=1,
            chunk_index=0,
        )

import pytest

from app.rag.chunker import DocumentChunker
from app.rag.models import RAGDocument


def test_chunker_keeps_small_document_as_single_chunk() -> None:
    document = RAGDocument(
        content="API: User API\nEndpoint: GET /users",
        specification_id=1,
        endpoint_id=10,
        path="/users",
        method="GET",
        operation_id="listUsers",
        metadata={"api_title": "User API"},
    )

    chunker = DocumentChunker(max_chunk_size=100)

    chunks = chunker.chunk(document)

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk.content == document.content
    assert chunk.chunk_index == 0
    assert chunk.specification_id == 1
    assert chunk.endpoint_id == 10
    assert chunk.path == "/users"
    assert chunk.method == "GET"
    assert chunk.operation_id == "listUsers"
    assert chunk.metadata == {"api_title": "User API"}


def test_chunker_splits_document_on_section_boundaries() -> None:
    document = RAGDocument(
        content=("API: User API\n" "Endpoint: POST /users\n" "Summary: Create user"),
        specification_id=1,
        endpoint_id=10,
    )

    chunker = DocumentChunker(max_chunk_size=30)

    chunks = chunker.chunk(document)

    assert len(chunks) == 3

    assert chunks[0].content == "API: User API"
    assert chunks[1].content == "Endpoint: POST /users"
    assert chunks[2].content == "Summary: Create user"

    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]


def test_chunker_splits_large_section_on_word_boundaries() -> None:
    document = RAGDocument(
        content="Description: creates users with validated account information",
        specification_id=1,
    )

    chunker = DocumentChunker(max_chunk_size=25)

    chunks = chunker.chunk(document)

    assert len(chunks) > 1
    assert all(len(chunk.content) <= 25 for chunk in chunks)

    reconstructed = " ".join(chunk.content for chunk in chunks)

    assert reconstructed == document.content


def test_chunker_preserves_metadata_across_chunks() -> None:
    document = RAGDocument(
        content="API: Example\nEndpoint: GET /items\nSummary: List items",
        specification_id=7,
        endpoint_id=42,
        path="/items",
        method="GET",
        operation_id="listItems",
        metadata={
            "api_title": "Example",
            "api_version": "2.0",
        },
    )

    chunker = DocumentChunker(max_chunk_size=20)

    chunks = chunker.chunk(document)

    assert len(chunks) > 1

    for index, chunk in enumerate(chunks):
        assert chunk.chunk_index == index
        assert chunk.specification_id == 7
        assert chunk.endpoint_id == 42
        assert chunk.path == "/items"
        assert chunk.method == "GET"
        assert chunk.operation_id == "listItems"
        assert chunk.metadata == {
            "api_title": "Example",
            "api_version": "2.0",
        }


def test_chunker_rejects_invalid_max_chunk_size() -> None:
    with pytest.raises(
        ValueError,
        match="Maximum chunk size must be positive",
    ):
        DocumentChunker(max_chunk_size=0)


def test_chunker_handles_oversized_single_word() -> None:
    document = RAGDocument(
        content="a" * 25,
        specification_id=1,
    )

    chunker = DocumentChunker(max_chunk_size=10)

    chunks = chunker.chunk(document)

    assert [chunk.content for chunk in chunks] == [
        "a" * 10,
        "a" * 10,
        "a" * 5,
    ]

    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]
    assert all(len(chunk.content) <= 10 for chunk in chunks)

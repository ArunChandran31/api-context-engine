from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.api.rag import get_rag_dependencies
from app.main import app
from app.rag.dependencies import RAGDependencies
from app.rag.retrieval_service import RetrievalResult


def test_query_rag_returns_retrieved_results() -> None:
    retrieval_service = MagicMock()

    retrieval_service.retrieve.return_value = [
        RetrievalResult(
            content="Endpoint: POST /users",
            score=0.95,
            metadata={
                "path": "/users",
                "method": "POST",
            },
        )
    ]

    dependencies = MagicMock(spec=RAGDependencies)
    dependencies.retrieval_service = retrieval_service
    dependencies.retrieval_limit = 5

    app.dependency_overrides[get_rag_dependencies] = lambda: dependencies

    try:
        client = TestClient(app)

        response = client.post(
            "/api/rag/query",
            json={
                "query": "How do I create a user?",
                "limit": 3,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    assert response.json() == {
        "query": "How do I create a user?",
        "results": [
            {
                "content": "Endpoint: POST /users",
                "score": 0.95,
                "metadata": {
                    "path": "/users",
                    "method": "POST",
                },
            }
        ],
    }

    retrieval_service.retrieve.assert_called_once_with(
        query="How do I create a user?",
        limit=3,
    )


def test_query_rag_uses_configured_default_limit() -> None:
    retrieval_service = MagicMock()
    retrieval_service.retrieve.return_value = []

    dependencies = MagicMock(spec=RAGDependencies)
    dependencies.retrieval_service = retrieval_service
    dependencies.retrieval_limit = 7

    app.dependency_overrides[get_rag_dependencies] = lambda: dependencies

    try:
        client = TestClient(app)

        response = client.post(
            "/api/rag/query",
            json={
                "query": "How do I list users?",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    retrieval_service.retrieve.assert_called_once_with(
        query="How do I list users?",
        limit=7,
    )


def test_query_rag_rejects_empty_query() -> None:
    dependencies = MagicMock(spec=RAGDependencies)

    app.dependency_overrides[get_rag_dependencies] = lambda: dependencies

    try:
        client = TestClient(app)

        response = client.post(
            "/api/rag/query",
            json={
                "query": "",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_query_rag_rejects_invalid_limit() -> None:
    dependencies = MagicMock(spec=RAGDependencies)

    app.dependency_overrides[get_rag_dependencies] = lambda: dependencies

    try:
        client = TestClient(app)

        response = client.post(
            "/api/rag/query",
            json={
                "query": "How do I create a user?",
                "limit": 0,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_query_rag_returns_empty_results_when_no_context_matches() -> None:
    retrieval_service = MagicMock()
    retrieval_service.retrieve.return_value = []

    dependencies = MagicMock(spec=RAGDependencies)
    dependencies.retrieval_service = retrieval_service
    dependencies.retrieval_limit = 5

    app.dependency_overrides[get_rag_dependencies] = lambda: dependencies

    try:
        client = TestClient(app)

        response = client.post(
            "/api/rag/query",
            json={
                "query": "Unknown API operation",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    assert response.json() == {
        "query": "Unknown API operation",
        "results": [],
    }

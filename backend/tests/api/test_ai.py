from unittest.mock import MagicMock

from app.ai.dependencies import AIDependencies
from app.ai.exceptions import LLMProviderError
from app.ai.models import GenerationResult
from app.ai.question_answering_service import QuestionAnswerResult
from app.api.ai import get_ai_dependencies
from app.main import app
from app.rag.retrieval_service import RetrievalResult
from fastapi.testclient import TestClient


def test_question_endpoint_returns_answer() -> None:
    qa_service = MagicMock()

    qa_service.answer.return_value = QuestionAnswerResult(
        answer=GenerationResult(
            content="POST /pets creates a pet.",
        ),
        sources=[],
    )

    dependencies = AIDependencies(
        llm_provider=MagicMock(),
        prompt_builder=MagicMock(),
        question_answering_service=qa_service,
        test_case_prompt_builder=MagicMock(),
        test_case_generation_service=MagicMock(),
        debug_prompt_builder=MagicMock(),
        debug_generator=MagicMock(),
        debug_service=MagicMock(),
    )

    app.dependency_overrides[get_ai_dependencies] = lambda: dependencies

    client = TestClient(app)

    response = client.post(
        "/api/ai/question",
        json={
            "question": "Which endpoint creates a pet?",
            "specification_id": 3,
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    assert response.json() == {
        "answer": "POST /pets creates a pet.",
        "sources": [],
    }

    qa_service.answer.assert_called_once_with(
        question="Which endpoint creates a pet?",
        specification_id=3,
    )


def test_question_endpoint_returns_answer_with_sources() -> None:
    qa_service = MagicMock()

    qa_service.answer.return_value = QuestionAnswerResult(
        answer=GenerationResult(
            content="GET /products/{product_id} retrieves a product by ID.",
        ),
        sources=[
            RetrievalResult(
                content=(
                    "API: Rich Products API\n"
                    "Version: 1.0.0\n"
                    "Endpoint: GET /products/{product_id}\n"
                    "Summary: Get product\n"
                    "Description: Returns a product by ID.\n"
                    "Operation ID: getProduct"
                ),
                score=0.5261700749397278,
                metadata={
                    "specification_id": 6,
                    "endpoint_id": 11,
                    "method": "GET",
                    "path": "/products/{product_id}",
                    "operation_id": "getProduct",
                },
            ),
        ],
    )

    dependencies = AIDependencies(
        llm_provider=MagicMock(),
        prompt_builder=MagicMock(),
        question_answering_service=qa_service,
        test_case_prompt_builder=MagicMock(),
        test_case_generation_service=MagicMock(),
        debug_prompt_builder=MagicMock(),
        debug_generator=MagicMock(),
        debug_service=MagicMock(),
    )

    app.dependency_overrides[get_ai_dependencies] = lambda: dependencies

    client = TestClient(app)

    response = client.post(
        "/api/ai/question",
        json={
            "question": "What endpoint retrieves a product by ID?",
            "specification_id": 6,
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    assert response.json() == {
        "answer": "GET /products/{product_id} retrieves a product by ID.",
        "sources": [
            {
                "specification_id": 6,
                "endpoint_id": 11,
                "method": "GET",
                "path": "/products/{product_id}",
                "operation_id": "getProduct",
            }
        ],
    }

    qa_service.answer.assert_called_once_with(
        question="What endpoint retrieves a product by ID?",
        specification_id=6,
    )


def test_question_endpoint_rejects_empty_question() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/ai/question",
        json={
            "question": "",
            "specification_id": 3,
        },
    )

    assert response.status_code == 422


def test_question_endpoint_returns_503_for_llm_provider_error() -> None:
    qa_service = MagicMock()

    qa_service.answer.side_effect = LLMProviderError(
        "LLM provider is temporarily unavailable.",
    )

    dependencies = AIDependencies(
        llm_provider=MagicMock(),
        prompt_builder=MagicMock(),
        question_answering_service=qa_service,
        test_case_prompt_builder=MagicMock(),
        test_case_generation_service=MagicMock(),
        debug_prompt_builder=MagicMock(),
        debug_generator=MagicMock(),
        debug_service=MagicMock(),
    )

    app.dependency_overrides[get_ai_dependencies] = lambda: dependencies

    client = TestClient(app)

    response = client.post(
        "/api/ai/question",
        json={
            "question": "Which endpoint creates a pet?",
            "specification_id": 3,
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 503

    assert response.json() == {
        "error": "llm_provider_error",
        "message": "LLM provider is temporarily unavailable.",
    }


def test_question_endpoint_preserves_llm_provider_status_code() -> None:
    qa_service = MagicMock()

    qa_service.answer.side_effect = LLMProviderError(
        "LLM provider rate limit exceeded.",
        status_code=429,
    )

    dependencies = AIDependencies(
        llm_provider=MagicMock(),
        prompt_builder=MagicMock(),
        question_answering_service=qa_service,
        test_case_prompt_builder=MagicMock(),
        test_case_generation_service=MagicMock(),
        debug_prompt_builder=MagicMock(),
        debug_generator=MagicMock(),
        debug_service=MagicMock(),
    )

    app.dependency_overrides[get_ai_dependencies] = lambda: dependencies

    client = TestClient(app)

    response = client.post(
        "/api/ai/question",
        json={
            "question": "Which endpoint creates a pet?",
            "specification_id": 3,
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 429

    assert response.json() == {
        "error": "llm_provider_error",
        "message": "LLM provider rate limit exceeded.",
    }

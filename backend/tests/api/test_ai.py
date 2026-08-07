from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.ai.dependencies import AIDependencies
from app.ai.models import GenerationResult
from app.api.ai import get_ai_dependencies
from app.main import app


def test_question_endpoint_returns_answer() -> None:
    qa_service = MagicMock()

    qa_service.answer.return_value = GenerationResult(
        content="POST /pets creates a pet.",
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
        json={"question": "Which endpoint creates a pet?"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200

    assert response.json() == {"answer": "POST /pets creates a pet."}

    qa_service.answer.assert_called_once_with("Which endpoint creates a pet?")


def test_question_endpoint_rejects_empty_question() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/ai/question",
        json={
            "question": "",
        },
    )

    assert response.status_code == 422

import pytest

from app.schemas.ai import QuestionRequest, QuestionResponse


def test_question_request_creation() -> None:
    request = QuestionRequest(
        question="Which endpoint creates a pet?",
    )

    assert request.question == "Which endpoint creates a pet?"


def test_question_request_rejects_empty_question() -> None:
    with pytest.raises(ValueError):
        QuestionRequest(question="")


def test_question_response_creation() -> None:
    response = QuestionResponse(
        answer="POST /pets",
    )

    assert response.answer == "POST /pets"

import pytest
from pydantic import ValidationError

from app.schemas.debug import (
    DebugRequest,
    DebugResponse,
)


def test_request_schema_accepts_question() -> None:
    request = DebugRequest(
        question="Why does POST /pets return 500?",
    )

    assert request.question == "Why does POST /pets return 500?"


def test_request_schema_rejects_empty_question() -> None:
    with pytest.raises(ValidationError):
        DebugRequest(
            question="",
        )


def test_response_schema() -> None:
    response = DebugResponse(
        explanation="The endpoint returns an internal server error.",
    )

    assert response.explanation == "The endpoint returns an internal server error."

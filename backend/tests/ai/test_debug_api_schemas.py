import pytest
from pydantic import ValidationError

from app.schemas.debug import (
    DebugRequest,
    DebugResponse,
)


def test_request_schema_accepts_question() -> None:
    request = DebugRequest(
        question="Why does POST /pets return 500?",
        specification_id=6,
        endpoint="POST /pets",
        status_code=500,
        error_message="Internal Server Error",
        request_body='{"name": "Buddy"}',
        response_body='{"message": "Internal Server Error"}',
    )

    assert request.question == "Why does POST /pets return 500?"
    assert request.specification_id == 6
    assert request.endpoint == "POST /pets"
    assert request.status_code == 500
    assert request.error_message == "Internal Server Error"
    assert request.request_body == '{"name": "Buddy"}'
    assert request.response_body == '{"message": "Internal Server Error"}'


def test_request_schema_rejects_empty_question() -> None:
    with pytest.raises(ValidationError):
        DebugRequest(
            question="",
            specification_id=6,
            endpoint="POST /pets",
            status_code=500,
            error_message="Internal Server Error",
        )


def test_request_schema_rejects_invalid_specification_id() -> None:
    with pytest.raises(ValidationError):
        DebugRequest(
            question="Why does POST /pets return 500?",
            specification_id=0,
            endpoint="POST /pets",
            status_code=500,
            error_message="Internal Server Error",
        )


def test_request_schema_rejects_invalid_status_code() -> None:
    with pytest.raises(ValidationError):
        DebugRequest(
            question="Why does POST /pets return 500?",
            specification_id=6,
            endpoint="POST /pets",
            status_code=99,
            error_message="Internal Server Error",
        )


def test_request_schema_rejects_empty_endpoint() -> None:
    with pytest.raises(ValidationError):
        DebugRequest(
            question="Why does POST /pets return 500?",
            specification_id=6,
            endpoint="",
            status_code=500,
            error_message="Internal Server Error",
        )


def test_request_schema_rejects_empty_error_message() -> None:
    with pytest.raises(ValidationError):
        DebugRequest(
            question="Why does POST /pets return 500?",
            specification_id=6,
            endpoint="POST /pets",
            status_code=500,
            error_message="",
        )


def test_request_schema_allows_empty_optional_bodies() -> None:
    request = DebugRequest(
        question="Why does POST /pets return 500?",
        specification_id=6,
        endpoint="POST /pets",
        status_code=500,
        error_message="Internal Server Error",
    )

    assert request.request_body == ""
    assert request.response_body == ""


def test_response_schema() -> None:
    response = DebugResponse(
        explanation="The endpoint returns an internal server error.",
    )

    assert response.explanation == ("The endpoint returns an internal server error.")

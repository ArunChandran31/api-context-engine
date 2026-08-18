from app.ai.debug_models import DebugRequest
from app.ai.debug_prompt_builder import DebugPromptBuilder


def build_request() -> DebugRequest:
    builder = DebugPromptBuilder()

    return builder.build(
        question="Why does POST /pets return 500?",
        endpoint="POST /pets",
        status_code=500,
        error_message="Internal Server Error",
        request_body='{"name": "Buddy"}',
        response_body='{"message": "Internal Server Error"}',
        context="POST /pets returns 500.",
    )


def test_prompt_builder_returns_debug_request() -> None:
    request = build_request()

    assert isinstance(request, DebugRequest)


def test_prompt_contains_question() -> None:
    request = build_request()

    assert "Why does POST /pets return 500?" in request.prompt


def test_prompt_contains_context() -> None:
    request = build_request()

    assert "POST /pets returns 500." in request.prompt


def test_prompt_contains_endpoint() -> None:
    request = build_request()

    assert "POST /pets" in request.prompt


def test_prompt_contains_status_code() -> None:
    request = build_request()

    assert "500" in request.prompt


def test_prompt_contains_error_message() -> None:
    request = build_request()

    assert "Internal Server Error" in request.prompt


def test_prompt_contains_request_body() -> None:
    request = build_request()

    assert '{"name": "Buddy"}' in request.prompt


def test_prompt_contains_response_body() -> None:
    request = build_request()

    assert '{"message": "Internal Server Error"}' in request.prompt


def test_prompt_instructs_model_to_use_context() -> None:
    request = build_request()

    assert "ONLY the API context" in request.prompt


def test_prompt_instructs_model_not_to_invent_information() -> None:
    request = build_request()

    assert "Do not invent endpoints" in request.prompt


def test_prompt_handles_empty_request_and_response_bodies() -> None:
    builder = DebugPromptBuilder()

    request = builder.build(
        question="Why does POST /pets return 500?",
        endpoint="POST /pets",
        status_code=500,
        error_message="Internal Server Error",
        request_body="",
        response_body="",
        context="POST /pets returns 500.",
    )

    assert "(empty)" in request.prompt

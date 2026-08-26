from unittest.mock import MagicMock

import pytest
from app.ai.debug_generator import DebugGenerator
from app.ai.debug_models import DebugResult
from app.ai.debug_prompt_builder import DebugPromptBuilder
from app.ai.debug_service import DebugService
from app.rag.retrieval_service import (
    RAGRetrievalService,
    RetrievalResult,
)


def test_debug_retrieves_context_and_generates_response() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)

    retrieval_service.retrieve.return_value = [
        RetrievalResult(
            content="POST /pets returns 500.",
            score=0.95,
            metadata={
                "specification_id": 6,
                "path": "/pets",
                "method": "POST",
            },
        ),
    ]

    prompt_builder = MagicMock(spec=DebugPromptBuilder)

    debug_generator = MagicMock(spec=DebugGenerator)

    debug_generator.generate.return_value = DebugResult(
        explanation="The endpoint raises a server error.",
    )

    service = DebugService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        debug_generator=debug_generator,
    )

    result = service.debug(
        question="Why does POST /pets return 500?",
        specification_id=6,
        endpoint="POST /pets",
        status_code=500,
        error_message="Internal Server Error",
        request_body='{"name": "Buddy"}',
        response_body='{"message": "Internal Server Error"}',
    )

    assert result.explanation == ("The endpoint raises a server error.")

    retrieval_service.retrieve.assert_called_once_with(
        query=(
            "POST /pets\n"
            "HTTP Status: 500\n"
            "Error: Internal Server Error\n"
            "Question: Why does POST /pets return 500?\n"
            'Request Body: {"name": "Buddy"}\n'
            'Response / Stack Trace: {"message": "Internal Server Error"}'
        ),
        limit=5,
        specification_id=6,
    )

    prompt_builder.build.assert_called_once_with(
        question="Why does POST /pets return 500?",
        endpoint="POST /pets",
        status_code=500,
        error_message="Internal Server Error",
        request_body='{"name": "Buddy"}',
        response_body='{"message": "Internal Server Error"}',
        context="POST /pets returns 500.",
    )

    debug_generator.generate.assert_called_once()


def test_debug_supports_empty_retrieval_results() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)

    retrieval_service.retrieve.return_value = []

    prompt_builder = MagicMock(spec=DebugPromptBuilder)

    debug_generator = MagicMock(spec=DebugGenerator)

    debug_generator.generate.return_value = DebugResult(
        explanation="Insufficient context.",
    )

    service = DebugService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        debug_generator=debug_generator,
    )

    result = service.debug(
        question="Why does this endpoint fail?",
        specification_id=6,
        endpoint="POST /pets",
        status_code=500,
        error_message="Internal Server Error",
    )

    assert result.explanation == "Insufficient context."

    retrieval_service.retrieve.assert_called_once_with(
        query=(
            "POST /pets\n"
            "HTTP Status: 500\n"
            "Error: Internal Server Error\n"
            "Question: Why does this endpoint fail?"
        ),
        limit=5,
        specification_id=6,
    )

    prompt_builder.build.assert_called_once_with(
        question="Why does this endpoint fail?",
        endpoint="POST /pets",
        status_code=500,
        error_message="Internal Server Error",
        request_body="",
        response_body="",
        context="",
    )


def test_debug_retrieval_query_includes_failure_details() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)

    retrieval_service.retrieve.return_value = []

    prompt_builder = MagicMock(spec=DebugPromptBuilder)

    debug_generator = MagicMock(spec=DebugGenerator)

    debug_generator.generate.return_value = DebugResult(
        explanation="Insufficient context.",
    )

    service = DebugService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        debug_generator=debug_generator,
    )

    service.debug(
        question="Why is the request unauthorized?",
        specification_id=6,
        endpoint="GET /products/{product_id}",
        status_code=401,
        error_message="Authentication required",
        request_body='{"id": 123}',
        response_body='{"detail": "Authentication required"}',
    )

    retrieval_service.retrieve.assert_called_once()

    query = retrieval_service.retrieve.call_args.kwargs["query"]

    assert "GET /products/{product_id}" in query
    assert "HTTP Status: 401" in query
    assert "Error: Authentication required" in query
    assert "Question: Why is the request unauthorized?" in query
    assert 'Request Body: {"id": 123}' in query
    assert 'Response / Stack Trace: {"detail": "Authentication required"}' in query


def test_debug_retrieval_query_omits_empty_optional_details() -> None:
    retrieval_service = MagicMock(spec=RAGRetrievalService)

    retrieval_service.retrieve.return_value = []

    prompt_builder = MagicMock(spec=DebugPromptBuilder)

    debug_generator = MagicMock(spec=DebugGenerator)

    debug_generator.generate.return_value = DebugResult(
        explanation="Insufficient context.",
    )

    service = DebugService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        debug_generator=debug_generator,
    )

    service.debug(
        question="Why does the endpoint fail?",
        specification_id=6,
        endpoint="GET /products/{product_id}",
        status_code=404,
        error_message="Product not found",
        request_body="",
        response_body="",
    )

    query = retrieval_service.retrieve.call_args.kwargs["query"]

    assert query == (
        "GET /products/{product_id}\n"
        "HTTP Status: 404\n"
        "Error: Product not found\n"
        "Question: Why does the endpoint fail?"
    )


def test_debug_rejects_empty_question() -> None:
    retrieval_service = MagicMock(
        spec=RAGRetrievalService,
    )

    prompt_builder = MagicMock(
        spec=DebugPromptBuilder,
    )

    debug_generator = MagicMock(
        spec=DebugGenerator,
    )

    service = DebugService(
        retrieval_service=retrieval_service,
        prompt_builder=prompt_builder,
        debug_generator=debug_generator,
    )

    with pytest.raises(
        ValueError,
        match="Debug question cannot be empty.",
    ):
        service.debug(
            question="",
            specification_id=6,
            endpoint="POST /pets",
            status_code=500,
            error_message="Internal Server Error",
        )

    retrieval_service.retrieve.assert_not_called()
    prompt_builder.build.assert_not_called()
    debug_generator.generate.assert_not_called()


def test_debug_rejects_invalid_specification_id() -> None:
    service = DebugService(
        retrieval_service=MagicMock(
            spec=RAGRetrievalService,
        ),
        prompt_builder=MagicMock(
            spec=DebugPromptBuilder,
        ),
        debug_generator=MagicMock(
            spec=DebugGenerator,
        ),
    )

    with pytest.raises(
        ValueError,
        match="Specification ID must be greater than zero.",
    ):
        service.debug(
            question="Why does POST /pets return 500?",
            specification_id=0,
            endpoint="POST /pets",
            status_code=500,
            error_message="Internal Server Error",
        )


def test_debug_rejects_empty_endpoint() -> None:
    service = DebugService(
        retrieval_service=MagicMock(
            spec=RAGRetrievalService,
        ),
        prompt_builder=MagicMock(
            spec=DebugPromptBuilder,
        ),
        debug_generator=MagicMock(
            spec=DebugGenerator,
        ),
    )

    with pytest.raises(
        ValueError,
        match="Endpoint cannot be empty.",
    ):
        service.debug(
            question="Why does the request fail?",
            specification_id=6,
            endpoint="",
            status_code=500,
            error_message="Internal Server Error",
        )


def test_debug_rejects_invalid_status_code() -> None:
    service = DebugService(
        retrieval_service=MagicMock(
            spec=RAGRetrievalService,
        ),
        prompt_builder=MagicMock(
            spec=DebugPromptBuilder,
        ),
        debug_generator=MagicMock(
            spec=DebugGenerator,
        ),
    )

    with pytest.raises(
        ValueError,
        match="Status code must be between 100 and 599.",
    ):
        service.debug(
            question="Why does the request fail?",
            specification_id=6,
            endpoint="POST /pets",
            status_code=600,
            error_message="Internal Server Error",
        )


def test_debug_rejects_empty_error_message() -> None:
    service = DebugService(
        retrieval_service=MagicMock(
            spec=RAGRetrievalService,
        ),
        prompt_builder=MagicMock(
            spec=DebugPromptBuilder,
        ),
        debug_generator=MagicMock(
            spec=DebugGenerator,
        ),
    )

    with pytest.raises(
        ValueError,
        match="Error message cannot be empty.",
    ):
        service.debug(
            question="Why does the request fail?",
            specification_id=6,
            endpoint="POST /pets",
            status_code=500,
            error_message="",
        )


def test_service_rejects_invalid_retrieval_limit() -> None:
    with pytest.raises(
        ValueError,
        match="Retrieval limit must be greater than zero.",
    ):
        DebugService(
            retrieval_service=MagicMock(
                spec=RAGRetrievalService,
            ),
            prompt_builder=MagicMock(
                spec=DebugPromptBuilder,
            ),
            debug_generator=MagicMock(
                spec=DebugGenerator,
            ),
            retrieval_limit=0,
        )

import hashlib

import pytest

from app.cache.keys import (
    build_ai_question_cache_key,
    build_ai_question_cache_pattern,
)


def test_build_ai_question_cache_key_is_deterministic() -> None:
    key = build_ai_question_cache_key(
        question="What fields are required?",
        specification_id=14,
        provider="groq",
        model="openai/gpt-oss-20b",
    )

    expected_hash = hashlib.sha256(
        b"What fields are required?",
    ).hexdigest()

    assert key == (
        "api-context-engine:v1:"
        f"ai:question:{expected_hash}:"
        "specification:14:"
        "provider:groq:"
        "model:openai/gpt-oss-20b"
    )


def test_build_ai_question_cache_key_normalizes_whitespace() -> None:
    key_one = build_ai_question_cache_key(
        question="What   fields are   required?",
        specification_id=14,
        provider="groq",
        model="openai/gpt-oss-20b",
    )

    key_two = build_ai_question_cache_key(
        question="  What fields are required?  ",
        specification_id=14,
        provider="groq",
        model="openai/gpt-oss-20b",
    )

    assert key_one == key_two


def test_build_ai_question_cache_key_changes_with_specification() -> None:
    key_one = build_ai_question_cache_key(
        question="What fields are required?",
        specification_id=14,
        provider="groq",
        model="openai/gpt-oss-20b",
    )

    key_two = build_ai_question_cache_key(
        question="What fields are required?",
        specification_id=15,
        provider="groq",
        model="openai/gpt-oss-20b",
    )

    assert key_one != key_two


def test_build_ai_question_cache_key_changes_with_provider() -> None:
    key_one = build_ai_question_cache_key(
        question="What fields are required?",
        specification_id=14,
        provider="groq",
        model="openai/gpt-oss-20b",
    )

    key_two = build_ai_question_cache_key(
        question="What fields are required?",
        specification_id=14,
        provider="gemini",
        model="openai/gpt-oss-20b",
    )

    assert key_one != key_two


def test_build_ai_question_cache_key_changes_with_model() -> None:
    key_one = build_ai_question_cache_key(
        question="What fields are required?",
        specification_id=14,
        provider="groq",
        model="openai/gpt-oss-20b",
    )

    key_two = build_ai_question_cache_key(
        question="What fields are required?",
        specification_id=14,
        provider="groq",
        model="another-model",
    )

    assert key_one != key_two


def test_build_ai_question_cache_key_rejects_invalid_specification() -> None:
    with pytest.raises(ValueError, match="Specification ID must be greater than zero"):
        build_ai_question_cache_key(
            question="What fields are required?",
            specification_id=0,
            provider="groq",
            model="openai/gpt-oss-20b",
        )


def test_build_ai_question_cache_pattern() -> None:
    pattern = build_ai_question_cache_pattern(14)

    assert pattern == (
        "api-context-engine:v1:"
        "ai:question:*:"
        "specification:14:"
        "provider:*:"
        "model:*"
    )


def test_build_ai_question_cache_pattern_rejects_invalid_specification() -> None:
    with pytest.raises(ValueError, match="Specification ID must be greater than zero"):
        build_ai_question_cache_pattern(0)

import hashlib

CACHE_NAMESPACE = "api-context-engine"
CACHE_VERSION = "v1"


def build_rag_query_cache_key(
    query: str,
    limit: int,
    specification_id: int | None = None,
) -> str:
    """
    Build a deterministic cache key for an RAG query.
    """
    normalized_query = " ".join(query.split())

    query_hash = hashlib.sha256(
        normalized_query.encode("utf-8"),
    ).hexdigest()

    return (
        f"{CACHE_NAMESPACE}:"
        f"{CACHE_VERSION}:"
        f"rag:query:"
        f"{query_hash}:"
        f"limit:{limit}:"
        f"specification:{specification_id}"
    )


def build_rag_query_cache_pattern(
    specification_id: int,
) -> str:
    """
    Build a Redis key pattern matching all cached RAG queries
    for a specific API specification.
    """
    if specification_id <= 0:
        raise ValueError("Specification ID must be greater than zero.")

    return (
        f"{CACHE_NAMESPACE}:"
        f"{CACHE_VERSION}:"
        f"rag:query:*:"
        f"limit:*:"
        f"specification:{specification_id}"
    )


def build_ai_question_cache_key(
    question: str,
    specification_id: int,
    provider: str,
    model: str,
) -> str:
    """
    Build a deterministic cache key for an AI question.
    """
    if specification_id <= 0:
        raise ValueError("Specification ID must be greater than zero.")

    normalized_question = " ".join(question.split())

    question_hash = hashlib.sha256(
        normalized_question.encode("utf-8"),
    ).hexdigest()

    return (
        f"{CACHE_NAMESPACE}:"
        f"{CACHE_VERSION}:"
        f"ai:question:"
        f"{question_hash}:"
        f"specification:{specification_id}:"
        f"provider:{provider}:"
        f"model:{model}"
    )


def build_ai_question_cache_pattern(
    specification_id: int,
) -> str:
    """
    Build a Redis key pattern matching all cached AI questions
    for a specific API specification.
    """
    if specification_id <= 0:
        raise ValueError("Specification ID must be greater than zero.")

    return (
        f"{CACHE_NAMESPACE}:"
        f"{CACHE_VERSION}:"
        f"ai:question:*:"
        f"specification:{specification_id}:"
        f"provider:*:"
        f"model:*"
    )

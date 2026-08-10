import hashlib

CACHE_NAMESPACE = "api-context-engine"
CACHE_VERSION = "v1"


def build_rag_query_cache_key(
    query: str,
    limit: int,
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
        f"limit:{limit}"
    )

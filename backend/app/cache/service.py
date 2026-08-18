import json
import logging
from collections.abc import Iterator
from typing import Any, Protocol

from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class CacheClient(Protocol):
    """Interface required by CacheService."""

    def get(self, key: str) -> Any: ...

    def set(self, key: str, value: str, ex: int) -> Any: ...

    def delete(self, key: str) -> int: ...

    def scan_iter(self, match: str) -> Iterator[str]: ...


class CacheService:
    """
    Application-level cache service backed by Redis.
    """

    def __init__(self, client: CacheClient) -> None:
        self._client = client

    def get(self, key: str) -> Any | None:
        """
        Retrieve a cached value.

        Returns None when the key does not exist, Redis is unavailable,
        or the cached value is invalid JSON.
        """
        try:
            value = self._client.get(key)
        except RedisError as exc:
            logger.warning(
                "Redis cache GET failed",
                extra={"cache_key": key},
                exc_info=exc,
            )
            return None

        if value is None:
            return None

        try:
            return json.loads(value)
        except (TypeError, json.JSONDecodeError) as exc:
            logger.warning(
                "Redis cache value is invalid JSON",
                extra={"cache_key": key},
                exc_info=exc,
            )
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int,
    ) -> None:
        """
        Store a value in Redis with a TTL.

        Redis failures are treated as cache failures and do not
        propagate to the caller.
        """
        if ttl_seconds <= 0:
            raise ValueError("TTL must be greater than zero.")

        try:
            self._client.set(
                key,
                json.dumps(value),
                ex=ttl_seconds,
            )
        except RedisError as exc:
            logger.warning(
                "Redis cache SET failed",
                extra={"cache_key": key},
                exc_info=exc,
            )

    def delete(self, key: str) -> bool:
        """
        Delete a cached value.

        Returns True when a value was deleted and False when the
        key does not exist or Redis is unavailable.
        """
        try:
            return bool(self._client.delete(key))
        except RedisError as exc:
            logger.warning(
                "Redis cache DELETE failed",
                extra={"cache_key": key},
                exc_info=exc,
            )
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all cached values whose Redis keys match the pattern.

        Returns the number of deleted keys.

        Redis failures are treated as cache failures and do not
        propagate to the caller.
        """
        deleted_count = 0

        try:
            for key in self._client.scan_iter(match=pattern):
                deleted_count += int(self._client.delete(key))

        except RedisError as exc:
            logger.warning(
                "Redis cache PATTERN DELETE failed",
                extra={"cache_pattern": pattern},
                exc_info=exc,
            )

        return deleted_count

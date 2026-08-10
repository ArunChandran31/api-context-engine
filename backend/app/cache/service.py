import json
from typing import Any

from redis import Redis


class CacheService:
    """
    Application-level cache service backed by Redis.
    """

    def __init__(self, client: Redis) -> None:
        self._client = client

    def get(self, key: str) -> Any | None:
        """
        Retrieve a cached value.

        Returns None when the key does not exist.
        """
        value = self._client.get(key)

        if value is None:
            return None

        return json.loads(value)

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int,
    ) -> None:
        """
        Store a value in Redis with a TTL.
        """
        if ttl_seconds <= 0:
            raise ValueError("TTL must be greater than zero.")

        self._client.set(
            key,
            json.dumps(value),
            ex=ttl_seconds,
        )

    def delete(self, key: str) -> bool:
        """
        Delete a cached value.

        Returns True when a value was deleted.
        """
        return bool(self._client.delete(key))

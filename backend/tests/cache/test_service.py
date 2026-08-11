import json

import pytest
from redis.exceptions import RedisError

from app.cache.service import CacheService


class FakeRedis:
    def __init__(self) -> None:
        self.data: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    def get(self, key: str) -> str | None:
        return self.data.get(key)

    def set(self, key: str, value: str, ex: int) -> None:
        self.data[key] = value
        self.ttls[key] = ex

    def delete(self, key: str) -> int:
        if key not in self.data:
            return 0

        del self.data[key]
        self.ttls.pop(key, None)
        return 1


class FailingRedis:
    def get(self, key: str) -> str | None:
        raise RedisError("Redis unavailable")

    def set(self, key: str, value: str, ex: int) -> None:
        raise RedisError("Redis unavailable")

    def delete(self, key: str) -> int:
        raise RedisError("Redis unavailable")


class CorruptRedis(FakeRedis):
    def get(self, key: str) -> str | None:
        return "{invalid-json"


def test_get_returns_none_for_missing_key() -> None:
    cache = CacheService(FakeRedis())

    assert cache.get("missing") is None


def test_set_and_get_round_trip() -> None:
    redis = FakeRedis()
    cache = CacheService(redis)

    value = {
        "query": "Which endpoint creates a pet?",
        "results": [
            {
                "content": "POST /pets",
                "score": 0.91,
            }
        ],
    }

    cache.set("rag:test", value, ttl_seconds=60)

    assert cache.get("rag:test") == value


def test_set_stores_json_and_ttl() -> None:
    redis = FakeRedis()
    cache = CacheService(redis)

    value = {"answer": "POST /pets"}

    cache.set("rag:test", value, ttl_seconds=120)

    assert json.loads(redis.data["rag:test"]) == value
    assert redis.ttls["rag:test"] == 120


def test_set_rejects_non_positive_ttl() -> None:
    cache = CacheService(FakeRedis())

    with pytest.raises(ValueError, match="TTL must be greater than zero"):
        cache.set("rag:test", {"value": 1}, ttl_seconds=0)


def test_delete_returns_true_when_key_exists() -> None:
    redis = FakeRedis()
    cache = CacheService(redis)

    cache.set("rag:test", {"value": 1}, ttl_seconds=60)

    assert cache.delete("rag:test") is True
    assert cache.get("rag:test") is None


def test_delete_returns_false_when_key_does_not_exist() -> None:
    cache = CacheService(FakeRedis())

    assert cache.delete("missing") is False


def test_get_returns_none_when_redis_is_unavailable() -> None:
    cache = CacheService(FailingRedis())

    assert cache.get("rag:test") is None


def test_get_returns_none_for_invalid_json() -> None:
    cache = CacheService(CorruptRedis())

    assert cache.get("rag:test") is None


def test_set_does_not_raise_when_redis_is_unavailable() -> None:
    cache = CacheService(FailingRedis())

    cache.set("rag:test", {"value": 1}, ttl_seconds=60)


def test_delete_returns_false_when_redis_is_unavailable() -> None:
    cache = CacheService(FailingRedis())

    assert cache.delete("rag:test") is False

from redis import Redis

from app.core.config import settings


def get_redis_client() -> Redis:
    """
    Create a Redis client using the application configuration.
    """
    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

from app.cache.service import CacheService
from app.core.redis import get_redis_client


def get_cache_service() -> CacheService:
    """
    Provide the application cache service.
    """
    return CacheService(get_redis_client())

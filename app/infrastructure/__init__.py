"""
Infrastructure package for ExoHabitabilityLab.

Contains cross-cutting concerns:
- Caching
- Logging configuration  
- Error handling
- External API clients
"""

from app.infrastructure.caching import (
    CacheBackend,
    InMemoryCache,
    RedisCache,
    configure_cache,
    get_cache,
    cached,
    CacheTTL,
    make_cache_key,
    make_api_cache_key,
    make_scoring_cache_key,
)

__all__ = [
    "CacheBackend",
    "InMemoryCache", 
    "RedisCache",
    "configure_cache",
    "get_cache",
    "cached",
    "CacheTTL",
    "make_cache_key",
    "make_api_cache_key",
    "make_scoring_cache_key",
]

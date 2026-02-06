"""
Caching Layer for ExoHabitabilityLab.

This module provides caching infrastructure for:
- NASA/ESA API responses
- Scoring results
- Image generation prompts

Supports multiple backends:
- In-memory (for development/testing)
- Redis (for production)
- File-based (for simple deployments)
"""

import json
import hashlib
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any, Dict, TypeVar, Generic, Callable
from datetime import datetime, timedelta
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """A cached value with metadata."""
    
    value: T
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    hit_count: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if this entry has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    @property
    def age_seconds(self) -> float:
        """Get age of this entry in seconds."""
        return time.time() - self.created_at


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set a value in cache with optional TTL."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass


class InMemoryCache(CacheBackend):
    """
    Simple in-memory cache implementation.
    
    Suitable for development and single-instance deployments.
    Not shared between processes.
    """
    
    def __init__(self, max_size: int = 10000):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired:
                del self._cache[key]
                self._misses += 1
                return None
            
            entry.hit_count += 1
            self._hits += 1
            return entry.value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Set a value in cache."""
        async with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self._max_size and key not in self._cache:
                await self._evict_oldest()
            
            expires_at = None
            if ttl_seconds is not None:
                expires_at = time.time() + ttl_seconds
            
            self._cache[key] = CacheEntry(
                value=value,
                expires_at=expires_at,
            )
    
    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            if entry.is_expired:
                del self._cache[key]
                return False
            return True
    
    async def clear(self) -> None:
        """Clear all cached values."""
        async with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            return {
                "backend": "in_memory",
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
            }
    
    async def _evict_oldest(self) -> None:
        """Evict the oldest entry (simple LRU approximation)."""
        if not self._cache:
            return
        
        # Find oldest entry
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
        del self._cache[oldest_key]


class RedisCache(CacheBackend):
    """
    Redis-based cache implementation.
    
    Suitable for production deployments with multiple instances.
    Requires redis package: pip install redis
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        prefix: str = "exohab:",
        password: Optional[str] = None,
    ):
        self._host = host
        self._port = port
        self._db = db
        self._prefix = prefix
        self._password = password
        self._client = None
        self._hits = 0
        self._misses = 0
    
    async def _get_client(self):
        """Lazy initialization of Redis client."""
        if self._client is None:
            try:
                import redis.asyncio as redis
                self._client = redis.Redis(
                    host=self._host,
                    port=self._port,
                    db=self._db,
                    password=self._password,
                    decode_responses=True,
                )
            except ImportError:
                raise ImportError(
                    "Redis cache requires redis package. "
                    "Install with: pip install redis"
                )
        return self._client
    
    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self._prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis."""
        client = await self._get_client()
        full_key = self._make_key(key)
        
        value = await client.get(full_key)
        
        if value is None:
            self._misses += 1
            return None
        
        self._hits += 1
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Set a value in Redis."""
        client = await self._get_client()
        full_key = self._make_key(key)
        
        # Serialize value
        serialized = json.dumps(value) if not isinstance(value, str) else value
        
        if ttl_seconds:
            await client.setex(full_key, ttl_seconds, serialized)
        else:
            await client.set(full_key, serialized)
    
    async def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        client = await self._get_client()
        full_key = self._make_key(key)
        result = await client.delete(full_key)
        return result > 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        client = await self._get_client()
        full_key = self._make_key(key)
        return await client.exists(full_key) > 0
    
    async def clear(self) -> None:
        """Clear all keys with our prefix."""
        client = await self._get_client()
        
        # Find all keys with our prefix
        cursor = 0
        while True:
            cursor, keys = await client.scan(cursor, match=f"{self._prefix}*", count=100)
            if keys:
                await client.delete(*keys)
            if cursor == 0:
                break
        
        self._hits = 0
        self._misses = 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        client = await self._get_client()
        
        # Count our keys
        key_count = 0
        cursor = 0
        while True:
            cursor, keys = await client.scan(cursor, match=f"{self._prefix}*", count=100)
            key_count += len(keys)
            if cursor == 0:
                break
        
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
        
        return {
            "backend": "redis",
            "host": self._host,
            "port": self._port,
            "db": self._db,
            "size": key_count,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
        }


# ============================================================
# Cache Key Generators
# ============================================================

def make_cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from arguments.
    
    Uses MD5 hash for consistent, reasonably short keys.
    """
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def make_api_cache_key(service: str, endpoint: str, params: Dict[str, Any]) -> str:
    """Generate cache key for API responses."""
    return f"api:{service}:{endpoint}:{make_cache_key(**params)}"


def make_scoring_cache_key(planet_name: str, config_hash: str) -> str:
    """Generate cache key for scoring results."""
    return f"score:{planet_name}:{config_hash}"


def make_image_prompt_cache_key(planet_name: str, style: str, format: str) -> str:
    """Generate cache key for image prompts."""
    return f"img:{planet_name}:{style}:{format}"


# ============================================================
# Caching Decorators
# ============================================================

def cached(
    ttl_seconds: int = 3600,
    key_func: Optional[Callable[..., str]] = None,
    cache: Optional[CacheBackend] = None,
):
    """
    Decorator to cache async function results.
    
    Args:
        ttl_seconds: Time-to-live for cached values
        key_func: Optional function to generate cache key from args
        cache: Cache backend to use (uses global cache if not provided)
    
    Usage:
        @cached(ttl_seconds=300)
        async def fetch_exoplanet(name: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache backend
            cache_backend = cache or _global_cache
            if cache_backend is None:
                # No cache configured, just call function
                return await func(*args, **kwargs)
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__module__}.{func.__name__}:{make_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = await cache_backend.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache_backend.set(cache_key, result, ttl_seconds)
            logger.debug(f"Cached {cache_key} for {ttl_seconds}s")
            
            return result
        
        return wrapper
    return decorator


# ============================================================
# Global Cache Instance
# ============================================================

_global_cache: Optional[CacheBackend] = None


def configure_cache(backend: str = "memory", **kwargs) -> CacheBackend:
    """
    Configure and set the global cache backend.
    
    Args:
        backend: One of "memory", "redis", "none"
        **kwargs: Backend-specific configuration
        
    Returns:
        Configured cache backend
    """
    global _global_cache
    
    if backend == "memory":
        _global_cache = InMemoryCache(**kwargs)
    elif backend == "redis":
        _global_cache = RedisCache(**kwargs)
    elif backend == "none":
        _global_cache = None
    else:
        raise ValueError(f"Unknown cache backend: {backend}")
    
    logger.info(f"Configured cache backend: {backend}")
    return _global_cache


def get_cache() -> Optional[CacheBackend]:
    """Get the global cache backend."""
    return _global_cache


# ============================================================
# Cache TTL Constants
# ============================================================

class CacheTTL:
    """Standard TTL values for different data types."""
    
    # API responses (can change occasionally)
    NASA_API = 3600 * 6  # 6 hours
    ESA_API = 3600 * 6   # 6 hours
    
    # Scoring results (depends on config, but data doesn't change often)
    SCORING_RESULT = 3600 * 24  # 24 hours
    
    # Image prompts (deterministic, can cache longer)
    IMAGE_PROMPT = 3600 * 24 * 7  # 7 days
    
    # Generated images (expensive, cache for a while)
    GENERATED_IMAGE = 3600 * 24 * 30  # 30 days
    
    # Exoplanet catalog data (changes infrequently)
    CATALOG_DATA = 3600 * 24  # 24 hours
    
    # Health checks and stats (very short)
    STATS = 60  # 1 minute

"""
Redis caching layer for AI responses, stadium info, routes, and translations.

Provides significant performance improvements by caching expensive operations:
- AI responses (300s TTL)
- Stadium information (600s TTL)
- Navigation routes (300s TTL)
- Translation results (600s TTL)

Falls back gracefully when Redis is unavailable - all operations continue
to work without caching.
"""
from __future__ import annotations

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional

from app.config import get_settings

logger = logging.getLogger("stadiumos.cache")
settings = get_settings()

_redis_client = None
_redis_available = False
_redis_init_attempted = False


def _get_redis_client():
    """Lazily initialize Redis client. Returns None if Redis is unavailable."""
    global _redis_client, _redis_available, _redis_init_attempted
    
    if _redis_init_attempted:
        return _redis_client if _redis_available else None
    
    _redis_init_attempted = True
    
    try:
        import redis
        
        _redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        # Test connection
        _redis_client.ping()
        _redis_available = True
        logger.info("Redis cache initialized successfully")
        return _redis_client
    except Exception as exc:
        logger.warning("Redis unavailable, caching disabled: %s", exc)
        _redis_client = None
        _redis_available = False
        return None


def _generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a deterministic cache key from function arguments."""
    # Convert args and kwargs to a stable string representation
    key_data = {
        "args": [str(arg) for arg in args],
        "kwargs": {k: str(v) for k, v in sorted(kwargs.items())}
    }
    key_str = json.dumps(key_data, sort_keys=True)
    key_hash = hashlib.sha256(key_str.encode()).hexdigest()[:16]
    return f"{prefix}:{key_hash}"


async def get_cached(key: str) -> Optional[str]:
    """Retrieve cached value. Returns None if not found or Redis unavailable."""
    client = _get_redis_client()
    if client is None:
        return None
    
    try:
        value = client.get(key)
        if value:
            logger.debug("Cache hit: %s", key)
        return value
    except Exception as exc:
        logger.warning("Cache get failed for %s: %s", key, exc)
        return None


async def set_cached(key: str, value: str, expire_seconds: int = 300) -> bool:
    """Store value in cache with expiration. Returns False if Redis unavailable."""
    client = _get_redis_client()
    if client is None:
        return False
    
    try:
        client.setex(key, expire_seconds, value)
        logger.debug("Cache set: %s (TTL: %ds)", key, expire_seconds)
        return True
    except Exception as exc:
        logger.warning("Cache set failed for %s: %s", key, exc)
        return False


async def delete_cached(key: str) -> bool:
    """Delete cached value. Returns False if Redis unavailable."""
    client = _get_redis_client()
    if client is None:
        return False
    
    try:
        client.delete(key)
        logger.debug("Cache delete: %s", key)
        return True
    except Exception as exc:
        logger.warning("Cache delete failed for %s: %s", key, exc)
        return False


async def flush_cache(pattern: str = "*") -> int:
    """
    Flush cache entries matching pattern.
    Returns count of deleted keys, or 0 if Redis unavailable.
    
    WARNING: Use with caution in production.
    """
    client = _get_redis_client()
    if client is None:
        return 0
    
    try:
        keys = client.keys(pattern)
        if keys:
            count = client.delete(*keys)
            logger.info("Flushed %d cache entries matching '%s'", count, pattern)
            return count
        return 0
    except Exception as exc:
        logger.warning("Cache flush failed for pattern '%s': %s", pattern, exc)
        return 0


def cached(prefix: str, expire_seconds: int = 300):
    """
    Decorator to cache function results in Redis.
    
    Args:
        prefix: Cache key prefix (e.g., "ai_response", "navigation")
        expire_seconds: Cache TTL in seconds (default: 300)
    
    Example:
        @cached("navigation", expire_seconds=300)
        async def get_route(origin: str, dest: str):
            # expensive computation
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            cache_key = _generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = await get_cached(cache_key)
            if cached_value is not None:
                try:
                    # Deserialize cached result
                    return json.loads(cached_value)
                except json.JSONDecodeError:
                    # If deserialization fails, return as string
                    return cached_value
            
            # Cache miss - compute result
            result = await func(*args, **kwargs)
            
            # Store in cache (only if result is not None)
            if result is not None:
                try:
                    serialized = json.dumps(result) if not isinstance(result, str) else result
                    await set_cached(cache_key, serialized, expire_seconds)
                except (TypeError, json.JSONEncodeError):
                    # If serialization fails, log but don't crash
                    logger.warning("Failed to cache result for %s", cache_key)
            
            return result
        return wrapper
    return decorator


def is_cache_available() -> bool:
    """Check if Redis cache is available."""
    client = _get_redis_client()
    return client is not None and _redis_available


async def get_cache_stats() -> dict[str, Any]:
    """Get cache statistics for monitoring."""
    client = _get_redis_client()
    if client is None:
        return {
            "available": False,
            "keys": 0,
            "memory_used": "N/A",
        }
    
    try:
        info = client.info("stats")
        keyspace = client.info("keyspace")
        
        total_keys = sum(
            int(db_info.get("keys", 0))
            for db_info in keyspace.values()
            if isinstance(db_info, dict)
        )
        
        return {
            "available": True,
            "keys": total_keys,
            "total_commands_processed": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": (
                info.get("keyspace_hits", 0) / 
                (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
            ) * 100,
        }
    except Exception as exc:
        logger.warning("Failed to get cache stats: %s", exc)
        return {
            "available": False,
            "error": str(exc),
        }

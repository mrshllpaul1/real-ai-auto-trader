"""Smart Caching Service with Redis fallback to In-Memory

Provides intelligent caching with:
- Redis primary cache (if available)
- In-memory fallback cache
- Request deduplication
- Cache invalidation strategies
"""

import os
import json
import hashlib
import asyncio
from typing import Optional, Any, Dict, Callable
from datetime import datetime, timedelta
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Try to import redis
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.info("Redis not available, using in-memory cache")


class InMemoryCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, max_size: int = 10000):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self._cache:
            entry = self._cache[key]
            if entry["expires_at"] > datetime.utcnow():
                self._stats["hits"] += 1
                return entry["value"]
            else:
                del self._cache[key]
        self._stats["misses"] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL in seconds."""
        # Evict oldest entries if at capacity
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["created_at"])
            del self._cache[oldest_key]
            self._stats["evictions"] += 1
        
        self._cache[key] = {
            "value": value,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(seconds=ttl)
        }
        self._stats["sets"] += 1
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    async def clear(self) -> bool:
        """Clear all cache entries."""
        self._cache.clear()
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._stats["hits"] + self._stats["misses"]
        return {
            **self._stats,
            "size": len(self._cache),
            "max_size": self._max_size,
            "hit_rate": (self._stats["hits"] / total * 100) if total > 0 else 0
        }


class SmartCache:
    """Smart cache with Redis primary and in-memory fallback."""
    
    def __init__(self):
        self._redis: Optional[Any] = None
        self._memory_cache = InMemoryCache()
        self._use_redis = False
        self._initialized = False
    
    async def initialize(self):
        """Initialize cache connections."""
        if self._initialized:
            return
        
        if REDIS_AVAILABLE:
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
            try:
                self._redis = aioredis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self._redis.ping()
                self._use_redis = True
                logger.info("Redis cache connected successfully")
            except Exception as e:
                logger.warning(f"Redis connection failed, using in-memory: {e}")
                self._use_redis = False
        
        self._initialized = True
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        await self.initialize()
        
        if self._use_redis:
            try:
                value = await self._redis.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get error, falling back to memory: {e}")
        
        return await self._memory_cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache."""
        await self.initialize()
        
        # Always set in memory cache as backup
        await self._memory_cache.set(key, value, ttl)
        
        if self._use_redis:
            try:
                await self._redis.setex(key, ttl, json.dumps(value))
                return True
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
        
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        await self.initialize()
        await self._memory_cache.delete(key)
        
        if self._use_redis:
            try:
                await self._redis.delete(key)
            except Exception:
                pass
        return True
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        count = 0
        if self._use_redis:
            try:
                keys = await self._redis.keys(pattern)
                if keys:
                    count = await self._redis.delete(*keys)
            except Exception:
                pass
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "backend": "redis" if self._use_redis else "memory",
            "redis_available": REDIS_AVAILABLE,
            "redis_connected": self._use_redis,
            "memory_stats": self._memory_cache.get_stats()
        }


class RequestDeduplicator:
    """Deduplicates concurrent identical requests."""
    
    def __init__(self):
        self._pending: Dict[str, asyncio.Task] = {}
        self._stats = {
            "deduplicated": 0,
            "unique": 0
        }
    
    def _make_key(self, *args, **kwargs) -> str:
        """Create a unique key from arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def deduplicate(
        self,
        key: str,
        coroutine: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute coroutine with deduplication."""
        if key in self._pending:
            self._stats["deduplicated"] += 1
            return await self._pending[key]
        
        self._stats["unique"] += 1
        task = asyncio.create_task(coroutine(*args, **kwargs))
        self._pending[key] = task
        
        try:
            result = await task
            return result
        finally:
            self._pending.pop(key, None)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics."""
        total = self._stats["deduplicated"] + self._stats["unique"]
        return {
            **self._stats,
            "pending": len(self._pending),
            "dedup_rate": (self._stats["deduplicated"] / total * 100) if total > 0 else 0
        }


# Singleton instances
_smart_cache: Optional[SmartCache] = None
_deduplicator: Optional[RequestDeduplicator] = None


def get_smart_cache() -> SmartCache:
    """Get or create smart cache instance."""
    global _smart_cache
    if _smart_cache is None:
        _smart_cache = SmartCache()
    return _smart_cache


def get_deduplicator() -> RequestDeduplicator:
    """Get or create deduplicator instance."""
    global _deduplicator
    if _deduplicator is None:
        _deduplicator = RequestDeduplicator()
    return _deduplicator


def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_smart_cache()
            
            # Generate cache key
            key_data = json.dumps({
                "func": func.__name__,
                "args": args[1:] if args else [],  # Skip 'self' if present
                "kwargs": kwargs
            }, sort_keys=True, default=str)
            cache_key = f"{key_prefix}{func.__name__}:{hashlib.md5(key_data.encode()).hexdigest()}"
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


def deduplicated(func: Callable):
    """Decorator for deduplicating concurrent requests."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        dedup = get_deduplicator()
        
        # Generate deduplication key
        key_data = json.dumps({
            "func": func.__name__,
            "args": args[1:] if args else [],
            "kwargs": kwargs
        }, sort_keys=True, default=str)
        dedup_key = f"{func.__name__}:{hashlib.md5(key_data.encode()).hexdigest()}"
        
        return await dedup.deduplicate(dedup_key, func, *args, **kwargs)
    
    return wrapper

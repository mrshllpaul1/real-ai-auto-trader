"""
Response Caching Utility
Provides decorators and utilities for caching API responses
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ResponseCache:
    """
    Simple in-memory response cache with TTL
    For production, consider using Redis for distributed caching
    """
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize response cache
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self.cache = {}
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()
    
    def _generate_key(self, request: Request, **kwargs) -> str:
        """Generate cache key from request using SHA-256 for better collision resistance"""
        # Include path, query params, and any additional kwargs
        key_parts = [
            request.url.path,
            str(sorted(request.query_params.items())),
            str(sorted(kwargs.items()))
        ]
        key_string = "|".join(key_parts)
        # Use SHA-256 instead of MD5 for better collision resistance
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[dict]:
        """Get cached response if not expired"""
        async with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                if datetime.now() < entry['expires_at']:
                    logger.debug(f"Cache HIT: {key}")
                    return entry['data']
                else:
                    # Expired, remove it
                    del self.cache[key]
                    logger.debug(f"Cache EXPIRED: {key}")
            
            logger.debug(f"Cache MISS: {key}")
            return None
    
    async def set(self, key: str, data: dict, ttl: Optional[int] = None):
        """Set cached response with TTL"""
        async with self._lock:
            ttl = ttl or self.default_ttl
            expires_at = datetime.now() + timedelta(seconds=ttl)
            self.cache[key] = {
                'data': data,
                'expires_at': expires_at,
                'created_at': datetime.now()
            }
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
    
    async def clear(self, pattern: Optional[str] = None):
        """Clear cache entries matching pattern (or all if None)"""
        async with self._lock:
            if pattern is None:
                count = len(self.cache)
                self.cache.clear()
                logger.info(f"Cache cleared: {count} entries removed")
            else:
                keys_to_remove = [k for k in self.cache.keys() if pattern in k]
                for key in keys_to_remove:
                    del self.cache[key]
                logger.info(f"Cache cleared: {len(keys_to_remove)} entries matching '{pattern}' removed")
    
    async def get_stats(self) -> dict:
        """Get cache statistics (optimized to avoid expensive serialization)"""
        async with self._lock:
            total = len(self.cache)
            expired = sum(1 for e in self.cache.values() if datetime.now() >= e['expires_at'])
            active = total - expired
            
            # Estimate cache size without expensive json.dumps
            import sys
            cache_size_bytes = sum(sys.getsizeof(v) for v in self.cache.values())
            
            return {
                'total_entries': total,
                'active_entries': active,
                'expired_entries': expired,
                'cache_size_bytes': cache_size_bytes
            }
    
    async def cleanup_expired(self):
        """Remove expired entries from cache"""
        async with self._lock:
            now = datetime.now()
            expired_keys = [k for k, v in self.cache.items() if now >= v['expires_at']]
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.info(f"Cache cleanup: {len(expired_keys)} expired entries removed")


# Global cache instance
_response_cache = ResponseCache(default_ttl=300)


def get_response_cache() -> ResponseCache:
    """Get the global response cache instance"""
    return _response_cache


def cached_response(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching FastAPI endpoint responses
    
    Args:
        ttl: Time-to-live in seconds
        key_prefix: Optional prefix for cache key
    
    Example:
        @router.get("/expensive-endpoint")
        @cached_response(ttl=60)
        async def expensive_endpoint(request: Request):
            # ... expensive computation ...
            return {"data": result}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find Request object in args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request is None:
                # No request object, can't cache
                return await func(*args, **kwargs)
            
            # Generate cache key
            cache_key = f"{key_prefix}:{_response_cache._generate_key(request, **kwargs)}"
            
            # Check cache
            cached_data = await _response_cache.get(cache_key)
            if cached_data is not None:
                # Add cache header
                return JSONResponse(
                    content=cached_data,
                    headers={
                        "X-Cache": "HIT",
                        "X-Cache-TTL": str(ttl),
                        "Cache-Control": f"public, max-age={ttl}"
                    }
                )
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache the result if it's a dict
            if isinstance(result, dict):
                await _response_cache.set(cache_key, result, ttl)
                
                # Add cache header to response
                return JSONResponse(
                    content=result,
                    headers={
                        "X-Cache": "MISS",
                        "X-Cache-TTL": str(ttl),
                        "Cache-Control": f"public, max-age={ttl}"
                    }
                )
            
            return result
        
        return wrapper
    return decorator


def etag_response(func: Callable) -> Callable:
    """
    Decorator for adding ETag support to responses
    Enables conditional requests with If-None-Match header
    
    Example:
        @router.get("/data")
        @etag_response
        async def get_data(request: Request):
            return {"data": "value"}
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Find Request object
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        # Execute function
        result = await func(*args, **kwargs)
        
        if not isinstance(result, dict):
            return result
        
        # Generate ETag from response content using SHA-256
        content_str = json.dumps(result, sort_keys=True)
        # Use SHA-256 instead of MD5 for better collision resistance
        etag = hashlib.sha256(content_str.encode()).hexdigest()[:32]  # Truncate for readability
        
        # Check If-None-Match header
        if request and request.headers.get("If-None-Match") == etag:
            # Content hasn't changed, return 304
            return Response(status_code=304, headers={"ETag": etag})
        
        # Return response with ETag
        return JSONResponse(
            content=result,
            headers={"ETag": etag}
        )
    
    return wrapper


async def start_cache_cleanup_task():
    """Start periodic cache cleanup task"""
    async def cleanup_loop():
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            try:
                await _response_cache.cleanup_expired()
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    asyncio.create_task(cleanup_loop())
    logger.info("✅ Response cache cleanup task started")


# Export public API
__all__ = [
    'ResponseCache',
    'get_response_cache',
    'cached_response',
    'etag_response',
    'start_cache_cleanup_task'
]

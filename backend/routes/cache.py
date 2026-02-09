"""
Cache Management API Routes
Monitor and manage ML caching system
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from services.ml_cache import (
    ml_cache,
    get_cache_stats,
    cache_health_check,
    clear_all_caches,
    clear_expired_caches
)

router = APIRouter(prefix="/cache", tags=["cache"])


class CacheStatsResponse(BaseModel):
    type: str
    stats: Dict[str, Any]
    health: str


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_statistics():
    """
    Get cache statistics and performance metrics
    
    Returns:
        - Cache type (Redis or Disk)
        - Number of keys
        - Memory usage
        - Hit/miss rate
        - Health status
    """
    try:
        stats = get_cache_stats()
        health = cache_health_check()
        
        return {
            "type": stats.get("type", "unknown"),
            "stats": stats,
            "health": health.get("status", "unknown")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def check_cache_health():
    """
    Check cache system health
    
    Tests:
    - Connectivity
    - Read/write operations
    - Performance
    """
    health = cache_health_check()
    
    if health["status"] != "healthy":
        raise HTTPException(
            status_code=503,
            detail=f"Cache unhealthy: {health.get('error', 'Unknown error')}"
        )
    
    return health


@router.post("/clear/all")
async def clear_all_cache_data():
    """
    Clear ALL cache data
    
    ⚠️ WARNING: This will clear all cached features, predictions, and training data.
    Use only when necessary (e.g., model updates, data corruption).
    """
    try:
        clear_all_caches()
        return {
            "message": "All caches cleared successfully",
            "timestamp": "now"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear/expired")
async def clear_expired_cache_data():
    """
    Clear expired cache entries
    
    Note: Redis handles this automatically.
    This endpoint is mainly for disk cache cleanup.
    """
    try:
        clear_expired_caches()
        return {
            "message": "Expired caches cleared",
            "timestamp": "now"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear/pattern/{pattern}")
async def clear_cache_pattern(pattern: str):
    """
    Clear caches matching a pattern
    
    Examples:
    - `features:*` - Clear all feature caches
    - `prediction:*:BTC:*` - Clear all BTC predictions
    - `training:*` - Clear all training data caches
    """
    try:
        ml_cache.clear_pattern(pattern)
        return {
            "message": f"Caches matching '{pattern}' cleared",
            "pattern": pattern
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keys/count")
async def get_cache_key_count():
    """Get total number of cached items"""
    stats = get_cache_stats()
    return {
        "total_keys": stats.get("keys", 0),
        "type": stats.get("type", "unknown")
    }


@router.get("/performance")
async def get_cache_performance():
    """
    Get cache performance metrics
    
    Returns hit rate, latency, and efficiency stats
    """
    stats = get_cache_stats()
    
    # Calculate performance metrics
    hits = stats.get("hits", 0)
    misses = stats.get("misses", 0)
    total = hits + misses
    
    if total > 0:
        hit_rate = (hits / total) * 100
        efficiency = "excellent" if hit_rate > 80 else "good" if hit_rate > 60 else "needs improvement"
    else:
        hit_rate = 0
        efficiency = "no data"
    
    return {
        "hit_rate_percent": round(hit_rate, 2),
        "total_requests": total,
        "cache_hits": hits,
        "cache_misses": misses,
        "efficiency": efficiency,
        "memory_used": stats.get("memory_used", "N/A")
    }

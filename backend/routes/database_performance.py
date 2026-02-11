"""
Database Performance Monitoring Route
Provides endpoints for monitoring database indexes, query performance, and response caching
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/database", tags=["database"])


@router.get("/indexes/stats")
async def get_index_stats() -> Dict[str, Any]:
    """
    Get statistics about database indexes
    Returns index counts and sizes for all collections
    """
    try:
        from init.database_indexes import get_index_stats
        stats = await get_index_stats()
        
        # Calculate totals
        total_indexes = sum(s.get('index_count', 0) for s in stats.values())
        total_size_mb = sum(s.get('total_index_size_mb', 0) for s in stats.values())
        
        return {
            "status": "success",
            "total_indexes": total_indexes,
            "total_size_mb": round(total_size_mb, 2),
            "collections": stats
        }
    except Exception as e:
        logger.error(f"Failed to get index stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indexes/slow-queries")
async def analyze_slow_queries() -> Dict[str, Any]:
    """
    Analyze slow queries and get optimization recommendations
    Returns queries that took more than 100ms
    """
    try:
        from init.database_indexes import analyze_slow_queries
        recommendations = await analyze_slow_queries()
        
        return {
            "status": "success",
            "slow_query_count": len(recommendations),
            "queries": recommendations[:20]  # Limit to top 20
        }
    except Exception as e:
        logger.error(f"Failed to analyze slow queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/indexes/rebuild")
async def rebuild_indexes() -> Dict[str, Any]:
    """
    Rebuild all database indexes
    Use this to recreate indexes after schema changes or for maintenance
    """
    try:
        from init.database_indexes import ensure_database_indexes
        result = await ensure_database_indexes()
        
        return {
            "status": "success",
            "message": "Indexes rebuilt successfully",
            "stats": result
        }
    except Exception as e:
        logger.error(f"Failed to rebuild indexes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/pool")
async def get_connection_pool_stats() -> Dict[str, Any]:
    """
    Get connection pool statistics
    Returns current connections, available connections, and pool configuration
    """
    try:
        from config.database import get_pool_stats
        stats = await get_pool_stats()
        
        return {
            "status": "success",
            **stats
        }
    except Exception as e:
        logger.error(f"Failed to get pool stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def database_health() -> Dict[str, Any]:
    """
    Comprehensive database health check
    Returns database status, connection pool info, and index stats
    """
    try:
        from config.database import health_check
        health = await health_check()
        
        return {
            "status": "success",
            "health": health
        }
    except Exception as e:
        logger.error(f"Failed to check database health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get response cache statistics
    Returns cache size, hit/miss rates, and active entries
    """
    try:
        from middleware.response_cache import get_response_cache
        cache = get_response_cache()
        stats = await cache.get_stats()
        
        return {
            "status": "success",
            **stats
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache(pattern: str = None) -> Dict[str, Any]:
    """
    Clear response cache
    Optionally provide a pattern to clear specific entries
    """
    try:
        from middleware.response_cache import get_response_cache
        cache = get_response_cache()
        await cache.clear(pattern)
        
        return {
            "status": "success",
            "message": f"Cache cleared{f' (pattern: {pattern})' if pattern else ''}"
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

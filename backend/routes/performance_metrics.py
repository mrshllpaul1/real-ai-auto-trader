"""
Performance Metrics API
=======================
Endpoints for monitoring cache, circuit breakers, and database performance.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/performance", tags=["Performance Metrics"])


@router.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics including hit rate, size, and efficiency.
    """
    try:
        from services.cache_manager import get_cache_manager
        cache = get_cache_manager()
        return {
            "status": "ok",
            "cache": cache.get_stats()
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/cache/clear")
async def clear_cache(prefix: str = None) -> Dict[str, Any]:
    """
    Clear cache entries, optionally by prefix.
    
    Args:
        prefix: Optional prefix to clear specific cache entries
    """
    try:
        from services.cache_manager import get_cache_manager
        cache = get_cache_manager()
        await cache.clear(prefix)
        return {
            "status": "ok",
            "message": f"Cache cleared" + (f" for prefix '{prefix}'" if prefix else "")
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.get("/circuit-breakers")
async def get_circuit_breaker_stats() -> Dict[str, Any]:
    """
    Get status of all circuit breakers.
    """
    try:
        from utils.circuit_breaker import get_all_circuit_breakers
        return {
            "status": "ok",
            "circuit_breakers": get_all_circuit_breakers()
        }
    except Exception as e:
        logger.error(f"Failed to get circuit breaker stats: {e}")
        return {"status": "error", "message": str(e), "circuit_breakers": {}}


@router.get("/database/indexes")
async def get_database_indexes() -> Dict[str, Any]:
    """
    Get database index statistics.
    """
    try:
        from config.database import db
        from init.database_indexes import get_index_stats
        stats = await get_index_stats(db)
        return {
            "status": "ok",
            "indexes": stats
        }
    except Exception as e:
        logger.error(f"Failed to get index stats: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/database/create-indexes")
async def create_database_indexes() -> Dict[str, Any]:
    """
    Create performance indexes for all collections.
    Safe to run multiple times - existing indexes are skipped.
    """
    try:
        from config.database import db
        from init.database_indexes import create_indexes
        results = await create_indexes(db)
        return {
            "status": "ok",
            "results": results
        }
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.get("/summary")
async def get_performance_summary() -> Dict[str, Any]:
    """
    Get comprehensive performance summary including all metrics.
    """
    summary = {
        "status": "ok",
        "cache": {},
        "circuit_breakers": {},
        "database": {},
    }
    
    # Cache stats
    try:
        from services.cache_manager import get_cache_manager
        cache = get_cache_manager()
        summary["cache"] = cache.get_stats()
    except Exception as e:
        summary["cache"] = {"error": "An internal error occurred"}
    
    # Circuit breaker stats
    try:
        from utils.circuit_breaker import get_all_circuit_breakers
        summary["circuit_breakers"] = get_all_circuit_breakers()
    except Exception as e:
        summary["circuit_breakers"] = {"error": "An internal error occurred"}
    
    # Database pool stats
    try:
        from config.database import get_pool_stats
        summary["database"] = await get_pool_stats()
    except Exception as e:
        summary["database"] = {"error": "An internal error occurred"}
    
    return summary

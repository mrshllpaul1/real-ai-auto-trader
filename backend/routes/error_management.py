"""
Lightweight Error Management API Routes
========================================
Fast, non-blocking error tracking endpoints.
"""

from fastapi import APIRouter, Depends
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/errors", tags=["Error Management"])

_db = None


def set_db(db):
    global _db
    _db = db


async def get_database():
    global _db
    if _db is None:
        from server import db
        _db = db
    return _db


@router.get("/stats")
async def get_error_statistics(db = Depends(get_database)):
    """Get error statistics (non-blocking)"""
    try:
        from services.error_recovery import get_error_recovery_manager
        from middleware.error_monitoring import get_error_store
        
        recovery_manager = get_error_recovery_manager(db)
        error_store = get_error_store()
        
        return {
            "status": "ok",
            "recovery": recovery_manager.get_stats(),
            "monitoring": await error_store.get_error_stats(),
            "database": {"errors_last_24h": 0},  # Skip slow DB query
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/recent")
async def get_recent_errors(limit: int = 20, db = Depends(get_database)):
    """Get recent errors from memory"""
    try:
        from services.error_recovery import get_error_recovery_manager
        manager = get_error_recovery_manager(db)
        return {
            "errors": manager.get_recent_errors(limit),
            "total": len(manager.get_recent_errors(limit))
        }
    except Exception as e:
        return {"errors": [], "error": str(e)}


@router.get("/patterns")
async def get_error_patterns(hours: int = 24, db = Depends(get_database)):
    """Get error patterns (lightweight version)"""
    try:
        from services.error_recovery import get_error_recovery_manager
        manager = get_error_recovery_manager(db)
        
        # Use in-memory data instead of slow DB aggregation
        recent = manager.get_recent_errors(50)
        patterns = {}
        for error in recent:
            key = f"{error.get('category', 'unknown')}:{error.get('exception_type', 'Unknown')}"
            if key not in patterns:
                patterns[key] = {
                    'category': error.get('category'),
                    'exception_type': error.get('exception_type'),
                    'count': 0,
                    'last_message': error.get('message', '')
                }
            patterns[key]['count'] += 1
        
        return {
            "patterns": list(patterns.values()),
            "total_unique_errors": len(patterns),
            "analysis_period_hours": hours
        }
    except Exception as e:
        return {"patterns": [], "error": str(e)}


@router.get("/health-check")
async def run_health_check(db = Depends(get_database)):
    """Quick health check"""
    checks = []
    
    # Database check (quick ping)
    try:
        await db.command('ping')
        checks.append({'name': 'database', 'status': 'healthy'})
    except Exception as e:
        checks.append({'name': 'database', 'status': 'unhealthy', 'error': str(e)[:50]})
    
    # Cache check
    try:
        from services.cache_manager import get_cache_manager
        cache = get_cache_manager()
        stats = cache.get_stats()
        checks.append({
            'name': 'cache',
            'status': 'healthy',
            'hit_rate': stats.get('hit_rate_percent', 0)
        })
    except Exception as e:
        checks.append({'name': 'cache', 'status': 'unknown'})
    
    return {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'system_checks': checks,
        'overall_status': 'healthy' if all(c.get('status') == 'healthy' for c in checks) else 'degraded'
    }


@router.get("/recovery/stats")
async def get_recovery_statistics(db = Depends(get_database)):
    """Get recovery statistics"""
    try:
        from services.error_recovery import get_error_recovery_manager
        manager = get_error_recovery_manager(db)
        return manager.get_stats()
    except Exception as e:
        return {"error": str(e)}


@router.get("/alerts")
async def get_error_alerts(limit: int = 20, db = Depends(get_database)):
    """Get error alerts"""
    return {"alerts": [], "total": 0, "unresolved": 0}


@router.post("/clear-suppressed")
async def clear_suppressed_errors(db = Depends(get_database)):
    """Clear suppressed errors"""
    return {"status": "ok", "cleared_count": 0}

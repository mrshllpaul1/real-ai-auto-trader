"""
Error Management API Routes
============================
Endpoints for error tracking, recovery status, and debugging.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
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


class ErrorQueryParams(BaseModel):
    category: Optional[str] = None
    severity: Optional[str] = None
    hours: int = 24
    limit: int = 100


@router.get("/stats")
async def get_error_statistics(db = Depends(get_database)):
    """
    Get comprehensive error statistics including:
    - Total errors by category
    - Recovery rate
    - Recent error trends
    """
    try:
        from services.error_recovery import get_error_recovery_manager
        from middleware.error_monitoring import get_error_store
        
        recovery_manager = get_error_recovery_manager(db)
        error_store = get_error_store()
        
        # Get stats from both sources
        recovery_stats = recovery_manager.get_stats()
        monitoring_stats = await error_store.get_error_stats()
        
        # Get recent errors from database
        recent_count = 0
        if db is not None:
            try:
                cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
                recent_count = await db.error_history.count_documents({
                    'timestamp': {'$gte': cutoff.isoformat()}
                })
            except Exception:
                pass
        
        return {
            "status": "ok",
            "recovery": recovery_stats,
            "monitoring": monitoring_stats,
            "database": {
                "errors_last_24h": recent_count
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get error stats: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/recent")
async def get_recent_errors(
    category: Optional[str] = None,
    severity: Optional[str] = None,
    hours: int = 24,
    limit: int = 50,
    db = Depends(get_database)
):
    """
    Get recent errors with filtering options.
    """
    try:
        from middleware.error_monitoring import get_error_store
        
        # Get from in-memory store
        error_store = get_error_store()
        in_memory_errors = await error_store.get_recent_errors(
            limit=limit,
            severity=severity,
            error_type=category
        )
        
        # Get from database if available
        db_errors = []
        if db:
            query = {}
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            query['timestamp'] = {'$gte': cutoff.isoformat()}
            
            if category:
                query['category'] = category
            
            cursor = db.error_history.find(query).sort('timestamp', -1).limit(limit)
            async for doc in cursor:
                doc['_id'] = str(doc['_id'])
                db_errors.append(doc)
        
        return {
            "in_memory": in_memory_errors,
            "from_database": db_errors,
            "total": len(in_memory_errors) + len(db_errors)
        }
    except Exception as e:
        logger.error(f"Failed to get recent errors: {e}")
        return {"errors": [], "error": str(e)}


@router.get("/patterns")
async def get_error_patterns(hours: int = 24, db = Depends(get_database)):
    """
    Analyze error patterns to identify recurring issues.
    """
    try:
        if db is None:
            return {"patterns": [], "message": "Database not available"}
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Aggregate errors by fingerprint
        pipeline = [
            {'$match': {'timestamp': {'$gte': cutoff.isoformat()}}},
            {'$group': {
                '_id': '$fingerprint',
                'count': {'$sum': 1},
                'category': {'$first': '$category'},
                'message': {'$first': '$message'},
                'first_seen': {'$min': '$timestamp'},
                'last_seen': {'$max': '$timestamp'}
            }},
            {'$sort': {'count': -1}},
            {'$limit': 20}
        ]
        
        patterns = []
        try:
            async for doc in db.error_history.aggregate(pipeline):
                patterns.append({
                    'fingerprint': doc['_id'],
                    'occurrences': doc['count'],
                    'category': doc['category'],
                    'message': doc['message'][:200] if doc.get('message') else '',
                    'first_seen': doc['first_seen'],
                    'last_seen': doc['last_seen'],
                    'is_recurring': doc['count'] > 3
                })
        except Exception as e:
            logger.warning(f"Error aggregating patterns: {e}")
        
        return {
            "patterns": patterns,
            "total_unique_errors": len(patterns),
            "recurring_count": sum(1 for p in patterns if p['is_recurring']),
            "analysis_period_hours": hours
        }
    except Exception as e:
        logger.error(f"Failed to analyze error patterns: {e}")
        return {"patterns": [], "error": str(e)}


@router.get("/health-check")
async def run_health_check(db = Depends(get_database)):
    """
    Run comprehensive health check and report issues.
    """
    try:
        from services.error_recovery import get_error_recovery_manager
        
        manager = get_error_recovery_manager(db)
        results = await manager.run_health_check()
        
        # Add additional system checks
        checks = []
        
        # Database check
        try:
            await db.command('ping')
            checks.append({'name': 'database', 'status': 'healthy'})
        except Exception as e:
            checks.append({'name': 'database', 'status': 'unhealthy', 'error': str(e)})
        
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
            checks.append({'name': 'cache', 'status': 'unhealthy', 'error': str(e)})
        
        # Circuit breaker check
        try:
            from utils.circuit_breaker import get_all_circuit_breakers
            breakers = get_all_circuit_breakers()
            open_breakers = [name for name, cb in breakers.items() if cb.get('state') == 'open']
            checks.append({
                'name': 'circuit_breakers',
                'status': 'degraded' if open_breakers else 'healthy',
                'open_circuits': open_breakers
            })
        except Exception as e:
            checks.append({'name': 'circuit_breakers', 'status': 'unknown', 'error': str(e)})
        
        results['system_checks'] = checks
        results['overall_status'] = 'healthy' if all(
            c.get('status') in ['healthy', 'unknown'] for c in checks
        ) else 'degraded'
        
        return results
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/clear-suppressed")
async def clear_suppressed_errors(db = Depends(get_database)):
    """
    Clear suppressed error fingerprints to allow alerts again.
    """
    try:
        from services.error_recovery import get_error_recovery_manager
        
        manager = get_error_recovery_manager(db)
        count = len(manager._suppressed_errors)
        manager._suppressed_errors.clear()
        
        return {
            "status": "ok",
            "cleared_count": count,
            "message": f"Cleared {count} suppressed error fingerprints"
        }
    except Exception as e:
        logger.error(f"Failed to clear suppressed errors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recovery/stats")
async def get_recovery_statistics(db = Depends(get_database)):
    """
    Get error recovery statistics.
    """
    try:
        from services.error_recovery import get_error_recovery_manager
        
        manager = get_error_recovery_manager(db)
        return manager.get_stats()
    except Exception as e:
        logger.error(f"Failed to get recovery stats: {e}")
        return {"error": str(e)}


@router.get("/alerts")
async def get_error_alerts(
    resolved: Optional[bool] = None,
    limit: int = 50,
    db = Depends(get_database)
):
    """
    Get error alerts.
    """
    try:
        if db is None:
            return {"alerts": [], "message": "Database not available"}
        
        query = {'type': 'error_alert'}
        if resolved is not None:
            query['resolved'] = resolved
        
        cursor = db.alerts.find(query).sort('timestamp', -1).limit(limit)
        
        alerts = []
        async for doc in cursor:
            doc['_id'] = str(doc['_id'])
            alerts.append(doc)
        
        return {
            "alerts": alerts,
            "total": len(alerts),
            "unresolved": sum(1 for a in alerts if not a.get('resolved'))
        }
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        return {"alerts": [], "error": str(e)}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, db = Depends(get_database)):
    """
    Mark an alert as resolved.
    """
    try:
        if db is None:
            raise HTTPException(status_code=503, detail="Database not available")
        
        from bson import ObjectId
        result = await db.alerts.update_one(
            {'_id': ObjectId(alert_id)},
            {'$set': {
                'resolved': True,
                'resolved_at': datetime.now(timezone.utc)
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"status": "ok", "alert_id": alert_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/endpoint/{endpoint_path:path}")
async def debug_endpoint(endpoint_path: str, db = Depends(get_database)):
    """
    Get debug information for a specific endpoint.
    """
    try:
        if not db:
            return {"message": "Database not available"}
        
        # Get recent errors for this endpoint
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        
        errors = []
        cursor = db.error_history.find({
            'context.endpoint': {'$regex': endpoint_path, '$options': 'i'},
            'timestamp': {'$gte': cutoff.isoformat()}
        }).sort('timestamp', -1).limit(20)
        
        async for doc in cursor:
            doc['_id'] = str(doc['_id'])
            errors.append(doc)
        
        return {
            "endpoint": endpoint_path,
            "errors_24h": len(errors),
            "recent_errors": errors,
            "recommendations": _get_debug_recommendations(errors)
        }
    except Exception as e:
        logger.error(f"Failed to debug endpoint: {e}")
        return {"error": str(e)}


def _get_debug_recommendations(errors: List[Dict]) -> List[str]:
    """Generate debugging recommendations based on errors"""
    recommendations = []
    
    if not errors:
        return ["No recent errors found for this endpoint"]
    
    # Analyze error categories
    categories = [e.get('category', 'unknown') for e in errors]
    
    if categories.count('timeout') > len(errors) * 0.3:
        recommendations.append("Consider increasing timeout values or optimizing slow operations")
    
    if categories.count('database') > len(errors) * 0.3:
        recommendations.append("Check database connection pool and query performance")
    
    if categories.count('external_api') > len(errors) * 0.3:
        recommendations.append("Check external API status and implement better fallback mechanisms")
    
    if categories.count('rate_limit') > len(errors) * 0.3:
        recommendations.append("Implement request throttling or caching to reduce API calls")
    
    if len(set(e.get('fingerprint') for e in errors)) < len(errors) * 0.5:
        recommendations.append("Many duplicate errors detected - consider fixing the root cause")
    
    if not recommendations:
        recommendations.append("Review error messages and stack traces for specific issues")
    
    return recommendations

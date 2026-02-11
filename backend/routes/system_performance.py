"""
System Performance Monitoring API Routes
Provides endpoints for monitoring system resource usage and performance
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

from services.performance_optimizer import (
    get_performance_monitor,
    MemoryOptimizer
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system-performance", tags=["System Performance"])

# Global references
_db = None


def set_dependencies(database):
    """Set dependencies from main app"""
    global _db
    _db = database


@router.get("/metrics")
async def get_system_metrics():
    """
    Get current system performance metrics
    
    Returns:
        Current CPU, memory usage, and uptime
    """
    try:
        monitor = get_performance_monitor()
        metrics = monitor.get_current_metrics()
        
        return {
            "success": True,
            "metrics": metrics,
            "status": "healthy" if metrics.get("memory_percent", 100) < 90 else "warning"
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory")
async def get_memory_stats():
    """
    Get detailed memory statistics
    
    Returns:
        Memory usage breakdown
    """
    try:
        monitor = get_performance_monitor()
        metrics = monitor.get_current_metrics()
        
        return {
            "success": True,
            "memory_mb": metrics.get("memory_mb", 0),
            "memory_percent": metrics.get("memory_percent", 0),
            "threshold_warning": 80,  # Warning at 80%
            "threshold_critical": 90,  # Critical at 90%
            "status": "ok" if metrics.get("memory_percent", 0) < 80 else "warning"
        }
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def force_memory_cleanup():
    """
    Force garbage collection and memory cleanup
    
    Use sparingly - only when memory usage is high
    """
    try:
        # Get metrics before cleanup
        monitor = get_performance_monitor()
        before = monitor.get_current_metrics()
        
        # Force garbage collection
        MemoryOptimizer.force_garbage_collection()
        
        # Get metrics after cleanup
        after = monitor.get_current_metrics()
        
        memory_freed = before.get("memory_mb", 0) - after.get("memory_mb", 0)
        
        return {
            "success": True,
            "message": "Memory cleanup completed",
            "memory_before_mb": before.get("memory_mb", 0),
            "memory_after_mb": after.get("memory_mb", 0),
            "memory_freed_mb": round(memory_freed, 2)
        }
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def system_health_check():
    """
    Check overall system health based on performance metrics
    
    Returns:
        Health status with recommendations
    """
    try:
        monitor = get_performance_monitor()
        metrics = monitor.get_current_metrics()
        
        cpu_percent = metrics.get("cpu_percent", 0)
        memory_percent = metrics.get("memory_percent", 0)
        
        # Determine health status
        issues = []
        recommendations = []
        
        if cpu_percent > 80:
            issues.append("High CPU usage")
            recommendations.append("Consider reducing concurrent operations")
        
        if memory_percent > 80:
            issues.append("High memory usage")
            recommendations.append("Run /system-performance/cleanup to free memory")
        
        if memory_percent > 90:
            issues.append("Critical memory usage")
            recommendations.append("Restart application if issues persist")
        
        status = "healthy"
        if len(issues) > 0:
            status = "warning" if memory_percent < 90 and cpu_percent < 90 else "critical"
        
        return {
            "success": True,
            "status": status,
            "metrics": metrics,
            "issues": issues,
            "recommendations": recommendations
        }
    except Exception as e:
        logger.error(f"Error checking health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/training-stats")
async def get_training_performance_stats():
    """
    Get performance statistics for training operations
    
    Returns:
        Training-specific performance metrics
    """
    try:
        if _db is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Get recent training tasks
        training_tasks = await _db.training_tasks.find(
            {},
            {
                "task_id": 1,
                "task_type": 1,
                "duration_seconds": 1,
                "memory_used_mb": 1,
                "status": 1,
                "created_at": 1
            }
        ).sort("created_at", -1).limit(10).to_list(length=10)
        
        # Calculate averages
        total_duration = sum(task.get("duration_seconds", 0) for task in training_tasks)
        avg_duration = total_duration / len(training_tasks) if training_tasks else 0
        
        total_memory = sum(task.get("memory_used_mb", 0) for task in training_tasks)
        avg_memory = total_memory / len(training_tasks) if training_tasks else 0
        
        return {
            "success": True,
            "recent_tasks": len(training_tasks),
            "avg_duration_seconds": round(avg_duration, 2),
            "avg_memory_mb": round(avg_memory, 2),
            "tasks": training_tasks
        }
    except Exception as e:
        logger.error(f"Error getting training stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bottlenecks")
async def identify_bottlenecks():
    """
    Identify potential performance bottlenecks
    
    Returns:
        List of potential bottlenecks with severity
    """
    try:
        monitor = get_performance_monitor()
        metrics = monitor.get_current_metrics()
        
        bottlenecks = []
        
        # Check CPU
        cpu_percent = metrics.get("cpu_percent", 0)
        if cpu_percent > 80:
            bottlenecks.append({
                "type": "cpu",
                "severity": "high" if cpu_percent > 90 else "medium",
                "current_value": cpu_percent,
                "threshold": 80,
                "recommendation": "Reduce concurrent operations or optimize algorithms"
            })
        
        # Check Memory
        memory_percent = metrics.get("memory_percent", 0)
        if memory_percent > 70:
            bottlenecks.append({
                "type": "memory",
                "severity": "high" if memory_percent > 85 else "medium",
                "current_value": memory_percent,
                "threshold": 70,
                "recommendation": "Clear caches or run garbage collection"
            })
        
        # Check for slow queries (if database is available)
        if _db is not None:
            try:
                # Get slow query stats (example)
                slow_queries = await _db.command("profile", -1)
                if slow_queries and len(slow_queries) > 0:
                    bottlenecks.append({
                        "type": "database",
                        "severity": "medium",
                        "current_value": len(slow_queries),
                        "threshold": 0,
                        "recommendation": "Review and optimize slow database queries"
                    })
            except Exception:
                pass  # Profiling might not be enabled
        
        return {
            "success": True,
            "bottlenecks_found": len(bottlenecks),
            "bottlenecks": bottlenecks,
            "status": "ok" if len(bottlenecks) == 0 else "needs_attention"
        }
    except Exception as e:
        logger.error(f"Error identifying bottlenecks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

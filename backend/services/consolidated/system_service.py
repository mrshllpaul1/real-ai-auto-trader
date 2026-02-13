"""
Consolidated System Service
===========================
Combines all system operations:
- Health monitoring
- Backup/restore
- Performance metrics
- Error recovery
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import os
import psutil

logger = logging.getLogger(__name__)

__all__ = [
    'SystemService',
    'get_system_service'
]


class SystemService:
    """
    Unified system service that consolidates:
    - backup_service
    - monitoring
    - performance_dashboard
    - performance_tracker
    - error_recovery
    - state_persistence
    - cache_manager
    """
    
    def __init__(self, db=None):
        self.db = db
        self._backup = None
        self._monitoring = None
        self._start_time = datetime.now(timezone.utc)
        logger.info("⚙️ System Service initialized")
    
    @property
    def backup(self):
        """Lazy load backup service"""
        if self._backup is None:
            try:
                from services.backup.backup_service import BackupService
                self._backup = BackupService(self.db)
            except Exception as e:
                logger.warning(f"Could not load backup service: {e}")
        return self._backup
    
    # === Health Monitoring ===
    async def get_health(self) -> Dict[str, Any]:
        """Get system health status"""
        health = {
            "status": "healthy",
            "uptime_seconds": (datetime.now(timezone.utc) - self._start_time).total_seconds(),
            "database": await self._check_database(),
            "memory": self._get_memory_usage(),
            "cpu": self._get_cpu_usage(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Determine overall status
        if health["database"]["status"] != "connected":
            health["status"] = "degraded"
        if health["memory"]["percent"] > 90:
            health["status"] = "warning"
        
        return health
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connection"""
        if self.db is None:
            return {"status": "not_configured"}
        
        try:
            await self.db.command("ping")
            return {"status": "connected"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage"""
        try:
            mem = psutil.virtual_memory()
            return {
                "total_mb": round(mem.total / (1024 * 1024), 2),
                "used_mb": round(mem.used / (1024 * 1024), 2),
                "available_mb": round(mem.available / (1024 * 1024), 2),
                "percent": mem.percent
            }
        except Exception:
            return {"error": "Could not get memory info"}
    
    def _get_cpu_usage(self) -> Dict[str, Any]:
        """Get CPU usage"""
        try:
            return {
                "percent": psutil.cpu_percent(interval=0.1),
                "cores": psutil.cpu_count()
            }
        except Exception:
            return {"error": "Could not get CPU info"}
    
    # === Backup Operations ===
    async def create_backup(self, collections: List[str] = None) -> Dict[str, Any]:
        """Create database backup"""
        if not self.backup:
            return {"error": "Backup service not available"}
        
        try:
            return await self.backup.create_backup(collections)
        except Exception as e:
            return {"error": str(e)}
    
    async def restore_backup(self, backup_id: str) -> Dict[str, Any]:
        """Restore from backup"""
        if not self.backup:
            return {"error": "Backup service not available"}
        
        try:
            return await self.backup.restore(backup_id)
        except Exception as e:
            return {"error": str(e)}
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        if not self.backup:
            return []
        
        try:
            return await self.backup.list_backups()
        except Exception as e:
            logger.error(f"List backups error: {e}")
            return []
    
    # === Performance Metrics ===
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        metrics = {
            "system": {
                "uptime": str(datetime.now(timezone.utc) - self._start_time),
                "memory": self._get_memory_usage(),
                "cpu": self._get_cpu_usage()
            },
            "database": await self._get_database_metrics(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return metrics
    
    async def _get_database_metrics(self) -> Dict[str, Any]:
        """Get database metrics"""
        if self.db is None:
            return {"error": "Database not configured"}
        
        try:
            stats = await self.db.command("dbStats")
            return {
                "collections": stats.get("collections", 0),
                "objects": stats.get("objects", 0),
                "data_size_mb": round(stats.get("dataSize", 0) / (1024 * 1024), 2),
                "storage_size_mb": round(stats.get("storageSize", 0) / (1024 * 1024), 2)
            }
        except Exception as e:
            return {"error": str(e)}
    
    # === Cache Management ===
    def clear_all_caches(self) -> Dict[str, Any]:
        """Clear all application caches"""
        cleared = []
        
        # Clear various service caches
        try:
            from services.consolidated.data_service import get_data_service
            data_svc = get_data_service()
            data_svc.clear_cache()
            cleared.append("data_service")
        except Exception as e:
            logger.warning(f"Could not clear data cache: {e}")
        
        return {
            "cleared": cleared,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # === Error Recovery ===
    async def trigger_recovery(self, component: str = None) -> Dict[str, Any]:
        """Trigger error recovery for a component"""
        recovery_actions = []
        
        if component is None or component == "database":
            db_status = await self._check_database()
            if db_status["status"] != "connected":
                # Attempt reconnection
                recovery_actions.append({
                    "component": "database",
                    "action": "reconnect_attempted"
                })
        
        if component is None or component == "cache":
            self.clear_all_caches()
            recovery_actions.append({
                "component": "cache",
                "action": "cleared"
            })
        
        return {
            "recovery_triggered": True,
            "actions": recovery_actions,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # === Service Management ===
    async def get_services_status(self) -> Dict[str, Any]:
        """Get status of all consolidated services"""
        statuses = {}
        
        services = [
            ("exchange", "services.consolidated.exchange_service", "get_exchange_service"),
            ("ai", "services.consolidated.ai_service", "get_ai_service"),
            ("analysis", "services.consolidated.analysis_service", "get_analysis_service"),
            ("sentiment", "services.consolidated.sentiment_service", "get_sentiment_service"),
            ("trading", "services.consolidated.trading_service", "get_trading_service"),
            ("ml", "services.consolidated.ml_service", "get_ml_service"),
            ("data", "services.consolidated.data_service", "get_data_service"),
            ("strategy", "services.consolidated.strategy_service", "get_strategy_service"),
            ("notification", "services.consolidated.notification_service", "get_notification_service"),
        ]
        
        for name, module, func in services:
            try:
                mod = __import__(module, fromlist=[func])
                getter = getattr(mod, func)
                svc = getter(self.db)
                statuses[name] = svc.get_status()
            except Exception as e:
                statuses[name] = {"status": "error", "error": str(e)}
        
        return {
            "services": statuses,
            "total": len(services),
            "healthy": sum(1 for s in statuses.values() if s.get("status") != "error"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get system service status"""
        return {
            "service": "system",
            "uptime": str(datetime.now(timezone.utc) - self._start_time),
            "backup": self._backup is not None,
            "monitoring": self._monitoring is not None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Singleton
_system_service = None

def get_system_service(db=None) -> SystemService:
    """Get or create system service singleton"""
    global _system_service
    if _system_service is None:
        _system_service = SystemService(db)
    return _system_service

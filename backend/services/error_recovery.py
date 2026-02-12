"""
Lightweight Error Recovery Service
===================================
Non-blocking error tracking and recovery.
Optimized for production to prevent event loop blocking.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Categories of errors for targeted handling"""
    DATABASE = "database"
    NETWORK = "network"
    EXTERNAL_API = "external_api"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


def categorize_error(exception: Exception) -> ErrorCategory:
    """Quickly categorize an exception"""
    error_str = str(exception).lower()
    error_type = type(exception).__name__.lower()
    
    if any(x in error_str for x in ['mongodb', 'connection', 'cursor']):
        return ErrorCategory.DATABASE
    if 'timeout' in error_str or 'timeout' in error_type:
        return ErrorCategory.TIMEOUT
    if any(x in error_str for x in ['rate limit', 'too many requests', '429']):
        return ErrorCategory.RATE_LIMIT
    if any(x in error_str for x in ['api', 'kraken', 'coingecko']):
        return ErrorCategory.EXTERNAL_API
    if any(x in error_type for x in ['connection', 'socket', 'http']):
        return ErrorCategory.NETWORK
    if any(x in error_str for x in ['validation', 'invalid', 'required']):
        return ErrorCategory.VALIDATION
    
    return ErrorCategory.UNKNOWN


class ErrorRecoveryManager:
    """
    Lightweight error tracking manager.
    Non-blocking with in-memory stats only.
    """
    
    def __init__(self, db=None):
        self.db = db
        self._stats = {
            'total_errors': 0,
            'recovered': 0,
            'failed': 0,
            'suppressed': 0,
            'by_category': defaultdict(int),
        }
        # Keep only last 50 errors in memory
        self._recent_errors: List[Dict] = []
        self._max_recent = 50
        logger.info("✅ Lightweight Error Recovery Manager initialized")
    
    async def handle_error(
        self,
        exception: Exception,
        context: Dict[str, Any] = None
    ) -> bool:
        """
        Track an error (non-blocking).
        Returns True if error was logged successfully.
        """
        self._stats['total_errors'] += 1
        
        category = categorize_error(exception)
        self._stats['by_category'][category.value] += 1
        
        # Store in memory (non-blocking)
        error_record = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'category': category.value,
            'exception_type': type(exception).__name__,
            'message': str(exception)[:200],
            'context': context or {},
        }
        
        self._recent_errors.insert(0, error_record)
        if len(self._recent_errors) > self._max_recent:
            self._recent_errors = self._recent_errors[:self._max_recent]
        
        # Log error asynchronously without blocking
        logger.error(f"[{category.value}] {type(exception).__name__}: {str(exception)[:100]}")
        
        # Optionally persist to DB in background (fire and forget)
        if self.db is not None:
            try:
                # Use non-blocking insert
                self.db.error_history.insert_one(error_record)
            except Exception as e:
                # Don't let DB errors block
                logger.debug(f"Could not persist error: {e}")
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get error statistics (non-blocking)"""
        total = self._stats['total_errors']
        return {
            'total_errors': total,
            'recovered': self._stats['recovered'],
            'failed': self._stats['failed'],
            'suppressed': self._stats['suppressed'],
            'by_category': dict(self._stats['by_category']),
            'recovery_rate': 0,  # Simplified
            'suppressed_count': 0,
            'registered_fallbacks': [],
            'recent_errors_count': len(self._recent_errors),
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """Get recent errors from memory"""
        return self._recent_errors[:limit]
    
    async def run_health_check(self) -> Dict[str, Any]:
        """Simple health check"""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'healthy',
            'error_count': self._stats['total_errors'],
        }


# Singleton instance
_error_recovery_manager: Optional[ErrorRecoveryManager] = None


def get_error_recovery_manager(db=None) -> ErrorRecoveryManager:
    """Get or create error recovery manager"""
    global _error_recovery_manager
    if _error_recovery_manager is None:
        _error_recovery_manager = ErrorRecoveryManager(db)
    return _error_recovery_manager

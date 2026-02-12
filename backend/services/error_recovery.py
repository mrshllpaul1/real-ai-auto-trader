"""
Enhanced Error Recovery & Self-Healing System
==============================================
Provides automatic error recovery, retry mechanisms, and self-healing capabilities.

Features:
- Automatic retry with exponential backoff
- Self-healing service recovery
- Error pattern detection
- Automatic fallback mechanisms
- Health check integration
- Error aggregation and deduplication
"""

import asyncio
import logging
import traceback
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Callable, List, Tuple
from functools import wraps
from collections import defaultdict
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class RecoveryAction(str, Enum):
    """Actions that can be taken to recover from errors"""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    RESTART_SERVICE = "restart_service"
    CLEAR_CACHE = "clear_cache"
    RECONNECT = "reconnect"
    ALERT = "alert"
    NONE = "none"


class ErrorCategory(str, Enum):
    """Categories of errors for targeted handling"""
    DATABASE = "database"
    NETWORK = "network"
    EXTERNAL_API = "external_api"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    RESOURCE = "resource"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    UNKNOWN = "unknown"


def categorize_error(exception: Exception) -> ErrorCategory:
    """Categorize an exception for targeted handling"""
    error_str = str(exception).lower()
    error_type = type(exception).__name__.lower()
    
    # Database errors
    if any(x in error_str for x in ['mongodb', 'connection', 'cursor', 'collection']):
        return ErrorCategory.DATABASE
    if 'motor' in error_type or 'pymongo' in error_type:
        return ErrorCategory.DATABASE
    
    # Network errors
    if any(x in error_type for x in ['connection', 'socket', 'http', 'ssl']):
        return ErrorCategory.NETWORK
    if any(x in error_str for x in ['connection refused', 'network unreachable']):
        return ErrorCategory.NETWORK
    
    # Timeout errors
    if 'timeout' in error_str or 'timeout' in error_type:
        return ErrorCategory.TIMEOUT
    
    # Rate limit errors
    if any(x in error_str for x in ['rate limit', 'too many requests', '429']):
        return ErrorCategory.RATE_LIMIT
    
    # External API errors
    if any(x in error_str for x in ['api', 'kraken', 'coingecko', 'external']):
        return ErrorCategory.EXTERNAL_API
    
    # Authentication errors
    if any(x in error_str for x in ['auth', 'token', 'credential', 'permission', '401', '403']):
        return ErrorCategory.AUTHENTICATION
    
    # Validation errors
    if any(x in error_str for x in ['validation', 'invalid', 'required', 'missing']):
        return ErrorCategory.VALIDATION
    
    # Resource errors
    if any(x in error_str for x in ['memory', 'disk', 'resource', 'quota']):
        return ErrorCategory.RESOURCE
    
    return ErrorCategory.UNKNOWN


class ErrorFingerprint:
    """Generate unique fingerprint for error deduplication"""
    
    @staticmethod
    def generate(exception: Exception, context: Dict = None) -> str:
        """Generate a fingerprint for an error"""
        parts = [
            type(exception).__name__,
            str(exception)[:100],
            context.get('endpoint', '') if context else '',
        ]
        fingerprint_str = '|'.join(parts)
        return hashlib.md5(fingerprint_str.encode()).hexdigest()[:12]


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Tuple = (Exception,),
        non_retryable_exceptions: Tuple = (KeyboardInterrupt, SystemExit)
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions
        self.non_retryable_exceptions = non_retryable_exceptions
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        import random
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        if self.jitter:
            delay *= (0.5 + random.random())
        return delay


class ErrorRecoveryManager:
    """
    Manages error recovery strategies and automatic healing.
    """
    
    # Default recovery strategies by error category
    DEFAULT_STRATEGIES: Dict[ErrorCategory, List[RecoveryAction]] = {
        ErrorCategory.DATABASE: [RecoveryAction.RETRY, RecoveryAction.RECONNECT],
        ErrorCategory.NETWORK: [RecoveryAction.RETRY, RecoveryAction.FALLBACK],
        ErrorCategory.EXTERNAL_API: [RecoveryAction.RETRY, RecoveryAction.FALLBACK, RecoveryAction.CLEAR_CACHE],
        ErrorCategory.TIMEOUT: [RecoveryAction.RETRY, RecoveryAction.SKIP],
        ErrorCategory.RATE_LIMIT: [RecoveryAction.RETRY],  # With longer delay
        ErrorCategory.AUTHENTICATION: [RecoveryAction.ALERT],
        ErrorCategory.VALIDATION: [RecoveryAction.NONE],
        ErrorCategory.RESOURCE: [RecoveryAction.CLEAR_CACHE, RecoveryAction.ALERT],
        ErrorCategory.UNKNOWN: [RecoveryAction.RETRY, RecoveryAction.ALERT],
    }
    
    def __init__(self, db=None):
        self.db = db
        self._error_history: Dict[str, List[Dict]] = defaultdict(list)
        self._recovery_attempts: Dict[str, int] = defaultdict(int)
        self._suppressed_errors: Dict[str, datetime] = {}
        self._fallbacks: Dict[str, Callable] = {}
        self._health_callbacks: List[Callable] = []
        
        # Stats
        self._stats = {
            'total_errors': 0,
            'recovered': 0,
            'failed': 0,
            'suppressed': 0,
            'by_category': defaultdict(int),
        }
        
        logger.info("✅ Error Recovery Manager initialized")
    
    def register_fallback(self, key: str, fallback_fn: Callable):
        """Register a fallback function for a specific operation"""
        self._fallbacks[key] = fallback_fn
        logger.debug(f"Registered fallback for: {key}")
    
    def register_health_callback(self, callback: Callable):
        """Register a callback to run during health recovery"""
        self._health_callbacks.append(callback)
    
    async def handle_error(
        self,
        exception: Exception,
        context: Dict[str, Any] = None,
        retry_config: RetryConfig = None
    ) -> Tuple[bool, Any]:
        """
        Handle an error with automatic recovery.
        
        Returns:
            Tuple of (recovered: bool, result: Any)
        """
        context = context or {}
        self._stats['total_errors'] += 1
        
        # Categorize the error
        category = categorize_error(exception)
        self._stats['by_category'][category.value] += 1
        
        # Generate fingerprint for deduplication
        fingerprint = ErrorFingerprint.generate(exception, context)
        
        # Check if error is suppressed (rate-limited alerts)
        if self._is_suppressed(fingerprint):
            self._stats['suppressed'] += 1
            logger.debug(f"Suppressed duplicate error: {fingerprint}")
            return False, None
        
        # Record error
        await self._record_error(exception, category, fingerprint, context)
        
        # Get recovery strategies
        strategies = self.DEFAULT_STRATEGIES.get(category, [RecoveryAction.NONE])
        
        # Try recovery strategies
        for action in strategies:
            success, result = await self._execute_recovery(
                action, exception, category, context, retry_config
            )
            if success:
                self._stats['recovered'] += 1
                logger.info(f"✅ Recovered from {category.value} error using {action.value}")
                return True, result
        
        self._stats['failed'] += 1
        logger.error(f"❌ Failed to recover from {category.value} error: {exception}")
        return False, None
    
    def _is_suppressed(self, fingerprint: str) -> bool:
        """Check if error should be suppressed (deduplication)"""
        if fingerprint in self._suppressed_errors:
            suppress_until = self._suppressed_errors[fingerprint]
            if datetime.now(timezone.utc) < suppress_until:
                return True
        return False
    
    def _suppress_error(self, fingerprint: str, duration_seconds: int = 60):
        """Suppress an error for a duration"""
        self._suppressed_errors[fingerprint] = datetime.now(timezone.utc) + timedelta(seconds=duration_seconds)
    
    async def _record_error(
        self,
        exception: Exception,
        category: ErrorCategory,
        fingerprint: str,
        context: Dict
    ):
        """Record error to history and optionally to database"""
        error_record = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'category': category.value,
            'fingerprint': fingerprint,
            'exception_type': type(exception).__name__,
            'message': str(exception)[:500],
            'context': context,
        }
        
        self._error_history[fingerprint].append(error_record)
        
        # Persist to database if available
        if self.db:
            try:
                await self.db.error_history.insert_one({
                    **error_record,
                    'stack_trace': traceback.format_exc()[:2000]
                })
            except Exception as e:
                logger.warning(f"Could not persist error to database: {e}")
    
    async def _execute_recovery(
        self,
        action: RecoveryAction,
        exception: Exception,
        category: ErrorCategory,
        context: Dict,
        retry_config: RetryConfig = None
    ) -> Tuple[bool, Any]:
        """Execute a recovery action"""
        
        if action == RecoveryAction.RETRY:
            return await self._retry_operation(context, retry_config, category)
        
        elif action == RecoveryAction.FALLBACK:
            return await self._use_fallback(context)
        
        elif action == RecoveryAction.CLEAR_CACHE:
            return await self._clear_cache()
        
        elif action == RecoveryAction.RECONNECT:
            return await self._reconnect_services()
        
        elif action == RecoveryAction.RESTART_SERVICE:
            return await self._restart_service(context)
        
        elif action == RecoveryAction.ALERT:
            await self._send_alert(exception, category, context)
            return False, None
        
        elif action == RecoveryAction.SKIP:
            logger.warning(f"Skipping operation due to {category.value} error")
            return True, None
        
        return False, None
    
    async def _retry_operation(
        self,
        context: Dict,
        retry_config: RetryConfig = None,
        category: ErrorCategory = None
    ) -> Tuple[bool, Any]:
        """Retry the failed operation"""
        operation = context.get('operation')
        if not operation or not callable(operation):
            return False, None
        
        config = retry_config or RetryConfig()
        
        # Adjust delay for rate limit errors
        if category == ErrorCategory.RATE_LIMIT:
            config.base_delay = 5.0
            config.max_delay = 60.0
        
        args = context.get('args', ())
        kwargs = context.get('kwargs', {})
        
        for attempt in range(config.max_retries):
            try:
                delay = config.get_delay(attempt)
                logger.info(f"Retry attempt {attempt + 1}/{config.max_retries} after {delay:.1f}s")
                await asyncio.sleep(delay)
                
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)
                
                return True, result
                
            except config.non_retryable_exceptions:
                raise
            except Exception as e:
                logger.warning(f"Retry {attempt + 1} failed: {e}")
                continue
        
        return False, None
    
    async def _use_fallback(self, context: Dict) -> Tuple[bool, Any]:
        """Use registered fallback function"""
        fallback_key = context.get('fallback_key')
        if fallback_key and fallback_key in self._fallbacks:
            try:
                fallback_fn = self._fallbacks[fallback_key]
                if asyncio.iscoroutinefunction(fallback_fn):
                    result = await fallback_fn()
                else:
                    result = fallback_fn()
                return True, result
            except Exception as e:
                logger.error(f"Fallback failed: {e}")
        return False, None
    
    async def _clear_cache(self) -> Tuple[bool, Any]:
        """Clear application cache"""
        try:
            from services.cache_manager import get_cache_manager
            cache = get_cache_manager()
            await cache.clear()
            logger.info("🗑️ Cache cleared as recovery action")
            return True, None
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False, None
    
    async def _reconnect_services(self) -> Tuple[bool, Any]:
        """Attempt to reconnect to services"""
        try:
            # Reconnect to database
            from config.database import reconnect_database
            await reconnect_database()
            logger.info("🔄 Services reconnected")
            return True, None
        except Exception as e:
            logger.error(f"Failed to reconnect services: {e}")
            return False, None
    
    async def _restart_service(self, context: Dict) -> Tuple[bool, Any]:
        """Restart a specific service"""
        service_name = context.get('service_name')
        if not service_name:
            return False, None
        
        logger.warning(f"Service restart requested for: {service_name}")
        # In production, this would trigger service restart
        return False, None
    
    async def _send_alert(
        self,
        exception: Exception,
        category: ErrorCategory,
        context: Dict
    ):
        """Send alert for critical errors"""
        logger.error(f"🚨 ALERT: {category.value} error - {exception}")
        
        # Persist alert
        if self.db:
            try:
                await self.db.alerts.insert_one({
                    'type': 'error_alert',
                    'category': category.value,
                    'message': str(exception),
                    'context': context,
                    'timestamp': datetime.now(timezone.utc),
                    'resolved': False
                })
            except Exception as e:
                logger.error(f"Failed to persist alert: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get error recovery statistics"""
        return {
            **self._stats,
            'by_category': dict(self._stats['by_category']),
            'recovery_rate': (
                self._stats['recovered'] / self._stats['total_errors'] * 100
                if self._stats['total_errors'] > 0 else 0
            ),
            'suppressed_count': len(self._suppressed_errors),
            'registered_fallbacks': list(self._fallbacks.keys()),
        }
    
    async def run_health_check(self) -> Dict[str, Any]:
        """Run health check and self-healing if needed"""
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': [],
            'healing_actions': [],
        }
        
        # Run registered health callbacks
        for callback in self._health_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    result = await callback()
                else:
                    result = callback()
                results['checks'].append({
                    'name': callback.__name__,
                    'status': 'passed',
                    'result': result
                })
            except Exception as e:
                results['checks'].append({
                    'name': callback.__name__,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results


# Singleton instance
_error_recovery_manager: Optional[ErrorRecoveryManager] = None


def get_error_recovery_manager(db=None) -> ErrorRecoveryManager:
    """Get or create error recovery manager"""
    global _error_recovery_manager
    if _error_recovery_manager is None:
        _error_recovery_manager = ErrorRecoveryManager(db)
    return _error_recovery_manager


def with_error_recovery(
    fallback_key: str = None,
    retry_config: RetryConfig = None,
    reraise: bool = False
):
    """
    Decorator for automatic error recovery.
    
    Usage:
        @with_error_recovery(fallback_key="market_prices", retry_config=RetryConfig(max_retries=3))
        async def get_market_prices():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)
            except Exception as e:
                manager = get_error_recovery_manager()
                
                context = {
                    'operation': func,
                    'args': args,
                    'kwargs': kwargs,
                    'fallback_key': fallback_key,
                    'endpoint': func.__name__,
                }
                
                recovered, result = await manager.handle_error(
                    e, context, retry_config
                )
                
                if recovered:
                    return result
                
                if reraise:
                    raise
                
                return None
        
        return wrapper
    return decorator

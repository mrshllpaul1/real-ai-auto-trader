"""
Error Monitoring Middleware
Enterprise-level error monitoring for faster issue resolution
"""

import logging
import traceback
import uuid
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from collections import deque
import os

logger = logging.getLogger(__name__)


class ErrorSeverity:
    """Error severity levels"""
    CRITICAL = 'critical'  # System down
    ERROR = 'error'        # Feature broken
    WARNING = 'warning'    # Degraded performance
    INFO = 'info'          # Informational


class ErrorRecord:
    """Structured error record"""
    
    def __init__(
        self,
        error_id: str,
        timestamp: datetime,
        severity: str,
        error_type: str,
        message: str,
        stack_trace: str,
        request_info: Dict,
        user_id: Optional[str] = None,
        additional_context: Optional[Dict] = None
    ):
        self.error_id = error_id
        self.timestamp = timestamp
        self.severity = severity
        self.error_type = error_type
        self.message = message
        self.stack_trace = stack_trace
        self.request_info = request_info
        self.user_id = user_id
        self.additional_context = additional_context or {}
    
    def to_dict(self) -> Dict:
        return {
            'error_id': self.error_id,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity,
            'error_type': self.error_type,
            'message': self.message,
            'stack_trace': self.stack_trace,
            'request_info': self.request_info,
            'user_id': self.user_id,
            'additional_context': self.additional_context
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class ErrorStore:
    """In-memory error store with persistence hooks"""
    
    def __init__(self, max_errors: int = 1000):
        self.errors: deque = deque(maxlen=max_errors)
        self.error_counts: Dict[str, int] = {}
        self.error_rates: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()
    
    async def add_error(self, error: ErrorRecord):
        """Add error to store"""
        async with self._lock:
            self.errors.append(error)
            
            # Update error counts
            error_key = f"{error.error_type}:{error.severity}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            
            # Track error rate (errors per minute)
            minute_key = error.timestamp.strftime('%Y-%m-%d %H:%M')
            if minute_key not in self.error_rates:
                self.error_rates[minute_key] = []
            self.error_rates[minute_key].append(error.timestamp.timestamp())
    
    async def get_recent_errors(
        self, 
        limit: int = 100,
        severity: Optional[str] = None,
        error_type: Optional[str] = None
    ) -> List[Dict]:
        """Get recent errors with optional filtering"""
        async with self._lock:
            errors = list(self.errors)
            
            if severity:
                errors = [e for e in errors if e.severity == severity]
            if error_type:
                errors = [e for e in errors if e.error_type == error_type]
            
            return [e.to_dict() for e in errors[-limit:]]
    
    async def get_error_stats(self) -> Dict:
        """Get error statistics"""
        async with self._lock:
            now = datetime.utcnow()
            
            # Count errors in last hour
            hour_ago = now.timestamp() - 3600
            recent_errors = [e for e in self.errors if e.timestamp.timestamp() > hour_ago]
            
            # Group by severity
            by_severity = {}
            for error in recent_errors:
                by_severity[error.severity] = by_severity.get(error.severity, 0) + 1
            
            # Group by type
            by_type = {}
            for error in recent_errors:
                by_type[error.error_type] = by_type.get(error.error_type, 0) + 1
            
            return {
                'total_errors': len(self.errors),
                'errors_last_hour': len(recent_errors),
                'by_severity': by_severity,
                'by_type': by_type,
                'error_counts': dict(self.error_counts)
            }


# Global error store
_error_store: Optional[ErrorStore] = None


def get_error_store() -> ErrorStore:
    """Get or create the global error store"""
    global _error_store
    if _error_store is None:
        _error_store = ErrorStore()
    return _error_store


class ErrorMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for capturing and monitoring errors"""
    
    def __init__(
        self, 
        app,
        error_store: Optional[ErrorStore] = None,
        log_all_requests: bool = False,
        alert_on_critical: bool = True
    ):
        super().__init__(app)
        self.error_store = error_store or get_error_store()
        self.log_all_requests = log_all_requests
        self.alert_on_critical = alert_on_critical
    
    def _extract_request_info(self, request: Request) -> Dict:
        """Extract relevant request information"""
        return {
            'method': request.method,
            'url': str(request.url),
            'path': request.url.path,
            'query_params': dict(request.query_params),
            'client_host': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('user-agent', 'unknown'),
            'headers': {
                k: v for k, v in request.headers.items()
                if k.lower() not in ['authorization', 'x-api-key', 'cookie']
            }
        }
    
    def _determine_severity(self, status_code: int, exception: Optional[Exception]) -> str:
        """Determine error severity based on status code and exception type"""
        if status_code >= 500:
            return ErrorSeverity.ERROR
        elif status_code == 429:
            return ErrorSeverity.WARNING
        elif status_code >= 400:
            return ErrorSeverity.INFO
        elif exception:
            if isinstance(exception, (ConnectionError, TimeoutError)):
                return ErrorSeverity.ERROR
            return ErrorSeverity.WARNING
        return ErrorSeverity.INFO
    
    async def dispatch(self, request: Request, call_next):
        error_id = str(uuid.uuid4())[:8]
        start_time = datetime.utcnow()
        
        try:
            response = await call_next(request)
            
            # Log slow requests
            duration = (datetime.utcnow() - start_time).total_seconds()
            if duration > 5.0:  # Requests taking more than 5 seconds
                logger.warning(
                    f"Slow request [{error_id}]: {request.method} {request.url.path} "
                    f"took {duration:.2f}s"
                )
            
            # Log errors (4xx, 5xx)
            if response.status_code >= 400:
                error_record = ErrorRecord(
                    error_id=error_id,
                    timestamp=datetime.utcnow(),
                    severity=self._determine_severity(response.status_code, None),
                    error_type=f"HTTP_{response.status_code}",
                    message=f"HTTP {response.status_code} response",
                    stack_trace='',
                    request_info=self._extract_request_info(request),
                    user_id=request.headers.get('X-User-ID')
                )
                await self.error_store.add_error(error_record)
                
                if response.status_code >= 500:
                    logger.error(
                        f"Error [{error_id}]: {request.method} {request.url.path} "
                        f"returned {response.status_code}"
                    )
            
            # Add error ID to response headers
            response.headers['X-Request-ID'] = error_id
            
            return response
            
        except Exception as exc:
            # Capture unhandled exceptions
            error_record = ErrorRecord(
                error_id=error_id,
                timestamp=datetime.utcnow(),
                severity=ErrorSeverity.CRITICAL,
                error_type=type(exc).__name__,
                message=str(exc),
                stack_trace=traceback.format_exc(),
                request_info=self._extract_request_info(request),
                user_id=request.headers.get('X-User-ID')
            )
            await self.error_store.add_error(error_record)
            
            logger.critical(
                f"Unhandled exception [{error_id}]: {type(exc).__name__}: {str(exc)}\n"
                f"Path: {request.method} {request.url.path}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    'detail': 'Internal server error',
                    'error_id': error_id,
                    'timestamp': datetime.utcnow().isoformat()
                },
                headers={'X-Request-ID': error_id}
            )


# Error monitoring endpoints
from fastapi import APIRouter

error_router = APIRouter(prefix='/api/monitoring', tags=['monitoring'])


@error_router.get('/errors')
async def get_errors(
    limit: int = 100,
    severity: Optional[str] = None,
    error_type: Optional[str] = None
):
    """Get recent errors"""
    store = get_error_store()
    errors = await store.get_recent_errors(limit, severity, error_type)
    return {'errors': errors, 'count': len(errors)}


@error_router.get('/errors/stats')
async def get_error_stats():
    """Get error statistics"""
    store = get_error_store()
    stats = await store.get_error_stats()
    return stats


@error_router.get('/health/detailed')
async def detailed_health():
    """Detailed health check with error stats"""
    from config.database import health_check as db_health_check
    
    store = get_error_store()
    error_stats = await store.get_error_stats()
    db_health = await db_health_check()
    
    return {
        'status': 'healthy' if db_health['connected'] else 'degraded',
        'database': db_health,
        'errors': error_stats,
        'timestamp': datetime.utcnow().isoformat()
    }


# Pydantic models for frontend error reporting
from pydantic import BaseModel
from typing import List, Dict, Any, Optional as PydanticOptional

class FrontendError(BaseModel):
    error_id: PydanticOptional[str] = None
    type: PydanticOptional[str] = 'frontend_error'
    severity: PydanticOptional[str] = 'medium'
    category: PydanticOptional[str] = 'unknown'
    message: str
    stack: PydanticOptional[str] = ''
    component_stack: PydanticOptional[str] = ''
    component_name: PydanticOptional[str] = 'Unknown'
    url: PydanticOptional[str] = ''
    pathname: PydanticOptional[str] = ''
    user_agent: PydanticOptional[str] = ''
    timestamp: PydanticOptional[str] = None
    session_id: PydanticOptional[str] = None
    user_id: PydanticOptional[str] = 'anonymous'

class BatchErrorRequest(BaseModel):
    errors: List[Dict[str, Any]]


@error_router.post('/errors')
async def report_frontend_error(error: FrontendError):
    """Report a single frontend error"""
    try:
        store = get_error_store()
        
        # Create error info for storage
        error_info = {
            'error_id': error.error_id or f"fe_{datetime.utcnow().timestamp()}",
            'type': error.type,
            'severity': error.severity,
            'category': error.category,
            'message': error.message,
            'stack': error.stack,
            'component_stack': error.component_stack,
            'component_name': error.component_name,
            'url': error.url,
            'pathname': error.pathname,
            'user_agent': error.user_agent,
            'session_id': error.session_id,
            'user_id': error.user_id,
            'timestamp': error.timestamp or datetime.utcnow().isoformat(),
            'source': 'frontend',
        }
        
        # Store the error
        await store.record_frontend_error(error_info)
        
        return {
            'status': 'recorded',
            'error_id': error_info['error_id'],
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to record frontend error: {e}")
        return {'status': 'failed', 'error': str(e)}


@error_router.post('/errors/batch')
async def report_batch_errors(request: BatchErrorRequest):
    """Report multiple frontend errors at once"""
    try:
        store = get_error_store()
        recorded = 0
        failed = 0
        
        for error_data in request.errors:
            try:
                error_info = {
                    'error_id': error_data.get('id') or f"fe_{datetime.utcnow().timestamp()}_{recorded}",
                    'type': error_data.get('category', 'unknown'),
                    'severity': error_data.get('severity', 'medium'),
                    'message': error_data.get('message', 'Unknown error'),
                    'stack': error_data.get('stack', ''),
                    'component_stack': error_data.get('componentStack', ''),
                    'url': error_data.get('context', {}).get('url', ''),
                    'pathname': error_data.get('context', {}).get('pathname', ''),
                    'user_agent': error_data.get('device', {}).get('userAgent', ''),
                    'session_id': error_data.get('context', {}).get('sessionId'),
                    'user_id': error_data.get('context', {}).get('userId', 'anonymous'),
                    'fingerprint': error_data.get('fingerprint', ''),
                    'timestamp': error_data.get('context', {}).get('timestamp') or datetime.utcnow().isoformat(),
                    'source': 'frontend_batch',
                    'device_info': error_data.get('device', {}),
                    'request_info': error_data.get('request', {}),
                }
                
                await store.record_frontend_error(error_info)
                recorded += 1
            except Exception as e:
                logger.error(f"Failed to record batch error: {e}")
                failed += 1
        
        return {
            'status': 'processed',
            'recorded': recorded,
            'failed': failed,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to process batch errors: {e}")
        return {'status': 'failed', 'error': str(e)}


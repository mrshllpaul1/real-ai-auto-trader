"""
Request Validation Middleware
Enhanced with NoSQL injection detection and input sanitization.
"""

import logging
import json
from typing import Optional, Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class ValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for request validation, sanitization, and injection detection"""
    
    # Maximum request body size (10MB)
    MAX_BODY_SIZE = 10 * 1024 * 1024
    
    # Paths to skip validation (exact match or prefix with specific endings)
    SKIP_PATHS = {
        '/api/health',
        '/api/health/deep',
        '/api/docs',
        '/api/redoc',
        '/api/openapi.json',
        '/health',
    }
    
    # Exact paths to skip
    EXACT_SKIP = {'/', '/api/'}
    
    # MongoDB operators that should NEVER be in user input
    DANGEROUS_OPERATORS = [
        '$gt', '$gte', '$lt', '$lte', '$ne', '$nin', '$in',
        '$or', '$and', '$not', '$nor', '$exists', '$type',
        '$regex', '$where', '$expr', '$lookup', '$project',
        '$set', '$unset', '$push', '$pull',
    ]
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Skip validation for health/docs paths
        if path in self.EXACT_SKIP or any(path.startswith(skip) for skip in self.SKIP_PATHS):
            return await call_next(request)
        
        # Check content length
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                if int(content_length) > self.MAX_BODY_SIZE:
                    return JSONResponse(
                        status_code=413,
                        content={
                            'detail': 'Request body too large',
                            'max_size_mb': self.MAX_BODY_SIZE / (1024 * 1024)
                        }
                    )
            except ValueError:
                pass
        
        # Check query parameters for NoSQL injection
        try:
            for param_name, param_value in request.query_params.items():
                if self._contains_injection(param_value):
                    client_ip = request.client.host if request.client else "unknown"
                    logger.warning(
                        f"NOSQL INJECTION BLOCKED | IP={client_ip} | "
                        f"Path={request.url.path} | Param={param_name} | "
                        f"Value={param_value[:100]}"
                    )
                    return JSONResponse(
                        status_code=400,
                        content={'detail': 'Invalid request parameters detected'}
                    )
        except Exception as e:
            logger.debug(f"Query param validation error: {e}")
        
        # Check URL path segments for injection
        try:
            path_parts = request.url.path.split('/')
            for part in path_parts:
                if part.startswith('$'):
                    client_ip = request.client.host if request.client else "unknown"
                    logger.warning(
                        f"PATH INJECTION BLOCKED | IP={client_ip} | "
                        f"Path={request.url.path}"
                    )
                    return JSONResponse(
                        status_code=400,
                        content={'detail': 'Invalid request path'}
                    )
        except Exception as e:
            logger.debug(f"Path validation error: {e}")
        
        return await call_next(request)
    
    def _contains_injection(self, value: str) -> bool:
        """Check if a value contains potential NoSQL injection patterns"""
        if not isinstance(value, str):
            return False
        
        value_lower = value.lower().strip()
        
        # Check for MongoDB operators
        for op in self.DANGEROUS_OPERATORS:
            if op in value_lower:
                return True
        
        # Check for JavaScript injection
        if 'javascript:' in value_lower:
            return True
        
        return False
    
    def _body_contains_injection(self, body_text: str) -> bool:
        """Check if JSON body contains suspicious MongoDB operator keys"""
        try:
            data = json.loads(body_text)
            return self._check_dict_for_operators(data)
        except (json.JSONDecodeError, TypeError):
            return False
    
    def _check_dict_for_operators(self, data: Any, depth: int = 0) -> bool:
        """Recursively check dict keys for MongoDB operators"""
        if depth > 10:  # Prevent infinite recursion
            return False
        
        if isinstance(data, dict):
            for key in data.keys():
                if isinstance(key, str) and key.startswith('$'):
                    return True
                if self._check_dict_for_operators(data[key], depth + 1):
                    return True
        elif isinstance(data, list):
            for item in data:
                if self._check_dict_for_operators(item, depth + 1):
                    return True
        
        return False

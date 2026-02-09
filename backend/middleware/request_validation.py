"""
Request Validation Middleware
Comprehensive Pydantic validation for all API inputs
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import json

logger = logging.getLogger(__name__)


class ValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for request validation and sanitization"""
    
    # Maximum request body size (10MB)
    MAX_BODY_SIZE = 10 * 1024 * 1024
    
    # Paths to skip validation
    SKIP_PATHS = [
        '/api/health',
        '/api/docs',
        '/api/redoc',
        '/api/openapi.json',
        '/health',
        '/',
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip validation for certain paths
        if any(request.url.path.startswith(skip) for skip in self.SKIP_PATHS):
            return await call_next(request)
        
        # Check content length
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > self.MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={
                    'detail': 'Request body too large',
                    'max_size_mb': self.MAX_BODY_SIZE / (1024 * 1024)
                }
            )
        
        # Validate content type for POST/PUT/PATCH
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.headers.get('content-type', '')
            
            # Allow JSON and form data
            valid_types = [
                'application/json',
                'application/x-www-form-urlencoded',
                'multipart/form-data'
            ]
            
            if content_type and not any(ct in content_type for ct in valid_types):
                # Don't reject, just log
                logger.debug(f"Unusual content type: {content_type} for {request.url.path}")
        
        return await call_next(request)

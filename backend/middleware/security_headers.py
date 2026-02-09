"""
Security Headers Middleware
Comprehensive security headers for attack protection
"""

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security configuration"""
    
    # Content Security Policy
    CSP_DIRECTIVES = {
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],  # Needed for React
        'style-src': ["'self'", "'unsafe-inline'"],
        'img-src': ["'self'", 'data:', 'https:', 'blob:'],
        'font-src': ["'self'", 'data:'],
        'connect-src': ["'self'", 'https:', 'wss:'],
        'frame-ancestors': ["'self'"],
        'form-action': ["'self'"],
        'base-uri': ["'self'"],
        'object-src': ["'none'"],
    }
    
    # Permissions Policy
    PERMISSIONS_POLICY = {
        'accelerometer': [],
        'camera': [],
        'geolocation': [],
        'gyroscope': [],
        'magnetometer': [],
        'microphone': [],
        'payment': ['self'],
        'usb': [],
    }
    
    # CORS Configuration
    ALLOWED_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    ALLOWED_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']
    ALLOWED_HEADERS = ['*']
    
    # Paths to skip security headers (like docs)
    SKIP_PATHS = [
        '/api/docs',
        '/api/redoc',
        '/api/openapi.json',
    ]


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add comprehensive security headers to all responses"""
    
    def __init__(
        self, 
        app, 
        enable_hsts: bool = True,
        hsts_max_age: int = 31536000,  # 1 year
        enable_csp: bool = True,
        custom_csp: Optional[Dict] = None
    ):
        super().__init__(app)
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age
        self.enable_csp = enable_csp
        self.csp_directives = custom_csp or SecurityConfig.CSP_DIRECTIVES
    
    def _build_csp_header(self) -> str:
        """Build Content-Security-Policy header value"""
        directives = []
        for directive, values in self.csp_directives.items():
            if values:
                directives.append(f"{directive} {' '.join(values)}")
            else:
                directives.append(f"{directive} 'none'")
        return '; '.join(directives)
    
    def _build_permissions_policy(self) -> str:
        """Build Permissions-Policy header value"""
        policies = []
        for feature, allowlist in SecurityConfig.PERMISSIONS_POLICY.items():
            if allowlist:
                policies.append(f"{feature}=({' '.join(allowlist)})")
            else:
                policies.append(f"{feature}=()")
        return ', '.join(policies)
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Skip security headers for docs
        if any(request.url.path.startswith(skip) for skip in SecurityConfig.SKIP_PATHS):
            return response
        
        # Core Security Headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HSTS (HTTP Strict Transport Security)
        if self.enable_hsts:
            response.headers['Strict-Transport-Security'] = (
                f'max-age={self.hsts_max_age}; includeSubDomains; preload'
            )
        
        # Content Security Policy
        if self.enable_csp:
            response.headers['Content-Security-Policy'] = self._build_csp_header()
        
        # Permissions Policy
        response.headers['Permissions-Policy'] = self._build_permissions_policy()
        
        # Additional Security Headers
        response.headers['X-DNS-Prefetch-Control'] = 'off'
        response.headers['X-Download-Options'] = 'noopen'
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
        
        # Cache Control for sensitive data
        if '/api/' in request.url.path:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        return response

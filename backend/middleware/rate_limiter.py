"""
API Rate Limiting Middleware
Per-user rate limiting to prevent abuse
"""

import time
import logging
from collections import defaultdict
from typing import Dict, Optional, Tuple
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import asyncio

logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Rate limit configuration by tier"""
    TIERS = {
        'free': {
            'requests_per_minute': 60,
            'requests_per_hour': 500,
            'requests_per_day': 2000,
            'burst_limit': 10,
        },
        'pro': {
            'requests_per_minute': 300,
            'requests_per_hour': 5000,
            'requests_per_day': 50000,
            'burst_limit': 50,
        },
        'enterprise': {
            'requests_per_minute': 1000,
            'requests_per_hour': 20000,
            'requests_per_day': 200000,
            'burst_limit': 100,
        }
    }
    
    # Endpoint-specific limits (overrides tier limits)
    ENDPOINT_LIMITS = {
        '/api/training/train': {'requests_per_minute': 5, 'requests_per_hour': 20},
        '/api/enhanced-ai/train': {'requests_per_minute': 5, 'requests_per_hour': 20},
        '/api/tethys-trading/start': {'requests_per_minute': 10, 'requests_per_hour': 50},
        '/api/triggers/check-now': {'requests_per_minute': 30, 'requests_per_hour': 200},
    }
    
    # Paths to skip rate limiting
    SKIP_PATHS = [
        '/api/health',
        '/api/docs',
        '/api/redoc',
        '/api/openapi.json',
        '/health',
        '/',
        '/api/training/',
        '/api/training-progress/',
        '/api/tethys-train/',
        '/api/enhanced-mtf-training/',
        '/api/learning/',
    ]


class TokenBucket:
    """Token bucket algorithm for rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> Tuple[bool, float]:
        """Try to consume tokens. Returns (success, wait_time)"""
        async with self.lock:
            now = time.time()
            # Refill tokens based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0
            else:
                wait_time = (tokens - self.tokens) / self.refill_rate
                return False, wait_time


class RateLimiter:
    """Per-user rate limiter with multiple time windows"""
    
    def __init__(self):
        self.user_buckets: Dict[str, Dict[str, TokenBucket]] = defaultdict(dict)
        self.request_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.window_starts: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._cleanup_task = None
    
    def _get_user_tier(self, user_id: str) -> str:
        """Get user tier (can be extended to check database)"""
        # Default to 'free' tier, can be extended to check user subscription
        return 'free'
    
    def _get_user_id(self, request: Request) -> str:
        """Extract user identifier from request"""
        # Try to get from header, then from IP
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            user_id = request.headers.get('X-API-Key', '')[:16]  # Use partial API key
        if not user_id:
            user_id = request.client.host if request.client else 'unknown'
        return user_id
    
    async def check_rate_limit(
        self, 
        request: Request
    ) -> Tuple[bool, Optional[Dict]]:
        """Check if request is within rate limits"""
        path = request.url.path
        
        # Skip rate limiting for certain paths
        if any(path.startswith(skip) for skip in RateLimitConfig.SKIP_PATHS):
            return True, None
        
        user_id = self._get_user_id(request)
        tier = self._get_user_tier(user_id)
        limits = RateLimitConfig.TIERS.get(tier, RateLimitConfig.TIERS['free'])
        
        # Check endpoint-specific limits
        endpoint_limits = RateLimitConfig.ENDPOINT_LIMITS.get(path)
        if endpoint_limits:
            limits = {**limits, **endpoint_limits}
        
        now = time.time()
        
        # Check minute window
        minute_key = f"{user_id}:{path}:minute"
        minute_window_start = self.window_starts[user_id].get('minute', 0)
        if now - minute_window_start >= 60:
            self.request_counts[user_id]['minute'] = 0
            self.window_starts[user_id]['minute'] = now
        
        if self.request_counts[user_id]['minute'] >= limits['requests_per_minute']:
            retry_after = 60 - (now - minute_window_start)
            return False, {
                'error': 'Rate limit exceeded',
                'limit': limits['requests_per_minute'],
                'window': 'minute',
                'retry_after': round(retry_after),
                'tier': tier
            }
        
        # Check hour window
        hour_window_start = self.window_starts[user_id].get('hour', 0)
        if now - hour_window_start >= 3600:
            self.request_counts[user_id]['hour'] = 0
            self.window_starts[user_id]['hour'] = now
        
        if self.request_counts[user_id]['hour'] >= limits['requests_per_hour']:
            retry_after = 3600 - (now - hour_window_start)
            return False, {
                'error': 'Rate limit exceeded',
                'limit': limits['requests_per_hour'],
                'window': 'hour',
                'retry_after': round(retry_after),
                'tier': tier
            }
        
        # Increment counters
        self.request_counts[user_id]['minute'] += 1
        self.request_counts[user_id]['hour'] += 1
        
        return True, {
            'remaining_minute': limits['requests_per_minute'] - self.request_counts[user_id]['minute'],
            'remaining_hour': limits['requests_per_hour'] - self.request_counts[user_id]['hour'],
            'tier': tier
        }
    
    async def cleanup_old_entries(self):
        """Periodically cleanup old rate limit entries"""
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            now = time.time()
            
            # Remove entries older than 1 hour
            users_to_remove = []
            for user_id, windows in self.window_starts.items():
                if all(now - start > 3600 for start in windows.values()):
                    users_to_remove.append(user_id)
            
            for user_id in users_to_remove:
                del self.request_counts[user_id]
                del self.window_starts[user_id]
            
            if users_to_remove:
                logger.debug(f"Cleaned up rate limit data for {len(users_to_remove)} users")


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, app, rate_limiter: Optional[RateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or get_rate_limiter()
    
    async def dispatch(self, request: Request, call_next):
        allowed, info = await self.rate_limiter.check_rate_limit(request)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for {request.client.host}: {info}")
            return JSONResponse(
                status_code=429,
                content={
                    'detail': info['error'],
                    'limit': info['limit'],
                    'window': info['window'],
                    'retry_after': info['retry_after'],
                    'tier': info['tier']
                },
                headers={
                    'Retry-After': str(info['retry_after']),
                    'X-RateLimit-Limit': str(info['limit']),
                    'X-RateLimit-Window': info['window'],
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers to response
        if info:
            response.headers['X-RateLimit-Remaining-Minute'] = str(info.get('remaining_minute', 0))
            response.headers['X-RateLimit-Remaining-Hour'] = str(info.get('remaining_hour', 0))
            response.headers['X-RateLimit-Tier'] = info.get('tier', 'free')
        
        return response

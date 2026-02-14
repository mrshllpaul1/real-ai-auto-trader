"""CSRF Protection Middleware
Double-submit cookie pattern for SPA.

- Issues a CSRF cookie on every response if not present
- Validates X-CSRF-Token header matches the cookie on state-changing requests (POST/PUT/DELETE/PATCH)
- Skips CSRF for API-key-authenticated requests (programmatic, non-browser)
- Skips CSRF for health/docs/websocket endpoints
"""

import secrets
import logging
from typing import Set
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from config.app_config import COOKIE_SECURE, COOKIE_SAMESITE

logger = logging.getLogger(__name__)

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"
CSRF_TOKEN_LENGTH = 64  # 64 hex chars = 256 bits

# Paths exempt from CSRF validation
CSRF_EXEMPT_PATHS: Set[str] = {
    "/api/auth/session",
    "/api/auth/csrf-token",
    "/api/health",
    "/api/health/deep",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
    "/health",
}

CSRF_EXEMPT_PREFIXES = (
    "/ws/",          # WebSocket
    "/api/health",   # Health checks
)

STATE_CHANGING_METHODS = {"POST", "PUT", "DELETE", "PATCH"}


def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token."""
    return secrets.token_hex(CSRF_TOKEN_LENGTH // 2)


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF protection for SPAs."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method

        # ---- Always let exempt paths through ----
        if path in CSRF_EXEMPT_PATHS or path.startswith(CSRF_EXEMPT_PREFIXES):
            response = await call_next(request)
            self._ensure_csrf_cookie(request, response)
            return response

        # ---- Skip CSRF for API-key-authenticated callers ----
        if request.headers.get("x-api-key"):
            response = await call_next(request)
            return response

        # ---- Validate on state-changing methods ----
        if method in STATE_CHANGING_METHODS:
            cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
            header_token = request.headers.get(CSRF_HEADER_NAME)

            if not cookie_token or not header_token:
                client_ip = request.client.host if request.client else "unknown"
                logger.warning(
                    f"CSRF BLOCKED (missing token) | IP={client_ip} | "
                    f"{method} {path} | cookie={'present' if cookie_token else 'absent'} "
                    f"header={'present' if header_token else 'absent'}"
                )
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": {
                            "message": "CSRF validation failed. Missing security token.",
                            "code": "CSRF_MISSING",
                            "hint": "Include the csrf_token cookie value in the X-CSRF-Token header."
                        }
                    },
                )

            if not secrets.compare_digest(cookie_token, header_token):
                client_ip = request.client.host if request.client else "unknown"
                logger.warning(
                    f"CSRF BLOCKED (mismatch) | IP={client_ip} | {method} {path}"
                )
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": {
                            "message": "CSRF validation failed. Token mismatch.",
                            "code": "CSRF_MISMATCH"
                        }
                    },
                )

        # ---- Proceed normally ----
        response = await call_next(request)
        self._ensure_csrf_cookie(request, response)
        return response

    # ------------------------------------------------------------------
    @staticmethod
    def _ensure_csrf_cookie(request: Request, response):
        """Set the CSRF cookie if it is not already present."""
        if CSRF_COOKIE_NAME not in request.cookies:
            token = generate_csrf_token()
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=token,
                httponly=False,   # JS must read this for double-submit
                samesite=COOKIE_SAMESITE,
                secure=COOKIE_SECURE,
                max_age=86400,    # 24 hours
                path="/",
            )

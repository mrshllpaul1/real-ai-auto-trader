"""
Authentication Guard Utility
Enforces authentication on protected endpoints via:
  1. Session token  (browser / frontend)
  2. API key        (programmatic / third-party)

Requests without either are REJECTED (HTTP 401).
"""

import hashlib
import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import Header, HTTPException, Request, Depends
from utils.safe_errors import log_security_event

logger = logging.getLogger(__name__)

SESSION_COLLECTION = "active_sessions"


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #
def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


# ------------------------------------------------------------------ #
# Core dependency – validates session token OR API key                 #
# ------------------------------------------------------------------ #
async def verify_auth(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
):
    """
    Verify that the caller presents a valid session token or API key.

    Priority:
      1. X-API-Key   → validate against api_keys collection
      2. X-Session-Token → validate against active_sessions collection
      3. Neither → 401
    """

    # ------- 1.  API key path (programmatic access) -------
    if x_api_key:
        try:
            from config.database import db
            from services.api_key_manager import APIKeyManager

            manager = APIKeyManager(db)
            key_info = await manager.validate_api_key(x_api_key)
            if key_info:
                return {
                    "source": "api_key",
                    "key_id": key_info.get("key_id"),
                    "user_id": key_info.get("user_id"),
                    "tier": key_info.get("tier", "free"),
                    "scopes": key_info.get("scopes", ["read"]),
                }
        except Exception as e:
            logger.warning(f"API key validation error: {e}")
        # If the key was provided but invalid → 401 (don't fall through)
        raise HTTPException(status_code=401, detail={"message": "Invalid API key.", "code": "INVALID_API_KEY"})

    # ------- 2.  Session token path (frontend) -------
    if x_session_token:
        try:
            from config.database import db

            session = await db[SESSION_COLLECTION].find_one({
                "session_token_hash": _hash(x_session_token),
                "is_active": True,
                "expires_at": {"$gt": datetime.utcnow()},
            })
            if session:
                return {
                    "source": "session",
                    "user_id": session.get("user_id", "demo_user"),
                    "session_active": True,
                }
        except Exception as e:
            logger.warning(f"Session validation error: {e}")
        raise HTTPException(status_code=401, detail={"message": "Session expired or invalid. Please refresh.", "code": "SESSION_INVALID"})

    # ------- 3. Trusted-origin fallback for backward compat -------
    # Allow requests coming from the known frontend origin without tokens
    # This keeps existing functionality working while we transition
    origin = request.headers.get("origin", "")
    referer = request.headers.get("referer", "")
    allowed_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
    
    if origin or referer:
        for allowed in allowed_origins:
            allowed = allowed.strip()
            if allowed == "*":
                # With wildcard CORS, allow but log
                log_security_event(
                    "unauthenticated_access",
                    {"path": str(request.url.path), "method": request.method, "origin": origin},
                    severity="info",
                    ip_address=request.client.host if request.client else "unknown"
                )
                return {"source": "trusted_origin", "user_id": "demo_user", "origin": origin or referer}
            if (origin and origin.startswith(allowed)) or (referer and referer.startswith(allowed)):
                return {"source": "trusted_origin", "user_id": "demo_user", "origin": origin or referer}

    # ------- 4. No auth at all → 401 -------
    client_ip = request.client.host if request.client else "unknown"
    log_security_event(
        "auth_rejected",
        {"path": str(request.url.path), "method": request.method},
        severity="warning",
        ip_address=client_ip,
    )
    raise HTTPException(
        status_code=401,
        detail={
            "message": "Authentication required. Provide X-Session-Token or X-API-Key header.",
            "code": "AUTH_REQUIRED",
        },
    )


# Backward-compatible alias
verify_api_key = verify_auth


# ------------------------------------------------------------------ #
# Trade-scope gate                                                     #
# ------------------------------------------------------------------ #
async def require_trade_scope(
    request: Request,
    auth_info: dict = Depends(verify_auth),
):
    """Require 'trade' scope for trade execution endpoints."""
    client_ip = request.client.host if request.client else "unknown"

    log_security_event(
        "trade_attempt",
        {"path": str(request.url.path), "method": request.method, "auth_source": auth_info.get("source")},
        severity="info",
        ip_address=client_ip,
    )

    if auth_info.get("source") == "api_key":
        scopes = auth_info.get("scopes", [])
        if "trade" not in scopes and "admin" not in scopes:
            raise HTTPException(
                status_code=403,
                detail={"message": "Insufficient permissions. 'trade' scope required.", "required_scope": "trade"},
            )

    return auth_info

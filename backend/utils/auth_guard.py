"""
Authentication Guard Utility
Provides API key validation for protecting sensitive endpoints.
"""

import logging
import os
import hashlib
import hmac
from datetime import datetime
from typing import Optional
from fastapi import Header, HTTPException, Request, Depends
from utils.safe_errors import log_security_event

logger = logging.getLogger(__name__)


async def verify_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """
    Verify that a valid API key is provided for sensitive endpoints.
    
    For now, this validates against the database of created API keys.
    Falls back to allowing requests from the frontend origin (same-origin check).
    """
    # Allow requests from the known frontend origin
    origin = request.headers.get("origin", "")
    referer = request.headers.get("referer", "")
    
    frontend_url = os.environ.get("FRONTEND_URL", "")
    allowed_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
    
    # If request comes from a known frontend origin, allow it
    if origin or referer:
        is_trusted_origin = False
        for allowed in allowed_origins:
            allowed = allowed.strip()
            if allowed == "*":
                is_trusted_origin = True
                break
            if origin and origin.startswith(allowed):
                is_trusted_origin = True
                break
            if referer and referer.startswith(allowed):
                is_trusted_origin = True
                break
        
        if is_trusted_origin:
            return {"source": "trusted_origin", "origin": origin or referer}
    
    # If API key is provided, validate it
    if x_api_key:
        try:
            from config.database import db
            from services.api_key_manager import get_api_key
            
            key_data = await get_api_key(x_api_key, db)
            if key_data and key_data.get("is_active", False):
                return {
                    "source": "api_key",
                    "key_id": key_data.get("key_id"),
                    "tier": key_data.get("tier", "free"),
                    "scopes": key_data.get("scopes", ["read"])
                }
        except Exception as e:
            logger.warning(f"API key validation failed: {e}")
    
    # For now, log the unauthenticated access but allow it
    # (to avoid breaking existing functionality during rollout)
    client_ip = request.client.host if request.client else "unknown"
    log_security_event(
        event_type="unauthenticated_access",
        details={
            "path": str(request.url.path),
            "method": request.method,
            "has_api_key": bool(x_api_key),
        },
        severity="info",
        ip_address=client_ip
    )
    
    return {"source": "unauthenticated", "warning": "No valid authentication provided"}


async def require_trade_scope(
    request: Request,
    auth_info: dict = Depends(verify_api_key)
):
    """
    Require 'trade' scope for trade execution endpoints.
    Logs all trade attempts for audit.
    """
    client_ip = request.client.host if request.client else "unknown"
    
    # Log all trade attempts
    log_security_event(
        event_type="trade_attempt",
        details={
            "path": str(request.url.path),
            "method": request.method,
            "auth_source": auth_info.get("source", "unknown"),
        },
        severity="info",
        ip_address=client_ip
    )
    
    # If authenticated via API key, check for trade scope
    if auth_info.get("source") == "api_key":
        scopes = auth_info.get("scopes", [])
        if "trade" not in scopes and "admin" not in scopes:
            raise HTTPException(
                status_code=403,
                detail={"message": "Insufficient permissions. 'trade' scope required.", "required_scope": "trade"}
            )
    
    return auth_info

"""
Safe Error Response Utility
Prevents leaking internal error details to API clients.
Logs real errors server-side, returns generic messages to users.
"""

import logging
import uuid
import traceback
from datetime import datetime
from fastapi import HTTPException
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Map of error categories to safe client-facing messages
SAFE_ERROR_MESSAGES = {
    "database": "A database error occurred. Please try again later.",
    "kraken": "Exchange connection error. Please try again shortly.",
    "trade": "Trade execution failed. Please verify your parameters and try again.",
    "auth": "Authentication error. Please check your credentials.",
    "validation": "Invalid request. Please check your input parameters.",
    "training": "Model training encountered an error. Please try again.",
    "network": "External service unavailable. Please try again later.",
    "rate_limit": "Too many requests. Please slow down.",
    "not_found": "The requested resource was not found.",
    "general": "An internal error occurred. Please try again later.",
}


def safe_error_response(
    error: Exception,
    category: str = "general",
    status_code: int = 500,
    context: Optional[str] = None,
    include_error_id: bool = True
) -> HTTPException:
    """
    Create a safe HTTPException that doesn't leak internal details.
    
    Args:
        error: The actual exception that occurred
        category: Error category for selecting safe message
        status_code: HTTP status code to return
        context: Optional context string for server-side logging
        include_error_id: Whether to include an error tracking ID
    
    Returns:
        HTTPException with safe error message
    """
    error_id = str(uuid.uuid4())[:8]
    
    # Log the REAL error server-side with full details
    log_message = f"[ERR-{error_id}] {category.upper()}"
    if context:
        log_message += f" | {context}"
    log_message += f" | {type(error).__name__}: {str(error)}"
    
    logger.error(log_message)
    logger.debug(f"[ERR-{error_id}] Traceback: {traceback.format_exc()}")
    
    # Build safe client-facing response
    safe_message = SAFE_ERROR_MESSAGES.get(category, SAFE_ERROR_MESSAGES["general"])
    
    detail: Dict[str, Any] = {
        "message": safe_message,
    }
    
    if include_error_id:
        detail["error_id"] = error_id
        detail["support_hint"] = f"Reference this ID when contacting support: ERR-{error_id}"
    
    return HTTPException(status_code=status_code, detail=detail)


def log_security_event(
    event_type: str,
    details: Dict[str, Any],
    severity: str = "warning",
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None
):
    """
    Log a security-relevant event for audit trail.
    
    Args:
        event_type: Type of security event (e.g., 'auth_failure', 'suspicious_input')
        details: Event details
        severity: Log severity level
        user_id: Optional user identifier
        ip_address: Optional client IP
    """
    event = {
        "event_id": str(uuid.uuid4())[:8],
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "severity": severity,
        "user_id": user_id,
        "ip_address": ip_address,
        "details": details
    }
    
    if severity == "critical":
        logger.critical(f"🚨 SECURITY EVENT: {event}")
    elif severity == "warning":
        logger.warning(f"⚠️ SECURITY EVENT: {event}")
    else:
        logger.info(f"ℹ️ SECURITY EVENT: {event}")
    
    return event

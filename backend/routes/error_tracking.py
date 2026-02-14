"""
Error Tracking API Routes
=========================
Receives and logs frontend errors for monitoring and debugging.
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/error-tracking", tags=["Error Tracking"])

# In-memory error storage (last 100 errors)
_errors: List[Dict[str, Any]] = []
_db = None


def set_db(db):
    global _db
    _db = db


class ErrorReport(BaseModel):
    error_id: Optional[str] = None
    message: str
    stack: Optional[str] = None
    componentStack: Optional[str] = None
    url: Optional[str] = None
    timestamp: Optional[str] = None
    severity: Optional[str] = "error"
    user_agent: Optional[str] = None
    additional_context: Optional[Dict[str, Any]] = None


@router.post("/report")
async def report_error(report: ErrorReport, request: Request):
    """
    Receive error reports from the frontend.
    Stores errors for analysis and debugging.
    """
    global _errors
    
    error_entry = {
        "error_id": report.error_id or f"err_{datetime.now().timestamp()}",
        "message": report.message,
        "stack": report.stack,
        "component_stack": report.componentStack,
        "url": report.url,
        "severity": report.severity or "error",
        "timestamp": report.timestamp or datetime.now(timezone.utc).isoformat(),
        "received_at": datetime.now(timezone.utc).isoformat(),
        "user_agent": report.user_agent or request.headers.get("user-agent"),
        "client_ip": request.client.host if request.client else None,
        "additional_context": report.additional_context or {}
    }
    
    # Log the error
    if report.severity == "error" or report.severity == "critical":
        logger.error(f"Frontend error: {report.message[:200]}")
    else:
        logger.warning(f"Frontend {report.severity}: {report.message[:200]}")
    
    # Store in memory
    _errors.append(error_entry)
    if len(_errors) > 100:
        _errors = _errors[-100:]
    
    # Store in database if available
    if _db is not None:
        try:
            await _db.frontend_errors.insert_one(error_entry)
        except Exception as e:
            logger.warning(f"Could not store error in DB: {e}")
    
    return {
        "success": True,
        "error_id": error_entry["error_id"],
        "message": "Error reported successfully"
    }


@router.get("/recent")
async def get_recent_errors(limit: int = 20):
    """Get recent frontend errors"""
    return {
        "errors": _errors[-limit:],
        "total": len(_errors)
    }


@router.get("/stats")
async def get_error_stats():
    """Get error statistics"""
    if not _errors:
        return {
            "total": 0,
            "by_severity": {},
            "recent_count": 0
        }
    
    by_severity = {}
    for err in _errors:
        sev = err.get("severity", "unknown")
        by_severity[sev] = by_severity.get(sev, 0) + 1
    
    return {
        "total": len(_errors),
        "by_severity": by_severity,
        "recent_count": len(_errors),
        "oldest": _errors[0].get("timestamp") if _errors else None,
        "newest": _errors[-1].get("timestamp") if _errors else None
    }


@router.delete("/clear")
async def clear_errors():
    """Clear all stored errors"""
    global _errors
    count = len(_errors)
    _errors = []
    return {
        "success": True,
        "cleared": count
    }

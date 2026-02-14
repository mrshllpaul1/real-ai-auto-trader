"""Session Authentication Routes
Provides session token issuance and CSRF token retrieval.
"""

import secrets
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field
from typing import Optional
from config.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

SESSION_TTL_HOURS = 24
SESSION_COLLECTION = "active_sessions"


class SessionResponse(BaseModel):
    session_token: str
    expires_at: str
    user_id: str


@router.post("/session")
async def create_session(request: Request, response: Response):
    """
    Issue a new session token for the frontend.
    The token must be sent as X-Session-Token header on subsequent requests.
    Also ensures a CSRF cookie is set.
    """
    user_id = request.headers.get("x-user-id") or "demo_user"
    client_ip = request.client.host if request.client else "unknown"

    # Generate session token
    session_token = f"sess_{secrets.token_urlsafe(48)}"
    expires_at = datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS)

    # Store session in DB
    session_doc = {
        "session_token_hash": _hash(session_token),
        "user_id": user_id,
        "client_ip": client_ip,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at,
        "is_active": True,
    }
    await db[SESSION_COLLECTION].insert_one(session_doc)

    # Ensure CSRF cookie
    csrf_token = request.cookies.get("csrf_token")
    if not csrf_token:
        csrf_token = secrets.token_hex(32)
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=False,
            samesite="lax",
            secure=False,
            max_age=86400,
            path="/",
        )

    logger.info(f"Session created | user={user_id} | ip={client_ip}")

    return SessionResponse(
        session_token=session_token,
        expires_at=expires_at.isoformat(),
        user_id=user_id,
    )


@router.get("/csrf-token")
async def get_csrf_token(request: Request, response: Response):
    """
    Ensure a CSRF cookie is present and return its value.
    Useful for the frontend to bootstrap the CSRF header.
    """
    existing = request.cookies.get("csrf_token")
    if existing:
        return {"csrf_token": existing}

    token = secrets.token_hex(32)
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,
        samesite="lax",
        secure=False,
        max_age=86400,
        path="/",
    )
    return {"csrf_token": token}


@router.post("/session/validate")
async def validate_session(request: Request):
    """Validate a session token."""
    token = request.headers.get("x-session-token", "")
    if not token:
        return {"valid": False, "reason": "No session token provided"}

    session = await db[SESSION_COLLECTION].find_one({
        "session_token_hash": _hash(token),
        "is_active": True,
        "expires_at": {"$gt": datetime.utcnow()},
    })

    if session:
        return {"valid": True, "user_id": session["user_id"], "expires_at": session["expires_at"].isoformat()}
    return {"valid": False, "reason": "Session expired or invalid"}


@router.post("/session/revoke")
async def revoke_session(request: Request):
    """Revoke / log-out a session."""
    token = request.headers.get("x-session-token", "")
    if not token:
        return {"revoked": False}

    result = await db[SESSION_COLLECTION].update_one(
        {"session_token_hash": _hash(token)},
        {"$set": {"is_active": False}},
    )
    return {"revoked": result.modified_count > 0}


# --------------- helpers ---------------
import hashlib

def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()

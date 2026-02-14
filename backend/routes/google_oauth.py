"""
Google OAuth Authentication Routes
==================================
Implements Emergent-managed Google OAuth for social login.
Includes session management, user storage, and 2FA support.
"""

from fastapi import APIRouter, HTTPException, Request, Response, Depends, Cookie
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone, timedelta
import httpx
import uuid
import pyotp
import qrcode
import io
import base64

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

_db = None

def set_dependencies(db):
    global _db
    _db = db

def get_db():
    if _db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return _db

# REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH

# ==================== Models ====================

class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None

class SessionRequest(BaseModel):
    session_id: str

class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: list

class TwoFactorVerifyRequest(BaseModel):
    code: str

# ==================== Session Management ====================

@router.post("/session")
async def exchange_session(request: SessionRequest, response: Response):
    """
    Exchange Emergent session_id for user data and set session cookie.
    Called after Google OAuth redirect with session_id in URL fragment.
    """
    db = get_db()
    
    try:
        # Call Emergent Auth to get user data
        async with httpx.AsyncClient() as client:
            auth_response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": request.session_id},
                timeout=10.0
            )
            
            if auth_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session_id")
            
            auth_data = auth_response.json()
        
        email = auth_data.get("email")
        name = auth_data.get("name", "User")
        picture = auth_data.get("picture")
        session_token = auth_data.get("session_token")
        
        if not email or not session_token:
            raise HTTPException(status_code=400, detail="Invalid auth response")
        
        # Check if user exists
        existing_user = await db.users.find_one({"email": email}, {"_id": 0})
        
        if existing_user:
            user_id = existing_user["user_id"]
            # Update user data if changed
            await db.users.update_one(
                {"email": email},
                {"$set": {
                    "name": name,
                    "picture": picture,
                    "last_login": datetime.now(timezone.utc)
                }}
            )
        else:
            # Create new user
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            await db.users.insert_one({
                "user_id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "created_at": datetime.now(timezone.utc),
                "last_login": datetime.now(timezone.utc),
                "two_factor_enabled": False,
                "two_factor_secret": None,
                "onboarding_completed": False
            })
        
        # Store session
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await db.user_sessions.replace_one(
            {"user_id": user_id},
            {
                "user_id": user_id,
                "session_token": session_token,
                "expires_at": expires_at,
                "created_at": datetime.now(timezone.utc)
            },
            upsert=True
        )
        
        # Set httpOnly cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            max_age=7 * 24 * 60 * 60  # 7 days
        )
        
        # Get user data to return
        user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        
        return {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "two_factor_enabled": user_doc.get("two_factor_enabled", False),
            "onboarding_completed": user_doc.get("onboarding_completed", False)
        }
        
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail="An internal error occurred. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.get("/me")
async def get_current_user(
    request: Request,
    session_token: Optional[str] = Cookie(None)
):
    """
    Get current authenticated user from session cookie.
    Used by frontend to verify authentication status.
    """
    db = get_db()
    
    # Try cookie first, then Authorization header
    token = session_token
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Find session
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Check expiry
    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Get user
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "picture": user.get("picture"),
        "two_factor_enabled": user.get("two_factor_enabled", False),
        "onboarding_completed": user.get("onboarding_completed", False)
    }


@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    session_token: Optional[str] = Cookie(None)
):
    """Logout and clear session"""
    db = get_db()
    
    token = session_token
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    
    response.delete_cookie(
        key="session_token",
        path="/",
        secure=True,
        samesite="none"
    )
    
    return {"message": "Logged out successfully"}


# ==================== 2FA (Two-Factor Authentication) ====================

@router.post("/2fa/setup")
async def setup_two_factor(
    request: Request,
    session_token: Optional[str] = Cookie(None)
):
    """
    Generate 2FA secret and QR code for authenticator apps.
    Returns secret, QR code (base64), and backup codes.
    """
    db = get_db()
    
    # Get current user
    token = session_token
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Generate secret
    secret = pyotp.random_base32()
    
    # Generate QR code
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=user["email"],
        issuer_name="AICryptoTrade"
    )
    
    # Create QR code image
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    # Generate backup codes
    backup_codes = [uuid.uuid4().hex[:8].upper() for _ in range(8)]
    
    # Store temporarily (not enabled yet)
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "two_factor_secret_pending": secret,
            "two_factor_backup_codes": backup_codes
        }}
    )
    
    return {
        "secret": secret,
        "qr_code": f"data:image/png;base64,{qr_base64}",
        "backup_codes": backup_codes
    }


@router.post("/2fa/verify")
async def verify_two_factor(
    verify_request: TwoFactorVerifyRequest,
    request: Request,
    session_token: Optional[str] = Cookie(None)
):
    """
    Verify 2FA code and enable two-factor authentication.
    """
    db = get_db()
    
    token = session_token
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Get pending secret
    secret = user.get("two_factor_secret_pending")
    if not secret:
        raise HTTPException(status_code=400, detail="No 2FA setup in progress")
    
    # Verify code
    totp = pyotp.TOTP(secret)
    if not totp.verify(verify_request.code):
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    # Enable 2FA
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {
            "$set": {
                "two_factor_enabled": True,
                "two_factor_secret": secret
            },
            "$unset": {"two_factor_secret_pending": ""}
        }
    )
    
    return {"message": "Two-factor authentication enabled", "enabled": True}


@router.post("/2fa/disable")
async def disable_two_factor(
    verify_request: TwoFactorVerifyRequest,
    request: Request,
    session_token: Optional[str] = Cookie(None)
):
    """
    Disable 2FA after verifying current code.
    """
    db = get_db()
    
    token = session_token
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.get("two_factor_enabled"):
        raise HTTPException(status_code=400, detail="2FA not enabled")
    
    # Verify code
    totp = pyotp.TOTP(user["two_factor_secret"])
    if not totp.verify(verify_request.code):
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    # Disable 2FA
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {
            "$set": {"two_factor_enabled": False},
            "$unset": {
                "two_factor_secret": "",
                "two_factor_backup_codes": ""
            }
        }
    )
    
    return {"message": "Two-factor authentication disabled", "enabled": False}


# ==================== Onboarding ====================

@router.post("/onboarding/complete")
async def complete_onboarding(
    request: Request,
    session_token: Optional[str] = Cookie(None)
):
    """Mark onboarding as complete for user"""
    db = get_db()
    
    token = session_token
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    await db.users.update_one(
        {"user_id": session["user_id"]},
        {"$set": {"onboarding_completed": True}}
    )
    
    return {"message": "Onboarding completed", "onboarding_completed": True}


# ==================== Security Settings ====================

@router.get("/sessions")
async def get_active_sessions(
    request: Request,
    session_token: Optional[str] = Cookie(None)
):
    """Get all active sessions for security overview"""
    db = get_db()
    
    token = session_token
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Get all sessions for this user
    sessions = await db.user_sessions.find(
        {"user_id": session["user_id"]},
        {"_id": 0, "session_token": 0}  # Don't expose tokens
    ).to_list(100)
    
    return {
        "sessions": sessions,
        "current_session_id": session["user_id"]
    }


@router.delete("/sessions/all")
async def revoke_all_sessions(
    response: Response,
    request: Request,
    session_token: Optional[str] = Cookie(None)
):
    """Revoke all sessions (logout everywhere)"""
    db = get_db()
    
    token = session_token
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Delete all sessions
    await db.user_sessions.delete_many({"user_id": session["user_id"]})
    
    # Clear cookie
    response.delete_cookie(
        key="session_token",
        path="/",
        secure=True,
        samesite="none"
    )
    
    return {"message": "All sessions revoked"}

"""
Email Digest API Routes
Provides endpoints for managing email digests and preferences
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/digest", tags=["Email Digest"])

# Global references
_db = None
_digest_service = None


def set_dependencies(database, digest_service):
    """Set dependencies from main app"""
    global _db, _digest_service
    _db = database
    _digest_service = digest_service


class EmailPreferences(BaseModel):
    """User email preferences"""
    digest_enabled: bool = True
    daily_digest: bool = True
    weekly_digest: bool = True
    trade_alerts: bool = True
    strategy_alerts: bool = True


class SendDigestRequest(BaseModel):
    """Request to send digest"""
    user_id: str
    period: str = "daily"  # daily or weekly


@router.post("/send")
async def send_digest(request: SendDigestRequest):
    """
    Manually send an email digest to a user
    
    Args:
        user_id: User ID
        period: 'daily' or 'weekly'
    
    Returns:
        Status of email send
    """
    try:
        if _digest_service is None:
            raise HTTPException(status_code=500, detail="Digest service not initialized")
        
        if request.period not in ["daily", "weekly"]:
            raise HTTPException(status_code=400, detail="Period must be 'daily' or 'weekly'")
        
        result = await _digest_service.send_digest(request.user_id, request.period)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to send digest"))
        
        return {
            "success": True,
            "message": result.get("message"),
            "email": result.get("email")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending digest: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preferences")
async def get_email_preferences(user_id: str = Query(..., description="User ID")):
    """
    Get user's email digest preferences
    
    Args:
        user_id: User ID
    
    Returns:
        Email preferences
    """
    try:
        if _db is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        user = await _db.users.find_one({"user_id": user_id})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        preferences = user.get("email_preferences", {
            "digest_enabled": True,
            "daily_digest": True,
            "weekly_digest": True,
            "trade_alerts": True,
            "strategy_alerts": True
        })
        
        return preferences
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences")
async def update_email_preferences(
    user_id: str = Query(..., description="User ID"),
    preferences: EmailPreferences = None
):
    """
    Update user's email digest preferences
    
    Args:
        user_id: User ID
        preferences: New email preferences
    
    Returns:
        Updated preferences
    """
    try:
        if _db is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Update preferences
        result = await _db.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "email_preferences": preferences.dict()
                }
            },
            upsert=True
        )
        
        return {
            "success": True,
            "message": "Preferences updated successfully",
            "preferences": preferences.dict()
        }
        
    except Exception as e:
        logger.error(f"Error updating preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def send_test_digest(user_id: str = Query(..., description="User ID")):
    """
    Send a test digest email to verify configuration
    
    Args:
        user_id: User ID
    
    Returns:
        Status of test email
    """
    try:
        if _digest_service is None:
            raise HTTPException(status_code=500, detail="Digest service not initialized")
        
        result = await _digest_service.send_digest(user_id, "daily")
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to send test digest"))
        
        return {
            "success": True,
            "message": "Test digest sent successfully",
            "email": result.get("email")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test digest: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

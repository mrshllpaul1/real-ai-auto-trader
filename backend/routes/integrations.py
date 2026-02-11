"""
Integration Settings API Routes
Handles blockchain API and social trading platform configurations.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["Integrations"])

# Global database reference
_db = None


def set_db(db):
    global _db
    _db = db


# Models
class BlockchainKeysRequest(BaseModel):
    alchemy_api_key: Optional[str] = None
    moralis_api_key: Optional[str] = None
    infura_api_key: Optional[str] = None
    quicknode_api_key: Optional[str] = None


class SocialTradingRequest(BaseModel):
    platform_type: str
    api_key: str
    api_secret: Optional[str] = None
    username: Optional[str] = None


# Blockchain API Endpoints
@router.post("/blockchain/save")
async def save_blockchain_keys(keys: BlockchainKeysRequest):
    """Save blockchain API keys for DeFi integration"""
    if _db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    # Filter out empty keys
    keys_to_save = {k: v for k, v in keys.model_dump().items() if v and v.strip()}
    
    if not keys_to_save:
        raise HTTPException(status_code=400, detail="No valid API keys provided")
    
    # Save to database
    await _db.integration_settings.update_one(
        {"type": "blockchain"},
        {
            "$set": {
                "type": "blockchain",
                "keys": keys_to_save,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "providers_configured": list(keys_to_save.keys())
            }
        },
        upsert=True
    )
    
    logger.info(f"Saved blockchain API keys for: {list(keys_to_save.keys())}")
    
    return {
        "success": True,
        "message": "Blockchain API keys saved successfully",
        "providers_configured": list(keys_to_save.keys())
    }


@router.get("/blockchain/status")
async def get_blockchain_status():
    """Get status of blockchain API integrations"""
    if _db is None:
        return {"configured": False, "providers": []}
    
    settings = await _db.integration_settings.find_one(
        {"type": "blockchain"},
        {"_id": 0}
    )
    
    if not settings or not settings.get("keys"):
        return {
            "configured": False,
            "providers": [],
            "message": "No blockchain APIs configured"
        }
    
    providers = settings.get("providers_configured", [])
    
    return {
        "configured": True,
        "providers": providers,
        "alchemy": "alchemy_api_key" in providers,
        "moralis": "moralis_api_key" in providers,
        "infura": "infura_api_key" in providers,
        "quicknode": "quicknode_api_key" in providers,
        "updated_at": settings.get("updated_at")
    }


# Social Trading Platform Endpoints
@router.post("/social-trading/connect")
async def connect_social_platform(request: SocialTradingRequest):
    """Connect a social trading platform for copy trading"""
    if _db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    supported_platforms = ['etoro', 'zulutrade', 'naga', '3commas', 'shrimpy', 'custom']
    
    if request.platform_type not in supported_platforms:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported platform. Supported: {', '.join(supported_platforms)}"
        )
    
    if not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    # Save connection details
    await _db.integration_settings.update_one(
        {"type": "social_trading"},
        {
            "$set": {
                "type": "social_trading",
                "platform": request.platform_type,
                "api_key": request.api_key[:8] + "..." + request.api_key[-4:] if len(request.api_key) > 12 else "***",
                "has_secret": bool(request.api_secret),
                "username": request.username,
                "connected": True,
                "connected_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    # Store actual credentials securely (in production, use encryption)
    await _db.secure_credentials.update_one(
        {"type": "social_trading"},
        {
            "$set": {
                "type": "social_trading",
                "platform": request.platform_type,
                "api_key": request.api_key,
                "api_secret": request.api_secret,
                "username": request.username,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    logger.info(f"Connected social trading platform: {request.platform_type}")
    
    return {
        "success": True,
        "message": f"Successfully connected to {request.platform_type}",
        "platform": request.platform_type,
        "copy_trading_enabled": True
    }


@router.get("/social-trading/status")
async def get_social_trading_status():
    """Get status of social trading platform connection"""
    if _db is None:
        return {"connected": False, "platform": None}
    
    settings = await _db.integration_settings.find_one(
        {"type": "social_trading"},
        {"_id": 0}
    )
    
    if not settings or not settings.get("connected"):
        return {
            "connected": False,
            "platform": None,
            "message": "No social trading platform connected"
        }
    
    return {
        "connected": True,
        "platform": settings.get("platform"),
        "username": settings.get("username"),
        "connected_at": settings.get("connected_at"),
        "copy_trading_enabled": True
    }


@router.delete("/social-trading/disconnect")
async def disconnect_social_platform():
    """Disconnect the social trading platform"""
    if _db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    await _db.integration_settings.delete_one({"type": "social_trading"})
    await _db.secure_credentials.delete_one({"type": "social_trading"})
    
    return {
        "success": True,
        "message": "Social trading platform disconnected"
    }


# Get all integration statuses
@router.get("/status")
async def get_all_integrations_status():
    """Get status of all integrations"""
    blockchain = await get_blockchain_status()
    social = await get_social_trading_status()
    
    return {
        "blockchain": blockchain,
        "social_trading": social,
        "defi_enabled": blockchain.get("configured", False),
        "copy_trading_enabled": social.get("connected", False)
    }

"""
API Key Management System
Handles API key creation, validation, and rate limiting
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

# API Key security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

class APIKey(BaseModel):
    """API Key model"""
    key_id: str
    user_id: str
    key_hash: str
    name: str
    tier: str = "free"  # free, pro, enterprise
    scopes: list[str] = ["read"]  # read, trade, admin
    rate_limit_per_day: int = 100
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True
    requests_today: int = 0
    requests_last_reset: datetime = datetime.utcnow()

class APIKeyManager:
    """
    Manages API keys for third-party developers
    """
    
    def __init__(self, db):
        self.db = db
        self.collection = db.api_keys
        
    def generate_api_key(self) -> str:
        """Generate a secure API key"""
        return f"sk-{secrets.token_urlsafe(32)}"
    
    def hash_key(self, api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    async def create_api_key(
        self,
        user_id: str,
        name: str,
        tier: str = "free",
        scopes: list[str] = None,
        expires_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new API key
        
        Args:
            user_id: User ID
            name: Friendly name for the key
            tier: Subscription tier (free, pro, enterprise)
            scopes: List of permission scopes
            expires_days: Days until expiration (None = never)
            
        Returns:
            Dict with plain key (only shown once) and key info
        """
        if scopes is None:
            scopes = ["read"]
            
        # Generate key
        api_key = self.generate_api_key()
        key_hash = self.hash_key(api_key)
        key_id = f"key_{secrets.token_urlsafe(16)}"
        
        # Rate limits by tier
        rate_limits = {
            "free": 100,
            "pro": 10000,
            "enterprise": 1000000  # Effectively unlimited
        }
        
        # Calculate expiration
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        # Create key document
        key_doc = {
            "key_id": key_id,
            "user_id": user_id,
            "key_hash": key_hash,
            "name": name,
            "tier": tier,
            "scopes": scopes,
            "rate_limit_per_day": rate_limits.get(tier, 100),
            "created_at": datetime.utcnow(),
            "last_used_at": None,
            "expires_at": expires_at,
            "is_active": True,
            "requests_today": 0,
            "requests_last_reset": datetime.utcnow()
        }
        
        await self.collection.insert_one(key_doc)
        
        return {
            "api_key": api_key,  # Only shown once!
            "key_id": key_id,
            "name": name,
            "tier": tier,
            "scopes": scopes,
            "rate_limit_per_day": rate_limits.get(tier, 100),
            "created_at": key_doc["created_at"],
            "expires_at": expires_at
        }
    
    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate an API key and return key info
        
        Args:
            api_key: Plain text API key
            
        Returns:
            Key info dict if valid, None if invalid
        """
        if not api_key or not api_key.startswith("sk-"):
            return None
        
        key_hash = self.hash_key(api_key)
        
        # Find key
        key_doc = await self.collection.find_one({"key_hash": key_hash})
        
        if not key_doc:
            return None
        
        # Check if active
        if not key_doc.get("is_active", False):
            return None
        
        # Check if expired
        expires_at = key_doc.get("expires_at")
        if expires_at and datetime.utcnow() > expires_at:
            # Deactivate expired key
            await self.collection.update_one(
                {"key_hash": key_hash},
                {"$set": {"is_active": False}}
            )
            return None
        
        # Check rate limit
        last_reset = key_doc.get("requests_last_reset", datetime.utcnow())
        requests_today = key_doc.get("requests_today", 0)
        
        # Reset counter if new day
        if (datetime.utcnow() - last_reset).days >= 1:
            requests_today = 0
            last_reset = datetime.utcnow()
            await self.collection.update_one(
                {"key_hash": key_hash},
                {
                    "$set": {
                        "requests_today": 0,
                        "requests_last_reset": last_reset
                    }
                }
            )
        
        # Check if over limit
        rate_limit = key_doc.get("rate_limit_per_day", 100)
        if requests_today >= rate_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Limit: {rate_limit} requests/day. Resets in {24 - (datetime.utcnow() - last_reset).seconds // 3600} hours."
            )
        
        # Increment request count and update last used
        await self.collection.update_one(
            {"key_hash": key_hash},
            {
                "$inc": {"requests_today": 1},
                "$set": {"last_used_at": datetime.utcnow()}
            }
        )
        
        return {
            "key_id": key_doc["key_id"],
            "user_id": key_doc["user_id"],
            "name": key_doc["name"],
            "tier": key_doc["tier"],
            "scopes": key_doc["scopes"],
            "rate_limit_per_day": rate_limit,
            "requests_today": requests_today + 1,
            "requests_remaining": max(0, rate_limit - requests_today - 1)
        }
    
    async def list_user_keys(self, user_id: str) -> list[Dict[str, Any]]:
        """List all API keys for a user"""
        keys = await self.collection.find(
            {"user_id": user_id},
            {"key_hash": 0}  # Don't return hash
        ).to_list(100)
        
        return keys
    
    async def revoke_api_key(self, key_id: str, user_id: str) -> bool:
        """Revoke (deactivate) an API key"""
        result = await self.collection.update_one(
            {"key_id": key_id, "user_id": user_id},
            {"$set": {"is_active": False}}
        )
        
        return result.modified_count > 0
    
    async def delete_api_key(self, key_id: str, user_id: str) -> bool:
        """Permanently delete an API key"""
        result = await self.collection.delete_one(
            {"key_id": key_id, "user_id": user_id}
        )
        
        return result.deleted_count > 0
    
    async def get_key_usage(self, key_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get usage statistics for an API key"""
        key_doc = await self.collection.find_one(
            {"key_id": key_id, "user_id": user_id},
            {"key_hash": 0}
        )
        
        if not key_doc:
            return None
        
        return {
            "key_id": key_doc["key_id"],
            "name": key_doc["name"],
            "tier": key_doc["tier"],
            "requests_today": key_doc.get("requests_today", 0),
            "rate_limit_per_day": key_doc.get("rate_limit_per_day", 100),
            "last_used_at": key_doc.get("last_used_at"),
            "created_at": key_doc["created_at"],
            "is_active": key_doc["is_active"]
        }


# Dependency for protected routes
async def get_api_key(
    api_key: str = Security(api_key_header),
    db = None
) -> Dict[str, Any]:
    """
    Dependency to validate API key and return key info
    
    Usage:
        @app.get("/protected")
        async def protected_route(key_info: dict = Depends(get_api_key)):
            user_id = key_info["user_id"]
            ...
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include X-API-Key header."
        )
    
    # Get database from app state
    from config.database import db as database
    if db is None:
        db = database
    
    manager = APIKeyManager(db)
    key_info = await manager.validate_api_key(api_key)
    
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key"
        )
    
    return key_info


# Scope checker dependency
def require_scope(required_scope: str):
    """
    Dependency factory to check for specific scope
    
    Usage:
        @app.post("/trade")
        async def trade_endpoint(
            key_info: dict = Depends(get_api_key),
            _: None = Depends(require_scope("trade"))
        ):
            ...
    """
    async def check_scope(key_info: dict = Security(get_api_key)):
        scopes = key_info.get("scopes", [])
        if required_scope not in scopes and "admin" not in scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scope: {required_scope}"
            )
        return key_info
    
    return check_scope

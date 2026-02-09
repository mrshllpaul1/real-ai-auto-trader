"""
API Key Management Routes
Allows users to create and manage API keys for third-party access
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from config.database import db
from services.api_key_manager import APIKeyManager, get_api_key

router = APIRouter(prefix="/api-keys", tags=["auth"])

# Request/Response models
class CreateAPIKeyRequest(BaseModel):
    name: str = Field(..., description="Friendly name for the API key")
    tier: str = Field("free", description="Subscription tier: free, pro, enterprise")
    scopes: List[str] = Field(["read"], description="Permission scopes: read, trade, admin")
    expires_days: Optional[int] = Field(None, description="Days until expiration (None = never)")

class APIKeyResponse(BaseModel):
    api_key: Optional[str] = Field(None, description="Plain API key (only shown once!)")
    key_id: str
    name: str
    tier: str
    scopes: List[str]
    rate_limit_per_day: int
    created_at: datetime
    expires_at: Optional[datetime] = None

class APIKeyInfo(BaseModel):
    key_id: str
    name: str
    tier: str
    scopes: List[str]
    rate_limit_per_day: int
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    requests_today: int = 0

class APIKeyUsage(BaseModel):
    key_id: str
    name: str
    tier: str
    requests_today: int
    rate_limit_per_day: int
    last_used_at: Optional[datetime] = None
    created_at: datetime
    is_active: bool


# Initialize manager
manager = APIKeyManager(db)


@router.post("/create", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateAPIKeyRequest,
    user_id: str = "demo_user"  # TODO: Get from auth
):
    """
    Create a new API key for programmatic access
    
    **Important:** The API key is only shown once. Save it securely!
    
    ## Scopes
    - `read`: Read-only access to portfolio and market data
    - `trade`: Execute trades (requires read scope)
    - `admin`: Full access to all features
    
    ## Rate Limits
    - **Free**: 100 requests/day
    - **Pro**: 10,000 requests/day
    - **Enterprise**: Unlimited
    """
    try:
        key_data = await manager.create_api_key(
            user_id=user_id,
            name=request.name,
            tier=request.tier,
            scopes=request.scopes,
            expires_days=request.expires_days
        )
        
        return APIKeyResponse(**key_data)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get("/list", response_model=List[APIKeyInfo])
async def list_api_keys(user_id: str = "demo_user"):
    """
    List all API keys for the current user
    
    Returns key metadata (not the actual keys)
    """
    try:
        keys = await manager.list_user_keys(user_id)
        return [APIKeyInfo(**key) for key in keys]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}"
        )


@router.get("/usage/{key_id}", response_model=APIKeyUsage)
async def get_key_usage(
    key_id: str,
    user_id: str = "demo_user"
):
    """
    Get usage statistics for a specific API key
    """
    usage = await manager.get_key_usage(key_id, user_id)
    
    if not usage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return APIKeyUsage(**usage)


@router.post("/revoke/{key_id}")
async def revoke_api_key(
    key_id: str,
    user_id: str = "demo_user"
):
    """
    Revoke (deactivate) an API key
    
    The key will no longer work but remains in the database for audit purposes.
    """
    success = await manager.revoke_api_key(key_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return {"message": "API key revoked successfully", "key_id": key_id}


@router.delete("/delete/{key_id}")
async def delete_api_key(
    key_id: str,
    user_id: str = "demo_user"
):
    """
    Permanently delete an API key
    
    This action cannot be undone.
    """
    success = await manager.delete_api_key(key_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return {"message": "API key deleted successfully", "key_id": key_id}


@router.get("/validate")
async def validate_current_key(key_info: dict = Depends(get_api_key)):
    """
    Validate the current API key and return info
    
    Useful for testing your API key.
    """
    return {
        "valid": True,
        "key_id": key_info["key_id"],
        "user_id": key_info["user_id"],
        "tier": key_info["tier"],
        "scopes": key_info["scopes"],
        "rate_limit_per_day": key_info["rate_limit_per_day"],
        "requests_today": key_info["requests_today"],
        "requests_remaining": key_info["requests_remaining"]
    }

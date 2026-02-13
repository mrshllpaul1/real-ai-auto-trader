"""
AI Auto-Discovery Routes
Endpoints for managing AI-powered coin discovery.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel

router = APIRouter(prefix="/ai-discovery", tags=["AI Discovery"])

# Will be set by server.py
_discovery_service = None


def set_dependencies(discovery_service):
    """Set dependencies from server.py"""
    global _discovery_service
    _discovery_service = discovery_service


class DiscoverySettingsUpdate(BaseModel):
    enabled: Optional[bool] = None
    min_score: Optional[int] = None
    max_daily_additions: Optional[int] = None
    require_approval: Optional[bool] = None
    min_market_cap: Optional[int] = None
    min_volume_24h: Optional[int] = None


@router.get("/stats")
async def get_discovery_stats():
    """Get AI discovery statistics"""
    if not _discovery_service:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")
    
    stats = await _discovery_service.get_stats()
    return stats


@router.post("/scan")
async def run_discovery_scan():
    """
    Trigger an AI discovery scan.
    Fetches trending coins, analyzes them, and adds promising ones to the universe.
    """
    if not _discovery_service:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")
    
    results = await _discovery_service.run_discovery_scan()
    return results


@router.get("/history")
async def get_discovery_history(limit: int = 20):
    """Get history of discovery runs"""
    if not _discovery_service:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")
    
    history = await _discovery_service.get_discovery_history(limit)
    return {"history": history, "count": len(history)}


@router.get("/pending")
async def get_pending_discoveries():
    """Get discoveries pending approval"""
    if not _discovery_service:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")
    
    pending = await _discovery_service.get_pending_discoveries()
    return {"pending": pending, "count": len(pending)}


@router.post("/approve/{coin_id}")
async def approve_discovery(coin_id: str):
    """Approve a pending discovery to add it to the universe"""
    if not _discovery_service:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")
    
    result = await _discovery_service.approve_discovery(coin_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error', 'Approval failed'))
    
    return result


@router.post("/reject/{coin_id}")
async def reject_discovery(coin_id: str, reason: str = ""):
    """Reject a pending discovery"""
    if not _discovery_service:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")
    
    result = await _discovery_service.reject_discovery(coin_id, reason)
    if not result.get('success'):
        raise HTTPException(status_code=404, detail="Discovery not found")
    
    return {"message": f"Rejected {coin_id}"}


@router.get("/settings")
async def get_settings():
    """Get current discovery settings"""
    if not _discovery_service:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")
    
    settings = await _discovery_service.load_settings()
    return settings


@router.post("/settings")
async def update_settings(updates: DiscoverySettingsUpdate):
    """Update discovery settings"""
    if not _discovery_service:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")
    
    update_dict = {k: v for k, v in updates.dict().items() if v is not None}
    settings = await _discovery_service.save_settings(update_dict)
    return {"message": "Settings updated", "settings": settings}

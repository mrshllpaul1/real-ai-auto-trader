"""
AI Universe Management Routes
Allows viewing, adding, and managing the dynamic coin universe.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter(prefix="/ai-universe", tags=["AI Universe"])

# Will be set by server.py
_universe_manager = None


def set_dependencies(universe_manager):
    """Set dependencies from server.py"""
    global _universe_manager
    _universe_manager = universe_manager


class AddCoinRequest(BaseModel):
    coin_id: str
    symbol: str
    category: Optional[str] = "discovered"
    reason: Optional[str] = None


class AIDiscoverRequest(BaseModel):
    coin_id: str
    symbol: str
    reason: str
    potential_score: Optional[float] = 0
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None


class UpdateCoinRequest(BaseModel):
    category: Optional[str] = None
    active: Optional[bool] = None
    metadata: Optional[dict] = None


@router.get("/stats")
async def get_universe_stats():
    """Get statistics about the coin universe"""
    if not _universe_manager:
        raise HTTPException(status_code=503, detail="Universe manager not initialized")
    
    stats = await _universe_manager.get_universe_stats()
    return stats


@router.get("/coins")
async def get_all_coins():
    """Get all active coins in the universe"""
    if not _universe_manager:
        raise HTTPException(status_code=503, detail="Universe manager not initialized")
    
    coins = await _universe_manager.get_all_coins()
    return {"coins": coins, "count": len(coins)}


@router.get("/coins/training")
async def get_training_coins():
    """Get all coins for AI training, sorted by priority"""
    if not _universe_manager:
        raise HTTPException(status_code=503, detail="Universe manager not initialized")
    
    coins = await _universe_manager.get_training_coins()
    return {"coins": coins, "count": len(coins)}


@router.get("/coins/gems")
async def get_gem_candidates():
    """Get coins that could be gems (high risk/reward)"""
    if not _universe_manager:
        raise HTTPException(status_code=503, detail="Universe manager not initialized")
    
    coins = await _universe_manager.get_gem_candidates()
    return {"coins": coins, "count": len(coins)}


@router.get("/coins/discovered")
async def get_ai_discovered_coins():
    """Get all coins discovered by AI"""
    if not _universe_manager:
        raise HTTPException(status_code=503, detail="Universe manager not initialized")
    
    coins = await _universe_manager.get_ai_discovered_coins()
    return {"coins": coins, "count": len(coins)}


@router.get("/coins/category/{category}")
async def get_coins_by_category(category: str):
    """Get all coins in a specific category"""
    if not _universe_manager:
        raise HTTPException(status_code=503, detail="Universe manager not initialized")
    
    coins = await _universe_manager.get_coins_by_category(category)
    return {"category": category, "coins": coins, "count": len(coins)}


@router.get("/coin/{coin_id}")
async def get_coin(coin_id: str):
    """Get details for a specific coin"""
    if not _universe_manager:
        raise HTTPException(status_code=503, detail="Universe manager not initialized")
    
    coin = await _universe_manager.get_coin(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")
    return coin


@router.post("/coins/add")
async def add_coin(request: AddCoinRequest):
    """Add a new coin to the universe (manual)"""
    if not _universe_manager:
        raise HTTPException(status_code=503, detail="Universe manager not initialized")
    
    result = await _universe_manager.add_coin(
        coin_id=request.coin_id,
        symbol=request.symbol,
        category=request.category,
        added_by="user",
        reason=request.reason
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error', 'Failed to add coin'))
    
    return result


@router.post("/coins/ai-discover")
async def ai_discover_coin(request: AIDiscoverRequest):
    """AI-driven coin discovery - add a coin found by AI analysis"""
    if not _universe_manager:
        raise HTTPException(status_code=503, detail="Universe manager not initialized")
    
    result = await _universe_manager.ai_discover_coin(
        coin_id=request.coin_id,
        symbol=request.symbol,
        reason=request.reason,
        potential_score=request.potential_score,
        market_cap=request.market_cap,
        volume_24h=request.volume_24h
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error', 'Failed to add coin'))
    
    return result


@router.put("/coin/{coin_id}")
async def update_coin(coin_id: str, request: UpdateCoinRequest):
    """Update a coin's information"""
    if not _universe_manager:
        raise HTTPException(status_code=503, detail="Universe manager not initialized")
    
    updates = {}
    if request.category is not None:
        updates['category'] = request.category
    if request.active is not None:
        updates['active'] = request.active
    if request.metadata is not None:
        updates['metadata'] = request.metadata
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    result = await _universe_manager.update_coin(coin_id, updates)
    
    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error', 'Coin not found'))
    
    return result


@router.delete("/coin/{coin_id}")
async def deactivate_coin(coin_id: str, reason: Optional[str] = None):
    """Deactivate a coin (soft delete)"""
    if not _universe_manager:
        raise HTTPException(status_code=503, detail="Universe manager not initialized")
    
    result = await _universe_manager.deactivate_coin(coin_id, reason)
    
    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error', 'Coin not found'))
    
    return result


@router.post("/initialize")
async def initialize_universe():
    """Initialize the coin universe from base coins (idempotent)"""
    if not _universe_manager:
        raise HTTPException(status_code=503, detail="Universe manager not initialized")
    
    result = await _universe_manager.initialize()
    return result


@router.get("/categories")
async def get_categories():
    """Get all available coin categories"""
    from services.dynamic_coin_universe import CATEGORIES
    return {"categories": CATEGORIES}

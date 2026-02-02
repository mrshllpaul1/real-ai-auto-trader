"""
Coin Universe API Routes
Manage the dynamic coin universe - AI can discover and add new coins.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

router = APIRouter(prefix="/universe", tags=["Coin Universe"])

# Global reference
universe_manager = None


def set_dependencies(manager):
    global universe_manager
    universe_manager = manager


class AddCoinRequest(BaseModel):
    coin_id: str
    symbol: str
    category: Optional[str] = 'discovered'
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
    metadata: Optional[Dict[str, Any]] = None


@router.get("/")
async def get_universe_stats():
    """Get coin universe statistics"""
    if universe_manager is None:
        raise HTTPException(status_code=500, detail="Universe manager not initialized")
    
    stats = await universe_manager.get_universe_stats()
    return stats


@router.get("/coins")
async def get_all_coins(category: Optional[str] = None, active_only: bool = True):
    """
    Get all coins in the universe.
    Optionally filter by category.
    """
    if universe_manager is None:
        raise HTTPException(status_code=500, detail="Universe manager not initialized")
    
    if category:
        coins = await universe_manager.get_coins_by_category(category)
    else:
        coin_ids = await universe_manager.get_all_coins()
        coins = [{'coin_id': c} for c in coin_ids]
    
    return {
        "coins": coins,
        "count": len(coins),
        "category": category
    }


@router.get("/training-coins")
async def get_training_coins():
    """Get all coins used for AI training (priority sorted)"""
    if universe_manager is None:
        raise HTTPException(status_code=500, detail="Universe manager not initialized")
    
    coins = await universe_manager.get_training_coins()
    return {
        "coins": coins,
        "count": len(coins)
    }


@router.get("/gem-candidates")
async def get_gem_candidates():
    """Get coins that could be hidden gems (high risk/reward)"""
    if universe_manager is None:
        raise HTTPException(status_code=500, detail="Universe manager not initialized")
    
    coins = await universe_manager.get_gem_candidates()
    return {
        "coins": coins,
        "count": len(coins)
    }


@router.get("/ai-discovered")
async def get_ai_discovered():
    """Get all coins discovered by AI"""
    if universe_manager is None:
        raise HTTPException(status_code=500, detail="Universe manager not initialized")
    
    coins = await universe_manager.get_ai_discovered_coins()
    return {
        "coins": coins,
        "count": len(coins)
    }


@router.get("/coin/{coin_id}")
async def get_coin(coin_id: str):
    """Get details for a specific coin"""
    if universe_manager is None:
        raise HTTPException(status_code=500, detail="Universe manager not initialized")
    
    coin = await universe_manager.get_coin(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")
    
    return coin


@router.post("/add")
async def add_coin(request: AddCoinRequest):
    """
    Manually add a new coin to the universe.
    """
    if universe_manager is None:
        raise HTTPException(status_code=500, detail="Universe manager not initialized")
    
    result = await universe_manager.add_coin(
        coin_id=request.coin_id,
        symbol=request.symbol,
        category=request.category,
        added_by='user',
        reason=request.reason
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))
    
    return result


@router.post("/ai-discover")
async def ai_discover_coin(request: AIDiscoverRequest):
    """
    AI discovers and adds a new coin to the universe.
    Called when AI identifies a promising coin during market scanning.
    """
    if universe_manager is None:
        raise HTTPException(status_code=500, detail="Universe manager not initialized")
    
    result = await universe_manager.ai_discover_coin(
        coin_id=request.coin_id,
        symbol=request.symbol,
        reason=request.reason,
        potential_score=request.potential_score,
        market_cap=request.market_cap,
        volume_24h=request.volume_24h
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))
    
    return result


@router.put("/coin/{coin_id}")
async def update_coin(coin_id: str, request: UpdateCoinRequest):
    """Update a coin's information"""
    if universe_manager is None:
        raise HTTPException(status_code=500, detail="Universe manager not initialized")
    
    updates = {}
    if request.category is not None:
        updates['category'] = request.category
    if request.active is not None:
        updates['active'] = request.active
    if request.metadata is not None:
        updates['metadata'] = request.metadata
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    result = await universe_manager.update_coin(coin_id, updates)
    
    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error'))
    
    return result


@router.delete("/coin/{coin_id}")
async def deactivate_coin(coin_id: str, reason: Optional[str] = None):
    """Deactivate a coin (soft delete)"""
    if universe_manager is None:
        raise HTTPException(status_code=500, detail="Universe manager not initialized")
    
    result = await universe_manager.deactivate_coin(coin_id, reason)
    
    if not result.get('success'):
        raise HTTPException(status_code=404, detail=result.get('error'))
    
    return result


@router.post("/initialize")
async def initialize_universe():
    """Initialize the coin universe from base coins"""
    if universe_manager is None:
        raise HTTPException(status_code=500, detail="Universe manager not initialized")
    
    result = await universe_manager.initialize()
    return result

"""
AI Universe Expansion API Routes
Endpoints for training AI and expanding the trading universe.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/ai-universe-expand", tags=["AI Universe Expansion"])

# Dependencies
_db = None
_market_service = None
_expander = None

def set_dependencies(db, market_service, expander):
    """Set dependencies from server.py"""
    global _db, _market_service, _expander
    _db = db
    _market_service = market_service
    _expander = expander


class ExpansionRequest(BaseModel):
    target_count: Optional[int] = 30


# Track background tasks
_expansion_status = {
    "running": False,
    "last_run": None,
    "result": None
}


async def run_expansion_task(target_count: int):
    """Background task to run universe expansion"""
    global _expansion_status
    _expansion_status["running"] = True
    _expansion_status["started_at"] = datetime.utcnow().isoformat()
    
    try:
        result = await _expander.expand_universe(target_count)
        _expansion_status["result"] = result
        _expansion_status["last_run"] = datetime.utcnow().isoformat()
    except Exception as e:
        _expansion_status["result"] = {"error": str(e)}
    finally:
        _expansion_status["running"] = False


@router.post("/expand")
async def expand_universe(request: ExpansionRequest, background_tasks: BackgroundTasks):
    """
    Expand the trading universe with AI-selected coins.
    
    This will:
    1. Fetch available coins from market data
    2. Analyze each coin's potential
    3. Use AI to select best candidates
    4. Add them to the trading universe
    5. Compare with existing recommendations
    
    Runs in background due to long processing time.
    """
    if not _expander:
        raise HTTPException(status_code=503, detail="Universe expander not initialized")
    
    if _expansion_status["running"]:
        return {
            "status": "already_running",
            "started_at": _expansion_status.get("started_at"),
            "message": "Expansion is already in progress. Check /status for updates."
        }
    
    # Start background task
    background_tasks.add_task(run_expansion_task, request.target_count)
    
    return {
        "status": "started",
        "target_count": request.target_count,
        "message": "Universe expansion started. Check /status endpoint for progress."
    }


@router.get("/status")
async def get_expansion_status():
    """Get the status of universe expansion"""
    return {
        "running": _expansion_status["running"],
        "last_run": _expansion_status.get("last_run"),
        "started_at": _expansion_status.get("started_at") if _expansion_status["running"] else None,
        "result": _expansion_status.get("result") if not _expansion_status["running"] else None
    }


@router.get("/last-result")
async def get_last_expansion_result():
    """Get the result of the last expansion"""
    if not _expansion_status.get("result"):
        return {"message": "No expansion has been run yet"}
    return _expansion_status["result"]


@router.get("/comparison")
async def get_weekly_comparison():
    """Get comparison of AI recommendations vs actual performance"""
    if not _expander:
        raise HTTPException(status_code=503, detail="Universe expander not initialized")
    
    result = await _expander.get_weekly_comparison()
    return result


@router.get("/current-universe")
async def get_current_universe():
    """Get all coins currently in the trading universe"""
    if not _db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    cursor = _db.coin_universe.find({"is_active": True})
    coins = await cursor.to_list(length=500)
    
    # Group by source
    by_source = {}
    for coin in coins:
        coin.pop('_id', None)
        source = coin.get('source', 'unknown')
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(coin)
    
    return {
        "total_coins": len(coins),
        "by_source": by_source,
        "sources": list(by_source.keys()),
        "coins": coins
    }


@router.get("/expansion-history")
async def get_expansion_history(limit: int = 10):
    """Get history of universe expansions"""
    if not _db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    cursor = _db.universe_expansions.find().sort("timestamp", -1).limit(limit)
    expansions = await cursor.to_list(length=limit)
    
    for exp in expansions:
        exp.pop('_id', None)
    
    return {
        "count": len(expansions),
        "expansions": expansions
    }


@router.post("/quick-analyze")
async def quick_analyze_coins(coin_ids: list):
    """Quickly analyze a list of coins for potential"""
    if not _expander:
        raise HTTPException(status_code=503, detail="Universe expander not initialized")
    
    if not coin_ids or len(coin_ids) > 10:
        raise HTTPException(status_code=400, detail="Provide 1-10 coin IDs")
    
    results = []
    for coin_id in coin_ids:
        analysis = await _expander.analyze_coin_potential({"id": coin_id})
        if analysis:
            results.append(analysis)
    
    return {
        "analyzed": len(results),
        "results": results
    }

"""
Gem Finder API Routes
Real-time hidden gem detection endpoints.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/gems", tags=["Gem Finder"])

# Global references
db = None
gem_finder = None


def set_dependencies(database, finder):
    """Set dependencies from main app"""
    global db, gem_finder
    db = database
    gem_finder = finder


class GemScanRequest(BaseModel):
    max_gems: Optional[int] = 3
    min_score: Optional[float] = 50.0


@router.post("/scan")
async def scan_for_gems(request: GemScanRequest):
    """
    Scan for hidden gems with 10-100x potential.
    Uses trained AI model to detect breakout candidates.
    """
    if gem_finder is None:
        raise HTTPException(status_code=500, detail="Gem finder not initialized")
    
    try:
        gems = await gem_finder.find_gems(
            week_start=datetime.now(),
            max_gems=request.max_gems
        )
        
        # Filter by minimum score
        filtered = [g for g in gems if g['total_score'] >= request.min_score]
        
        return {
            'success': True,
            'scan_time': datetime.now().isoformat(),
            'gems_found': len(filtered),
            'gems': filtered
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.get("/top-gems")
async def get_top_gems():
    """Get historically best performing gems based on learned scores"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    scores = await db.gem_finder_scores.find_one({}, {'_id': 0})
    
    if not scores:
        return {'gems': [], 'message': 'No gem data yet'}
    
    sorted_gems = sorted(
        scores.get('scores', {}).items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    return {
        'top_gems': [{'coin_id': k, 'score': v} for k, v in sorted_gems],
        'last_updated': scores.get('updated_at')
    }


@router.get("/backtest-results")
async def get_gem_backtest_results():
    """Get latest gem finder backtest results"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    result = await db.gem_backtest_results.find_one(
        {}, {'_id': 0, 'results': 0},
        sort=[('completed_at', -1)]
    )
    
    if not result:
        return {'message': 'No backtest results yet'}
    
    return result


@router.post("/backtest")
async def run_gem_backtest(background_tasks: BackgroundTasks):
    """Run gem finder backtest in background"""
    if gem_finder is None:
        raise HTTPException(status_code=500, detail="Gem finder not initialized")
    
    async def backtest():
        try:
            await gem_finder.backtest_gems(
                start_date=datetime(2021, 6, 1),
                end_date=datetime(2025, 12, 31)
            )
        except Exception as e:
            print(f"Backtest error: {e}")
    
    import asyncio
    background_tasks.add_task(lambda: asyncio.create_task(backtest()))
    
    return {
        'success': True,
        'message': 'Gem backtest started in background'
    }


@router.get("/alerts")
async def get_gem_alerts():
    """Get recent gem alerts"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    alerts = await db.gem_alerts.find(
        {}, {'_id': 0}
    ).sort('created_at', -1).limit(20).to_list(20)
    
    return {'alerts': alerts}


class WatchlistAddRequest(BaseModel):
    coin_id: str
    symbol: Optional[str] = None
    reason: Optional[str] = "Manual add"
    target_gain: Optional[float] = 100.0  # Target % gain
    entry_price: Optional[float] = None
    score: Optional[float] = None


@router.get("/watchlist")
async def get_gem_watchlist():
    """Get current gem watchlist"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    watchlist = await db.gem_watchlist.find(
        {"active": True}, {'_id': 0}
    ).sort('added_at', -1).to_list(100)
    
    return {
        'count': len(watchlist),
        'watchlist': watchlist
    }


@router.post("/watchlist/add")
async def add_to_gem_watchlist(request: WatchlistAddRequest):
    """Add a coin to the gem watchlist"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    # Check if already exists
    existing = await db.gem_watchlist.find_one({
        "coin_id": request.coin_id.lower(),
        "active": True
    })
    
    if existing:
        return {
            "status": "already_exists",
            "coin_id": request.coin_id,
            "message": f"{request.coin_id} is already on the watchlist"
        }
    
    watchlist_entry = {
        "coin_id": request.coin_id.lower(),
        "symbol": request.symbol or request.coin_id.upper(),
        "reason": request.reason,
        "target_gain": request.target_gain,
        "entry_price": request.entry_price,
        "score": request.score,
        "added_at": datetime.utcnow(),
        "active": True,
        "alerts_sent": 0,
        "peak_gain": 0.0,
        "status": "watching"
    }
    
    await db.gem_watchlist.insert_one(watchlist_entry)
    watchlist_entry.pop('_id', None)
    
    return {
        "status": "added",
        "coin": watchlist_entry
    }


@router.post("/watchlist/add-bulk")
async def add_bulk_to_watchlist(coins: List[WatchlistAddRequest]):
    """Add multiple coins to watchlist at once"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    added = []
    skipped = []
    
    for coin in coins:
        existing = await db.gem_watchlist.find_one({
            "coin_id": coin.coin_id.lower(),
            "active": True
        })
        
        if existing:
            skipped.append(coin.coin_id)
            continue
        
        entry = {
            "coin_id": coin.coin_id.lower(),
            "symbol": coin.symbol or coin.coin_id.upper(),
            "reason": coin.reason,
            "target_gain": coin.target_gain,
            "entry_price": coin.entry_price,
            "score": coin.score,
            "added_at": datetime.utcnow(),
            "active": True,
            "alerts_sent": 0,
            "peak_gain": 0.0,
            "status": "watching"
        }
        await db.gem_watchlist.insert_one(entry)
        added.append(coin.coin_id)
    
    return {
        "status": "completed",
        "added": added,
        "skipped": skipped,
        "total_added": len(added)
    }


@router.delete("/watchlist/{coin_id}")
async def remove_from_watchlist(coin_id: str):
    """Remove a coin from watchlist (soft delete)"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    result = await db.gem_watchlist.update_one(
        {"coin_id": coin_id.lower(), "active": True},
        {"$set": {"active": False, "removed_at": datetime.utcnow()}}
    )
    
    if result.modified_count > 0:
        return {"status": "removed", "coin_id": coin_id}
    
    return {"status": "not_found", "coin_id": coin_id}

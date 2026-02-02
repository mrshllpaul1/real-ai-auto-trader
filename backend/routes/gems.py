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
        raise HTTPException(status_code=500, detail=str(e))


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

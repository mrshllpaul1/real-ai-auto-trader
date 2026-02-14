"""
Growth Engine API Routes
Goal: $500 → $100,000
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/growth", tags=["Growth Engine"])

# Global references
db = None
growth_engine = None


def set_dependencies(database, engine):
    global db, growth_engine
    db = database
    growth_engine = engine


class GrowthExecuteRequest(BaseModel):
    capital: Optional[float] = 500
    paper_trade: Optional[bool] = True


@router.post("/execute")
async def execute_growth_strategy(request: GrowthExecuteRequest):
    """Execute aggressive growth strategy"""
    if growth_engine is None:
        raise HTTPException(status_code=500, detail="Growth engine not initialized")
    
    result = await growth_engine.execute_growth_strategy(
        capital=request.capital,
        paper_trade=request.paper_trade
    )
    return result


@router.get("/portfolio")
async def get_portfolio_value():
    """Get current portfolio value and progress toward $100k"""
    if growth_engine is None:
        raise HTTPException(status_code=500, detail="Growth engine not initialized")
    
    return await growth_engine.get_current_portfolio_value()


@router.get("/stats")
async def get_growth_stats():
    """Get comprehensive growth statistics"""
    if growth_engine is None:
        raise HTTPException(status_code=500, detail="Growth engine not initialized")
    
    return await growth_engine.get_growth_stats()


@router.post("/monitor")
async def monitor_positions():
    """Check all positions for SL/TP triggers"""
    if growth_engine is None:
        raise HTTPException(status_code=500, detail="Growth engine not initialized")
    
    return await growth_engine.monitor_positions()


@router.post("/compound")
async def compound_profits():
    """Compound realized profits"""
    if growth_engine is None:
        raise HTTPException(status_code=500, detail="Growth engine not initialized")
    
    return await growth_engine.compound_profits()


@router.get("/positions")
async def get_positions(status: str = "OPEN"):
    """Get growth positions"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    query = {'status': status} if status != 'ALL' else {}
    positions = await db.growth_positions.find(
        query, {'_id': 0}
    ).sort('opened_at', -1).to_list(100)
    
    return {'positions': positions, 'count': len(positions)}


@router.get("/history")
async def get_execution_history(limit: int = 10):
    """Get growth execution history"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    history = await db.growth_executions.find(
        {}, {'_id': 0}
    ).sort('timestamp', -1).limit(limit).to_list(limit)
    
    return {'history': history}


@router.get("/status")
async def get_growth_status():
    """Get growth engine status including autopilot state"""
    if growth_engine is None:
        # Return basic status when engine not initialized
        return {
            'autopilot_active': False,
            'current_value': 500.0,
            'initial_value': 500.0,
            'total_pnl': 0.0,
            'total_pnl_pct': 0.0,
            'target_value': 100000.0,
            'progress_pct': 0.5,
            'positions_count': 0,
            'engine_initialized': False
        }
    
    try:
        # Get portfolio value
        portfolio = await growth_engine.get_current_portfolio_value()
        stats = await growth_engine.get_growth_stats()
        
        current_value = portfolio.get('total_value', 500.0)
        initial_value = 500.0
        total_pnl = current_value - initial_value
        total_pnl_pct = ((current_value / initial_value) - 1) * 100 if initial_value > 0 else 0
        target_value = 100000.0
        progress_pct = (current_value / target_value) * 100
        
        return {
            'autopilot_active': getattr(growth_engine, 'autopilot_active', False),
            'current_value': current_value,
            'initial_value': initial_value,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'target_value': target_value,
            'progress_pct': progress_pct,
            'positions_count': stats.get('open_positions', 0),
            'trades_executed': stats.get('total_trades', 0),
            'engine_initialized': True
        }
    except Exception as e:
        return {
            'autopilot_active': False,
            'current_value': 500.0,
            'initial_value': 500.0,
            'total_pnl': 0.0,
            'total_pnl_pct': 0.0,
            'target_value': 100000.0,
            'progress_pct': 0.5,
            'positions_count': 0,
            'engine_initialized': False,
            'error': str(e)
        }


@router.post("/start")
async def start_autopilot():
    """Start the growth engine autopilot"""
    if growth_engine is None:
        raise HTTPException(status_code=500, detail="Growth engine not initialized")
    
    try:
        growth_engine.autopilot_active = True
        return {'success': True, 'message': 'Autopilot started', 'autopilot_active': True}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.post("/stop")
async def stop_autopilot():
    """Stop the growth engine autopilot"""
    if growth_engine is None:
        raise HTTPException(status_code=500, detail="Growth engine not initialized")
    
    try:
        growth_engine.autopilot_active = False
        return {'success': True, 'message': 'Autopilot stopped', 'autopilot_active': False}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

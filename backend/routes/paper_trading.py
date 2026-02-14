"""
Paper Trading API Routes
Run simulations using all stored market and sentiment data.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/paper-trading", tags=["Paper Trading"])

_db = None
_paper_trader = None
_simulation_status = {
    "running": False,
    "progress": 0,
    "message": "",
    "result": None
}


def set_dependencies(database, paper_trader):
    global _db, _paper_trader
    _db = database
    _paper_trader = paper_trader


class SimulationRequest(BaseModel):
    initial_balance: float = 500.0
    days_back: int = 30
    coins: Optional[List[str]] = None


async def _run_simulation_background(request: SimulationRequest):
    """Background task for running simulation"""
    global _simulation_status
    _simulation_status["running"] = True
    _simulation_status["progress"] = 0
    _simulation_status["message"] = "Starting simulation..."
    
    try:
        await _paper_trader.initialize(request.initial_balance)
        _simulation_status["progress"] = 10
        _simulation_status["message"] = "Initialized portfolio..."
        
        result = await _paper_trader.run_simulation(
            days_back=request.days_back,
            coins=request.coins
        )
        
        _simulation_status["result"] = result
        _simulation_status["progress"] = 100
        _simulation_status["message"] = "Simulation complete!"
        
    except Exception as e:
        _simulation_status["result"] = {"error": str(e)}
        _simulation_status["message"] = f"Simulation failed: {str(e)}"
    finally:
        _simulation_status["running"] = False


@router.post("/simulate")
async def run_paper_trading_simulation(
    request: SimulationRequest,
    background_tasks: BackgroundTasks
):
    """
    Run a paper trading simulation using all stored historical data.
    
    Uses:
    - Historical OHLCV data
    - News sentiment
    - Social sentiment
    - Fear & Greed Index
    - Technical indicators (RSI, MACD, BB, etc.)
    
    Args:
        initial_balance: Starting balance (default $500)
        days_back: Number of days to simulate (default 30)
        coins: List of coins to trade (default: top 15)
    """
    global _simulation_status
    
    if _paper_trader is None:
        raise HTTPException(status_code=503, detail="Paper trader not initialized")
    
    if _simulation_status["running"]:
        return {
            "status": "already_running",
            "progress": _simulation_status["progress"],
            "message": _simulation_status["message"]
        }
    
    _simulation_status = {
        "running": True,
        "progress": 0,
        "message": "Queued...",
        "result": None,
        "started_at": datetime.utcnow().isoformat()
    }
    
    background_tasks.add_task(_run_simulation_background, request)
    
    return {
        "status": "started",
        "message": f"Paper trading simulation started ({request.days_back} days, ${request.initial_balance})",
        "check_status": "/api/paper-trading/status"
    }


@router.get("/status")
async def get_simulation_status():
    """Get current simulation status and results"""
    return {
        **_simulation_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/results")
async def get_simulation_results(limit: int = Query(10, ge=1, le=50)):
    """Get historical simulation results"""
    if _paper_trader is None:
        raise HTTPException(status_code=503, detail="Paper trader not initialized")
    
    results = await _paper_trader.get_simulation_results(limit)
    
    return {
        "count": len(results),
        "results": results
    }


@router.get("/portfolio")
async def get_current_portfolio():
    """Get current paper trading portfolio state"""
    if _paper_trader is None:
        raise HTTPException(status_code=503, detail="Paper trader not initialized")
    
    positions_value = sum(
        p['quantity'] * p['entry_price'] for p in _paper_trader.positions.values()
    )
    
    return {
        "balance": round(_paper_trader.balance, 2),
        "positions": _paper_trader.positions,
        "positions_count": len(_paper_trader.positions),
        "positions_value": round(positions_value, 2),
        "total_value": round(_paper_trader.balance + positions_value, 2),
        "initial_balance": _paper_trader.initial_balance,
        "pnl": round(_paper_trader.balance + positions_value - _paper_trader.initial_balance, 2),
        "trades_executed": len(_paper_trader.trade_history)
    }


@router.get("/trades")
async def get_trade_history(limit: int = Query(50, ge=1, le=500)):
    """Get paper trading trade history"""
    if _paper_trader is None:
        raise HTTPException(status_code=503, detail="Paper trader not initialized")
    
    trades = _paper_trader.trade_history[-limit:]
    
    # Calculate stats
    winning = [t for t in trades if t.get('pnl', 0) > 0]
    losing = [t for t in trades if t.get('pnl', 0) < 0]
    
    return {
        "trades": trades,
        "count": len(trades),
        "stats": {
            "total_trades": len(trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": round(len(winning) / len(trades) * 100, 1) if trades else 0,
            "total_pnl": round(sum(t.get('pnl', 0) for t in trades), 2),
            "avg_pnl": round(sum(t.get('pnl', 0) for t in trades) / len(trades), 2) if trades else 0
        }
    }


@router.post("/reset")
async def reset_paper_trading(initial_balance: float = Query(500.0, ge=100, le=100000)):
    """Reset paper trading to initial state"""
    if _paper_trader is None:
        raise HTTPException(status_code=503, detail="Paper trader not initialized")
    
    result = await _paper_trader.initialize(initial_balance)
    
    return {
        "success": True,
        "message": f"Paper trading reset with ${initial_balance}",
        "balance": result["balance"]
    }


@router.get("/quick-test")
async def run_quick_test():
    """
    Run a quick 7-day paper trading test with default settings.
    Returns results immediately (synchronous).
    """
    if _paper_trader is None:
        raise HTTPException(status_code=503, detail="Paper trader not initialized")
    
    if _simulation_status.get("running"):
        raise HTTPException(status_code=409, detail="Simulation already running")
    
    try:
        await _paper_trader.initialize(500.0)
        result = await _paper_trader.run_simulation(days_back=7)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

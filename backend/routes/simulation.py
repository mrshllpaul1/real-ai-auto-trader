"""
Historical Trading Simulation API Routes
Run and monitor the 2009-2026 AI trading simulation.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/simulation", tags=["Historical Simulation"])

# Dependencies
_db = None
_market_service = None

def set_dependencies(db, market_service):
    """Set dependencies from server.py"""
    global _db, _market_service
    _db = db
    _market_service = market_service


class SimulationRequest(BaseModel):
    speed: Optional[str] = "monthly"  # daily, weekly, monthly
    starting_capital: Optional[float] = 500.0
    target_capital: Optional[float] = 100000.0


@router.post("/run")
async def run_historical_simulation(request: SimulationRequest, background_tasks: BackgroundTasks):
    """
    Run the historical AI trading simulation from 2009-2026.
    
    The AI will:
    1. Start with $500 (or custom amount)
    2. Build a coin universe from scratch as coins launch
    3. Develop a portfolio of 10 coins + hidden gems
    4. Try to reach $100,000+ using deep learning predictions
    
    This runs in the background due to the computation involved.
    """
    from services.historical_simulator import run_simulation_task, get_simulation_status
    
    status = get_simulation_status()
    if status["running"]:
        return {
            "status": "already_running",
            "started_at": status.get("started_at"),
            "progress": status.get("progress", 0)
        }
    
    # Start background simulation
    background_tasks.add_task(run_simulation_task, _db, _market_service)
    
    return {
        "status": "started",
        "message": "Historical simulation started (2009-2026)",
        "parameters": {
            "speed": request.speed,
            "starting_capital": request.starting_capital,
            "target_capital": request.target_capital
        }
    }


@router.get("/status")
async def get_simulation_status_endpoint():
    """Get the current status of the simulation"""
    from services.historical_simulator import get_simulation_status
    return get_simulation_status()


@router.get("/result")
async def get_simulation_result():
    """Get the result of the completed simulation"""
    from services.historical_simulator import get_simulation_status
    
    status = get_simulation_status()
    if status["running"]:
        return {"status": "still_running", "progress": status.get("progress", 0)}
    
    if not status.get("result"):
        return {"status": "no_simulation_run"}
    
    return status["result"]


@router.get("/summary")
async def get_simulation_summary():
    """Get a text summary of the simulation results"""
    from services.historical_simulator import get_simulator
    
    simulator = get_simulator()
    if not simulator:
        return {"summary": "No simulation has been run yet"}
    
    return {"summary": simulator.get_simulation_summary()}


@router.get("/trades")
async def get_simulation_trades(limit: int = 50):
    """Get the trades made during the simulation"""
    from services.historical_simulator import get_simulator
    
    simulator = get_simulator()
    if not simulator:
        return {"trades": [], "message": "No simulation has been run"}
    
    trades = simulator.trades[-limit:] if simulator.trades else []
    
    return {
        "total_trades": len(simulator.trades),
        "showing": len(trades),
        "trades": trades
    }


@router.get("/portfolio")
async def get_simulation_portfolio():
    """Get the current/final portfolio from the simulation"""
    from services.historical_simulator import get_simulator
    
    simulator = get_simulator()
    if not simulator:
        return {"portfolio": None, "message": "No simulation has been run"}
    
    holdings = [
        {
            "coin_id": k,
            "quantity": v["quantity"],
            "avg_price": v["avg_price"]
        }
        for k, v in simulator.portfolio["holdings"].items()
        if v["quantity"] > 0
    ]
    
    return {
        "cash": simulator.portfolio["cash"],
        "total_value": simulator.portfolio["total_value"],
        "holdings": holdings
    }


@router.get("/hidden-gems")
async def get_simulation_hidden_gems():
    """Get the hidden gems discovered during the simulation"""
    from services.historical_simulator import get_simulator
    
    simulator = get_simulator()
    if not simulator:
        return {"hidden_gems": [], "message": "No simulation has been run"}
    
    return {
        "count": len(simulator.hidden_gems),
        "hidden_gems": simulator.hidden_gems
    }


@router.get("/monthly-snapshots")
async def get_monthly_snapshots():
    """Get monthly portfolio snapshots from the simulation"""
    from services.historical_simulator import get_simulator
    
    simulator = get_simulator()
    if not simulator:
        return {"snapshots": [], "message": "No simulation has been run"}
    
    return {
        "count": len(simulator.monthly_snapshots),
        "snapshots": simulator.monthly_snapshots
    }


@router.get("/history")
async def get_simulation_history(limit: int = 10):
    """Get history of past simulations from database"""
    if _db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    cursor = _db.backtest_simulations.find().sort("completed_at", -1).limit(limit)
    simulations = await cursor.to_list(length=limit)
    
    for sim in simulations:
        sim.pop('_id', None)
    
    return {
        "count": len(simulations),
        "simulations": simulations
    }

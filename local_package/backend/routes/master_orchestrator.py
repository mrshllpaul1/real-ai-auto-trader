"""
Master Trading Orchestrator API Routes
=======================================
Control center for the automated trading system.
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/master", tags=["Master Orchestrator"])

_db = None


def set_db(db):
    global _db
    _db = db


class SetModeRequest(BaseModel):
    mode: str  # manual, hybrid, full_auto


class RiskLimitsRequest(BaseModel):
    max_position_pct: Optional[float] = None
    max_daily_loss_pct: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    min_confidence: Optional[float] = None
    small_trade_threshold: Optional[float] = None


@router.get("/status")
async def get_master_status():
    """Get master orchestrator status"""
    from services.master_orchestrator import get_master_orchestrator
    
    orchestrator = get_master_orchestrator(_db)
    status = orchestrator.get_status()
    
    # Check persisted state
    try:
        from services.state_persistence import get_state_persistence
        persistence = get_state_persistence(_db)
        if persistence:
            state = await persistence.get_state("master_orchestrator")
            status["persisted_running"] = state.get("is_running", False) if state else False
    except Exception as e:
        status["persisted_running"] = None
    
    return status


@router.post("/start")
async def start_orchestrator(background_tasks: BackgroundTasks):
    """Start the master orchestrator"""
    from services.master_orchestrator import get_master_orchestrator
    
    orchestrator = get_master_orchestrator(_db)
    
    if orchestrator.is_active:
        return {"status": "already_running", "current": orchestrator.get_status()}
    
    background_tasks.add_task(orchestrator.start)
    
    # Persist state
    try:
        from services.state_persistence import get_state_persistence
        persistence = get_state_persistence(_db)
        if persistence:
            await persistence.set_state("master_orchestrator", True, metadata={"mode": orchestrator.mode.value})
    except Exception as e:
        pass
    
    return {
        "status": "started",
        "mode": orchestrator.mode.value,
        "message": "Master orchestrator started in background"
    }


@router.post("/stop")
async def stop_orchestrator():
    """Stop the master orchestrator"""
    from services.master_orchestrator import get_master_orchestrator
    
    orchestrator = get_master_orchestrator(_db)
    orchestrator.stop()
    
    # Persist state
    try:
        from services.state_persistence import get_state_persistence
        persistence = get_state_persistence(_db)
        if persistence:
            await persistence.set_state("master_orchestrator", False)
    except Exception as e:
        pass
    
    return {"status": "stopped"}


@router.post("/set-mode")
async def set_trading_mode(request: SetModeRequest):
    """Set trading mode (manual, hybrid, full_auto)"""
    from services.master_orchestrator import get_master_orchestrator
    
    orchestrator = get_master_orchestrator(_db)
    orchestrator.set_mode(request.mode)
    
    return {
        "status": "mode_set",
        "mode": orchestrator.mode.value
    }


@router.post("/set-limits")
async def set_risk_limits(request: RiskLimitsRequest):
    """Update risk management limits"""
    from services.master_orchestrator import get_master_orchestrator
    
    orchestrator = get_master_orchestrator(_db)
    rm = orchestrator.risk_manager
    
    if request.max_position_pct is not None:
        rm.max_position_pct = request.max_position_pct
    if request.max_daily_loss_pct is not None:
        rm.max_daily_loss_pct = request.max_daily_loss_pct
    if request.max_drawdown_pct is not None:
        rm.max_drawdown_pct = request.max_drawdown_pct
    if request.min_confidence is not None:
        rm.min_confidence = request.min_confidence
    if request.small_trade_threshold is not None:
        orchestrator.small_trade_threshold = request.small_trade_threshold
    
    return {
        "status": "limits_updated",
        "risk_status": rm.get_status(),
        "small_trade_threshold": orchestrator.small_trade_threshold
    }


@router.get("/pending")
async def get_pending_confirmations():
    """Get signals waiting for confirmation"""
    from services.master_orchestrator import get_master_orchestrator
    
    orchestrator = get_master_orchestrator(_db)
    return {
        "pending": orchestrator.get_pending_confirmations(),
        "count": len(orchestrator.get_pending_confirmations())
    }


@router.post("/confirm/{signal_id}")
async def confirm_signal(signal_id: str):
    """Confirm and execute a pending signal"""
    from services.master_orchestrator import get_master_orchestrator
    
    orchestrator = get_master_orchestrator(_db)
    result = await orchestrator.confirm_signal(signal_id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.post("/reject/{signal_id}")
async def reject_signal(signal_id: str):
    """Reject a pending signal"""
    from services.master_orchestrator import get_master_orchestrator
    
    orchestrator = get_master_orchestrator(_db)
    result = await orchestrator.reject_signal(signal_id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/history")
async def get_trade_history(limit: int = 50):
    """Get recent trade history"""
    from services.master_orchestrator import get_master_orchestrator
    
    orchestrator = get_master_orchestrator(_db)
    
    executed = list(orchestrator.executed_signals)[-limit:]
    rejected = list(orchestrator.rejected_signals)[-limit:]
    
    return {
        "executed": executed,
        "rejected": rejected,
        "stats": orchestrator.stats
    }


@router.get("/risk")
async def get_risk_status():
    """Get current risk management status"""
    from services.master_orchestrator import get_master_orchestrator
    
    orchestrator = get_master_orchestrator(_db)
    return orchestrator.risk_manager.get_status()


@router.post("/reset-daily")
async def reset_daily_limits():
    """Reset daily risk counters"""
    from services.master_orchestrator import get_master_orchestrator
    
    orchestrator = get_master_orchestrator(_db)
    orchestrator.risk_manager.reset_daily()
    
    return {"status": "reset", "risk_status": orchestrator.risk_manager.get_status()}


@router.get("/dashboard")
async def get_dashboard_data():
    """Get comprehensive dashboard data"""
    from services.master_orchestrator import get_master_orchestrator
    from services.realtime_news_monitor import get_news_monitor
    from services.specialist_agents import get_specialist_ensemble
    
    orchestrator = get_master_orchestrator(_db)
    news_monitor = get_news_monitor(_db)
    ensemble = get_specialist_ensemble(_db)
    
    return {
        "orchestrator": orchestrator.get_status(),
        "news": {
            "is_running": news_monitor.is_running,
            "trending": news_monitor.detector.get_trending_summary(),
            "stats": news_monitor.stats
        },
        "specialists": {
            "regime": ensemble.regime_detector.get_regime_summary(),
            "agents": list(ensemble.agents.keys())
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

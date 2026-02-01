from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter()

# Global instances
_auto_executor = None
_ai_engine = None
_notification_service = None

class RiskProfileUpdate(BaseModel):
    enabled: Optional[bool] = None
    mode: Optional[str] = None  # 'paper' or 'live'
    min_score: Optional[int] = None
    min_alert_level: Optional[str] = None
    max_position_size_usd: Optional[float] = None
    max_daily_trades: Optional[int] = None
    max_open_positions: Optional[int] = None
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    allowed_signals: Optional[List[str]] = None
    blacklisted_coins: Optional[List[str]] = None
    preferred_coins: Optional[List[str]] = None

class ClosePositionRequest(BaseModel):
    trade_id: str
    exit_price: float
    reason: str = 'manual'

async def get_auto_executor():
    global _auto_executor, _ai_engine
    from server import db
    from services.gem_scanner import GemScanner
    from services.self_improving_ai import SelfImprovingAI
    from services.auto_execution import AutoExecutionEngine
    
    if _ai_engine is None:
        _ai_engine = SelfImprovingAI(db)
        await _ai_engine.initialize()
    
    if _auto_executor is None:
        scanner = GemScanner(db)
        _auto_executor = AutoExecutionEngine(db, scanner, _ai_engine)
        await _auto_executor.load_risk_profile()
    
    return _auto_executor

async def get_ai_engine():
    global _ai_engine
    from server import db
    from services.self_improving_ai import SelfImprovingAI
    
    if _ai_engine is None:
        _ai_engine = SelfImprovingAI(db)
        await _ai_engine.initialize()
    
    return _ai_engine

# ============= AUTO EXECUTION ENDPOINTS =============

@router.post("/start")
async def start_auto_execution(
    background_tasks: BackgroundTasks,
    interval: int = 60,
    executor = Depends(get_auto_executor)
):
    """
    Start automatic trade execution
    Monitors for HIGH priority gems and executes trades matching risk profile
    """
    try:
        if executor.is_running:
            return {"message": "Auto-execution already running", "status": "running"}
        
        background_tasks.add_task(executor.start_auto_execution, interval)
        
        return {
            "message": "Auto-execution started",
            "mode": executor.risk_profile.get('mode', 'paper'),
            "interval_seconds": interval,
            "risk_profile": executor.risk_profile
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_auto_execution(executor = Depends(get_auto_executor)):
    """Stop auto-execution"""
    try:
        executor.stop_auto_execution()
        return {"message": "Auto-execution stopped", "status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_execution_status(executor = Depends(get_auto_executor)):
    """Get current auto-execution status including open positions and stats"""
    try:
        return await executor.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute-now")
async def execute_now(executor = Depends(get_auto_executor)):
    """Perform immediate scan and execute trades"""
    try:
        result = await executor.scan_and_execute()
        return {
            "message": "Scan and execution complete",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= RISK PROFILE ENDPOINTS =============

@router.get("/risk-profile")
async def get_risk_profile(
    user_id: str = 'default',
    executor = Depends(get_auto_executor)
):
    """Get current risk profile"""
    try:
        await executor.load_risk_profile(user_id)
        return executor.risk_profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/risk-profile")
async def update_risk_profile(
    updates: RiskProfileUpdate,
    user_id: str = 'default',
    executor = Depends(get_auto_executor)
):
    """Update risk profile settings"""
    try:
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        result = await executor.update_risk_profile(user_id, update_dict)
        return {
            "message": "Risk profile updated",
            "risk_profile": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enable")
async def enable_auto_execution(
    mode: str = 'paper',
    user_id: str = 'default',
    executor = Depends(get_auto_executor)
):
    """Enable auto-execution with specified mode"""
    try:
        await executor.update_risk_profile(user_id, {'enabled': True, 'mode': mode})
        return {
            "message": f"Auto-execution enabled in {mode.upper()} mode",
            "enabled": True,
            "mode": mode
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/disable")
async def disable_auto_execution(
    user_id: str = 'default',
    executor = Depends(get_auto_executor)
):
    """Disable auto-execution"""
    try:
        await executor.update_risk_profile(user_id, {'enabled': False})
        return {"message": "Auto-execution disabled", "enabled": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= POSITIONS ENDPOINTS =============

@router.get("/positions")
async def get_positions(
    status: Optional[str] = None,
    executor = Depends(get_auto_executor)
):
    """Get positions (OPEN, CLOSED, or all)"""
    try:
        positions = await executor.get_positions(status)
        return {
            "count": len(positions),
            "filter": status,
            "positions": positions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/positions/open")
async def get_open_positions(executor = Depends(get_auto_executor)):
    """Get all open positions"""
    try:
        positions = await executor.get_positions('OPEN')
        return {
            "count": len(positions),
            "positions": positions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/positions/close")
async def close_position(
    request: ClosePositionRequest,
    executor = Depends(get_auto_executor)
):
    """Manually close a position"""
    try:
        result = await executor.close_position(
            request.trade_id,
            request.exit_price,
            request.reason
        )
        if not result:
            raise HTTPException(status_code=404, detail="Position not found")
        return {
            "message": "Position closed",
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= AI LEARNING ENDPOINTS =============

@router.get("/ai/status")
async def get_ai_status(ai = Depends(get_ai_engine)):
    """Get AI learning status"""
    try:
        return await ai.get_learning_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai/weights")
async def get_signal_weights(ai = Depends(get_ai_engine)):
    """Get current learned signal weights"""
    try:
        return {
            "signal_weights": ai.signal_weights,
            "description": "Weights > 1.0 mean signal is performing better than average"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai/performance")
async def get_ai_performance(ai = Depends(get_ai_engine)):
    """Get detailed AI performance analysis"""
    try:
        return await ai.analyze_performance()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/optimize")
async def optimize_strategy(ai = Depends(get_ai_engine)):
    """Trigger manual strategy optimization"""
    try:
        result = await ai.optimize_strategy()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai/insights")
async def get_ai_insights(ai = Depends(get_ai_engine)):
    """Get AI-generated trading insights"""
    try:
        return await ai.generate_ai_insights()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/start-learning")
async def start_continuous_learning(
    background_tasks: BackgroundTasks,
    ai = Depends(get_ai_engine)
):
    """Start continuous AI learning loop"""
    try:
        if ai.is_running:
            return {"message": "AI learning already running", "status": "running"}
        
        background_tasks.add_task(ai.continuous_learning_loop)
        
        return {
            "message": "AI continuous learning started",
            "status": "running",
            "learning_interval_seconds": ai.learning_interval
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai/stop-learning")
async def stop_continuous_learning(ai = Depends(get_ai_engine)):
    """Stop continuous AI learning"""
    try:
        ai.stop_learning()
        return {"message": "AI learning stopped", "status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

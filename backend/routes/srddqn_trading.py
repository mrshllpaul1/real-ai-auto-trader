"""
SRDDQN Trading Integration API Routes
Connects trained agent to live trading with continuous backtesting
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/srddqn-trading", tags=["SRDDQN Live Trading"])

_db = None
_integration = None
_backtest_scheduler = None


def set_dependencies(db, integration=None):
    global _db, _integration
    _db = db
    _integration = integration


def get_integration():
    global _integration
    if _integration is None:
        from services.srddqn_trading_integration import get_srddqn_integration
        _integration = get_srddqn_integration(_db)
    return _integration


class SignalRequest(BaseModel):
    symbol: str = "BTC"


class ExecuteRequest(BaseModel):
    symbol: str = "BTC"
    auto_execute: bool = False


class BacktestConfig(BaseModel):
    interval_hours: int = 6
    min_sharpe_threshold: float = 0.5


@router.get("/status")
async def get_integration_status():
    """Get SRDDQN trading integration status"""
    try:
        integration = get_integration()
        if integration is None:
            return {"initialized": False}
        return integration.get_status()
    except Exception as e:
        return {"error": str(e)}


@router.post("/initialize")
async def initialize_integration():
    """Initialize SRDDQN trading integration"""
    try:
        from services.srddqn_trading_integration import initialize_srddqn_integration
        
        global _integration
        _integration = await initialize_srddqn_integration(_db)
        
        return {
            "status": "initialized",
            "is_active": _integration.is_active,
            "features": [
                "Real-time signal generation from trained SRDDQN",
                "Safety guard enforcement",
                "Continuous backtesting validation",
                "Social sentiment integration",
                "Performance tracking"
            ]
        }
    except Exception as e:
        logger.error(f"Integration init error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signal")
async def get_trading_signal(request: SignalRequest):
    """Get trading signal from SRDDQN agent"""
    try:
        integration = get_integration()
        if integration is None:
            raise HTTPException(status_code=400, detail="Integration not initialized")
        
        signal = await integration.generate_trading_signal(request.symbol)
        return signal
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signal generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_trading_signal(request: ExecuteRequest):
    """Execute trading signal"""
    try:
        integration = get_integration()
        if integration is None:
            raise HTTPException(status_code=400, detail="Integration not initialized")
        
        # Generate signal
        signal = await integration.generate_trading_signal(request.symbol)
        
        # Execute if requested
        if request.auto_execute:
            result = await integration.execute_signal(signal)
            return {
                "signal": signal,
                "execution": result
            }
        
        return {
            "signal": signal,
            "execution": {"executed": False, "reason": "Auto-execute disabled"}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest")
async def run_backtest():
    """Run continuous backtest"""
    try:
        integration = get_integration()
        if integration is None:
            raise HTTPException(status_code=400, detail="Integration not initialized")
        
        result = await integration.run_continuous_backtest()
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/start-scheduler")
async def start_backtest_scheduler(config: BacktestConfig = None, background_tasks: BackgroundTasks = None):
    """Start continuous backtesting scheduler"""
    try:
        integration = get_integration()
        if integration is None:
            raise HTTPException(status_code=400, detail="Integration not initialized")
        
        config = config or BacktestConfig()
        
        from services.srddqn_trading_integration import ContinuousBacktestScheduler
        
        global _backtest_scheduler
        _backtest_scheduler = ContinuousBacktestScheduler(
            integration, 
            interval_hours=config.interval_hours
        )
        
        integration.min_sharpe_threshold = config.min_sharpe_threshold
        
        if background_tasks:
            background_tasks.add_task(_backtest_scheduler.start)
        
        return {
            "status": "scheduler_started",
            "interval_hours": config.interval_hours,
            "min_sharpe_threshold": config.min_sharpe_threshold
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest/stop-scheduler")
async def stop_backtest_scheduler():
    """Stop continuous backtesting scheduler"""
    global _backtest_scheduler
    
    if _backtest_scheduler:
        await _backtest_scheduler.stop()
        return {"status": "scheduler_stopped"}
    
    return {"status": "no_scheduler_running"}


@router.get("/backtest/history")
async def get_backtest_history(limit: int = 20):
    """Get backtest history"""
    try:
        cursor = _db.srddqn_backtests.find().sort("timestamp", -1).limit(limit)
        results = await cursor.to_list(length=limit)
        
        # Clean ObjectIds
        for r in results:
            r['_id'] = str(r['_id'])
        
        return {"backtests": results, "count": len(results)}
        
    except Exception as e:
        return {"error": str(e)}


@router.get("/signals/history")
async def get_signal_history(limit: int = 50):
    """Get signal history"""
    try:
        integration = get_integration()
        if integration is None:
            return {"signals": [], "message": "Integration not initialized"}
        
        signals = list(integration.signal_history)[-limit:]
        return {"signals": signals, "count": len(signals)}
        
    except Exception as e:
        return {"error": str(e)}


@router.get("/trades/history")
async def get_trade_history(limit: int = 50):
    """Get trade history"""
    try:
        cursor = _db.srddqn_trades.find().sort("timestamp", -1).limit(limit)
        trades = await cursor.to_list(length=limit)
        
        for t in trades:
            t['_id'] = str(t['_id'])
        
        return {"trades": trades, "count": len(trades)}
        
    except Exception as e:
        return {"error": str(e)}


@router.post("/sentiment/configure")
async def configure_sentiment(weight: float = 0.2, threshold: float = 0.3):
    """Configure sentiment integration"""
    try:
        integration = get_integration()
        if integration is None:
            raise HTTPException(status_code=400, detail="Integration not initialized")
        
        integration.sentiment_weight = weight
        integration.sentiment_threshold = threshold
        
        return {
            "status": "configured",
            "sentiment_weight": weight,
            "sentiment_threshold": threshold
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance_metrics():
    """Get trading performance metrics"""
    try:
        integration = get_integration()
        if integration is None:
            return {"error": "Integration not initialized"}
        
        # Get recent backtests
        cursor = _db.srddqn_backtests.find().sort("timestamp", -1).limit(10)
        backtests = await cursor.to_list(length=10)
        
        # Get recent trades
        cursor = _db.srddqn_trades.find().sort("timestamp", -1).limit(100)
        trades = await cursor.to_list(length=100)
        
        # Calculate metrics
        if backtests:
            avg_sharpe = sum(b.get('sharpe_ratio', 0) for b in backtests) / len(backtests)
            avg_return = sum(b.get('total_return', 0) for b in backtests) / len(backtests)
            avg_drawdown = sum(b.get('max_drawdown', 0) for b in backtests) / len(backtests)
        else:
            avg_sharpe = avg_return = avg_drawdown = 0
        
        buy_trades = sum(1 for t in trades if t.get('side') == 'buy')
        sell_trades = sum(1 for t in trades if t.get('side') == 'sell')
        
        return {
            "total_trades": len(trades),
            "buy_trades": buy_trades,
            "sell_trades": sell_trades,
            "avg_sharpe_ratio": float(avg_sharpe),
            "avg_return": float(avg_return),
            "avg_max_drawdown": float(avg_drawdown),
            "backtest_count": len(backtests),
            "integration_status": integration.get_status()
        }
        
    except Exception as e:
        return {"error": str(e)}


@router.get("/health")
async def health_check():
    """Check integration health"""
    try:
        integration = get_integration()
        
        health = {
            "integration_initialized": integration is not None,
            "integration_active": integration.is_active if integration else False,
            "pipeline_ready": False,
            "backtest_scheduler_running": _backtest_scheduler.is_running if _backtest_scheduler else False
        }
        
        if integration and integration.pipeline:
            health["pipeline_ready"] = integration.pipeline.current_phase >= 2
            health["pipeline_phase"] = integration.pipeline.current_phase
        
        # Check last backtest
        if integration and integration.backtest_results:
            last_bt = list(integration.backtest_results)[-1]
            health["last_backtest_passed"] = last_bt.get("passed", False)
            health["last_backtest_sharpe"] = last_bt.get("sharpe_ratio", 0)
        
        health["healthy"] = (
            health["integration_active"] and 
            health["pipeline_ready"]
        )
        
        return health
        
    except Exception as e:
        return {"healthy": False, "error": str(e)}

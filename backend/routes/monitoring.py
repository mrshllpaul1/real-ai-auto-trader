"""
Trading Monitoring API
======================
Real-time monitoring endpoints for trading dashboard.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitoring", tags=["Trading Monitoring"])

# Database dependency
async def get_database():
    from motor.motor_asyncio import AsyncIOMotorClient
    import os
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
    return client[os.environ.get('DB_NAME', 'tethys_trading')]


@router.get("/dashboard")
async def get_dashboard_metrics(db = Depends(get_database)) -> Dict[str, Any]:
    """Get all dashboard metrics in one call"""
    
    # Get portfolio value
    portfolio = await db.portfolio_snapshots.find_one(
        sort=[("timestamp", -1)]
    )
    portfolio_value = portfolio.get("total_value", 0) if portfolio else 0
    
    # Get today's trades
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    trades_today = await db.trades.count_documents({
        "timestamp": {"$gte": today_start}
    })
    
    # Get winning trades today
    winning_today = await db.trades.count_documents({
        "timestamp": {"$gte": today_start},
        "pnl": {"$gt": 0}
    })
    
    # Calculate daily PnL
    pipeline = [
        {"$match": {"timestamp": {"$gte": today_start}}},
        {"$group": {"_id": None, "total_pnl": {"$sum": "$pnl"}}}
    ]
    daily_pnl_result = await db.trades.aggregate(pipeline).to_list(1)
    daily_pnl = daily_pnl_result[0]["total_pnl"] if daily_pnl_result else 0
    
    # Get circuit breaker status
    from services.circuit_breaker import get_circuit_breaker
    circuit_breaker = get_circuit_breaker()
    cb_status = circuit_breaker.get_status()
    
    return {
        "portfolio": {
            "value": portfolio_value,
            "daily_pnl": daily_pnl,
            "daily_pnl_percent": (daily_pnl / portfolio_value * 100) if portfolio_value > 0 else 0
        },
        "trading": {
            "trades_today": trades_today,
            "winning_today": winning_today,
            "win_rate_today": (winning_today / trades_today * 100) if trades_today > 0 else 0
        },
        "circuit_breaker": cb_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/performance")
async def get_performance_metrics(
    days: int = 30,
    db = Depends(get_database)
) -> Dict[str, Any]:
    """Get performance metrics over specified period"""
    
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Get trades in period
    trades = await db.trades.find({
        "timestamp": {"$gte": start_date}
    }).to_list(1000)
    
    if not trades:
        return {
            "period_days": days,
            "total_trades": 0,
            "message": "No trades in period"
        }
    
    # Calculate metrics
    total_pnl = sum(t.get("pnl", 0) for t in trades)
    winning = [t for t in trades if t.get("pnl", 0) > 0]
    losing = [t for t in trades if t.get("pnl", 0) <= 0]
    
    gross_profit = sum(t.get("pnl", 0) for t in winning)
    gross_loss = abs(sum(t.get("pnl", 0) for t in losing))
    
    return {
        "period_days": days,
        "total_trades": len(trades),
        "winning_trades": len(winning),
        "losing_trades": len(losing),
        "win_rate": len(winning) / len(trades) if trades else 0,
        "total_pnl": total_pnl,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "profit_factor": gross_profit / gross_loss if gross_loss > 0 else 0,
        "avg_win": gross_profit / len(winning) if winning else 0,
        "avg_loss": gross_loss / len(losing) if losing else 0
    }


@router.get("/risk")
async def get_risk_metrics(db = Depends(get_database)) -> Dict[str, Any]:
    """Get current risk metrics"""
    
    from services.circuit_breaker import get_circuit_breaker
    from config.risk_config import DEFAULT_RISK_CONFIG
    
    cb = get_circuit_breaker()
    config = DEFAULT_RISK_CONFIG
    
    # Get portfolio history for drawdown
    snapshots = await db.portfolio_snapshots.find(
        sort=[("timestamp", -1)]
    ).to_list(100)
    
    if snapshots:
        values = [s.get("total_value", 0) for s in snapshots]
        peak = max(values) if values else 0
        current = values[0] if values else 0
        drawdown = ((peak - current) / peak * 100) if peak > 0 else 0
    else:
        drawdown = 0
        peak = current = 0
    
    return {
        "drawdown": {
            "current_percent": drawdown,
            "max_allowed_percent": config.max_portfolio_drawdown_percent,
            "peak_value": peak,
            "current_value": current
        },
        "limits": {
            "max_position_size": config.max_position_size_usd,
            "max_daily_loss": config.max_daily_loss_percent,
            "max_trades_per_day": config.max_trades_per_day,
            "min_confidence": config.min_confidence_threshold
        },
        "circuit_breaker": cb.get_status()
    }


@router.post("/kill-switch/activate")
async def activate_kill_switch(reason: str = "Manual activation"):
    """Activate the kill switch - EMERGENCY STOP ALL TRADING"""
    from services.circuit_breaker import get_circuit_breaker
    
    cb = get_circuit_breaker()
    result = cb.activate_kill_switch(reason)
    
    logger.critical(f"🚨 KILL SWITCH ACTIVATED: {reason}")
    
    return result


@router.post("/kill-switch/deactivate")
async def deactivate_kill_switch():
    """Deactivate the kill switch"""
    from services.circuit_breaker import get_circuit_breaker
    
    cb = get_circuit_breaker()
    result = cb.deactivate_kill_switch()
    
    logger.info("✅ Kill switch deactivated")
    
    return result


@router.get("/kill-switch/status")
async def get_kill_switch_status():
    """Get kill switch status"""
    from services.circuit_breaker import get_circuit_breaker
    
    cb = get_circuit_breaker()
    return {
        "active": cb.is_kill_switch_active(),
        "status": cb.get_status()
    }


@router.post("/circuit-breaker/reset")
async def reset_circuit_breaker():
    """Reset the circuit breaker"""
    from services.circuit_breaker import get_circuit_breaker
    
    cb = get_circuit_breaker()
    return cb.reset()


@router.get("/position-size")
async def calculate_position_size(
    portfolio_value: float,
    confidence: float,
    win_rate: float = 0.55,
    volatility: float = 0.02
):
    """Calculate recommended position size"""
    from services.position_sizing import get_position_sizing_service
    
    ps = get_position_sizing_service()
    result = ps.calculate_position_size(
        portfolio_value=portfolio_value,
        signal_confidence=confidence,
        win_rate=win_rate,
        volatility=volatility
    )
    
    return {
        "recommended_size_usd": result.recommended_size_usd,
        "position_percent": result.position_percent,
        "kelly_fraction": result.kelly_fraction,
        "max_allowed": result.max_allowed,
        "reasoning": result.reasoning
    }


@router.get("/stop-loss")
async def calculate_stop_loss(
    entry_price: float,
    volatility: float = 0.02,
    risk_percent: float = 2.0
):
    """Calculate stop loss levels"""
    from services.position_sizing import get_position_sizing_service
    
    ps = get_position_sizing_service()
    stop_loss = ps.calculate_stop_loss(entry_price, volatility, risk_percent)
    take_profit = ps.calculate_take_profit(entry_price, stop_loss["stop_price"])
    
    return {
        "stop_loss": stop_loss,
        "take_profit": take_profit
    }

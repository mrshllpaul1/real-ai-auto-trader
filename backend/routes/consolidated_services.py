"""
Consolidated Services API Routes
================================
Provides unified API access to all consolidated services.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/services", tags=["Consolidated Services"])

# Global registry
_registry = None


def set_registry(registry):
    """Set the service registry"""
    global _registry
    _registry = registry


@router.get("/status")
async def get_all_services_status():
    """Get status of all consolidated services"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    return {
        "services": _registry.get_all_status(),
        "consolidation": {
            "original_services": 141,
            "consolidated_services": 10,
            "reduction": "93%"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/exchange/portfolio")
async def get_portfolio():
    """Get current portfolio from exchange service"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    return await _registry.exchange.get_portfolio()


@router.get("/exchange/balance")
async def get_balance():
    """Get account balances"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    return await _registry.exchange.get_balance()


@router.get("/ai/prediction/{symbol}")
async def get_ai_prediction(symbol: str):
    """Get AI prediction for a symbol"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    return await _registry.ai.get_prediction(symbol.upper())


@router.get("/ai/explain/{symbol}")
async def explain_ai_prediction(symbol: str):
    """Get AI prediction explanation"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    return await _registry.ai.explain_prediction(symbol.upper())


@router.get("/analysis/{symbol}")
async def get_analysis(symbol: str):
    """Get technical analysis for a symbol"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    # Get OHLCV data first
    ohlcv = await _registry.data.get_ohlcv(symbol.upper(), "1h", 100)
    prices = [c.get("close", 0) for c in ohlcv]
    
    return await _registry.analysis.quick_analysis(symbol.upper(), prices)


@router.get("/sentiment/{symbol}")
async def get_sentiment(symbol: str):
    """Get combined sentiment for a symbol"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    return await _registry.sentiment.get_combined_sentiment(symbol.upper())


@router.get("/trading/can-trade")
async def can_trade():
    """Check if trading is allowed"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    return await _registry.trading.can_trade()


@router.post("/trading/kill-switch")
async def toggle_kill_switch(activate: bool = True, reason: str = "Manual"):
    """Toggle the trading kill switch"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    if activate:
        return await _registry.trading.activate_kill_switch(reason)
    else:
        return await _registry.trading.deactivate_kill_switch()


@router.get("/ml/status")
async def get_ml_status():
    """Get ML service status and available frameworks"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    return {
        "status": _registry.ml.get_status(),
        "available_models": await _registry.ml.get_available_models()
    }


@router.get("/data/price/{symbol}")
async def get_price(symbol: str):
    """Get current price for a symbol"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    return await _registry.data.get_price(symbol.upper())


@router.get("/data/ohlcv/{symbol}")
async def get_ohlcv(
    symbol: str,
    interval: str = Query("1h", description="Candle interval"),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get OHLCV data for a symbol"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    return await _registry.data.get_ohlcv(symbol.upper(), interval, limit)


@router.get("/strategy/list")
async def list_strategies():
    """Get available trading strategies"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    return {
        "strategies": _registry.strategy.get_available_strategies(),
        "active": _registry.strategy.get_active_strategies()
    }


@router.post("/strategy/activate")
async def activate_strategy(
    strategy_id: str,
    symbol: str,
    params: Dict[str, Any] = None
):
    """Activate a trading strategy"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    return await _registry.strategy.activate_strategy(strategy_id, symbol.upper(), params)


@router.get("/notification/alerts")
async def get_alerts(unread_only: bool = False):
    """Get notifications and alerts"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    return {
        "notifications": _registry.notification.get_notifications(unread_only),
        "price_alerts": _registry.notification.get_active_alerts()
    }


@router.post("/notification/price-alert")
async def create_price_alert(
    symbol: str,
    condition: str = Query(..., regex="^(above|below)$"),
    price: float = Query(..., gt=0)
):
    """Create a price alert"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    return await _registry.notification.create_price_alert(
        symbol.upper(), condition, price
    )


@router.get("/system/health")
async def get_system_health():
    """Get system health status"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    return await _registry.system.get_health()


@router.post("/system/backup")
async def create_backup(collections: List[str] = None):
    """Create database backup"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    return await _registry.system.create_backup(collections)


@router.get("/system/backups")
async def list_backups():
    """List available backups"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    return await _registry.system.list_backups()


@router.get("/system/metrics")
async def get_metrics():
    """Get system performance metrics"""
    if _registry is None:
        raise HTTPException(status_code=503, detail="Service registry not initialized")
    
    return await _registry.system.get_performance_metrics()

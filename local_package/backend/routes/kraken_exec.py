"""
Kraken Execution API Routes
Executes SRDDQN signals on Kraken exchange
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kraken-exec", tags=["Kraken Execution"])

_db = None
_executor = None


def set_dependencies(db, executor=None):
    global _db, _executor
    _db = db
    _executor = executor


def get_executor():
    global _executor
    if _executor is None:
        from services.kraken_executor import get_kraken_executor
        _executor = get_kraken_executor(_db)
    return _executor


class ExecuteSignalRequest(BaseModel):
    symbol: str = "BTC"
    signal: str = "buy"  # buy, sell, strong_buy, strong_sell, hold
    confidence: float = 0.7
    position: float = 0.5
    portfolio_value: float = 10000


class PlaceOrderRequest(BaseModel):
    symbol: str = "BTC"
    side: str = "buy"
    volume: float
    order_type: str = "market"
    price: Optional[float] = None


@router.get("/status")
async def get_executor_status():
    """Get Kraken executor status"""
    try:
        executor = get_executor()
        if executor is None:
            return {"initialized": False}
        return executor.get_status()
    except Exception as e:
        return {"error": str(e)}


@router.post("/initialize")
async def initialize_executor():
    """Initialize Kraken executor"""
    try:
        from services.kraken_executor import initialize_kraken_executor
        
        global _executor
        _executor = await initialize_kraken_executor(_db)
        
        return {
            "status": "initialized",
            **_executor.get_status()
        }
    except Exception as e:
        logger.error(f"Executor init error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/balance")
async def get_balance():
    """Get Kraken account balance"""
    try:
        executor = get_executor()
        if executor is None:
            raise HTTPException(status_code=400, detail="Executor not initialized")
        
        balance = await executor.get_balance()
        return {"balance": balance}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticker/{symbol}")
async def get_ticker(symbol: str = "BTC"):
    """Get ticker for symbol"""
    try:
        executor = get_executor()
        if executor is None:
            raise HTTPException(status_code=400, detail="Executor not initialized")
        
        ticker = await executor.get_ticker(symbol.upper())
        return ticker
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-signal")
async def execute_srddqn_signal(request: ExecuteSignalRequest):
    """Execute SRDDQN trading signal on Kraken"""
    try:
        executor = get_executor()
        if executor is None:
            raise HTTPException(status_code=400, detail="Executor not initialized")
        
        signal = {
            'symbol': request.symbol,
            'signal': request.signal,
            'confidence': request.confidence,
            'position': request.position
        }
        
        result = await executor.execute_signal(signal, request.portfolio_value)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signal execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/place-order")
async def place_order(request: PlaceOrderRequest):
    """Place order directly on Kraken"""
    try:
        executor = get_executor()
        if executor is None:
            raise HTTPException(status_code=400, detail="Executor not initialized")
        
        result = await executor.place_order(
            symbol=request.symbol,
            side=request.side,
            volume=request.volume,
            order_type=request.order_type,
            price=request.price
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/open-orders")
async def get_open_orders():
    """Get open orders"""
    try:
        executor = get_executor()
        if executor is None:
            raise HTTPException(status_code=400, detail="Executor not initialized")
        
        orders = await executor.get_open_orders()
        return {"open_orders": orders}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/order/{order_id}")
async def cancel_order(order_id: str):
    """Cancel an open order"""
    try:
        executor = get_executor()
        if executor is None:
            raise HTTPException(status_code=400, detail="Executor not initialized")
        
        success = await executor.cancel_order(order_id)
        return {"cancelled": success, "order_id": order_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trade-history")
async def get_trade_history(limit: int = 50):
    """Get trade history"""
    try:
        executor = get_executor()
        if executor is None:
            raise HTTPException(status_code=400, detail="Executor not initialized")
        
        trades = await executor.get_trade_history(limit)
        return {"trades": trades, "count": len(trades)}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-daily-limits")
async def reset_daily_limits():
    """Reset daily trading limits"""
    try:
        executor = get_executor()
        if executor is None:
            raise HTTPException(status_code=400, detail="Executor not initialized")
        
        executor.reset_daily_limits()
        return {"status": "reset", "daily_volume_usd": 0}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/full-execute")
async def full_signal_to_execution(symbol: str = "BTC"):
    """Generate SRDDQN signal and execute on Kraken"""
    try:
        # Get SRDDQN signal
        from services.srddqn_trading_integration import get_srddqn_integration
        
        integration = get_srddqn_integration(_db)
        if integration is None:
            raise HTTPException(status_code=400, detail="SRDDQN integration not initialized")
        
        # Generate signal
        signal = await integration.generate_trading_signal(symbol)
        
        if signal.get('signal') == 'hold':
            return {
                "signal": signal,
                "execution": {"executed": False, "reason": "Hold signal"}
            }
        
        # Execute on Kraken
        executor = get_executor()
        if executor is None:
            raise HTTPException(status_code=400, detail="Kraken executor not initialized")
        
        # Get portfolio value from balance
        balance = await executor.get_balance()
        usd_balance = balance.get('USD', 0) + balance.get('ZUSD', 0)
        portfolio_value = max(usd_balance, 1000)  # Min $1000
        
        result = await executor.execute_signal(signal, portfolio_value)
        
        return {
            "signal": signal,
            "execution": result,
            "portfolio_value": portfolio_value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Full execute error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-limits")
async def get_risk_limits():
    """Get current risk limits"""
    try:
        executor = get_executor()
        if executor is None:
            return {"error": "Executor not initialized"}
        
        return {
            "max_order_size_usd": executor.max_order_size_usd,
            "max_daily_volume_usd": executor.max_daily_volume_usd,
            "min_order_interval_seconds": executor.min_order_interval_seconds,
            "daily_volume_used": executor.daily_volume,
            "daily_volume_remaining": executor.max_daily_volume_usd - executor.daily_volume
        }
        
    except Exception as e:
        return {"error": str(e)}


@router.post("/risk-limits")
async def update_risk_limits(
    max_order_size_usd: float = None,
    max_daily_volume_usd: float = None,
    min_order_interval_seconds: int = None
):
    """Update risk limits"""
    try:
        executor = get_executor()
        if executor is None:
            raise HTTPException(status_code=400, detail="Executor not initialized")
        
        if max_order_size_usd is not None:
            executor.max_order_size_usd = max_order_size_usd
        if max_daily_volume_usd is not None:
            executor.max_daily_volume_usd = max_daily_volume_usd
        if min_order_interval_seconds is not None:
            executor.min_order_interval_seconds = min_order_interval_seconds
        
        return {
            "status": "updated",
            "max_order_size_usd": executor.max_order_size_usd,
            "max_daily_volume_usd": executor.max_daily_volume_usd,
            "min_order_interval_seconds": executor.min_order_interval_seconds
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

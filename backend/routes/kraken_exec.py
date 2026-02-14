"""
Kraken Execution API Routes
Executes SRDDQN signals on Kraken exchange.
HARDENED: Safe error handling, auth guards, input validation, audit logging.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import re

from utils.safe_errors import safe_error_response, log_security_event
from utils.auth_guard import verify_api_key, require_trade_scope
from utils.input_sanitizer import sanitize_symbol

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
    symbol: str = Field("BTC", max_length=20)
    signal: str = Field("buy", pattern="^(buy|sell|strong_buy|strong_sell|hold)$")
    confidence: float = Field(0.7, ge=0.0, le=1.0)
    position: float = Field(0.5, ge=0.0, le=1.0)
    portfolio_value: float = Field(10000, gt=0, le=10000000)

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        return re.sub(r'[^a-zA-Z0-9]', '', v).upper()[:20]


class PlaceOrderRequest(BaseModel):
    symbol: str = Field("BTC", max_length=20)
    side: str = Field("buy", pattern="^(buy|sell)$")
    volume: float = Field(..., gt=0, le=1000000)
    order_type: str = Field("market", pattern="^(market|limit|stop-loss|take-profit)$")
    price: Optional[float] = Field(None, gt=0)

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        return re.sub(r'[^a-zA-Z0-9]', '', v).upper()[:20]


@router.get("/status")
async def get_executor_status():
    """Get Kraken executor status"""
    try:
        executor = get_executor()
        if executor is None:
            return {"initialized": False}
        return executor.get_status()
    except Exception as e:
        logger.error(f"Executor status error: {e}")
        return {"initialized": False, "status": "error"}


@router.post("/initialize")
async def initialize_executor(auth: dict = Depends(verify_api_key)):
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
        raise safe_error_response(e, category="kraken", context="executor initialization")


@router.get("/balance")
async def get_balance(auth: dict = Depends(verify_api_key)):
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
        raise safe_error_response(e, category="kraken", context="get balance")


@router.get("/ticker/{symbol}")
async def get_ticker(symbol: str = "BTC"):
    """Get ticker for symbol"""
    try:
        clean_symbol = sanitize_symbol(symbol)
        if not clean_symbol:
            raise HTTPException(status_code=400, detail="Invalid symbol")
        
        executor = get_executor()
        if executor is None:
            raise HTTPException(status_code=400, detail="Executor not initialized")
        
        ticker = await executor.get_ticker(clean_symbol)
        return ticker
        
    except HTTPException:
        raise
    except Exception as e:
        raise safe_error_response(e, category="kraken", context=f"get ticker {symbol}")


@router.post("/execute-signal")
async def execute_srddqn_signal(
    request: ExecuteSignalRequest,
    req: Request = None,
    auth: dict = Depends(require_trade_scope)
):
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
        
        # Log the trade attempt
        logger.info(
            f"TRADE SIGNAL | Symbol={request.symbol} | Signal={request.signal} | "
            f"Confidence={request.confidence} | Value=${request.portfolio_value}"
        )
        
        result = await executor.execute_signal(signal, request.portfolio_value)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise safe_error_response(e, category="trade", context=f"execute signal {request.symbol}")


@router.post("/place-order")
async def place_order(
    request: PlaceOrderRequest,
    auth: dict = Depends(require_trade_scope)
):
    """Place order directly on Kraken"""
    try:
        executor = get_executor()
        if executor is None:
            raise HTTPException(status_code=400, detail="Executor not initialized")
        
        # Log the order placement
        logger.info(
            f"ORDER PLACEMENT | Symbol={request.symbol} | Side={request.side} | "
            f"Volume={request.volume} | Type={request.order_type} | Price={request.price}"
        )
        
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
        raise safe_error_response(e, category="trade", context=f"place order {request.symbol}")


@router.get("/open-orders")
async def get_open_orders(auth: dict = Depends(verify_api_key)):
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
        raise safe_error_response(e, category="kraken", context="get open orders")


@router.delete("/order/{order_id}")
async def cancel_order(
    order_id: str,
    auth: dict = Depends(require_trade_scope)
):
    """Cancel an open order"""
    try:
        # Sanitize order_id
        clean_order_id = re.sub(r'[^a-zA-Z0-9\-_]', '', order_id)[:64]
        if not clean_order_id:
            raise HTTPException(status_code=400, detail="Invalid order ID")
        
        executor = get_executor()
        if executor is None:
            raise HTTPException(status_code=400, detail="Executor not initialized")
        
        logger.info(f"ORDER CANCELLATION | OrderID={clean_order_id}")
        
        success = await executor.cancel_order(clean_order_id)
        return {"cancelled": success, "order_id": clean_order_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise safe_error_response(e, category="trade", context=f"cancel order {order_id}")


@router.get("/trade-history")
async def get_trade_history(limit: int = 50, auth: dict = Depends(verify_api_key)):
    """Get trade history"""
    try:
        # Clamp limit
        safe_limit = max(1, min(limit, 500))
        
        executor = get_executor()
        if executor is None:
            raise HTTPException(status_code=400, detail="Executor not initialized")
        
        trades = await executor.get_trade_history(safe_limit)
        return {"trades": trades, "count": len(trades)}
        
    except HTTPException:
        raise
    except Exception as e:
        raise safe_error_response(e, category="kraken", context="get trade history")


@router.post("/reset-daily-limits")
async def reset_daily_limits(auth: dict = Depends(require_trade_scope)):
    """Reset daily trading limits"""
    try:
        executor = get_executor()
        if executor is None:
            raise HTTPException(status_code=400, detail="Executor not initialized")
        
        executor.reset_daily_limits()
        logger.info("RISK LIMITS RESET | daily_volume reset to 0")
        return {"status": "reset", "daily_volume_usd": 0}
        
    except Exception as e:
        raise safe_error_response(e, category="trade", context="reset daily limits")


@router.post("/full-execute")
async def full_signal_to_execution(
    symbol: str = "BTC",
    auth: dict = Depends(require_trade_scope)
):
    """Generate SRDDQN signal and execute on Kraken"""
    try:
        clean_symbol = sanitize_symbol(symbol)
        if not clean_symbol:
            raise HTTPException(status_code=400, detail="Invalid symbol")
        
        # Get SRDDQN signal
        from services.srddqn_trading_integration import get_srddqn_integration
        
        integration = get_srddqn_integration(_db)
        if integration is None:
            raise HTTPException(status_code=400, detail="SRDDQN integration not initialized")
        
        # Generate signal
        signal = await integration.generate_trading_signal(clean_symbol)
        
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
        
        logger.info(
            f"FULL EXECUTE | Symbol={clean_symbol} | Signal={signal.get('signal')} | "
            f"PortfolioValue=${portfolio_value}"
        )
        
        result = await executor.execute_signal(signal, portfolio_value)
        
        return {
            "signal": signal,
            "execution": result,
            "portfolio_value": portfolio_value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise safe_error_response(e, category="trade", context=f"full execute {symbol}")


@router.get("/risk-limits")
async def get_risk_limits(auth: dict = Depends(verify_api_key)):
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
        raise safe_error_response(e, category="kraken", context="get risk limits")


@router.post("/risk-limits")
async def update_risk_limits(
    max_order_size_usd: float = None,
    max_daily_volume_usd: float = None,
    min_order_interval_seconds: int = None,
    auth: dict = Depends(require_trade_scope)
):
    """Update risk limits"""
    try:
        executor = get_executor()
        if executor is None:
            raise HTTPException(status_code=400, detail="Executor not initialized")
        
        # Validate bounds
        if max_order_size_usd is not None:
            if max_order_size_usd < 0 or max_order_size_usd > 1000000:
                raise HTTPException(status_code=400, detail="max_order_size_usd must be between 0 and 1,000,000")
            executor.max_order_size_usd = max_order_size_usd
        
        if max_daily_volume_usd is not None:
            if max_daily_volume_usd < 0 or max_daily_volume_usd > 10000000:
                raise HTTPException(status_code=400, detail="max_daily_volume_usd must be between 0 and 10,000,000")
            executor.max_daily_volume_usd = max_daily_volume_usd
        
        if min_order_interval_seconds is not None:
            if min_order_interval_seconds < 0 or min_order_interval_seconds > 86400:
                raise HTTPException(status_code=400, detail="min_order_interval_seconds must be between 0 and 86400")
            executor.min_order_interval_seconds = min_order_interval_seconds
        
        logger.info(
            f"RISK LIMITS UPDATED | MaxOrder=${max_order_size_usd} | "
            f"MaxDaily=${max_daily_volume_usd} | MinInterval={min_order_interval_seconds}s"
        )
        
        return {
            "status": "updated",
            "max_order_size_usd": executor.max_order_size_usd,
            "max_daily_volume_usd": executor.max_daily_volume_usd,
            "min_order_interval_seconds": executor.min_order_interval_seconds
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise safe_error_response(e, category="trade", context="update risk limits")

"""
Kraken Trading API Routes
Direct interface to Kraken exchange for trading operations.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/kraken", tags=["Kraken Trading"])

# Global references
_db = None
_kraken_service = None
_isolated_portfolio = None
_automated_trader = None


def set_dependencies(database, kraken_service, isolated_portfolio=None, automated_trader=None):
    """Set dependencies from main app"""
    global _db, _kraken_service, _isolated_portfolio, _automated_trader
    _db = database
    _kraken_service = kraken_service
    _isolated_portfolio = isolated_portfolio
    _automated_trader = automated_trader


class OrderRequest(BaseModel):
    pair: str  # e.g., "XXBTZUSD"
    side: str  # "buy" or "sell"
    order_type: str  # "market" or "limit"
    volume: float
    price: Optional[float] = None  # Required for limit orders


class CancelOrderRequest(BaseModel):
    order_id: str


@router.get("/status")
async def get_kraken_status():
    """
    Check Kraken connection status and API health.
    
    Returns:
    - connected: Whether we can reach Kraken API
    - authenticated: Whether API keys are valid
    - trading_enabled: Whether live trading is allowed
    """
    if _kraken_service is None:
        return {
            "connected": False,
            "authenticated": False,
            "trading_enabled": False,
            "error": "Kraken service not initialized"
        }
    
    status = {
        "connected": False,
        "authenticated": False,
        "trading_enabled": False,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        # Test public endpoint (connection check)
        ticker = await _kraken_service.get_ticker("XXBTZUSD")
        status["connected"] = ticker is not None
        
        if ticker:
            status["btc_price"] = float(ticker.get("c", [0])[0]) if ticker.get("c") else None
    except Exception as e:
        status["connection_error"] = str(e)
    
    try:
        # Test private endpoint (authentication check)
        balance = await _kraken_service.get_balance()
        status["authenticated"] = True
        status["has_usd_balance"] = float(balance.get("ZUSD", 0)) > 0
    except Exception as e:
        status["auth_error"] = str(e)
    
    # Check trading status from isolated portfolio
    if _isolated_portfolio:
        try:
            budget = await _isolated_portfolio.get_budget_status()
            status["trading_enabled"] = budget.get("real_trading_enabled", False)
            status["isolated_budget"] = budget.get("current_value", 0)
        except:
            pass
    
    return status


@router.get("/balance")
async def get_kraken_balance():
    """
    Get all Kraken account balances.
    
    Returns balances for all currencies in the account.
    """
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    try:
        balance = await _kraken_service.get_balance()
        
        # Format balances
        formatted = {}
        for currency, amount in balance.items():
            if float(amount) > 0:
                formatted[currency] = {
                    "amount": float(amount),
                    "display": f"{float(amount):.6f}"
                }
        
        return {
            "balances": formatted,
            "total_currencies": len(formatted),
            "usd_available": float(balance.get("ZUSD", 0)),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kraken API error: {str(e)}")


@router.get("/ticker/{pair}")
async def get_ticker(pair: str):
    """
    Get current ticker for a trading pair.
    
    Common pairs:
    - XXBTZUSD (Bitcoin/USD)
    - XETHZUSD (Ethereum/USD)
    - SOLUSD (Solana/USD)
    """
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    try:
        ticker = await _kraken_service.get_ticker(pair)
        
        if not ticker:
            raise HTTPException(status_code=404, detail=f"Ticker not found for pair: {pair}")
        
        return {
            "pair": pair,
            "ask": float(ticker.get("a", [0])[0]) if ticker.get("a") else None,
            "bid": float(ticker.get("b", [0])[0]) if ticker.get("b") else None,
            "last": float(ticker.get("c", [0])[0]) if ticker.get("c") else None,
            "volume_24h": float(ticker.get("v", [0, 0])[1]) if ticker.get("v") else None,
            "low_24h": float(ticker.get("l", [0, 0])[1]) if ticker.get("l") else None,
            "high_24h": float(ticker.get("h", [0, 0])[1]) if ticker.get("h") else None,
            "open_24h": float(ticker.get("o", 0)) if ticker.get("o") else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kraken API error: {str(e)}")


@router.get("/open-orders")
async def get_open_orders():
    """Get all open orders on Kraken"""
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    try:
        orders = await _kraken_service.get_open_orders()
        
        return {
            "orders": orders.get("open", {}),
            "count": len(orders.get("open", {})),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kraken API error: {str(e)}")


@router.get("/trade-history")
async def get_trade_history(limit: int = Query(50, ge=1, le=500)):
    """Get recent trade history from Kraken"""
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    try:
        history = await _kraken_service.get_trades_history()
        
        trades = history.get("trades", {})
        
        # Sort by time and limit
        sorted_trades = sorted(
            [(tid, t) for tid, t in trades.items()],
            key=lambda x: x[1].get("time", 0),
            reverse=True
        )[:limit]
        
        formatted_trades = []
        for trade_id, trade in sorted_trades:
            formatted_trades.append({
                "id": trade_id,
                "pair": trade.get("pair"),
                "type": trade.get("type"),
                "price": float(trade.get("price", 0)),
                "volume": float(trade.get("vol", 0)),
                "cost": float(trade.get("cost", 0)),
                "fee": float(trade.get("fee", 0)),
                "time": datetime.fromtimestamp(trade.get("time", 0)).isoformat()
            })
        
        return {
            "trades": formatted_trades,
            "count": len(formatted_trades),
            "total_available": history.get("count", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kraken API error: {str(e)}")


@router.post("/order")
async def place_order(request: OrderRequest):
    """
    Place an order on Kraken.
    
    IMPORTANT: Uses isolated budget by default. Real trading must be enabled.
    
    Args:
        pair: Trading pair (e.g., "XXBTZUSD")
        side: "buy" or "sell"
        order_type: "market" or "limit"
        volume: Amount to trade
        price: Required for limit orders
    """
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    # Check if real trading is enabled
    if _isolated_portfolio:
        budget = await _isolated_portfolio.get_budget_status()
        if not budget.get("real_trading_enabled"):
            raise HTTPException(
                status_code=403, 
                detail="Real trading not enabled. Enable it in Trading Budget settings."
            )
    
    try:
        if request.order_type.lower() == "limit" and request.price is None:
            raise HTTPException(status_code=400, detail="Price required for limit orders")
        
        result = await _kraken_service.place_order(
            pair=request.pair,
            side=request.side,
            ordertype=request.order_type,
            volume=str(request.volume),
            price=str(request.price) if request.price else "0"
        )
        
        return {
            "success": True,
            "order": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order failed: {str(e)}")


@router.post("/cancel-order")
async def cancel_order(request: CancelOrderRequest):
    """Cancel an open order"""
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    try:
        result = await _kraken_service.cancel_order(request.order_id)
        
        return {
            "success": True,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cancel failed: {str(e)}")


@router.get("/supported-pairs")
async def get_supported_pairs():
    """Get list of trading pairs supported by the auto trader"""
    if _automated_trader is None:
        return {
            "pairs": {},
            "note": "Auto trader not initialized"
        }
    
    return {
        "pairs": _automated_trader.kraken_symbols,
        "count": len(_automated_trader.kraken_symbols),
        "note": "Maps coin IDs to Kraken trading pairs"
    }


@router.get("/auto-trader/status")
async def get_auto_trader_status():
    """Get current status of the automated trader"""
    if _automated_trader is None:
        return {
            "initialized": False,
            "error": "Auto trader not initialized"
        }
    
    try:
        # Get portfolio balance (uses isolated budget)
        balance = await _automated_trader.get_portfolio_balance()
        
        # Get adaptive parameters
        params = await _automated_trader.get_adaptive_params()
        
        # Get current config
        config = _automated_trader.config
        
        return {
            "initialized": True,
            "balance": balance,
            "adaptive_params": params,
            "config": config,
            "kraken_connected": _kraken_service is not None,
            "services": _automated_trader.get_service_status() if hasattr(_automated_trader, 'get_service_status') else {
                "ai_trainer": _automated_trader.ai_trainer is not None,
                "gem_finder": _automated_trader.gem_finder is not None,
                "adaptive_strategy": _automated_trader.adaptive_strategy is not None,
                "regime_predictor": _automated_trader.regime_predictor is not None,
                "isolated_portfolio": _automated_trader.isolated_portfolio is not None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "initialized": True,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.post("/auto-trader/execute-weekly")
async def execute_weekly_strategy(paper_trade: bool = True):
    """
    Execute the weekly AI trading strategy.
    
    This will:
    1. Get AI coin selections
    2. Get gem recommendations
    3. Apply adaptive strategy based on market regime
    4. Execute trades (paper or real based on settings)
    
    Args:
        paper_trade: If True, simulate trades. If False, execute real trades.
    """
    if _automated_trader is None:
        raise HTTPException(status_code=503, detail="Auto trader not initialized")
    
    try:
        result = await _automated_trader.execute_weekly_rebalance(paper_trade=paper_trade)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@router.get("/auto-trader/positions")
async def get_auto_trader_positions():
    """Get current positions managed by the auto trader"""
    if _automated_trader is None or _isolated_portfolio is None:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    try:
        positions = await _isolated_portfolio.get_ai_positions()
        budget = await _isolated_portfolio.get_budget_status()
        
        return {
            "positions": positions,
            "count": len(positions),
            "budget": budget,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting positions: {str(e)}")

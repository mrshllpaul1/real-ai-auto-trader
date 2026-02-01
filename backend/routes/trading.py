from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class OrderRequest(BaseModel):
    user_id: str
    strategy_id: str
    coin_pair: str
    action: str  # BUY or SELL
    amount: float
    mode: str = "paper"  # paper or real

class TradeResponse(BaseModel):
    trade_id: str
    status: str
    message: Optional[str] = None

async def get_database():
    from server import db
    return db

async def get_trading_engine():
    from services.trading_engine import TradingEngine
    from server import db
    return TradingEngine(db)

async def get_risk_manager():
    from services.risk_manager import RiskManager
    from server import db
    return RiskManager(db)

@router.post("/execute", response_model=TradeResponse)
async def execute_trade(
    order: OrderRequest,
    db = Depends(get_database),
    trading_engine = Depends(get_trading_engine),
    risk_manager = Depends(get_risk_manager)
):
    """Execute a trade order"""
    try:
        # Validate trade against risk management rules
        validation = await risk_manager.validate_trade(
            order.user_id,
            order.amount,
            order.coin_pair
        )
        
        if not validation.get('valid'):
            raise HTTPException(status_code=400, detail=validation.get('reason'))
        
        # Get current market price (simplified - should fetch real price)
        market_service = await get_market_service()
        coin_id = order.coin_pair.split('/')[0].lower()
        price_data = await market_service.get_coin_price([coin_id])
        current_price = price_data.get(coin_id, {}).get('price_usd', 0)
        
        # Execute trade
        result = await trading_engine.execute_trade(
            user_id=order.user_id,
            strategy_id=order.strategy_id,
            coin_pair=order.coin_pair,
            action=order.action,
            amount=order.amount,
            price=current_price,
            mode=order.mode
        )
        
        if result.get('error'):
            raise HTTPException(status_code=500, detail=result['error'])
        
        return TradeResponse(
            trade_id=result['trade_id'],
            status=result['status'],
            message="Trade executed successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{user_id}")
async def get_trade_history(
    user_id: str,
    mode: str = "all",
    limit: int = 100,
    trading_engine = Depends(get_trading_engine)
):
    """Get trade history for a user"""
    try:
        trades = await trading_engine.get_trade_history(user_id, mode, limit)
        return {"trades": trades, "count": len(trades)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio/{user_id}")
async def get_portfolio_performance(
    user_id: str,
    trading_engine = Depends(get_trading_engine)
):
    """Get portfolio performance metrics"""
    try:
        # Get current prices for portfolio calculation
        market_service = await get_market_service()
        # Simplified - should fetch actual coin pairs from user's portfolio
        price_data = await market_service.get_coin_price(['bitcoin', 'ethereum'])
        
        current_prices = {
            'XBTUSD': price_data.get('bitcoin', {}).get('price_usd', 0),
            'ETHUSD': price_data.get('ethereum', {}).get('price_usd', 0)
        }
        
        performance = await trading_engine.calculate_portfolio_performance(
            user_id,
            current_prices
        )
        
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_market_service():
    from services.market_data_service import MarketDataService
    return MarketDataService()
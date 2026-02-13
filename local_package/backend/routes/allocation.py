from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict

router = APIRouter()

class AllocationRequest(BaseModel):
    user_id: str
    allocations: Dict[str, float]  # {'USD': 1000, 'BTC': 0.1}

class WithdrawRequest(BaseModel):
    user_id: str
    amount: float

async def get_database():
    from server import db
    return db

async def get_allocation_manager():
    from services.portfolio_allocation_manager import PortfolioAllocationManager
    from server import db
    return PortfolioAllocationManager(db)

@router.post("/allocate")
async def allocate_funds(
    request: AllocationRequest,
    manager = Depends(get_allocation_manager)
):
    """Allocate funds for bot to trade with (isolated from other Kraken assets)"""
    try:
        result = await manager.create_allocation(
            request.user_id,
            request.allocations
        )
        
        return {
            'message': 'Funds allocated successfully',
            'allocation': result,
            'protection': 'Bot will ONLY trade with allocated funds. Your other Kraken assets are untouched.'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/allocation/{user_id}")
async def get_allocation(
    user_id: str,
    manager = Depends(get_allocation_manager)
):
    """Get current allocation"""
    try:
        result = await manager.get_allocation(user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio/{user_id}")
async def get_bot_portfolio(
    user_id: str,
    manager = Depends(get_allocation_manager)
):
    """Get bot's isolated portfolio (separate from user's main Kraken holdings)"""
    try:
        portfolio = await manager.get_bot_portfolio(user_id)
        return portfolio
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/value/{user_id}")
async def get_portfolio_value(
    user_id: str,
    manager = Depends(get_allocation_manager)
):
    """Calculate current value of bot portfolio"""
    try:
        from services.market_data_service import MarketDataService
        market_service = MarketDataService()
        
        # Get current prices
        prices_data = await market_service.get_coin_price(['bitcoin', 'ethereum', 'solana'])
        current_prices = {
            'BTC': prices_data.get('bitcoin', {}).get('price_usd', 0),
            'ETH': prices_data.get('ethereum', {}).get('price_usd', 0),
            'SOL': prices_data.get('solana', {}).get('price_usd', 0)
        }
        
        value = await manager.calculate_portfolio_value(user_id, current_prices)
        return value
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/withdraw-profits")
async def withdraw_profits(
    request: WithdrawRequest,
    manager = Depends(get_allocation_manager)
):
    """Withdraw profits from bot portfolio (preserves trading capital)"""
    try:
        result = await manager.withdraw_profits(
            request.user_id,
            request.amount
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary/{user_id}")
async def get_allocation_summary(
    user_id: str,
    manager = Depends(get_allocation_manager)
):
    """Get comprehensive summary showing separation between bot and user funds"""
    try:
        summary = await manager.get_allocation_summary(user_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

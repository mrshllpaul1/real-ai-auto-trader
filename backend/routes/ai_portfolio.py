"""
AI Portfolio Management Routes
Endpoints for AI-managed autonomous portfolio trading
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

router = APIRouter()

# Will be set by server.py
ai_portfolio_manager = None

class InitializePortfolioRequest(BaseModel):
    user_id: str = "default"
    initial_capital: float  # USD amount to allocate to AI

class RebalanceRequest(BaseModel):
    user_id: str = "default"

@router.post("/initialize")
async def initialize_ai_portfolio(request: InitializePortfolioRequest):
    """
    Initialize AI-managed portfolio with allocated capital.
    The AI will develop its own trading strategy and manage this capital.
    """
    if not ai_portfolio_manager:
        raise HTTPException(status_code=500, detail="AI Portfolio Manager not initialized")
    
    if request.initial_capital < 100:
        raise HTTPException(status_code=400, detail="Minimum capital is $100")
    
    result = await ai_portfolio_manager.initialize_ai_portfolio(
        request.user_id,
        request.initial_capital
    )
    
    return {
        "success": True,
        "message": f"AI Portfolio initialized with ${request.initial_capital:,.2f}",
        "portfolio": result
    }

@router.post("/develop-strategy")
async def develop_strategy(request: RebalanceRequest):
    """
    Trigger AI to develop/update portfolio strategy.
    AI analyzes market conditions, news sentiment, and historical data.
    """
    if not ai_portfolio_manager:
        raise HTTPException(status_code=500, detail="AI Portfolio Manager not initialized")
    
    result = await ai_portfolio_manager.develop_portfolio_strategy(request.user_id)
    
    return {
        "success": True,
        "strategy": result
    }

@router.post("/rebalance")
async def rebalance_portfolio(request: RebalanceRequest):
    """
    Execute portfolio rebalancing to match AI target allocation.
    This will execute real trades on Kraken if configured.
    """
    if not ai_portfolio_manager:
        raise HTTPException(status_code=500, detail="AI Portfolio Manager not initialized")
    
    result = await ai_portfolio_manager.execute_rebalance(request.user_id)
    
    return result

@router.get("/status/{user_id}")
async def get_portfolio_status(user_id: str = "default"):
    """
    Get current AI portfolio status including:
    - Holdings and their current values
    - Profit/Loss
    - Target allocation
    - AI strategy details
    """
    if not ai_portfolio_manager:
        raise HTTPException(status_code=500, detail="AI Portfolio Manager not initialized")
    
    status = await ai_portfolio_manager.get_portfolio_status(user_id)
    
    return status

@router.post("/start-autonomous")
async def start_autonomous_trading(request: RebalanceRequest):
    """
    Start AI autonomous trading mode.
    AI will continuously monitor, develop strategies, and execute trades.
    """
    if not ai_portfolio_manager:
        raise HTTPException(status_code=500, detail="AI Portfolio Manager not initialized")
    
    # Start in background (non-blocking)
    import asyncio
    asyncio.create_task(ai_portfolio_manager.start_autonomous_trading(request.user_id))
    
    return {
        "success": True,
        "message": "AI Autonomous Trading started",
        "user_id": request.user_id
    }

@router.post("/stop-autonomous")
async def stop_autonomous_trading():
    """Stop AI autonomous trading"""
    if not ai_portfolio_manager:
        raise HTTPException(status_code=500, detail="AI Portfolio Manager not initialized")
    
    ai_portfolio_manager.stop_autonomous_trading()
    
    return {
        "success": True,
        "message": "AI Autonomous Trading stopped"
    }

@router.get("/trades/{user_id}")
async def get_ai_trades(user_id: str = "default", limit: int = 50):
    """Get history of AI-executed trades"""
    if not ai_portfolio_manager:
        raise HTTPException(status_code=500, detail="AI Portfolio Manager not initialized")
    
    trades = await ai_portfolio_manager.db.ai_trades.find(
        {'user_id': user_id},
        {'_id': 0}
    ).sort('timestamp', -1).limit(limit).to_list(limit)
    
    return {
        "user_id": user_id,
        "trades": trades,
        "count": len(trades)
    }

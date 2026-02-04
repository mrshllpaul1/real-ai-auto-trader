"""
Isolated Portfolio API Routes
Manage AI trading budget with strict isolation from your other assets.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

router = APIRouter(prefix="/isolated-portfolio", tags=["Isolated Portfolio"])

# Global references
db = None
isolated_portfolio = None


def set_dependencies(database, portfolio_manager):
    """Set dependencies from main app"""
    global db, isolated_portfolio
    db = database
    isolated_portfolio = portfolio_manager


class SetBudgetRequest(BaseModel):
    amount_usd: float
    enable_real_trading: bool = False


class SwapRequest(BaseModel):
    from_position_id: str
    to_coin_id: str
    to_symbol: str
    to_price: float


class ClosePositionRequest(BaseModel):
    position_id: str
    exit_price: float
    reason: str = "manual"


@router.post("/set-budget")
async def set_trading_budget(request: SetBudgetRequest):
    """
    Set the budget the AI is allowed to trade with.
    
    ⚠️ IMPORTANT: This is the ONLY money the AI will use.
    Your other assets will NEVER be touched.
    
    Args:
        amount_usd: Total USD budget for AI trading
        enable_real_trading: If True, execute real trades on Kraken
    """
    if not isolated_portfolio:
        raise HTTPException(status_code=503, detail="Portfolio manager not initialized")
    
    if request.amount_usd < 0:
        raise HTTPException(status_code=400, detail="Budget cannot be negative")
    
    return await isolated_portfolio.set_trading_budget(
        amount_usd=request.amount_usd,
        enable_real_trading=request.enable_real_trading
    )


@router.get("/status")
async def get_budget_status():
    """
    Get current AI trading budget status.
    
    Shows:
    - Initial budget allocation
    - Current portfolio value
    - Cash available for new trades
    - Open positions value
    - Total P&L
    """
    if not isolated_portfolio:
        raise HTTPException(status_code=503, detail="Portfolio manager not initialized")
    
    return await isolated_portfolio.get_budget_status()


@router.get("/positions")
async def get_ai_positions():
    """
    Get all AI-managed positions.
    
    These are positions opened by the AI within your allocated budget.
    Your other holdings are NOT included here - they are protected.
    """
    if not isolated_portfolio:
        raise HTTPException(status_code=503, detail="Portfolio manager not initialized")
    
    positions = await isolated_portfolio.get_ai_positions()
    return {
        "count": len(positions),
        "positions": positions
    }


@router.post("/close-position")
async def close_position(request: ClosePositionRequest):
    """
    Close an AI-managed position.
    
    Returns funds (plus any P&L) back to the AI budget.
    """
    if not isolated_portfolio:
        raise HTTPException(status_code=503, detail="Portfolio manager not initialized")
    
    return await isolated_portfolio.close_position(
        position_id=request.position_id,
        exit_price=request.exit_price,
        reason=request.reason
    )


@router.post("/swap")
async def swap_position(request: SwapRequest):
    """
    Swap one AI position for another.
    
    This is allowed because:
    - We're only managing AI-allocated funds
    - The swap stays within your budget
    - Your other assets are not affected
    """
    if not isolated_portfolio:
        raise HTTPException(status_code=503, detail="Portfolio manager not initialized")
    
    return await isolated_portfolio.swap_position(
        from_position_id=request.from_position_id,
        to_coin_id=request.to_coin_id,
        to_symbol=request.to_symbol,
        to_price=request.to_price
    )


@router.get("/transactions")
async def get_transaction_history(limit: int = 50):
    """Get AI trading transaction history"""
    if not isolated_portfolio:
        raise HTTPException(status_code=503, detail="Portfolio manager not initialized")
    
    history = await isolated_portfolio.get_transaction_history(limit)
    return {
        "count": len(history),
        "transactions": history
    }


@router.get("/verify-isolation")
async def verify_isolation():
    """
    Verify that AI trading is properly isolated.
    
    Confirms that:
    - Only your allocated budget is being used
    - Your other assets are protected
    - All trades are within budget constraints
    """
    if not isolated_portfolio:
        raise HTTPException(status_code=503, detail="Portfolio manager not initialized")
    
    return await isolated_portfolio.verify_isolation()


class EmergencyStopRequest(BaseModel):
    liquidate_positions: bool = False
    confirmation_code: str


class ResumeRequest(BaseModel):
    confirmation_code: str


@router.post("/emergency-stop")
async def emergency_stop(request: EmergencyStopRequest):
    """
    🚨 EMERGENCY STOP - Immediately halt all AI trading.
    
    ⚠️ REQUIRES DOUBLE CONFIRMATION:
    1. First call: confirmation_code = "CONFIRM_STEP_1"
    2. Second call: confirmation_code = "EMERGENCY_STOP_CONFIRMED"
    
    Options:
    - liquidate_positions=False: Just disable trading, keep positions
    - liquidate_positions=True: Disable trading AND close all positions at market
    """
    if not isolated_portfolio:
        raise HTTPException(status_code=503, detail="Portfolio manager not initialized")
    
    # Step 1 confirmation
    if request.confirmation_code == "CONFIRM_STEP_1":
        return {
            "step": 1,
            "status": "confirmation_required",
            "message": "⚠️ WARNING: You are about to activate EMERGENCY STOP. This will disable all AI trading immediately.",
            "liquidate_positions": request.liquidate_positions,
            "next_step": "Send confirmation_code='EMERGENCY_STOP_CONFIRMED' to proceed",
            "warning": "This action cannot be easily undone. Are you absolutely sure?"
        }
    
    # Step 2 - Final confirmation
    return await isolated_portfolio.emergency_stop(
        liquidate_positions=request.liquidate_positions,
        confirmation_code=request.confirmation_code
    )


@router.post("/resume-trading")
async def resume_trading(request: ResumeRequest):
    """
    Resume trading after emergency stop.
    
    Requires confirmation_code = "RESUME_TRADING_CONFIRMED"
    """
    if not isolated_portfolio:
        raise HTTPException(status_code=503, detail="Portfolio manager not initialized")
    
    return await isolated_portfolio.resume_trading(
        confirmation_code=request.confirmation_code
    )


@router.get("/emergency-status")
async def get_emergency_status():
    """
    Check if emergency stop is active.
    """
    if not isolated_portfolio:
        raise HTTPException(status_code=503, detail="Portfolio manager not initialized")
    
    budget = await db.trading_budgets.find_one({"user_id": "default"}, {"_id": 0})
    
    if not budget:
        return {
            "emergency_stopped": False,
            "trading_enabled": False,
            "reason": "No budget allocated"
        }
    
    return {
        "emergency_stopped": budget.get("emergency_stopped", False),
        "trading_enabled": budget.get("real_trading_enabled", False),
        "emergency_stop_at": budget.get("emergency_stop_at"),
        "resumed_at": budget.get("resumed_at")
    }


@router.get("/can-trade")
async def check_can_trade(amount_usd: float):
    """
    Check if a trade of the given amount is allowed within budget.
    """
    if not isolated_portfolio:
        raise HTTPException(status_code=503, detail="Portfolio manager not initialized")
    
    return await isolated_portfolio.can_trade(amount_usd)

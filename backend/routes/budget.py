"""
Budget Management API Routes
Control real money trading budget - only uses allocated funds.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/budget", tags=["Budget Management"])

# Global reference
budget_manager = None


def set_dependencies(manager):
    global budget_manager
    budget_manager = manager


class SetBudgetRequest(BaseModel):
    amount: float
    enable_real_trading: Optional[bool] = False


class AllocateFundsRequest(BaseModel):
    amount: float
    purpose: str


class SetConfidenceThresholdRequest(BaseModel):
    threshold: float  # 0-100


@router.get("/")
async def get_budget():
    """Get current trading budget"""
    if budget_manager is None:
        raise HTTPException(status_code=500, detail="Budget manager not initialized")
    
    return await budget_manager.get_budget()


@router.post("/set")
async def set_budget(request: SetBudgetRequest):
    """
    Set your trading budget. 
    This is the ONLY money the AI will use - it will NEVER touch your other assets.
    """
    if budget_manager is None:
        raise HTTPException(status_code=500, detail="Budget manager not initialized")
    
    if request.amount < 0:
        raise HTTPException(status_code=400, detail="Budget cannot be negative")
    
    return await budget_manager.set_budget(
        amount=request.amount,
        enable_real_trading=request.enable_real_trading
    )


@router.post("/confidence-threshold")
async def set_confidence_threshold(request: SetConfidenceThresholdRequest):
    """
    Set the minimum AI confidence required for real trades.
    - Trades with confidence >= threshold will execute with real money
    - Trades below threshold will only be paper traded
    - Default is 70% (conservative)
    - Range: 0-100
    """
    if budget_manager is None:
        raise HTTPException(status_code=500, detail="Budget manager not initialized")
    
    if request.threshold < 0 or request.threshold > 100:
        raise HTTPException(status_code=400, detail="Threshold must be between 0 and 100")
    
    return await budget_manager.set_confidence_threshold(request.threshold)


@router.get("/confidence-check")
async def check_confidence(confidence: float):
    """
    Check if a confidence level meets the threshold for real trading.
    """
    if budget_manager is None:
        raise HTTPException(status_code=500, detail="Budget manager not initialized")
    
    return await budget_manager.check_confidence_for_trade(confidence)


@router.post("/allocate")
async def allocate_funds(request: AllocateFundsRequest):
    """Allocate funds from budget for a trade"""
    if budget_manager is None:
        raise HTTPException(status_code=500, detail="Budget manager not initialized")
    
    return await budget_manager.allocate_funds(
        amount=request.amount,
        purpose=request.purpose
    )


@router.get("/can-trade")
async def can_trade_real(amount: float):
    """Check if real trading is allowed for the specified amount"""
    if budget_manager is None:
        raise HTTPException(status_code=500, detail="Budget manager not initialized")
    
    return await budget_manager.can_trade_real(amount)


@router.get("/history")
async def get_budget_history(limit: int = 50):
    """Get budget allocation/release history"""
    if budget_manager is None:
        raise HTTPException(status_code=500, detail="Budget manager not initialized")
    
    history = await budget_manager.get_budget_history(limit=limit)
    return {"history": history, "count": len(history)}

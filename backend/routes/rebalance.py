from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional

router = APIRouter()

class TargetAllocationRequest(BaseModel):
    allocations: Dict[str, float]

class AutoRebalanceConfig(BaseModel):
    enabled: bool
    frequency: str = 'weekly'
    threshold_pct: float = 5.0

async def get_rebalancer():
    from server import db
    from services.portfolio_rebalancer import PortfolioRebalancer
    return PortfolioRebalancer(db)

@router.get("/target/{user_id}")
async def get_target_allocation(
    user_id: str,
    rebalancer = Depends(get_rebalancer)
):
    """Get target portfolio allocation"""
    try:
        return await rebalancer.get_target_allocation(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/target/{user_id}")
async def set_target_allocation(
    user_id: str,
    request: TargetAllocationRequest,
    rebalancer = Depends(get_rebalancer)
):
    """Set target portfolio allocation (must sum to 100%)"""
    try:
        return await rebalancer.set_target_allocation(user_id, request.allocations)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio/{user_id}")
async def get_portfolio(
    user_id: str,
    rebalancer = Depends(get_rebalancer)
):
    """Get current portfolio holdings"""
    try:
        return await rebalancer.get_current_portfolio(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calculate/{user_id}")
async def calculate_rebalance(
    user_id: str,
    rebalancer = Depends(get_rebalancer)
):
    """Calculate trades needed to rebalance portfolio"""
    try:
        return await rebalancer.calculate_rebalance(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute/{user_id}")
async def execute_rebalance(
    user_id: str,
    mode: str = 'paper',
    rebalancer = Depends(get_rebalancer)
):
    """Execute rebalancing trades"""
    try:
        return await rebalancer.execute_rebalance(user_id, mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{user_id}")
async def get_rebalance_history(
    user_id: str,
    limit: int = 20,
    rebalancer = Depends(get_rebalancer)
):
    """Get rebalancing history"""
    try:
        history = await rebalancer.get_rebalance_history(user_id, limit)
        return {"history": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/auto-config/{user_id}")
async def get_auto_rebalance_config(
    user_id: str,
    rebalancer = Depends(get_rebalancer)
):
    """Get auto-rebalance configuration"""
    try:
        return await rebalancer.get_auto_rebalance_config(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto-config/{user_id}")
async def set_auto_rebalance_config(
    user_id: str,
    config: AutoRebalanceConfig,
    rebalancer = Depends(get_rebalancer)
):
    """Configure automatic rebalancing"""
    try:
        return await rebalancer.set_auto_rebalance(
            user_id,
            config.enabled,
            config.frequency,
            config.threshold_pct
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

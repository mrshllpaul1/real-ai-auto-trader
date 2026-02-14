from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()

class RiskSettingsUpdate(BaseModel):
    max_investment_per_trade: float
    stop_loss_percentage: float
    take_profit_percentage: float
    max_daily_trades: int
    max_portfolio_allocation: float
    risk_level: str

async def get_risk_manager():
    from services.risk_manager import RiskManager
    from server import db
    return RiskManager(db)

@router.get("/settings/{user_id}")
async def get_risk_settings(
    user_id: str,
    risk_manager = Depends(get_risk_manager)
):
    """Get risk management settings for a user"""
    try:
        settings = await risk_manager.get_risk_settings(user_id)
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.put("/settings/{user_id}")
async def update_risk_settings(
    user_id: str,
    settings: RiskSettingsUpdate,
    risk_manager = Depends(get_risk_manager)
):
    """Update risk management settings"""
    try:
        updated_settings = await risk_manager.update_risk_settings(
            user_id,
            settings.model_dump()
        )
        return updated_settings
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")
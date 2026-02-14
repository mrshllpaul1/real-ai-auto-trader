from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter()

class BacktestRequest(BaseModel):
    strategy: Dict[str, Any]
    coins: List[str] = ['bitcoin', 'ethereum', 'solana']
    days: int = 365
    initial_capital: float = 10000

class CompareStrategiesRequest(BaseModel):
    strategies: List[Dict[str, Any]]
    coins: List[str] = ['bitcoin', 'ethereum', 'solana']
    days: int = 365

async def get_backtester():
    from server import db
    from services.backtesting import BacktestingEngine
    return BacktestingEngine(db)

@router.post("/run")
async def run_backtest(
    request: BacktestRequest,
    backtester = Depends(get_backtester)
):
    """
    Run a backtest with specified strategy
    
    Strategy parameters:
    - min_score: Minimum signal score to trade (default: 50)
    - position_size_pct: % of capital per trade (default: 10)
    - stop_loss_pct: Stop loss % (default: 10)
    - take_profit_pct: Take profit % (default: 30)
    - max_positions: Max concurrent positions (default: 3)
    """
    try:
        result = await backtester.run_backtest(
            request.strategy,
            request.coins,
            request.days,
            request.initial_capital
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.post("/compare")
async def compare_strategies(
    request: CompareStrategiesRequest,
    backtester = Depends(get_backtester)
):
    """Compare multiple strategies side by side"""
    try:
        result = await backtester.compare_strategies(
            request.strategies,
            request.coins,
            request.days
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.get("/history")
async def get_backtest_history(
    limit: int = 20,
    backtester = Depends(get_backtester)
):
    """Get recent backtest results"""
    try:
        return await backtester.get_backtest_history(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.get("/presets")
async def get_strategy_presets():
    """Get preset strategy configurations"""
    return {
        "presets": [
            {
                "name": "Conservative",
                "description": "Low risk, steady gains",
                "strategy": {
                    "min_score": 70,
                    "position_size_pct": 5,
                    "stop_loss_pct": 5,
                    "take_profit_pct": 15,
                    "max_positions": 2
                }
            },
            {
                "name": "Balanced",
                "description": "Moderate risk/reward",
                "strategy": {
                    "min_score": 50,
                    "position_size_pct": 10,
                    "stop_loss_pct": 10,
                    "take_profit_pct": 30,
                    "max_positions": 3
                }
            },
            {
                "name": "Aggressive",
                "description": "High risk, high reward",
                "strategy": {
                    "min_score": 40,
                    "position_size_pct": 20,
                    "stop_loss_pct": 15,
                    "take_profit_pct": 50,
                    "max_positions": 5
                }
            },
            {
                "name": "Hidden Gems Hunter",
                "description": "Focus on 10x opportunities",
                "strategy": {
                    "min_score": 60,
                    "position_size_pct": 15,
                    "stop_loss_pct": 20,
                    "take_profit_pct": 100,
                    "max_positions": 4
                }
            }
        ]
    }

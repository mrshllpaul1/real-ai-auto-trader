"""
Adaptive Strategy API Routes
Real-time strategy adaptation endpoints for the trading system.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/strategy", tags=["Adaptive Strategy"])

# Global references
db = None
adaptive_strategy = None


def set_dependencies(database, strategy_engine):
    """Set dependencies from main app"""
    global db, adaptive_strategy
    db = database
    adaptive_strategy = strategy_engine


class AdaptationRequest(BaseModel):
    trigger_type: str  # flash_crash, major_news, exchange_issue, performance_drop, opportunity
    data: Optional[dict] = None


class PositionSizeRequest(BaseModel):
    coin_id: str
    ai_confidence: float
    portfolio_value: float
    current_exposure: float = 0


class ExitCheckRequest(BaseModel):
    coin_id: str
    entry_price: float
    current_price: float
    current_confidence: float
    position_age_hours: float


class EntrySignalRequest(BaseModel):
    coin_id: str
    ai_confidence: float
    technical_signal: str  # BUY, SELL, HOLD
    news_sentiment: str = "neutral"


class ParamUpdateRequest(BaseModel):
    param_name: str
    new_value: float


@router.get("/status")
async def get_strategy_status():
    """
    Get current adaptive strategy status.
    
    Returns:
    - Current market regime
    - Risk mode
    - Adapted parameters vs base
    - Recent adaptations
    - Regime history
    """
    if not adaptive_strategy:
        raise HTTPException(status_code=503, detail="Adaptive strategy not initialized")
    
    return await adaptive_strategy.get_strategy_status()


@router.post("/detect-regime")
async def detect_market_regime():
    """
    Detect current market regime based on BTC and market conditions.
    
    Possible regimes:
    - strong_bull: >20% monthly gain, low volatility
    - bull: 5-20% monthly gain
    - sideways: -5% to +5%
    - bear: -20% to -5%
    - strong_bear: <-20% loss
    - high_volatility: >30% swings
    - accumulation: Low volatility, range-bound
    """
    if not adaptive_strategy:
        raise HTTPException(status_code=503, detail="Adaptive strategy not initialized")
    
    regime = await adaptive_strategy.detect_market_regime()
    
    return {
        "regime": regime.value,
        "detected_at": datetime.utcnow().isoformat(),
        "description": {
            "strong_bull": "Strong uptrend - aggressive positions recommended",
            "bull": "Uptrend - normal long positions",
            "sideways": "Range-bound - reduce position sizes",
            "bear": "Downtrend - defensive positions",
            "strong_bear": "Strong downtrend - minimal exposure",
            "high_volatility": "High volatility - wider stops, smaller positions",
            "accumulation": "Accumulation phase - good entry opportunities"
        }.get(regime.value, "Unknown regime")
    }


@router.post("/adapt")
async def adapt_strategy(performance_data: Optional[dict] = None):
    """
    Adapt strategy based on current market regime and performance.
    
    Optional performance_data:
    - recent_accuracy: float (0-100)
    - win_rate: float (0-100)
    
    Returns adapted parameters and changes from base.
    """
    if not adaptive_strategy:
        raise HTTPException(status_code=503, detail="Adaptive strategy not initialized")
    
    result = await adaptive_strategy.adapt_strategy(performance_data=performance_data)
    return result


@router.post("/emergency-adapt")
async def emergency_adaptation(request: AdaptationRequest):
    """
    Trigger emergency strategy adaptation.
    
    Trigger types:
    - flash_crash: Immediate defensive mode
    - major_news: Wait for dust to settle
    - exchange_issue: Reduce exchange risk
    - performance_drop: Conservative mode
    - opportunity: Increase exposure
    """
    if not adaptive_strategy:
        raise HTTPException(status_code=503, detail="Adaptive strategy not initialized")
    
    valid_triggers = ["flash_crash", "major_news", "exchange_issue", "performance_drop", "opportunity"]
    if request.trigger_type not in valid_triggers:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid trigger type. Must be one of: {valid_triggers}"
        )
    
    result = await adaptive_strategy.trigger_emergency_adaptation(
        request.trigger_type, 
        request.data
    )
    return result


@router.post("/position-size")
async def calculate_position_size(request: PositionSizeRequest):
    """
    Calculate dynamic position size based on:
    - AI confidence
    - Current market regime
    - Portfolio value
    - Current exposure
    
    Returns recommended position size with stop-loss and take-profit levels.
    """
    if not adaptive_strategy:
        raise HTTPException(status_code=503, detail="Adaptive strategy not initialized")
    
    result = await adaptive_strategy.get_dynamic_position_size(
        request.coin_id,
        request.ai_confidence,
        request.portfolio_value,
        request.current_exposure
    )
    return result


@router.post("/check-exit")
async def check_exit_signal(request: ExitCheckRequest):
    """
    Check if a position should be exited based on adaptive rules.
    
    Checks:
    - Stop loss
    - Take profit
    - Trailing stop
    - Confidence drop
    - Regime change
    - Position age
    """
    if not adaptive_strategy:
        raise HTTPException(status_code=503, detail="Adaptive strategy not initialized")
    
    result = await adaptive_strategy.should_exit_position(
        request.coin_id,
        request.entry_price,
        request.current_price,
        request.current_confidence,
        request.position_age_hours
    )
    return result


@router.post("/entry-signal")
async def get_entry_signal(request: EntrySignalRequest):
    """
    Generate entry signal combining:
    - AI confidence
    - Technical analysis
    - News sentiment
    - Market regime
    
    Returns whether to enter and recommended position parameters.
    """
    if not adaptive_strategy:
        raise HTTPException(status_code=503, detail="Adaptive strategy not initialized")
    
    result = await adaptive_strategy.get_entry_signal(
        request.coin_id,
        request.ai_confidence,
        request.technical_signal,
        request.news_sentiment
    )
    return result


@router.post("/reset")
async def reset_strategy():
    """
    Reset strategy to base parameters.
    Use this to clear all adaptations and start fresh.
    """
    if not adaptive_strategy:
        raise HTTPException(status_code=503, detail="Adaptive strategy not initialized")
    
    result = await adaptive_strategy.reset_to_base()
    return result


@router.get("/params")
async def get_current_params():
    """Get current adapted parameters"""
    if not adaptive_strategy:
        raise HTTPException(status_code=503, detail="Adaptive strategy not initialized")
    
    return {
        "base_params": adaptive_strategy.base_params,
        "adapted_params": adaptive_strategy.adapted_params,
        "current_regime": adaptive_strategy.current_regime.value,
        "risk_mode": adaptive_strategy.current_risk_mode.value
    }


@router.put("/params/{param_name}")
async def update_param(param_name: str, request: ParamUpdateRequest):
    """
    Manually update a strategy parameter.
    
    Available parameters:
    - max_position_pct
    - min_position_pct
    - max_total_exposure
    - stop_loss_pct
    - take_profit_pct
    - trailing_stop_pct
    - min_confidence
    - exit_confidence
    - rebalance_hours
    - emergency_rebalance_drop
    """
    if not adaptive_strategy:
        raise HTTPException(status_code=503, detail="Adaptive strategy not initialized")
    
    if param_name not in adaptive_strategy.base_params:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown parameter: {param_name}. Available: {list(adaptive_strategy.base_params.keys())}"
        )
    
    old_value = adaptive_strategy.adapted_params.get(param_name)
    adaptive_strategy.adapted_params[param_name] = request.new_value
    
    # Log the manual change
    if db:
        await db.strategy_adaptations.insert_one({
            'timestamp': datetime.utcnow(),
            'action': 'manual_update',
            'param_name': param_name,
            'old_value': old_value,
            'new_value': request.new_value
        })
    
    return {
        "status": "updated",
        "param": param_name,
        "old_value": old_value,
        "new_value": request.new_value
    }


@router.get("/adaptation-history")
async def get_adaptation_history(limit: int = 20):
    """Get history of strategy adaptations"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    history = await db.strategy_adaptations.find(
        {}, {'_id': 0}
    ).sort('timestamp', -1).limit(limit).to_list(limit)
    
    return {
        "count": len(history),
        "history": history
    }


@router.get("/regime-history")
async def get_regime_history(limit: int = 50):
    """Get history of detected market regimes"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    history = await db.regime_detections.find(
        {}, {'_id': 0}
    ).sort('timestamp', -1).limit(limit).to_list(limit)
    
    return {
        "count": len(history),
        "history": history
    }

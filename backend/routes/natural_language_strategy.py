"""Natural Language Strategy Builder API

Allows users to create trading strategies using plain English.
Powered by Venice.ai with DeepSeek R1 model.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nl-strategy", tags=["Natural Language Strategy"])

# In-memory storage for strategies (would be MongoDB in production)
_strategies: Dict[str, Dict] = {}
_examples: List[Dict] = [
    {
        "input": "Buy BTC when RSI goes below 30 and sell when it goes above 70",
        "description": "Classic RSI oversold/overbought strategy"
    },
    {
        "input": "Enter long on ETH when MACD crosses above signal line with 5% stop loss",
        "description": "MACD crossover momentum strategy"
    },
    {
        "input": "DCA into BTC weekly when Fear & Greed Index is below 25",
        "description": "Fear-based accumulation strategy"
    },
    {
        "input": "Buy SOL when price breaks above 20-day SMA with volume spike, take profit at 15%",
        "description": "Breakout strategy with volume confirmation"
    }
]


class StrategyRequest(BaseModel):
    """Request to create a strategy from natural language."""
    input: str = Field(..., description="Natural language description of the strategy", min_length=10)
    coins: Optional[List[str]] = Field(default=None, description="Specific coins to apply strategy to")
    backtest: Optional[bool] = Field(default=False, description="Whether to run backtest after creation")


class StrategyResponse(BaseModel):
    """Response containing parsed strategy."""
    strategy_id: str
    status: str
    strategy: Optional[Dict] = None
    error: Optional[str] = None
    suggestions: Optional[List[str]] = None


@router.get("/examples")
async def get_strategy_examples():
    """Get example natural language strategy inputs."""
    return {
        "examples": _examples,
        "tips": [
            "Be specific about entry and exit conditions",
            "Include risk management (stop loss, take profit)",
            "Specify the timeframe (1h, 4h, 1d)",
            "Mention which coins the strategy applies to",
            "You can reference indicators like RSI, MACD, SMA, EMA, Volume, Fear & Greed"
        ],
        "available_indicators": [
            {"name": "RSI", "description": "Relative Strength Index (0-100)"},
            {"name": "MACD", "description": "Moving Average Convergence Divergence"},
            {"name": "SMA", "description": "Simple Moving Average"},
            {"name": "EMA", "description": "Exponential Moving Average"},
            {"name": "BB", "description": "Bollinger Bands (upper, middle, lower)"},
            {"name": "Volume", "description": "Trading volume"},
            {"name": "ATR", "description": "Average True Range (volatility)"},
            {"name": "FEAR_GREED", "description": "Fear & Greed Index (0-100)"}
        ]
    }


@router.post("/parse", response_model=StrategyResponse)
async def parse_strategy(request: StrategyRequest):
    """Parse natural language into a trading strategy."""
    try:
        from services.venice_llm import get_venice_llm
        
        llm = get_venice_llm()
        if llm is None:
            # Fallback to rule-based parsing
            return await _fallback_parse(request)
        
        result = await llm.parse_natural_language_strategy(request.input)
        
        if result.get("success"):
            strategy = result["strategy"]
            strategy_id = str(uuid.uuid4())
            
            # Override coins if specified in request
            if request.coins:
                strategy["coins"] = request.coins
            
            # Store strategy
            _strategies[strategy_id] = {
                **strategy,
                "id": strategy_id,
                "status": "parsed",
                "created_at": datetime.utcnow().isoformat()
            }
            
            return StrategyResponse(
                strategy_id=strategy_id,
                status="success",
                strategy=_strategies[strategy_id],
                suggestions=_generate_suggestions(strategy)
            )
        else:
            return StrategyResponse(
                strategy_id="",
                status="error",
                error=result.get("error", "Failed to parse strategy"),
                suggestions=[
                    "Try being more specific about entry conditions",
                    "Include specific indicator values (e.g., 'RSI below 30')",
                    "Specify stop loss and take profit percentages"
                ]
            )
            
    except Exception as e:
        logger.error(f"Strategy parsing error: {e}")
        return await _fallback_parse(request)


async def _fallback_parse(request: StrategyRequest) -> StrategyResponse:
    """Fallback rule-based strategy parser."""
    input_lower = request.input.lower()
    strategy_id = str(uuid.uuid4())
    
    # Basic rule-based parsing
    strategy = {
        "strategy_name": "Custom Strategy",
        "description": request.input,
        "entry_conditions": [],
        "exit_conditions": [],
        "risk_management": {
            "stop_loss_percent": 5,
            "take_profit_percent": 15,
            "position_size_percent": 10
        },
        "coins": request.coins or ["BTC"],
        "timeframe": "1h",
        "confidence": 0.5,
        "parsed_by": "fallback"
    }
    
    # Detect RSI conditions
    if "rsi" in input_lower:
        if "below" in input_lower or "under" in input_lower:
            strategy["entry_conditions"].append({
                "indicator": "RSI",
                "operator": "<",
                "value": 30,
                "timeframe": "1h"
            })
        if "above" in input_lower or "over" in input_lower:
            strategy["exit_conditions"].append({
                "indicator": "RSI",
                "operator": ">",
                "value": 70,
                "timeframe": "1h"
            })
    
    # Detect MACD conditions
    if "macd" in input_lower:
        if "cross" in input_lower:
            strategy["entry_conditions"].append({
                "indicator": "MACD",
                "operator": "crosses_above",
                "value": "MACD_SIGNAL",
                "timeframe": "1h"
            })
    
    # Detect stop loss
    import re
    stop_match = re.search(r'stop[- ]?loss[^0-9]*(\d+)', input_lower)
    if stop_match:
        strategy["risk_management"]["stop_loss_percent"] = int(stop_match.group(1))
    
    # Detect take profit
    tp_match = re.search(r'take[- ]?profit[^0-9]*(\d+)', input_lower)
    if tp_match:
        strategy["risk_management"]["take_profit_percent"] = int(tp_match.group(1))
    
    # Detect coins
    coins = []
    for coin in ["BTC", "ETH", "SOL", "XRP", "ADA", "DOT", "LINK", "AVAX", "MATIC"]:
        if coin.lower() in input_lower or coin in request.input:
            coins.append(coin)
    if coins:
        strategy["coins"] = coins
    
    _strategies[strategy_id] = {
        **strategy,
        "id": strategy_id,
        "status": "parsed",
        "created_at": datetime.utcnow().isoformat()
    }
    
    return StrategyResponse(
        strategy_id=strategy_id,
        status="success",
        strategy=_strategies[strategy_id],
        suggestions=[
            "Strategy parsed with basic rules. For better results, ensure Venice AI is configured.",
            "Review and adjust the parsed conditions before activating."
        ]
    )


def _generate_suggestions(strategy: Dict) -> List[str]:
    """Generate improvement suggestions for a strategy."""
    suggestions = []
    
    if not strategy.get("entry_conditions"):
        suggestions.append("Consider adding specific entry conditions")
    
    if not strategy.get("exit_conditions"):
        suggestions.append("Consider adding exit conditions to lock in profits")
    
    risk = strategy.get("risk_management", {})
    if risk.get("stop_loss_percent", 0) > 10:
        suggestions.append("Stop loss is quite wide. Consider tightening for better risk management.")
    
    if risk.get("position_size_percent", 0) > 20:
        suggestions.append("Position size is aggressive. Consider reducing for diversification.")
    
    if strategy.get("confidence", 1) < 0.7:
        suggestions.append("AI confidence is low. Review parsed conditions for accuracy.")
    
    if not suggestions:
        suggestions.append("Strategy looks well-defined! Consider backtesting before going live.")
    
    return suggestions


@router.get("/list")
async def list_strategies():
    """List all saved strategies."""
    return {
        "strategies": list(_strategies.values()),
        "total": len(_strategies)
    }


@router.get("/{strategy_id}")
async def get_strategy(strategy_id: str):
    """Get a specific strategy by ID."""
    if strategy_id not in _strategies:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return _strategies[strategy_id]


@router.post("/{strategy_id}/activate")
async def activate_strategy(strategy_id: str):
    """Activate a strategy for live trading."""
    if strategy_id not in _strategies:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    _strategies[strategy_id]["status"] = "active"
    _strategies[strategy_id]["activated_at"] = datetime.utcnow().isoformat()
    
    return {
        "message": "Strategy activated",
        "strategy": _strategies[strategy_id]
    }


@router.post("/{strategy_id}/deactivate")
async def deactivate_strategy(strategy_id: str):
    """Deactivate a strategy."""
    if strategy_id not in _strategies:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    _strategies[strategy_id]["status"] = "inactive"
    _strategies[strategy_id]["deactivated_at"] = datetime.utcnow().isoformat()
    
    return {
        "message": "Strategy deactivated",
        "strategy": _strategies[strategy_id]
    }


@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: str):
    """Delete a strategy."""
    if strategy_id not in _strategies:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    del _strategies[strategy_id]
    return {"message": "Strategy deleted", "strategy_id": strategy_id}


@router.post("/validate")
async def validate_strategy(strategy: Dict):
    """Validate a strategy configuration."""
    errors = []
    warnings = []
    
    # Check required fields
    if not strategy.get("entry_conditions"):
        errors.append("Entry conditions are required")
    
    if not strategy.get("coins"):
        warnings.append("No coins specified, will apply to all supported coins")
    
    risk = strategy.get("risk_management", {})
    if not risk.get("stop_loss_percent"):
        warnings.append("No stop loss defined - high risk")
    
    if risk.get("position_size_percent", 0) > 50:
        errors.append("Position size cannot exceed 50%")
    
    # Validate indicators
    valid_indicators = ["RSI", "MACD", "MACD_SIGNAL", "SMA", "EMA", "BB_UPPER", "BB_LOWER", "VOLUME", "PRICE", "ATR", "FEAR_GREED_INDEX"]
    for condition in strategy.get("entry_conditions", []) + strategy.get("exit_conditions", []):
        if condition.get("indicator") not in valid_indicators:
            warnings.append(f"Unknown indicator: {condition.get('indicator')}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "strategy": strategy
    }

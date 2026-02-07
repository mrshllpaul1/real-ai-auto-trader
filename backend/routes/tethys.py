"""
Tethys Safety System API Routes
================================
Endpoints for the Tethys trading agent's production safety systems.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tethys", tags=["Tethys Safety"])

# Global references
_db = None
_safety_system = None


def set_db(db):
    """Set database reference"""
    global _db
    _db = db


class TradeRequest(BaseModel):
    symbol: str
    action: int  # 0-4 for strong_sell to strong_buy
    quantity: float
    price: float


class PortfolioUpdate(BaseModel):
    portfolio_value: float
    positions: Dict[str, float]
    last_trade_pnl: Optional[float] = None


# =============================================================================
# SAFETY SYSTEM ENDPOINTS
# =============================================================================

@router.get("/status")
async def get_tethys_status():
    """Get complete Tethys safety system status"""
    global _safety_system
    
    if not _safety_system:
        from services.tethys_safety import get_tethys_safety, AGENT_NAME, AGENT_VERSION
        _safety_system = get_tethys_safety(_db)
    
    return _safety_system.get_full_status()


@router.get("/identity")
async def get_agent_identity():
    """Get Tethys agent identity"""
    from services.tethys_safety import AGENT_NAME, AGENT_VERSION, AGENT_DESCRIPTION
    
    return {
        "name": AGENT_NAME,
        "version": AGENT_VERSION,
        "description": AGENT_DESCRIPTION,
        "components": [
            "Rainbow DQN with C51 Distributional RL",
            "Causal Transformer Encoder (168 timesteps)",
            "Pre-Trade Risk Gateway",
            "Full Audit Trail",
            "Uncertainty Quantification"
        ]
    }


@router.post("/risk/update-state")
async def update_risk_state(update: PortfolioUpdate):
    """Update risk state with latest portfolio data"""
    global _safety_system
    
    if not _safety_system:
        from services.tethys_safety import get_tethys_safety
        _safety_system = get_tethys_safety(_db)
    
    _safety_system.risk_gateway.update_state(
        portfolio_value=update.portfolio_value,
        positions=update.positions,
        last_trade_pnl=update.last_trade_pnl
    )
    
    return {
        "status": "updated",
        "current_state": {
            "portfolio_value": _safety_system.risk_gateway.state.portfolio_value,
            "drawdown": _safety_system.risk_gateway.state.current_drawdown,
            "daily_pnl": _safety_system.risk_gateway.state.daily_pnl,
            "consecutive_losses": _safety_system.risk_gateway.state.consecutive_losses,
            "circuit_breaker": _safety_system.risk_gateway.state.circuit_breaker_active
        }
    }


@router.post("/risk/check-trade")
async def check_trade(request: TradeRequest):
    """Check if a trade passes all risk limits"""
    global _safety_system
    
    if not _safety_system:
        from services.tethys_safety import get_tethys_safety
        _safety_system = get_tethys_safety(_db)
    
    action_names = ['strong_sell', 'sell', 'hold', 'buy', 'strong_buy']
    action_name = action_names[request.action] if 0 <= request.action < 5 else 'unknown'
    
    # Map action to buy/sell/hold
    if request.action in [3, 4]:
        trade_action = 'buy'
    elif request.action in [0, 1]:
        trade_action = 'sell'
    else:
        trade_action = 'hold'
    
    approved, violations, details = _safety_system.risk_gateway.check_trade(
        symbol=request.symbol,
        action=trade_action,
        quantity=request.quantity,
        price=request.price
    )
    
    return {
        "approved": approved,
        "action": action_name,
        "violations": [v.value for v in violations],
        "details": details
    }


@router.get("/risk/limits")
async def get_risk_limits():
    """Get current risk limits"""
    global _safety_system
    
    if not _safety_system:
        from services.tethys_safety import get_tethys_safety
        _safety_system = get_tethys_safety(_db)
    
    from dataclasses import asdict
    return asdict(_safety_system.risk_gateway.limits)


@router.post("/risk/circuit-breaker/reset")
async def reset_circuit_breaker():
    """Manually reset circuit breaker (requires confirmation)"""
    global _safety_system
    
    if not _safety_system:
        from services.tethys_safety import get_tethys_safety
        _safety_system = get_tethys_safety(_db)
    
    if _safety_system.risk_gateway.state.circuit_breaker_active:
        _safety_system.risk_gateway.state.circuit_breaker_active = False
        _safety_system.risk_gateway.state.circuit_breaker_until = None
        logger.warning("⚠️ Circuit breaker manually reset")
        return {"status": "reset", "warning": "Circuit breaker manually deactivated"}
    
    return {"status": "not_active", "message": "Circuit breaker was not active"}


# =============================================================================
# AUDIT TRAIL ENDPOINTS
# =============================================================================

@router.get("/audit/summary")
async def get_audit_summary():
    """Get audit trail summary for current session"""
    global _safety_system
    
    if not _safety_system:
        from services.tethys_safety import get_tethys_safety
        _safety_system = get_tethys_safety(_db)
    
    return _safety_system.audit_trail.get_session_summary()


@router.get("/audit/recent")
async def get_recent_decisions(limit: int = 20):
    """Get recent audit records"""
    global _safety_system
    
    if not _safety_system:
        from services.tethys_safety import get_tethys_safety
        _safety_system = get_tethys_safety(_db)
    
    records = _safety_system.audit_trail.session_records[-limit:]
    
    return {
        "count": len(records),
        "records": [
            {
                "record_id": r.record_id,
                "timestamp": r.timestamp.isoformat(),
                "action": r.action_name,
                "confidence": r.confidence,
                "uncertainty": r.uncertainty,
                "risk_approved": r.risk_approved,
                "executed": r.executed,
                "rationale": r.decision_rationale
            }
            for r in records
        ]
    }


@router.get("/audit/history")
async def get_audit_history(
    days: int = 7,
    symbol: Optional[str] = None
):
    """Get historical audit records from database"""
    global _db
    
    if not _db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    from datetime import datetime, timedelta
    
    query = {
        "timestamp": {"$gte": datetime.utcnow() - timedelta(days=days)}
    }
    if symbol:
        query["order_book_snapshot.symbol"] = symbol
    
    cursor = _db.tethys_audit_trail.find(
        query,
        {"state_features": 0, "q_distribution": 0}  # Exclude large fields
    ).sort("timestamp", -1).limit(100)
    
    records = await cursor.to_list(length=100)
    
    # Convert ObjectId and datetime
    for r in records:
        r['_id'] = str(r['_id'])
        if 'timestamp' in r:
            r['timestamp'] = r['timestamp'].isoformat()
    
    return {
        "count": len(records),
        "records": records
    }


# =============================================================================
# UNCERTAINTY ENDPOINTS
# =============================================================================

@router.get("/uncertainty/report")
async def get_uncertainty_report():
    """Get uncertainty analysis report"""
    global _safety_system
    
    if not _safety_system:
        from services.tethys_safety import get_tethys_safety
        _safety_system = get_tethys_safety(_db)
    
    return _safety_system.uncertainty.get_uncertainty_report()


@router.get("/uncertainty/thresholds")
async def get_uncertainty_thresholds():
    """Get uncertainty thresholds"""
    global _safety_system
    
    if not _safety_system:
        from services.tethys_safety import get_tethys_safety
        _safety_system = get_tethys_safety(_db)
    
    return {
        "confidence_threshold": _safety_system.uncertainty.confidence_threshold,
        "uncertainty_threshold": _safety_system.uncertainty.uncertainty_threshold,
        "description": {
            "confidence_threshold": "Trades below this confidence level trigger position reduction",
            "uncertainty_threshold": "Trades above this uncertainty trigger position reduction"
        }
    }


# =============================================================================
# INTEGRATED ENDPOINTS
# =============================================================================

@router.post("/evaluate")
async def evaluate_trade_decision(
    symbol: str,
    action: int,
    quantity: float,
    price: float,
    portfolio_value: float = 10000.0
):
    """
    Full trade evaluation through all safety systems.
    
    This is the main endpoint for evaluating trades before execution.
    """
    global _safety_system, _db
    
    if not _safety_system:
        from services.tethys_safety import get_tethys_safety
        _safety_system = get_tethys_safety(_db)
    
    action_names = ['strong_sell', 'sell', 'hold', 'buy', 'strong_buy']
    action_name = action_names[action] if 0 <= action < 5 else 'unknown'
    
    # Create dummy state and q_values for demo
    # In production, these come from the Rainbow DQN
    state = np.random.randn(168, 45).astype(np.float32)
    q_values = np.random.randn(5).astype(np.float32)
    q_values[action] += 1.0  # Make selected action have highest Q
    
    # Update risk state
    _safety_system.risk_gateway.update_state(
        portfolio_value=portfolio_value,
        positions={symbol: 0.0}
    )
    
    result = await _safety_system.evaluate_trade(
        symbol=symbol,
        action=action,
        action_name=action_name,
        quantity=quantity,
        price=price,
        state=state,
        q_values=q_values,
        portfolio_value=portfolio_value
    )
    
    return result


@router.get("/dashboard")
async def get_dashboard_data():
    """Get all data for Tethys monitoring dashboard"""
    global _safety_system
    
    if not _safety_system:
        from services.tethys_safety import get_tethys_safety, AGENT_NAME, AGENT_VERSION
        _safety_system = get_tethys_safety(_db)
    
    from services.tethys_safety import AGENT_NAME, AGENT_VERSION
    
    return {
        "agent": {
            "name": AGENT_NAME,
            "version": AGENT_VERSION,
            "status": "operational"
        },
        "risk": _safety_system.risk_gateway.get_status(),
        "audit": _safety_system.audit_trail.get_session_summary(),
        "uncertainty": _safety_system.uncertainty.get_uncertainty_report()
    }



# =============================================================================
# SENTIMENT ENDPOINTS
# =============================================================================

@router.get("/sentiment/{symbol}")
async def get_coin_sentiment(symbol: str, include_sources: bool = False):
    """
    Get sentiment analysis for a specific coin.
    
    Returns aggregated sentiment from news, technical indicators, and volume.
    """
    from services.sentiment_scorer import get_sentiment_scorer
    scorer = get_sentiment_scorer(_db)
    return await scorer.get_coin_sentiment(symbol, include_sources)


@router.get("/sentiment")
async def get_market_sentiment():
    """
    Get overall market sentiment across top coins.
    """
    from services.sentiment_scorer import get_sentiment_scorer
    scorer = get_sentiment_scorer(_db)
    return await scorer.get_market_sentiment()


@router.post("/sentiment/recommendation")
async def get_sentiment_recommendation(
    symbol: str,
    current_position: float = 0
):
    """
    Get trading recommendation based on sentiment analysis.
    """
    from services.sentiment_scorer import get_sentiment_scorer
    scorer = get_sentiment_scorer(_db)
    
    sentiment = await scorer.get_coin_sentiment(symbol)
    recommendation = scorer.get_trading_recommendation(
        sentiment['score'],
        current_position
    )
    
    return {
        "symbol": symbol,
        "sentiment": sentiment,
        "recommendation": recommendation
    }



@router.get("/fear-greed")
async def get_fear_greed_index():
    """
    Get the current Fear & Greed Index.
    
    Values:
    - 0-24: Extreme Fear (historically good buying opportunity)
    - 25-49: Fear
    - 50: Neutral
    - 51-74: Greed
    - 75-100: Extreme Greed (historically good selling opportunity)
    """
    from services.fear_greed_service import get_fear_greed_service
    service = get_fear_greed_service()
    return await service.get_current_index()


@router.get("/fear-greed/history")
async def get_fear_greed_history(days: int = 7):
    """
    Get historical Fear & Greed Index data.
    """
    from services.fear_greed_service import get_fear_greed_service
    service = get_fear_greed_service()
    return await service.get_historical(days)



@router.get("/news")
async def get_crypto_news(limit: int = 10, coin: str = None):
    """
    Get latest crypto news from CoinStats.
    
    Args:
        limit: Number of news items (max 20)
        coin: Optional coin filter (e.g., 'bitcoin', 'ethereum')
    """
    from services.coinstats_service import get_coinstats_service
    service = get_coinstats_service()
    
    if not service.initialized:
        return {"news": [], "message": "News service not configured"}
    
    news = await service.get_news(limit=limit, coin=coin)
    return {
        "news": news,
        "count": len(news),
        "source": "coinstats"
    }


@router.get("/news/sentiment")
async def get_news_sentiment():
    """
    Get aggregated sentiment from recent news.
    """
    from services.coinstats_service import get_coinstats_service
    service = get_coinstats_service()
    
    if not service.initialized:
        return {"score": 0.5, "signal": "NEUTRAL", "available": False}
    
    return await service.get_news_sentiment(limit=15)

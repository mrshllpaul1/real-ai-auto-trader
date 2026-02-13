"""
Automated Trading API Routes
Endpoints for AI-powered automated trading execution.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/auto-trade", tags=["Automated Trading"])

# Global references
db = None
automated_trader = None
alert_service = None
sentiment_analyzer = None


def set_dependencies(database, trader, alerts, sentiment):
    """Set dependencies from main app"""
    global db, automated_trader, alert_service, sentiment_analyzer
    db = database
    automated_trader = trader
    alert_service = alerts
    sentiment_analyzer = sentiment


class ExecuteRequest(BaseModel):
    paper_trade: Optional[bool] = True


@router.post("/execute-weekly")
async def execute_weekly_rebalance(request: ExecuteRequest):
    """
    Execute weekly portfolio rebalance.
    Uses AI to select 10 coins + 1 gem and executes trades.
    """
    if automated_trader is None:
        raise HTTPException(status_code=500, detail="Automated trader not initialized")
    
    result = await automated_trader.execute_weekly_rebalance(
        paper_trade=request.paper_trade
    )
    
    return result


@router.get("/active-positions")
async def get_active_positions():
    """Get all active trading positions"""
    if automated_trader is None:
        raise HTTPException(status_code=500, detail="Automated trader not initialized")
    
    positions = await automated_trader.get_active_positions()
    return {'positions': positions, 'count': len(positions)}


@router.post("/check-positions")
async def check_positions():
    """Check positions for stop-loss/take-profit triggers"""
    if automated_trader is None:
        raise HTTPException(status_code=500, detail="Automated trader not initialized")
    
    result = await automated_trader.check_positions()
    return result


@router.get("/execution-history")
async def get_execution_history(limit: int = 10):
    """Get recent execution history"""
    if automated_trader is None:
        raise HTTPException(status_code=500, detail="Automated trader not initialized")
    
    history = await automated_trader.get_execution_history(limit)
    return {'history': history}


@router.get("/performance")
async def get_performance():
    """Get overall trading performance summary"""
    if automated_trader is None:
        raise HTTPException(status_code=500, detail="Automated trader not initialized")
    
    summary = await automated_trader.get_performance_summary()
    return summary


# Alert endpoints
@router.get("/alerts")
async def get_alerts(unread_only: bool = False, limit: int = 50):
    """Get trading alerts"""
    if alert_service is None:
        raise HTTPException(status_code=500, detail="Alert service not initialized")
    
    if unread_only:
        alerts = await alert_service.get_unread_alerts(limit)
    else:
        alerts = await db.gem_alerts.find(
            {}, {'_id': 0}
        ).sort('created_at', -1).limit(limit).to_list(limit)
    
    return {'alerts': alerts, 'count': len(alerts)}


@router.post("/alerts/mark-read")
async def mark_alerts_read():
    """Mark all alerts as read"""
    if alert_service is None:
        raise HTTPException(status_code=500, detail="Alert service not initialized")
    
    await alert_service.mark_alerts_read()
    return {'success': True}


# Sentiment endpoints
@router.get("/sentiment")
async def get_market_sentiment():
    """Get market sentiment analysis"""
    if sentiment_analyzer is None:
        raise HTTPException(status_code=500, detail="Sentiment analyzer not initialized")
    
    summary = await sentiment_analyzer.get_sentiment_summary()
    return summary


@router.get("/sentiment/{symbol}")
async def get_coin_sentiment(symbol: str):
    """Get sentiment for a specific coin"""
    if sentiment_analyzer is None:
        raise HTTPException(status_code=500, detail="Sentiment analyzer not initialized")
    
    sentiment = await sentiment_analyzer.get_coin_sentiment(symbol.upper())
    return sentiment


@router.get("/early-gems")
async def get_early_gems():
    """Detect early-stage gems via social sentiment"""
    if sentiment_analyzer is None:
        raise HTTPException(status_code=500, detail="Sentiment analyzer not initialized")
    
    gems = await sentiment_analyzer.detect_early_gems()
    return {'early_gems': gems, 'count': len(gems)}

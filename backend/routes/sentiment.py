"""
AI News Sentiment Routes
Endpoints for accessing sentiment analysis across the application.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/sentiment", tags=["Sentiment Analysis"])

# Will be set by server.py
_sentiment_service = None


def set_dependencies(sentiment_service):
    """Set dependencies from server.py"""
    global _sentiment_service
    _sentiment_service = sentiment_service


class BatchSentimentRequest(BaseModel):
    coins: List[dict]  # [{'coin_id': 'bitcoin', 'symbol': 'BTC'}, ...]


@router.get("/coin/{coin_id}")
async def get_coin_sentiment(coin_id: str, symbol: Optional[str] = None):
    """
    Get AI-powered sentiment analysis for a specific coin.
    Analyzes recent news and provides bullish/bearish signals.
    """
    if not _sentiment_service:
        raise HTTPException(status_code=503, detail="Sentiment service not initialized")
    
    sentiment = await _sentiment_service.get_coin_sentiment(coin_id, symbol)
    return sentiment


@router.post("/batch")
async def get_batch_sentiment(request: BatchSentimentRequest):
    """
    Get sentiment analysis for multiple coins efficiently.
    """
    if not _sentiment_service:
        raise HTTPException(status_code=503, detail="Sentiment service not initialized")
    
    if not request.coins:
        raise HTTPException(status_code=400, detail="No coins provided")
    
    if len(request.coins) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 coins per batch")
    
    sentiments = await _sentiment_service.get_batch_sentiment(request.coins)
    return {
        "sentiments": sentiments,
        "count": len(sentiments)
    }


@router.get("/market")
async def get_market_sentiment():
    """
    Get overall crypto market sentiment based on top coins.
    Provides weighted average sentiment across BTC, ETH, BNB, SOL, XRP.
    """
    if not _sentiment_service:
        raise HTTPException(status_code=503, detail="Sentiment service not initialized")
    
    market = await _sentiment_service.get_market_sentiment()
    return market


@router.get("/history/{coin_id}")
async def get_sentiment_history(coin_id: str, days: int = 7):
    """
    Get historical sentiment data for a coin.
    """
    if not _sentiment_service:
        raise HTTPException(status_code=503, detail="Sentiment service not initialized")
    
    if days > 30:
        days = 30
    
    history = await _sentiment_service.get_sentiment_history(coin_id, days)
    return {
        "coin_id": coin_id,
        "days": days,
        "history": history,
        "count": len(history)
    }


@router.get("/trending")
async def get_trending_news(limit: int = 20):
    """
    Get trending/rising crypto news from CryptoPanic.
    Great for discovering market-moving events.
    """
    if not _sentiment_service:
        raise HTTPException(status_code=503, detail="Sentiment service not initialized")
    
    if limit > 50:
        limit = 50
    
    news = await _sentiment_service.get_trending_news(limit)
    return {
        "news": news,
        "count": len(news),
        "source": "cryptopanic"
    }


@router.get("/news/{filter_type}")
async def get_filtered_news(filter_type: str):
    """
    Get news filtered by community sentiment.
    filter_type: 'bullish' or 'bearish'
    """
    if not _sentiment_service:
        raise HTTPException(status_code=503, detail="Sentiment service not initialized")
    
    if filter_type not in ['bullish', 'bearish']:
        raise HTTPException(status_code=400, detail="filter_type must be 'bullish' or 'bearish'")
    
    result = await _sentiment_service.get_bullish_bearish_news(filter_type)
    return result

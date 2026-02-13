"""
CoinDesk API Routes
Provides endpoints for news, sentiment analysis, and market insights from CoinDesk.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/coindesk", tags=["CoinDesk News"])

# Service dependency
_coindesk_service = None

def set_dependencies(coindesk_service):
    global _coindesk_service
    _coindesk_service = coindesk_service


@router.get("/status")
async def get_coindesk_status():
    """Get CoinDesk API status and credit usage"""
    from services.coindesk_service import get_credit_status
    
    return {
        "service": "coindesk",
        "initialized": _coindesk_service is not None,
        "credits": get_credit_status(),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/news")
async def get_latest_news(
    lang: str = Query("EN", description="Language code: EN, ES, FR, TR, JP, PT"),
    limit: int = Query(20, ge=1, le=100, description="Number of articles"),
    category: Optional[str] = Query(None, description="Filter by category name")
):
    """
    Get latest cryptocurrency news from CoinDesk.
    
    Returns up to 100 articles with title, body, sentiment, and metadata.
    Results are cached for 5 minutes to conserve API credits.
    """
    if not _coindesk_service:
        raise HTTPException(status_code=503, detail="CoinDesk service not initialized")
    
    categories = [category] if category else None
    result = await _coindesk_service.get_latest_news(
        lang=lang,
        limit=limit,
        categories=categories
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.get("/news/coin/{coin_symbol}")
async def get_coin_news(
    coin_symbol: str,
    limit: int = Query(10, ge=1, le=50, description="Number of articles")
):
    """
    Get news specific to a cryptocurrency (e.g., BTC, ETH, SOL).
    
    Searches article titles, body, and keywords for coin mentions.
    """
    if not _coindesk_service:
        raise HTTPException(status_code=503, detail="CoinDesk service not initialized")
    
    result = await _coindesk_service.get_crypto_specific_news(coin_symbol, limit)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.get("/news/sentiment/{sentiment}")
async def get_news_by_sentiment(
    sentiment: str,
    limit: int = Query(10, ge=1, le=50, description="Number of articles")
):
    """
    Get news filtered by sentiment: POSITIVE, NEGATIVE, or NEUTRAL.
    
    Useful for understanding market mood and bullish/bearish narratives.
    """
    if not _coindesk_service:
        raise HTTPException(status_code=503, detail="CoinDesk service not initialized")
    
    if sentiment.upper() not in ["POSITIVE", "NEGATIVE", "NEUTRAL"]:
        raise HTTPException(status_code=400, detail="Sentiment must be POSITIVE, NEGATIVE, or NEUTRAL")
    
    result = await _coindesk_service.get_news_by_sentiment(sentiment.upper(), limit)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.get("/sentiment")
async def get_market_sentiment():
    """
    Get overall market sentiment analysis from recent news.
    
    Returns:
    - Overall sentiment (BULLISH, BEARISH, NEUTRAL)
    - Sentiment distribution percentages
    - Top trending themes
    - Number of articles analyzed
    """
    if not _coindesk_service:
        raise HTTPException(status_code=503, detail="CoinDesk service not initialized")
    
    result = await _coindesk_service.get_market_sentiment_summary()
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.get("/categories")
async def get_news_categories():
    """
    Get available news categories for filtering.
    
    Categories include: Markets, Technology, Policy, Business, etc.
    """
    if not _coindesk_service:
        raise HTTPException(status_code=503, detail="CoinDesk service not initialized")
    
    result = await _coindesk_service.get_news_categories()
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.get("/sources")
async def get_news_sources():
    """
    Get available news sources.
    
    Returns list of publishers and their IDs for filtering.
    """
    if not _coindesk_service:
        raise HTTPException(status_code=503, detail="CoinDesk service not initialized")
    
    result = await _coindesk_service.get_news_sources()
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

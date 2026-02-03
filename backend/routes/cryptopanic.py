"""
CryptoPanic News API Routes
Provides access to crypto news from CryptoPanic with fallback to free news API.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/news", tags=["Crypto News"])

# Will be set by server.py
_cryptopanic_service = None
_news_aggregator = None


def set_dependencies(cryptopanic_service, news_aggregator=None):
    """Set dependencies from server.py"""
    global _cryptopanic_service, _news_aggregator
    _cryptopanic_service = cryptopanic_service
    _news_aggregator = news_aggregator


class MultiCoinRequest(BaseModel):
    symbols: List[str]
    limit: int = 30


@router.get("/status")
async def get_service_status():
    """Check if CryptoPanic service is available and configured"""
    if not _cryptopanic_service:
        return {
            "available": False,
            "message": "CryptoPanic service not initialized"
        }
    
    return {
        "available": _cryptopanic_service.is_available,
        "message": "CryptoPanic service ready" if _cryptopanic_service.is_available else "API key not configured",
        "setup_url": "https://cryptopanic.com/developers/api/" if not _cryptopanic_service.is_available else None
    }


@router.get("/trending")
async def get_trending_news(limit: int = Query(20, le=50)):
    """
    Get trending/rising crypto news.
    These are news articles gaining traction across the crypto community.
    Falls back to free news API if CryptoPanic quota is exceeded.
    """
    # Try CryptoPanic first
    if _cryptopanic_service and _cryptopanic_service.is_available:
        news = await _cryptopanic_service.get_trending_news(limit)
        if news:
            return {
                "filter": "trending",
                "news": news,
                "count": len(news),
                "source": "cryptopanic"
            }
    
    # Fallback to free news aggregator
    if _news_aggregator:
        try:
            news = await _news_aggregator.get_free_crypto_news(limit=limit)
            return {
                "filter": "trending",
                "news": news,
                "count": len(news),
                "source": "free_crypto_news"
            }
        except Exception as e:
            print(f"Free news fallback error: {e}")
    
    return {
        "filter": "trending",
        "news": [],
        "count": 0,
        "source": "none",
        "message": "News services temporarily unavailable"
    }


@router.get("/hot")
async def get_hot_news(limit: int = Query(20, le=50)):
    """Get hot/popular crypto news"""
    if not _cryptopanic_service or not _cryptopanic_service.is_available:
        raise HTTPException(status_code=503, detail="CryptoPanic service not available")
    
    news = await _cryptopanic_service.get_hot_news(limit)
    return {
        "filter": "hot",
        "news": news,
        "count": len(news)
    }


@router.get("/bullish")
async def get_bullish_news(limit: int = Query(20, le=50)):
    """Get news with bullish community sentiment"""
    if not _cryptopanic_service or not _cryptopanic_service.is_available:
        raise HTTPException(status_code=503, detail="CryptoPanic service not available")
    
    news = await _cryptopanic_service.get_bullish_news(limit)
    return {
        "filter": "bullish",
        "news": news,
        "count": len(news)
    }


@router.get("/bearish")
async def get_bearish_news(limit: int = Query(20, le=50)):
    """Get news with bearish community sentiment"""
    if not _cryptopanic_service or not _cryptopanic_service.is_available:
        raise HTTPException(status_code=503, detail="CryptoPanic service not available")
    
    news = await _cryptopanic_service.get_bearish_news(limit)
    return {
        "filter": "bearish",
        "news": news,
        "count": len(news)
    }


@router.get("/important")
async def get_important_news(limit: int = Query(20, le=50)):
    """Get news marked as important by the community"""
    if not _cryptopanic_service or not _cryptopanic_service.is_available:
        raise HTTPException(status_code=503, detail="CryptoPanic service not available")
    
    news = await _cryptopanic_service.get_important_news(limit)
    return {
        "filter": "important",
        "news": news,
        "count": len(news)
    }


@router.get("/coin/{symbol}")
async def get_coin_news(
    symbol: str,
    filter: Optional[str] = Query("hot", regex="^(hot|rising|bullish|bearish|important)$"),
    limit: int = Query(15, le=50)
):
    """
    Get news for a specific cryptocurrency.
    
    Args:
        symbol: Currency symbol (e.g., BTC, ETH, SOL)
        filter: News filter (hot, rising, bullish, bearish, important)
        limit: Maximum number of results
    """
    if not _cryptopanic_service or not _cryptopanic_service.is_available:
        raise HTTPException(status_code=503, detail="CryptoPanic service not available")
    
    from services.cryptopanic_service import NewsFilter
    
    filter_map = {
        'hot': NewsFilter.HOT,
        'rising': NewsFilter.RISING,
        'bullish': NewsFilter.BULLISH,
        'bearish': NewsFilter.BEARISH,
        'important': NewsFilter.IMPORTANT,
    }
    
    news = await _cryptopanic_service.get_news_for_coin(
        symbol=symbol,
        filter_type=filter_map.get(filter, NewsFilter.HOT),
        limit=limit
    )
    
    return {
        "symbol": symbol.upper(),
        "filter": filter,
        "news": news,
        "count": len(news)
    }


@router.post("/coins")
async def get_multi_coin_news(request: MultiCoinRequest):
    """
    Get news for multiple cryptocurrencies, grouped by symbol.
    
    Request body:
        symbols: List of currency symbols
        limit: Total limit distributed across coins
    """
    if not _cryptopanic_service or not _cryptopanic_service.is_available:
        raise HTTPException(status_code=503, detail="CryptoPanic service not available")
    
    if len(request.symbols) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 symbols per request")
    
    news = await _cryptopanic_service.get_multi_coin_news(
        symbols=request.symbols,
        limit=request.limit
    )
    
    return {
        "symbols": [s.upper() for s in request.symbols],
        "news_by_symbol": news,
        "total_count": sum(len(n) for n in news.values())
    }


@router.get("/sentiment/{symbol}")
async def get_coin_sentiment(symbol: str):
    """
    Analyze sentiment for a specific cryptocurrency based on recent news.
    
    Returns:
        Sentiment score (0-100), label, and supporting data
    """
    if not _cryptopanic_service or not _cryptopanic_service.is_available:
        raise HTTPException(status_code=503, detail="CryptoPanic service not available")
    
    sentiment = await _cryptopanic_service.analyze_sentiment_for_coin(symbol)
    return sentiment


@router.get("/market-overview")
async def get_market_overview():
    """
    Get overall crypto market news overview.
    
    Returns:
        Market sentiment, trending topics, top currencies, and key headlines
    """
    if not _cryptopanic_service or not _cryptopanic_service.is_available:
        raise HTTPException(status_code=503, detail="CryptoPanic service not available")
    
    overview = await _cryptopanic_service.get_market_overview()
    return overview


@router.post("/clear-cache")
async def clear_cache():
    """Clear the news cache to force fresh data"""
    if not _cryptopanic_service:
        raise HTTPException(status_code=503, detail="CryptoPanic service not initialized")
    
    _cryptopanic_service.clear_cache()
    return {"message": "Cache cleared successfully"}

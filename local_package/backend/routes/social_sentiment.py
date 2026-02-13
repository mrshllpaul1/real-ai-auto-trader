"""
Social Sentiment API Routes
Endpoints for social media sentiment analysis.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/social-sentiment", tags=["Social Sentiment"])

# Global references
db = None
sentiment_scraper = None


def set_dependencies(database, scraper):
    """Set dependencies from main app"""
    global db, sentiment_scraper
    db = database
    sentiment_scraper = scraper


@router.get("/aggregated")
async def get_aggregated_sentiment():
    """
    Get aggregated sentiment from all social sources.
    
    Sources:
    - Reddit (r/cryptocurrency, r/bitcoin)
    - Fear & Greed Index
    - CryptoPanic news
    
    Returns overall market sentiment and trading recommendation.
    """
    if not sentiment_scraper:
        raise HTTPException(status_code=503, detail="Sentiment scraper not initialized")
    
    return await sentiment_scraper.get_aggregated_sentiment()


@router.get("/reddit/{subreddit}")
async def get_reddit_sentiment(subreddit: str, limit: int = 30):
    """
    Get sentiment from a specific subreddit.
    
    Popular subreddits:
    - cryptocurrency
    - bitcoin
    - ethereum
    - altcoin
    - satoshistreetbets
    """
    if not sentiment_scraper:
        raise HTTPException(status_code=503, detail="Sentiment scraper not initialized")
    
    return await sentiment_scraper.scrape_reddit(subreddit, limit)


@router.get("/fear-greed")
async def get_fear_greed_index():
    """
    Get the Fear & Greed Index.
    
    Values:
    - 0-25: Extreme Fear (potential buy)
    - 26-45: Fear (accumulate)
    - 46-55: Neutral (hold)
    - 56-75: Greed (caution)
    - 76-100: Extreme Greed (potential sell)
    """
    if not sentiment_scraper:
        raise HTTPException(status_code=503, detail="Sentiment scraper not initialized")
    
    return await sentiment_scraper.get_fear_greed_index()


@router.get("/news")
async def get_cryptopanic_news(filter: str = "hot"):
    """
    Get news sentiment from CryptoPanic.
    
    Filters: hot, rising, bullish, bearish, important
    """
    if not sentiment_scraper:
        raise HTTPException(status_code=503, detail="Sentiment scraper not initialized")
    
    return await sentiment_scraper.scrape_cryptopanic(filter)


@router.get("/coin/{coin}")
async def get_coin_sentiment(coin: str):
    """
    Get sentiment specifically for a coin.
    
    Returns Reddit sentiment and mentions.
    """
    if not sentiment_scraper:
        raise HTTPException(status_code=503, detail="Sentiment scraper not initialized")
    
    return await sentiment_scraper.get_coin_sentiment(coin)


@router.get("/history")
async def get_sentiment_history(days: int = 7):
    """Get historical sentiment data"""
    if not sentiment_scraper:
        raise HTTPException(status_code=503, detail="Sentiment scraper not initialized")
    
    return await sentiment_scraper.get_sentiment_history(days)


@router.get("/quick")
async def get_quick_sentiment():
    """
    Quick sentiment check - just Fear & Greed and key signals.
    Faster than full aggregation.
    """
    if not sentiment_scraper:
        raise HTTPException(status_code=503, detail="Sentiment scraper not initialized")
    
    fng = await sentiment_scraper.get_fear_greed_index()
    
    return {
        'fear_greed': {
            'value': fng.get('current_value', 50),
            'classification': fng.get('classification', 'Unknown'),
            'trading_signal': fng.get('trading_signal', 'hold'),
            'trend': fng.get('trend_direction', 'unknown')
        },
        'timestamp': datetime.utcnow().isoformat()
    }

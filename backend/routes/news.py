from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

router = APIRouter()

async def get_news_service():
    from services.news_service import CryptoNewsAggregator
    return CryptoNewsAggregator()

async def get_database():
    from server import db
    return db

@router.get("/all")
async def get_all_news(
    currencies: Optional[str] = None,
    limit: int = 50,
    news_service = Depends(get_news_service)
):
    """Get aggregated news from all sources"""
    try:
        currency_list = currencies.split(',') if currencies else None
        news = await news_service.get_aggregated_news(
            currencies=currency_list,
            limit_per_source=limit
        )
        
        return {
            "news": news,
            "count": len(news),
            "sources": ['cryptopanic', 'coingecko'],
            "filtered_by": currency_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sentiment/{coin_id}")
async async def analyze_coin_sentiment(
    coin_id: str,
    news_service = Depends(get_news_service)
):
    """Analyze news sentiment for a specific cryptocurrency"""
    try:
        # Get recent news
        news = await news_service.get_aggregated_news(
            currencies=[coin_id],
            limit_per_source=25
        )
        
        # Analyze sentiment
        sentiment = await news_service.analyze_news_sentiment(news, coin_id)
        
        return sentiment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-moving")
async def get_market_moving_news(
    limit: int = 10,
    news_service = Depends(get_news_service)
):
    """Get high-impact market-moving news"""
    try:
        news = await news_service.get_market_moving_news(limit)
        return {
            "news": news,
            "count": len(news),
            "impact": "high"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache-update")
async def update_news_cache(
    db = Depends(get_database),
    news_service = Depends(get_news_service)
):
    """Update cached news data"""
    try:
        # Fetch latest news
        news = await news_service.get_aggregated_news(limit_per_source=50)
        
        # Store in cache
        from datetime import datetime
        await db.news_cache.delete_many({})  # Clear old cache
        
        for item in news:
            item['cached_at'] = datetime.now().isoformat()
            await db.news_cache.insert_one(item)
        
        return {
            "message": "News cache updated",
            "items_cached": len(news)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
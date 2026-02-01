from fastapi import APIRouter, HTTPException, Depends
from typing import List

router = APIRouter()

async def get_market_service():
    from services.market_data_service import MarketDataService
    return MarketDataService()

async def get_database():
    from server import db
    return db

@router.get("/prices")
async def get_crypto_prices(
    coin_ids: str,
    market_service = Depends(get_market_service)
):
    """Get current prices for cryptocurrencies"""
    try:
        coin_list = coin_ids.split(',')
        prices = await market_service.get_coin_price(coin_list)
        return prices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/historical/{coin_id}")
async def get_historical_data(
    coin_id: str,
    days: int = 30,
    market_service = Depends(get_market_service),
    db = Depends(get_database)
):
    """Get historical price data for a cryptocurrency"""
    try:
        # Check cache first
        from datetime import datetime, timedelta
        cache_expiry = datetime.now() - timedelta(minutes=5)
        
        cached = await db.market_data_cache.find_one({
            "coin_id": coin_id,
            "days": days,
            "cached_at": {"$gte": cache_expiry.isoformat()}
        }, {"_id": 0})
        
        if cached:
            return cached['data']
        
        # Fetch fresh data
        data = await market_service.get_historical_data(coin_id, days)
        
        # Cache the data
        await db.market_data_cache.insert_one({
            "coin_id": coin_id,
            "days": days,
            "data": data,
            "cached_at": datetime.now().isoformat()
        })
        
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trending")
async def get_trending_coins(market_service = Depends(get_market_service)):
    """Get trending cryptocurrencies"""
    try:
        trending = await market_service.get_trending_coins()
        return {"trending_coins": trending}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/news")
async def get_crypto_news(market_service = Depends(get_market_service)):
    """Get latest crypto news and events"""
    try:
        news = await market_service.get_crypto_news()
        return {"news": news, "count": len(news)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
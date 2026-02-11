from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List
from middleware.response_cache import cached_response

router = APIRouter()

async def get_market_service():
    from services.market_data_service import MarketDataService
    return MarketDataService()

async def get_enhanced_market_service():
    from services.enhanced_market_service import AggregatedMarketDataService
    return AggregatedMarketDataService()

async def get_database():
    from server import db
    return db

@router.get("/prices")
@cached_response(ttl=30, key_prefix="market_prices")  # Cache for 30 seconds
async def get_crypto_prices(
    request: Request,
    coin_ids: str = "bitcoin,ethereum,solana,binancecoin,ripple",
    enhanced: bool = True,
    market_service = Depends(get_market_service),
    enhanced_service = Depends(get_enhanced_market_service)
):
    """Get current prices for cryptocurrencies from multiple sources. 
    coin_ids defaults to top 5 coins if not provided."""
    import asyncio
    try:
        coin_list = coin_ids.split(',')
        
        if enhanced:
            # Use aggregated data with timeout
            try:
                prices = await asyncio.wait_for(
                    enhanced_service.get_aggregated_prices(coin_list),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                # Fallback to simple service
                prices = await market_service.get_coin_price(coin_list)
        else:
            # Use single source (CoinGecko)
            prices = await market_service.get_coin_price(coin_list)
        
        return prices
    except Exception as e:
        # Return empty prices on error
        return {coin: {"price": 0, "error": str(e)} for coin in coin_ids.split(',')}

@router.get("/global")
@cached_response(ttl=60, key_prefix="market_global")  # Cache for 1 minute
async def get_global_metrics(
    request: Request,
    enhanced_service = Depends(get_enhanced_market_service)
):
    """Get global cryptocurrency market metrics"""
    try:
        metrics = await enhanced_service.get_comprehensive_market_data()
        return metrics
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
@cached_response(ttl=300, key_prefix="market_trending")  # Cache for 5 minutes
async def get_trending_coins(request: Request, market_service = Depends(get_market_service)):
    """Get trending cryptocurrencies"""
    try:
        trending = await market_service.get_trending_coins()
        return {"trending_coins": trending}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/news")
@cached_response(ttl=180, key_prefix="market_news")  # Cache for 3 minutes
async def get_crypto_news(request: Request, market_service = Depends(get_market_service)):
    """Get latest crypto news and events"""
    try:
        news = await market_service.get_crypto_news()
        return {"news": news, "count": len(news)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
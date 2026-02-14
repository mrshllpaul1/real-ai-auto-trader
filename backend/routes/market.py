from fastapi import APIRouter, HTTPException, Depends
from typing import List
from services.cache_manager import cached, CacheManager
import logging

logger = logging.getLogger(__name__)

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


# Fallback prices for when all sources fail
FALLBACK_PRICES = {
    "bitcoin": {"price": 0, "source": "fallback", "cached": True},
    "ethereum": {"price": 0, "source": "fallback", "cached": True},
    "solana": {"price": 0, "source": "fallback", "cached": True},
    "binancecoin": {"price": 0, "source": "fallback", "cached": True},
    "ripple": {"price": 0, "source": "fallback", "cached": True},
}


@router.get("/prices")
async def get_crypto_prices(
    coin_ids: str = "bitcoin,ethereum,solana,binancecoin,ripple",
    enhanced: bool = True,
    market_service = Depends(get_market_service),
    enhanced_service = Depends(get_enhanced_market_service)
):
    """Get current prices for cryptocurrencies from multiple sources. 
    coin_ids defaults to top 5 coins if not provided.
    Cached for 30 seconds for 10x faster repeated requests.
    Includes automatic fallback on errors."""
    import asyncio
    from services.cache_manager import get_cache_manager
    from services.error_recovery import get_error_recovery_manager, categorize_error
    
    # Use cache for repeated requests
    cache = get_cache_manager()
    cache_key = f"market_prices:{coin_ids}:{enhanced}"
    
    hit, cached_data = await cache.get(cache_key)
    if hit:
        return cached_data
    
    coin_list = coin_ids.split(',')
    
    try:
        if enhanced:
            # Use aggregated data with timeout
            try:
                prices = await asyncio.wait_for(
                    enhanced_service.get_aggregated_prices(coin_list),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                logger.warning("Enhanced market service timeout, falling back to simple service")
                # Fallback to simple service
                prices = await market_service.get_coin_price(coin_list)
        else:
            # Use single source (CoinGecko)
            prices = await market_service.get_coin_price(coin_list)
        
        # Cache for 30 seconds
        await cache.set(cache_key, prices, ttl=30)
        return prices
        
    except Exception as e:
        # Log and track error
        logger.error(f"Market prices error: {e}")
        
        try:
            error_manager = get_error_recovery_manager()
            category = categorize_error(e)
            await error_manager.handle_error(e, {
                'endpoint': '/market/prices',
                'coin_ids': coin_ids,
            })
        except:
            pass
        
        # Return fallback prices with error indication
        fallback = {
            coin: {
                "price": FALLBACK_PRICES.get(coin, {}).get("price", 0),
                "error": str(e),
                "source": "fallback"
            } 
            for coin in coin_list
        }
        return fallback

@router.get("/global")
async def get_global_metrics(
    enhanced_service = Depends(get_enhanced_market_service)
):
    """Get global cryptocurrency market metrics"""
    try:
        metrics = await enhanced_service.get_comprehensive_market_data()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

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
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.get("/trending")
async def get_trending_coins(market_service = Depends(get_market_service)):
    """Get trending cryptocurrencies"""
    try:
        trending = await market_service.get_trending_coins()
        return {"trending_coins": trending}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.get("/news")
async def get_crypto_news(market_service = Depends(get_market_service)):
    """Get latest crypto news and events"""
    try:
        news = await market_service.get_crypto_news()
        return {"news": news, "count": len(news)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")
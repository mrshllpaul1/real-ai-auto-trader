"""
Enhanced Historical Data API Routes
Provides comprehensive endpoints for historical market and news data with quality monitoring.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime, timezone, timedelta

router = APIRouter()


async def get_database():
    """Get database instance"""
    from server import db
    return db


@router.get("/ohlcv/{symbol}")
async def get_historical_ohlcv(
    symbol: str,
    quote: str = "USD",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    interval: str = "daily",
    force_refresh: bool = False,
    db = Depends(get_database)
):
    """
    Get historical OHLCV data for a cryptocurrency with unified multi-source aggregation.
    
    - **symbol**: Coin symbol (BTC, ETH, SOL, etc.)
    - **quote**: Quote currency (USD, EUR, etc.)
    - **start_date**: Start date in ISO format (default: 1 year ago)
    - **end_date**: End date in ISO format (default: now)
    - **interval**: Timeframe (daily, hourly, 4h, weekly)
    - **force_refresh**: Skip cache and fetch fresh data
    """
    try:
        from services.historical_data_manager import get_historical_data_manager
        
        # Parse dates
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start_dt = None
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end_dt = None
        
        manager = get_historical_data_manager(db)
        result = await manager.get_historical_ohlcv(
            symbol=symbol.upper(),
            quote=quote.upper(),
            start_date=start_dt,
            end_date=end_dt,
            interval=interval,
            force_refresh=force_refresh
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/{symbol}")
async def get_data_quality(
    symbol: str,
    quote: str = "USD",
    interval: str = "daily",
    db = Depends(get_database)
):
    """
    Get comprehensive quality report for historical data.
    
    - **symbol**: Coin symbol (BTC, ETH, etc.)
    - **quote**: Quote currency (USD, EUR, etc.)
    - **interval**: Timeframe (daily, hourly, etc.)
    
    Returns:
    - Data completeness metrics
    - Gap analysis
    - Quality issues breakdown
    - Source attribution
    """
    try:
        from services.historical_data_manager import get_historical_data_manager
        
        manager = get_historical_data_manager(db)
        report = await manager.get_quality_report(
            symbol=symbol.upper(),
            quote=quote.upper(),
            interval=interval
        )
        
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gaps/{symbol}")
async def get_data_gaps(
    symbol: str,
    quote: str = "USD",
    interval: str = "daily",
    db = Depends(get_database)
):
    """
    Identify gaps in historical data.
    
    - **symbol**: Coin symbol
    - **quote**: Quote currency
    - **interval**: Timeframe
    
    Returns list of missing data periods.
    """
    try:
        from services.historical_data_manager import get_historical_data_manager
        
        manager = get_historical_data_manager(db)
        gaps = await manager.get_data_gaps(
            symbol=symbol.upper(),
            quote=quote.upper(),
            interval=interval
        )
        
        return {
            "symbol": symbol,
            "quote": quote,
            "interval": interval,
            "gaps": gaps,
            "gap_count": len(gaps)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news")
async def get_news(
    coins: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sentiment: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    db = Depends(get_database)
):
    """
    Get crypto news with filtering and sentiment analysis.
    
    - **coins**: Comma-separated coin symbols (e.g., "BTC,ETH,SOL")
    - **start_date**: Filter news after this date (ISO format)
    - **end_date**: Filter news before this date (ISO format)
    - **sentiment**: Filter by sentiment ("bullish", "bearish", "neutral")
    - **limit**: Max results (1-200)
    - **skip**: Skip results for pagination
    """
    try:
        from services.news_aggregator import get_news_aggregator
        
        # Parse parameters
        coin_list = coins.split(',') if coins else None
        
        start_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        end_dt = None
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        aggregator = get_news_aggregator(db)
        result = await aggregator.get_news(
            coins=coin_list,
            start_date=start_dt,
            end_date=end_dt,
            sentiment=sentiment,
            limit=limit,
            skip=skip
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/news/fetch")
async def fetch_news(
    coins: Optional[str] = None,
    limit: int = 50,
    force_refresh: bool = False,
    db = Depends(get_database)
):
    """
    Fetch fresh news from all sources and store in database.
    
    - **coins**: Comma-separated coin symbols (default: BTC,ETH,SOL,XRP,ADA)
    - **limit**: Max news items per source
    - **force_refresh**: Force refresh even if cached
    """
    try:
        from services.news_aggregator import get_news_aggregator
        
        coin_list = coins.split(',') if coins else None
        
        aggregator = get_news_aggregator(db)
        result = await aggregator.fetch_and_store_news(
            coins=coin_list,
            limit=limit,
            force_refresh=force_refresh
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news/sentiment/{coin}")
async def get_sentiment_summary(
    coin: str,
    days: int = Query(7, ge=1, le=90),
    db = Depends(get_database)
):
    """
    Get sentiment summary for a coin over a time period.
    
    - **coin**: Coin symbol (BTC, ETH, etc.)
    - **days**: Number of days to analyze (1-90)
    
    Returns:
    - Average sentiment score
    - Sentiment distribution (bullish/bearish/neutral)
    - Recent news highlights
    """
    try:
        from services.news_aggregator import get_news_aggregator
        
        aggregator = get_news_aggregator(db)
        result = await aggregator.get_sentiment_summary(
            coin=coin.upper(),
            days=days
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/correlation/analyze/{coin}")
async def analyze_news_market_correlation(
    coin: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db = Depends(get_database)
):
    """
    Analyze correlation between news sentiment and price movements.
    
    - **coin**: Coin symbol (BTC, ETH, etc.)
    - **start_date**: Start date for analysis (default: 30 days ago)
    - **end_date**: End date for analysis (default: now)
    
    Returns:
    - Correlation coefficients for different lag periods (1h, 4h, 24h, 1 week)
    - Statistical significance
    - Insights and recommendations
    """
    try:
        from services.news_market_correlation import get_correlation_analyzer
        
        start_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        end_dt = None
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        analyzer = get_correlation_analyzer(db)
        result = await analyzer.analyze_correlation(
            coin=coin.upper(),
            start_date=start_dt,
            end_date=end_dt
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correlation/history/{coin}")
async def get_correlation_history(
    coin: str,
    limit: int = Query(10, ge=1, le=50),
    db = Depends(get_database)
):
    """
    Get historical correlation analyses for a coin.
    
    - **coin**: Coin symbol
    - **limit**: Max results (1-50)
    """
    try:
        from services.news_market_correlation import get_correlation_analyzer
        
        analyzer = get_correlation_analyzer(db)
        results = await analyzer.get_correlation_history(
            coin=coin.upper(),
            limit=limit
        )
        
        return {
            "coin": coin,
            "history": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/{coin}")
async def get_predictive_signals(
    coin: str,
    recent_hours: int = Query(24, ge=1, le=168),
    db = Depends(get_database)
):
    """
    Get current predictive trading signals based on news-price correlations.
    
    - **coin**: Coin symbol (BTC, ETH, etc.)
    - **recent_hours**: Hours of recent news to analyze (1-168)
    
    Returns:
    - Trading signal (bullish/bearish/neutral)
    - Confidence level (0-1)
    - Supporting data and reasoning
    """
    try:
        from services.news_market_correlation import get_correlation_analyzer
        
        analyzer = get_correlation_analyzer(db)
        result = await analyzer.get_predictive_signals(
            coin=coin.upper(),
            recent_hours=recent_hours
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/multi-coin")
async def get_multi_coin_data(
    symbols: str,
    quote: str = "USD",
    days: int = Query(30, ge=1, le=365),
    interval: str = "daily",
    db = Depends(get_database)
):
    """
    Get historical data for multiple coins in parallel.
    
    - **symbols**: Comma-separated coin symbols (e.g., "BTC,ETH,SOL")
    - **quote**: Quote currency
    - **days**: Number of days of history
    - **interval**: Timeframe (daily, hourly, etc.)
    """
    try:
        from services.historical_data_manager import get_historical_data_manager
        import asyncio
        
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        
        if len(symbol_list) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 coins per request"
            )
        
        manager = get_historical_data_manager(db)
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Fetch data for all coins in parallel
        tasks = []
        for symbol in symbol_list:
            task = manager.get_historical_ohlcv(
                symbol=symbol,
                quote=quote,
                start_date=start_date,
                end_date=end_date,
                interval=interval
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Format response
        data = {}
        for symbol, result in zip(symbol_list, results):
            if isinstance(result, Exception):
                data[symbol] = {"error": str(result)}
            else:
                data[symbol] = result
        
        return {
            "coins": symbol_list,
            "quote": quote,
            "interval": interval,
            "days": days,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check(db = Depends(get_database)):
    """
    Check health status of historical data system.
    
    Returns:
    - Service status
    - Data freshness metrics
    - Database connectivity
    """
    try:
        # Check database connection
        await db.command('ping')
        
        # Check data freshness for major coins
        from services.historical_data_manager import get_historical_data_manager
        manager = get_historical_data_manager(db)
        
        freshness = {}
        for coin in ["BTC", "ETH", "SOL"]:
            try:
                data = await manager.get_historical_ohlcv(coin, quote="USD", interval="daily")
                if data.get("data"):
                    latest = data["data"][-1]
                    latest_date = datetime.fromisoformat(latest["date"])
                    age_hours = (datetime.now(timezone.utc) - latest_date.replace(tzinfo=timezone.utc)).total_seconds() / 3600
                    freshness[coin] = {
                        "latest_date": latest["date"],
                        "age_hours": round(age_hours, 2),
                        "is_fresh": age_hours < 48
                    }
            except Exception as e:
                freshness[coin] = {"error": str(e)}
        
        return {
            "status": "healthy",
            "database": "connected",
            "data_freshness": freshness,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

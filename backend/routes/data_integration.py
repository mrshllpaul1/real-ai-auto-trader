"""
Enhanced Data Integration API Routes
Provides endpoints for historical sentiment tracking and enhanced market data integration.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/data-integration", tags=["Enhanced Data Integration"])

# Service dependencies (set during initialization)
_db = None
_sentiment_tracker = None
_market_integrator = None


def set_dependencies(db, sentiment_tracker, market_integrator):
    """Set service dependencies"""
    global _db, _sentiment_tracker, _market_integrator
    _db = db
    _sentiment_tracker = sentiment_tracker
    _market_integrator = market_integrator


# Request models
class SentimentStoreRequest(BaseModel):
    coin_id: str
    sentiment_data: dict
    metadata: Optional[dict] = None


class SnapshotRequest(BaseModel):
    date: Optional[str] = None


class TrendRequest(BaseModel):
    coin_id: str
    days: int = 30


class MultiCoinRequest(BaseModel):
    coin_ids: List[str]
    date: Optional[str] = None


# === HISTORICAL SENTIMENT ENDPOINTS ===

@router.get("/sentiment/status")
async def get_sentiment_service_status():
    """Get historical sentiment tracking service status"""
    if not _sentiment_tracker:
        raise HTTPException(status_code=503, detail="Sentiment tracker not initialized")
    
    stats = await _sentiment_tracker.get_storage_stats()
    
    return {
        "status": "operational",
        "service": "historical_sentiment_tracker",
        "statistics": stats
    }


@router.post("/sentiment/store")
async def store_sentiment(request: SentimentStoreRequest):
    """
    Store a sentiment reading with timestamp.
    Used to persist sentiment analysis results for historical tracking.
    """
    if not _sentiment_tracker:
        raise HTTPException(status_code=503, detail="Sentiment tracker not initialized")
    
    result = await _sentiment_tracker.store_sentiment(
        coin_id=request.coin_id,
        sentiment_data=request.sentiment_data,
        metadata=request.metadata
    )
    
    return {
        "status": "success",
        "stored_document": result
    }


@router.get("/sentiment/history/{coin_id}")
async def get_sentiment_history(
    coin_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
):
    """
    Get historical sentiment data for a specific coin.
    
    Args:
        coin_id: Cryptocurrency identifier (e.g., 'bitcoin')
        start_date: Start date in ISO format (optional)
        end_date: End date in ISO format (optional)
        limit: Maximum records to return (default: 100)
    """
    if not _sentiment_tracker:
        raise HTTPException(status_code=503, detail="Sentiment tracker not initialized")
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    history = await _sentiment_tracker.get_coin_sentiment_history(
        coin_id=coin_id,
        start_date=start,
        end_date=end,
        limit=limit
    )
    
    return {
        "coin_id": coin_id,
        "records": len(history),
        "data": history
    }


@router.post("/sentiment/snapshot/create")
async def create_daily_snapshot(request: SnapshotRequest):
    """
    Create daily sentiment snapshots for all tracked coins.
    This aggregates sentiment readings from the past 24 hours.
    
    Args:
        date: ISO date string (YYYY-MM-DD), defaults to today
    """
    if not _sentiment_tracker:
        raise HTTPException(status_code=503, detail="Sentiment tracker not initialized")
    
    result = await _sentiment_tracker.create_daily_snapshot(date=request.date)
    
    return result


@router.get("/sentiment/snapshots")
async def get_daily_snapshots(
    coin_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 365
):
    """
    Get daily sentiment snapshots.
    
    Args:
        coin_id: Filter by specific coin (optional)
        start_date: Start date in ISO format (optional)
        end_date: End date in ISO format (optional)
        limit: Maximum snapshots to return (default: 365)
    """
    if not _sentiment_tracker:
        raise HTTPException(status_code=503, detail="Sentiment tracker not initialized")
    
    snapshots = await _sentiment_tracker.get_daily_snapshots(
        coin_id=coin_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return {
        "count": len(snapshots),
        "snapshots": snapshots
    }


@router.get("/sentiment/trend/{coin_id}")
async def get_sentiment_trend(coin_id: str, days: int = 30):
    """
    Analyze sentiment trend over time for a specific coin.
    
    Args:
        coin_id: Cryptocurrency identifier
        days: Number of days to analyze (default: 30)
    
    Returns:
        Trend analysis including direction, momentum, and volatility
    """
    if not _sentiment_tracker:
        raise HTTPException(status_code=503, detail="Sentiment tracker not initialized")
    
    trend = await _sentiment_tracker.get_sentiment_trend(
        coin_id=coin_id,
        days=days
    )
    
    return trend


@router.post("/sentiment/multi-coin")
async def get_multi_coin_sentiment(request: MultiCoinRequest):
    """
    Get sentiment for multiple coins on a specific date.
    
    Args:
        coin_ids: List of coin identifiers
        date: ISO date string (defaults to latest available)
    """
    if not _sentiment_tracker:
        raise HTTPException(status_code=503, detail="Sentiment tracker not initialized")
    
    results = await _sentiment_tracker.get_multi_coin_sentiment(
        coin_ids=request.coin_ids,
        date=request.date
    )
    
    return {
        "date": request.date or "latest",
        "coins_requested": len(request.coin_ids),
        "coins_found": len(results),
        "data": results
    }


@router.post("/sentiment/cleanup")
async def cleanup_old_sentiment_data(days_to_keep: int = 90):
    """
    Remove sentiment records older than specified days.
    Daily snapshots are preserved longer.
    
    Args:
        days_to_keep: Keep records from the last N days (default: 90)
    """
    if not _sentiment_tracker:
        raise HTTPException(status_code=503, detail="Sentiment tracker not initialized")
    
    result = await _sentiment_tracker.cleanup_old_data(days_to_keep=days_to_keep)
    
    return result


# === ENHANCED MARKET DATA ENDPOINTS ===

@router.get("/market/validated-price/{coin_id}")
async def get_validated_price(coin_id: str, validate: bool = True):
    """
    Get cryptocurrency price with multi-source validation.
    
    Args:
        coin_id: Cryptocurrency identifier (e.g., 'bitcoin')
        validate: Whether to cross-validate across multiple sources (default: True)
    
    Returns:
        Validated price data with quality metrics
    """
    if not _market_integrator:
        raise HTTPException(status_code=503, detail="Market integrator not initialized")
    
    result = await _market_integrator.get_validated_price(
        coin_id=coin_id,
        validate=validate
    )
    
    if 'error' in result and 'All data sources failed' in result['error']:
        raise HTTPException(status_code=503, detail="All market data sources unavailable")
    
    return result


@router.get("/market/quality-report")
async def get_data_quality_report():
    """
    Generate comprehensive data quality report across all market data sources.
    Tests multiple coins and provides success rates, response times, and availability.
    """
    if not _market_integrator:
        raise HTTPException(status_code=503, detail="Market integrator not initialized")
    
    report = await _market_integrator.get_data_quality_report()
    
    return report


@router.get("/market/source-status")
async def get_source_status():
    """
    Get current status of all market data sources.
    Shows availability, priority, and failure counts.
    """
    if not _market_integrator:
        raise HTTPException(status_code=503, detail="Market integrator not initialized")
    
    status = _market_integrator.get_source_status()
    
    return status


@router.get("/market/news-correlation/{coin_id}")
async def analyze_news_correlation(
    coin_id: str,
    news_timestamp: str,
    lookback_hours: int = 4,
    lookahead_hours: int = 4
):
    """
    Analyze price movement correlation with news events.
    
    Args:
        coin_id: Cryptocurrency identifier
        news_timestamp: When the news was published (ISO format)
        lookback_hours: Hours to look back before news (default: 4)
        lookahead_hours: Hours to look ahead after news (default: 4)
    
    Returns:
        Correlation analysis including price impact
    """
    if not _market_integrator:
        raise HTTPException(status_code=503, detail="Market integrator not initialized")
    
    try:
        timestamp = datetime.fromisoformat(news_timestamp.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format. Use ISO format.")
    
    result = await _market_integrator.correlate_news_with_price(
        coin_id=coin_id,
        news_timestamp=timestamp,
        lookback_hours=lookback_hours,
        lookahead_hours=lookahead_hours
    )
    
    return result


# === COMBINED ANALYSIS ENDPOINTS ===

@router.get("/combined/sentiment-and-price/{coin_id}")
async def get_combined_analysis(coin_id: str):
    """
    Get combined sentiment and price analysis for a coin.
    Provides both current market data and latest sentiment.
    """
    if not _sentiment_tracker or not _market_integrator:
        raise HTTPException(status_code=503, detail="Required services not initialized")
    
    # Get validated price
    price_data = await _market_integrator.get_validated_price(
        coin_id=coin_id,
        validate=True
    )
    
    # Get latest sentiment snapshot
    snapshots = await _sentiment_tracker.get_daily_snapshots(
        coin_id=coin_id,
        limit=1
    )
    
    sentiment_data = snapshots[0] if snapshots else None
    
    # Get 7-day trend
    trend = await _sentiment_tracker.get_sentiment_trend(
        coin_id=coin_id,
        days=7
    )
    
    return {
        "coin_id": coin_id,
        "timestamp": datetime.utcnow().isoformat(),
        "market_data": price_data,
        "sentiment_data": sentiment_data,
        "sentiment_trend": trend
    }


@router.get("/health")
async def health_check():
    """Health check endpoint for the enhanced data integration service"""
    return {
        "status": "healthy",
        "service": "enhanced_data_integration",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "sentiment_tracker": _sentiment_tracker is not None,
            "market_integrator": _market_integrator is not None,
            "database": _db is not None
        }
    }

"""
Historical Media Data API Routes
=================================
Endpoints for accessing archived news, sentiment data, and media analytics.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/historical-media", tags=["Historical Media"])

# Service dependencies
_historical_media_service = None
_news_aggregator = None


def set_dependencies(historical_media_service, news_aggregator=None):
    """Set service dependencies"""
    global _historical_media_service, _news_aggregator
    _historical_media_service = historical_media_service
    _news_aggregator = news_aggregator


# Request models
class ArchiveNewsRequest(BaseModel):
    source: str = "manual"
    articles: List[dict]


class NewsQueryRequest(BaseModel):
    coin_symbol: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    sentiment: Optional[str] = None
    min_impact_score: Optional[int] = None
    limit: int = 100
    skip: int = 0


@router.get("/status")
async def get_service_status():
    """Get historical media service status"""
    if not _historical_media_service:
        return {
            "status": "not_initialized",
            "message": "Historical media service not initialized"
        }
    
    # Get statistics for last 30 days
    stats = await _historical_media_service.calculate_news_statistics(days=30)
    
    return {
        "status": "operational",
        "service": "historical_media",
        "statistics": stats,
        "features": [
            "news_archive",
            "sentiment_history",
            "correlation_analysis",
            "event_timeline"
        ]
    }


@router.post("/archive/news")
async def archive_news_batch(request: ArchiveNewsRequest):
    """
    Archive a batch of news articles for historical analysis.
    Used by scheduled jobs to persist fetched news.
    """
    if not _historical_media_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        result = await _historical_media_service.archive_news_batch(
            request.articles,
            request.source
        )
        
        return {
            "status": "success",
            "source": request.source,
            **result
        }
    except Exception as e:
        logger.error(f"Error archiving news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/archive/live-news")
async def archive_live_news(
    background_tasks: BackgroundTasks,
    sources: Optional[str] = "all",
    limit_per_source: int = 50
):
    """
    Fetch and archive latest news from all sources.
    Runs as background task.
    """
    if not _historical_media_service or not _news_aggregator:
        raise HTTPException(status_code=500, detail="Services not initialized")
    
    async def fetch_and_archive():
        try:
            # Fetch latest news
            source_list = sources.split(',') if sources != "all" else None
            news = await _news_aggregator.get_aggregated_news(
                currencies=source_list,
                limit_per_source=limit_per_source
            )
            
            # Archive each article
            result = await _historical_media_service.archive_news_batch(
                news,
                source="aggregated"
            )
            
            logger.info(f"Archived {result['new']} new articles, updated {result['updated']}")
            
        except Exception as e:
            logger.error(f"Error in background archival: {e}")
    
    background_tasks.add_task(fetch_and_archive)
    
    return {
        "status": "started",
        "message": "News archival started in background",
        "sources": sources,
        "limit_per_source": limit_per_source
    }


@router.get("/news/historical")
async def get_historical_news(
    coin: Optional[str] = None,
    days: int = 30,
    sentiment: Optional[str] = None,
    impact_min: Optional[int] = None,
    limit: int = 100,
    skip: int = 0
):
    """
    Get historical news articles with filtering.
    
    Query Parameters:
    - coin: Filter by cryptocurrency symbol (e.g., BTC, ETH)
    - days: Number of days to look back (default: 30)
    - sentiment: Filter by sentiment (positive/negative/neutral)
    - impact_min: Minimum impact score (0-100)
    - limit: Maximum results to return
    - skip: Number of results to skip (pagination)
    """
    if not _historical_media_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        articles = await _historical_media_service.get_historical_news(
            coin_symbol=coin,
            start_date=start_date,
            sentiment=sentiment,
            min_impact_score=impact_min,
            limit=limit,
            skip=skip
        )
        
        # Get total count for pagination
        total_count = await _historical_media_service.get_news_count(
            coin_symbol=coin,
            days=days
        )
        
        return {
            "articles": articles,
            "count": len(articles),
            "total_count": total_count,
            "filters": {
                "coin": coin,
                "days": days,
                "sentiment": sentiment,
                "impact_min": impact_min
            },
            "pagination": {
                "limit": limit,
                "skip": skip,
                "has_more": total_count > (skip + len(articles))
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving historical news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news/timeline/{coin_symbol}")
async def get_news_timeline(
    coin_symbol: str,
    days: int = 7
):
    """
    Get chronological news timeline for a specific cryptocurrency.
    Useful for visualizing news events alongside price charts.
    """
    if not _historical_media_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        articles = await _historical_media_service.get_historical_news(
            coin_symbol=coin_symbol,
            start_date=start_date,
            limit=1000  # Get all articles for timeline
        )
        
        # Group by date
        timeline = {}
        for article in articles:
            date_key = article['published_at'].date().isoformat() if isinstance(article['published_at'], datetime) else article['published_at'][:10]
            if date_key not in timeline:
                timeline[date_key] = []
            timeline[date_key].append({
                "title": article['title'],
                "sentiment": article['sentiment'],
                "impact": article.get('is_market_moving', False),
                "published_at": article['published_at']
            })
        
        return {
            "coin_symbol": coin_symbol.upper(),
            "days": days,
            "timeline": timeline,
            "total_events": len(articles)
        }
    except Exception as e:
        logger.error(f"Error creating timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment/timeseries/{coin_symbol}")
async def get_sentiment_timeseries(
    coin_symbol: str,
    resolution: str = "daily",
    days: int = 30
):
    """
    Get aggregated sentiment time-series data.
    
    Parameters:
    - coin_symbol: Cryptocurrency symbol
    - resolution: Time resolution (hourly/daily/weekly)
    - days: Number of days to retrieve
    """
    if not _historical_media_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    if resolution not in ['hourly', 'daily', 'weekly']:
        raise HTTPException(status_code=400, detail="Resolution must be hourly, daily, or weekly")
    
    try:
        timeseries = await _historical_media_service.get_sentiment_timeseries(
            coin_symbol=coin_symbol,
            resolution=resolution,
            days=days
        )
        
        return {
            "coin_symbol": coin_symbol.upper(),
            "resolution": resolution,
            "days": days,
            "data": timeseries,
            "count": len(timeseries)
        }
    except Exception as e:
        logger.error(f"Error retrieving sentiment timeseries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_archive_statistics(days: int = 30):
    """
    Get comprehensive statistics about archived media data.
    """
    if not _historical_media_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        stats = await _historical_media_service.calculate_news_statistics(days=days)
        
        return {
            "status": "success",
            "statistics": stats,
            "period": f"last_{days}_days"
        }
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initialize-indexes")
async def initialize_indexes():
    """
    Create database indexes for historical media collections.
    Should be run once during setup.
    """
    if not _historical_media_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        await _historical_media_service.ensure_indexes()
        
        return {
            "status": "success",
            "message": "Database indexes created successfully",
            "collections": [
                "news_archive",
                "sentiment_history",
                "news_price_correlations",
                "media_events"
            ]
        }
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news/market-moving")
async def get_market_moving_news(
    days: int = 7,
    limit: int = 50
):
    """
    Get high-impact market-moving news from archive.
    """
    if not _historical_media_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query for market-moving news
        articles = await _historical_media_service.get_historical_news(
            start_date=start_date,
            limit=limit
        )
        
        # Filter for market-moving
        market_moving = [a for a in articles if a.get('is_market_moving', False)]
        
        return {
            "articles": market_moving,
            "count": len(market_moving),
            "days": days,
            "impact_level": "high"
        }
    except Exception as e:
        logger.error(f"Error retrieving market-moving news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/news/cleanup")
async def cleanup_old_news(days_to_keep: int = 730):
    """
    Clean up news articles older than specified days (default: 2 years).
    """
    if not _historical_media_service:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        result = await _historical_media_service.news_archive.delete_many({
            "published_at": {"$lt": cutoff_date}
        })
        
        return {
            "status": "success",
            "deleted_count": result.deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "days_kept": days_to_keep
        }
    except Exception as e:
        logger.error(f"Error cleaning up news: {e}")
        raise HTTPException(status_code=500, detail=str(e))

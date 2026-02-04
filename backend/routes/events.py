"""
Events API Routes
Endpoints for event correlation, historical events database, and event detection.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import asyncio

router = APIRouter(prefix="/events", tags=["Events"])

# Dependencies
_db = None
_correlation_engine = None
_events_db = None


def set_dependencies(db, correlation_engine, events_db):
    """Set dependencies from server.py"""
    global _db, _correlation_engine, _events_db
    _db = db
    _correlation_engine = correlation_engine
    _events_db = events_db


# Request models
class CorrelationRequest(BaseModel):
    coin: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD


class DateQueryRequest(BaseModel):
    date: str  # YYYY-MM-DD
    coin: Optional[str] = None


class KeywordSearchRequest(BaseModel):
    keyword: str
    days_back: Optional[int] = 365


# ================== Correlation Engine Endpoints ==================

@router.post("/correlate")
async def correlate_events(request: CorrelationRequest):
    """
    Find price movements and correlate them with news events.
    
    Analyzes a date range to find:
    - Significant price changes (5%+ by default)
    - News articles around each price movement
    - Correlation scores to identify likely causes
    
    Example:
    {"coin": "BTC", "start_date": "2022-11-01", "end_date": "2022-11-15"}
    (This would find the FTX collapse correlation)
    """
    if not _correlation_engine:
        raise HTTPException(status_code=503, detail="Correlation engine not initialized")
    
    try:
        start = datetime.strptime(request.start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end = datetime.strptime(request.end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    result = await _correlation_engine.analyze_date_range(
        coin_symbol=request.coin,
        start_date=start,
        end_date=end
    )
    
    return result


@router.get("/on-date")
async def get_events_on_date(date: str, coin: Optional[str] = None):
    """
    Find what events happened on a specific date.
    
    Example: /api/events/on-date?date=2022-11-09&coin=BTC
    (Returns news from the day FTX collapsed)
    """
    if not _correlation_engine:
        raise HTTPException(status_code=503, detail="Correlation engine not initialized")
    
    try:
        query_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    result = await _correlation_engine.find_events_for_date(query_date, coin)
    return result


@router.get("/search")
async def search_events_by_keyword(keyword: str, days_back: int = 730, limit: int = 30):
    """
    Search for events matching a keyword.
    
    Example: /api/events/search?keyword=elon&days_back=365
    (Finds all Elon Musk related news in the past year)
    """
    if not _correlation_engine:
        raise HTTPException(status_code=503, detail="Correlation engine not initialized")
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_back)
    
    events = await _correlation_engine.search_events_by_keyword(
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return {
        "keyword": keyword,
        "events_found": len(events),
        "events": events
    }


@router.get("/what-caused")
async def what_caused_price_change(coin: str, date: str, direction: Optional[str] = None):
    """
    Find what likely caused a price change on a specific date.
    
    Example: /api/events/what-caused?coin=DOGE&date=2021-05-08&direction=down
    (Finds that Elon's SNL appearance caused DOGE to crash)
    """
    if not _correlation_engine:
        raise HTTPException(status_code=503, detail="Correlation engine not initialized")
    
    try:
        query_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get price movement for that day
    start = query_date - timedelta(days=1)
    end = query_date + timedelta(days=1)
    
    movements = await _correlation_engine.find_price_movements(
        coin_symbol=coin,
        start_date=start,
        end_date=end,
        threshold_pct=2.0  # Lower threshold for specific date query
    )
    
    if not movements:
        return {
            "coin": coin,
            "date": date,
            "message": "No significant price movement found on this date"
        }
    
    # Filter by direction if specified
    if direction:
        movements = [m for m in movements if m["direction"] == direction.lower()]
    
    if not movements:
        return {
            "coin": coin,
            "date": date,
            "direction": direction,
            "message": f"No {direction} price movement found on this date"
        }
    
    # Find news for the movement
    movement = movements[0]
    news = await _correlation_engine.find_news_around_event(
        coin_symbol=coin,
        event_timestamp=movement["timestamp"],
        hours_before=48,
        hours_after=12
    )
    
    correlation = await _correlation_engine.correlate_event(movement, news)
    
    return {
        "coin": coin,
        "date": date,
        "price_change": f"{movement['change_pct']:+.2f}%",
        "direction": movement["direction"],
        "likely_cause": correlation.get("likely_cause"),
        "correlation_score": correlation.get("correlation_score"),
        "related_news": correlation.get("correlated_news", [])[:5]
    }


# ================== Historical Events Database Endpoints ==================

@router.post("/database/seed")
async def seed_events_database():
    """
    Seed the database with known major crypto events.
    
    Includes 40+ curated events from 2013-2024:
    - Mt. Gox collapse
    - Bitcoin halvings
    - Elon Musk tweets
    - FTX bankruptcy
    - ETF approvals
    """
    if not _events_db:
        raise HTTPException(status_code=503, detail="Events database not initialized")
    
    result = await _events_db.seed_major_events()
    return result


@router.post("/database/enrich")
async def enrich_events_with_news(limit: int = 20):
    """
    Enrich stored events with actual news articles from CoinDesk.
    """
    if not _events_db:
        raise HTTPException(status_code=503, detail="Events database not initialized")
    
    result = await _events_db.enrich_events_with_news(limit)
    return result


@router.post("/database/calculate-impact")
async def calculate_price_impact():
    """
    Calculate price impact for stored events using OHLCV data.
    
    Adds before/after price data and percentage changes.
    """
    if not _events_db:
        raise HTTPException(status_code=503, detail="Events database not initialized")
    
    result = await _events_db.add_price_impact()
    return result


@router.get("/database/stats")
async def get_events_stats():
    """Get statistics about stored events"""
    if not _events_db:
        raise HTTPException(status_code=503, detail="Events database not initialized")
    
    return await _events_db.get_stats()


@router.get("/database/list")
async def list_events(
    coin: Optional[str] = None,
    category: Optional[str] = None,
    impact: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50
):
    """
    Query events with filters.
    
    Categories: celebrity, regulatory, exchange, hack, institutional, technology, partnership, macro
    Impact: positive, negative, mixed
    
    Example: /api/events/database/list?coin=BTC&category=regulatory&limit=10
    """
    if not _events_db:
        raise HTTPException(status_code=503, detail="Events database not initialized")
    
    events = await _events_db.get_events(
        coin=coin,
        category=category,
        impact=impact,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return {
        "count": len(events),
        "filters": {"coin": coin, "category": category, "impact": impact},
        "events": events
    }


@router.get("/database/coin/{coin}")
async def get_events_for_coin(coin: str, limit: int = 20):
    """Get all events affecting a specific coin"""
    if not _events_db:
        raise HTTPException(status_code=503, detail="Events database not initialized")
    
    events = await _events_db.get_events_for_coin(coin, limit)
    return {
        "coin": coin.upper(),
        "count": len(events),
        "events": events
    }


@router.get("/database/category/{category}")
async def get_events_by_category(category: str, limit: int = 20):
    """
    Get events by category.
    
    Categories: celebrity, regulatory, exchange, hack, institutional, technology, partnership, macro, milestone
    """
    if not _events_db:
        raise HTTPException(status_code=503, detail="Events database not initialized")
    
    events = await _events_db.get_events_by_category(category, limit)
    return {
        "category": category,
        "count": len(events),
        "events": events
    }


@router.get("/database/search")
async def search_events_database(keyword: str, limit: int = 20):
    """Search events in the database by keyword"""
    if not _events_db:
        raise HTTPException(status_code=503, detail="Events database not initialized")
    
    events = await _events_db.search_events(keyword, limit)
    return {
        "keyword": keyword,
        "count": len(events),
        "events": events
    }


# ================== AI Chat Event Detection ==================

@router.get("/ai-query")
async def ai_event_query(query: str):
    """
    Natural language query for events (used by AI Chat).
    
    Examples:
    - "What happened to BTC on November 9, 2022?"
    - "Why did DOGE pump in May 2021?"
    - "Find Elon Musk crypto news"
    - "List FTX collapse events"
    """
    if not _events_db or not _correlation_engine:
        raise HTTPException(status_code=503, detail="Event services not initialized")
    
    query_lower = query.lower()
    
    # Parse query type
    result = {"query": query, "type": "unknown", "data": None}
    
    # Date-specific query
    import re
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}',
        r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
    ]
    
    # Check for date in query
    for pattern in date_patterns:
        match = re.search(pattern, query_lower)
        if match:
            result["type"] = "date_query"
            break
    
    # Keyword search
    keywords = ["elon", "musk", "ftx", "luna", "terra", "hack", "etf", "halving", "sec", "ban"]
    for kw in keywords:
        if kw in query_lower:
            result["type"] = "keyword_search"
            result["keyword"] = kw
            
            # Search events database first
            db_events = await _events_db.search_events(kw, limit=10)
            
            # Also search recent news
            news_events = await _correlation_engine.search_events_by_keyword(
                kw,
                start_date=datetime.now(timezone.utc) - timedelta(days=365),
                limit=10
            )
            
            result["data"] = {
                "database_events": db_events,
                "recent_news": news_events
            }
            return result
    
    # Coin-specific query
    coins = ["btc", "eth", "doge", "sol", "xrp", "bnb", "ada", "luna", "ftt"]
    for coin in coins:
        if coin in query_lower:
            result["type"] = "coin_query"
            result["coin"] = coin.upper()
            
            events = await _events_db.get_events_for_coin(coin, limit=15)
            result["data"] = {"events": events}
            return result
    
    # Category query
    categories = {
        "celebrity": ["celebrity", "influencer", "elon", "famous"],
        "regulatory": ["regulatory", "sec", "regulation", "legal", "ban"],
        "hack": ["hack", "exploit", "breach", "stolen"],
        "institutional": ["institutional", "etf", "blackrock", "fidelity"],
        "technology": ["technology", "upgrade", "fork", "merge", "halving"]
    }
    
    for cat, keywords in categories.items():
        if any(kw in query_lower for kw in keywords):
            result["type"] = "category_query"
            result["category"] = cat
            
            events = await _events_db.get_events_by_category(cat, limit=15)
            result["data"] = {"events": events}
            return result
    
    # Default: return recent major events
    result["type"] = "general"
    stats = await _events_db.get_stats()
    events = await _events_db.get_events(limit=10)
    result["data"] = {
        "stats": stats,
        "recent_events": events
    }
    
    return result



# ================== Predictable Patterns ==================

@router.get("/patterns/all")
async def get_all_predictable_patterns():
    """
    Get all known predictable event patterns.
    These are events with known timing or warning signs that can be anticipated.
    """
    if not _events_db:
        raise HTTPException(status_code=503, detail="Events database not initialized")
    
    patterns = _events_db.get_predictable_patterns()
    
    # Group by predictability
    high = [p for p in patterns if p["predictability"] == "HIGH"]
    medium = [p for p in patterns if p["predictability"] == "MEDIUM"]
    low = [p for p in patterns if p["predictability"] == "LOW"]
    
    return {
        "total_patterns": len(patterns),
        "high_predictability": high,
        "medium_predictability": medium,
        "low_predictability": low,
        "summary": {
            "highly_predictable": len(high),
            "moderately_predictable": len(medium),
            "difficult_to_predict": len(low)
        }
    }


@router.get("/patterns/upcoming")
async def get_upcoming_predictable_events():
    """
    Get upcoming events that can be predicted based on known patterns.
    Includes FOMC meetings, options expiries, known upgrades, etc.
    """
    if not _events_db:
        raise HTTPException(status_code=503, detail="Events database not initialized")
    
    return {
        "upcoming_events": await _events_db.get_upcoming_predictable_events(),
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/patterns/analysis")
async def analyze_pattern_accuracy():
    """
    Analyze how accurate each pattern type has been historically.
    Uses actual historical event data to validate pattern predictions.
    """
    if not _events_db:
        raise HTTPException(status_code=503, detail="Events database not initialized")
    
    return await _events_db.analyze_pattern_accuracy()


@router.post("/database/reseed")
async def reseed_events_database():
    """
    Reseed the events database with latest curated events.
    This adds new events from 2025-2026.
    """
    if not _events_db:
        raise HTTPException(status_code=503, detail="Events database not initialized")
    
    result = await _events_db.seed_major_events()
    return result


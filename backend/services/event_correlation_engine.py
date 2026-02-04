"""
Event Correlation Engine
Correlates news events with price movements to identify market-moving events.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import numpy as np


class EventCorrelationEngine:
    """
    Correlates news events with cryptocurrency price movements.
    
    Features:
    - Detect significant price movements
    - Find news events around price changes
    - Calculate correlation scores
    - Identify market-moving events (Elon tweets, regulations, hacks, etc.)
    """
    
    # Event categories for classification
    EVENT_CATEGORIES = {
        "celebrity": ["elon", "musk", "saylor", "cathie", "wood", "cuban", "snoop", "celebrity"],
        "regulatory": ["sec", "cftc", "gensler", "regulation", "ban", "legal", "lawsuit", "court", "senator", "congress"],
        "exchange": ["binance", "coinbase", "ftx", "kraken", "exchange", "listing", "delist"],
        "hack": ["hack", "exploit", "breach", "stolen", "attack", "vulnerability", "rug"],
        "institutional": ["blackrock", "fidelity", "goldman", "jpmorgan", "bank", "etf", "institution", "fund"],
        "technology": ["upgrade", "fork", "merge", "mainnet", "testnet", "layer", "scaling"],
        "partnership": ["partner", "collaboration", "integration", "adopt", "accept"],
        "macro": ["fed", "inflation", "recession", "economy", "rate", "treasury", "dollar"]
    }
    
    # Minimum price change to consider significant (%)
    SIGNIFICANT_CHANGE_THRESHOLD = 5.0
    
    def __init__(self, db: AsyncIOMotorDatabase, coindesk_service=None, cryptocompare_service=None):
        self.db = db
        self.coindesk_service = coindesk_service
        self.cryptocompare_service = cryptocompare_service
        self.events_collection = "correlated_events"
        self.correlations_collection = "event_correlations"
        
    async def find_price_movements(
        self,
        coin_symbol: str,
        start_date: datetime,
        end_date: datetime,
        threshold_pct: float = None
    ) -> List[Dict[str, Any]]:
        """
        Find significant price movements for a coin in a date range.
        """
        threshold = threshold_pct or self.SIGNIFICANT_CHANGE_THRESHOLD
        
        # Get OHLCV data from database
        data = await self.db.historical_ohlcv.find({
            "symbol": coin_symbol.upper(),
            "timestamp": {
                "$gte": int(start_date.timestamp()),
                "$lte": int(end_date.timestamp())
            }
        }, {"_id": 0}).sort("timestamp", 1).to_list(length=10000)
        
        if len(data) < 2:
            return []
        
        movements = []
        
        for i in range(1, len(data)):
            prev_close = data[i-1]["close"]
            curr_close = data[i]["close"]
            
            if prev_close <= 0:
                continue
            
            change_pct = ((curr_close - prev_close) / prev_close) * 100
            
            if abs(change_pct) >= threshold:
                movements.append({
                    "coin": coin_symbol.upper(),
                    "date": data[i]["date"],
                    "timestamp": data[i]["timestamp"],
                    "prev_price": prev_close,
                    "price": curr_close,
                    "change_pct": round(change_pct, 2),
                    "direction": "up" if change_pct > 0 else "down",
                    "volume": data[i].get("volume_to", 0),
                    "high": data[i].get("high", 0),
                    "low": data[i].get("low", 0)
                })
        
        return movements
    
    async def find_news_around_event(
        self,
        coin_symbol: str,
        event_timestamp: int,
        hours_before: int = 24,
        hours_after: int = 6,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find news articles around a specific event time.
        """
        if not self.coindesk_service:
            return []
        
        # Get news up to the event time
        to_ts = event_timestamp + (hours_after * 3600)
        
        try:
            result = await self.coindesk_service._request(
                "/news/v1/article/list",
                {
                    "limit": limit,
                    "to_ts": to_ts,
                    "categories": coin_symbol.upper(),
                    "lang": "EN"
                }
            )
            
            if "Data" not in result:
                # Try without category filter
                result = await self.coindesk_service._request(
                    "/news/v1/article/list",
                    {
                        "limit": limit * 2,
                        "to_ts": to_ts,
                        "lang": "EN"
                    }
                )
            
            articles = []
            start_ts = event_timestamp - (hours_before * 3600)
            
            for article in result.get("Data", []):
                pub_ts = article.get("PUBLISHED_ON", 0)
                
                # Filter to time window
                if start_ts <= pub_ts <= to_ts:
                    title = article.get("TITLE", "").lower()
                    
                    # Check if related to the coin
                    coin_lower = coin_symbol.lower()
                    is_related = (
                        coin_lower in title or
                        coin_symbol.upper() in article.get("TITLE", "") or
                        any(cat.get("NAME", "").upper() == coin_symbol.upper() 
                            for cat in article.get("CATEGORY_DATA", []))
                    )
                    
                    articles.append({
                        "id": article.get("ID"),
                        "title": article.get("TITLE", ""),
                        "body": article.get("BODY", "")[:500],
                        "url": article.get("URL", ""),
                        "published_at": pub_ts,
                        "published_date": datetime.fromtimestamp(pub_ts, tz=timezone.utc).isoformat(),
                        "sentiment": article.get("SENTIMENT", "NEUTRAL"),
                        "source": article.get("SOURCE_DATA", {}).get("NAME", "Unknown"),
                        "is_coin_related": is_related,
                        "categories": [cat.get("NAME") for cat in article.get("CATEGORY_DATA", [])]
                    })
            
            return sorted(articles, key=lambda x: x["published_at"], reverse=True)
            
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []
    
    def classify_event(self, title: str, body: str = "") -> Dict[str, Any]:
        """
        Classify an event based on keywords in title/body.
        """
        text = (title + " " + body).lower()
        
        matches = {}
        primary_category = "general"
        max_score = 0
        
        for category, keywords in self.EVENT_CATEGORIES.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                matches[category] = score
                if score > max_score:
                    max_score = score
                    primary_category = category
        
        # Extract key entities
        entities = []
        entity_keywords = [
            "elon musk", "michael saylor", "cz", "sbf", "sam bankman", "vitalik",
            "gary gensler", "sec", "blackrock", "fidelity", "tesla", "microstrategy"
        ]
        for entity in entity_keywords:
            if entity in text:
                entities.append(entity.title())
        
        return {
            "primary_category": primary_category,
            "category_scores": matches,
            "entities": entities,
            "is_high_impact": max_score >= 2 or any(e in text for e in ["elon", "sec", "hack", "etf"])
        }
    
    async def correlate_event(
        self,
        movement: Dict[str, Any],
        news_articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Correlate a price movement with news articles.
        """
        if not news_articles:
            return {
                "movement": movement,
                "correlated_news": [],
                "correlation_score": 0,
                "likely_cause": None
            }
        
        # Score each article's relevance
        scored_articles = []
        
        for article in news_articles:
            score = 0
            
            # Sentiment alignment
            if movement["direction"] == "up" and article["sentiment"] == "POSITIVE":
                score += 3
            elif movement["direction"] == "down" and article["sentiment"] == "NEGATIVE":
                score += 3
            elif article["sentiment"] == "NEUTRAL":
                score += 1
            
            # Coin relevance
            if article["is_coin_related"]:
                score += 5
            
            # Time proximity (closer = higher score)
            time_diff = abs(movement["timestamp"] - article["published_at"])
            hours_diff = time_diff / 3600
            if hours_diff < 2:
                score += 4
            elif hours_diff < 6:
                score += 3
            elif hours_diff < 12:
                score += 2
            else:
                score += 1
            
            # Classification
            classification = self.classify_event(article["title"], article.get("body", ""))
            if classification["is_high_impact"]:
                score += 3
            
            scored_articles.append({
                **article,
                "correlation_score": score,
                "classification": classification
            })
        
        # Sort by correlation score
        scored_articles.sort(key=lambda x: x["correlation_score"], reverse=True)
        
        # Determine likely cause
        likely_cause = None
        if scored_articles and scored_articles[0]["correlation_score"] >= 8:
            top = scored_articles[0]
            likely_cause = {
                "title": top["title"],
                "category": top["classification"]["primary_category"],
                "entities": top["classification"]["entities"],
                "sentiment": top["sentiment"],
                "confidence": min(100, top["correlation_score"] * 10)
            }
        
        return {
            "movement": movement,
            "correlated_news": scored_articles[:5],
            "total_articles_found": len(news_articles),
            "correlation_score": scored_articles[0]["correlation_score"] if scored_articles else 0,
            "likely_cause": likely_cause
        }
    
    async def analyze_date_range(
        self,
        coin_symbol: str,
        start_date: datetime,
        end_date: datetime,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze a date range for correlated events.
        """
        # Find significant price movements
        movements = await self.find_price_movements(coin_symbol, start_date, end_date)
        
        if not movements:
            return {
                "coin": coin_symbol,
                "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "movements_found": 0,
                "correlated_events": []
            }
        
        correlated_events = []
        
        for movement in movements[:20]:  # Limit to avoid too many API calls
            # Find news around this movement
            news = await self.find_news_around_event(
                coin_symbol,
                movement["timestamp"],
                hours_before=48,
                hours_after=12
            )
            
            # Correlate
            correlation = await self.correlate_event(movement, news)
            correlated_events.append(correlation)
            
            # Brief delay for rate limiting
            await asyncio.sleep(0.3)
        
        result = {
            "coin": coin_symbol,
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "movements_found": len(movements),
            "movements_analyzed": len(correlated_events),
            "correlated_events": correlated_events,
            "high_correlation_events": [
                e for e in correlated_events if e["correlation_score"] >= 8
            ],
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }
        
        if save_to_db:
            await self.db[self.correlations_collection].insert_one({
                **result,
                "created_at": datetime.now(timezone.utc)
            })
        
        return result
    
    async def find_events_for_date(
        self,
        date: datetime,
        coin_symbol: str = None
    ) -> Dict[str, Any]:
        """
        Find what events happened on a specific date.
        """
        start_ts = int(date.replace(hour=0, minute=0, second=0).timestamp())
        end_ts = start_ts + 86400  # 24 hours
        
        if not self.coindesk_service:
            return {"error": "CoinDesk service not available"}
        
        params = {
            "limit": 50,
            "to_ts": end_ts,
            "lang": "EN"
        }
        
        if coin_symbol:
            params["categories"] = coin_symbol.upper()
        
        result = await self.coindesk_service._request("/news/v1/article/list", params)
        
        events = []
        for article in result.get("Data", []):
            pub_ts = article.get("PUBLISHED_ON", 0)
            if start_ts <= pub_ts <= end_ts:
                classification = self.classify_event(
                    article.get("TITLE", ""),
                    article.get("BODY", "")[:500]
                )
                events.append({
                    "title": article.get("TITLE", ""),
                    "published_at": datetime.fromtimestamp(pub_ts, tz=timezone.utc).isoformat(),
                    "sentiment": article.get("SENTIMENT", "NEUTRAL"),
                    "source": article.get("SOURCE_DATA", {}).get("NAME", "Unknown"),
                    "url": article.get("URL", ""),
                    "classification": classification,
                    "categories": [cat.get("NAME") for cat in article.get("CATEGORY_DATA", [])]
                })
        
        return {
            "date": date.strftime("%Y-%m-%d"),
            "coin": coin_symbol,
            "events_found": len(events),
            "events": events,
            "high_impact_events": [e for e in events if e["classification"]["is_high_impact"]]
        }
    
    async def search_events_by_keyword(
        self,
        keyword: str,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Search for events matching a keyword.
        """
        if not self.coindesk_service:
            return []
        
        # Default to last 2 years if no dates provided
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            start_date = end_date - timedelta(days=730)
        
        # We need to search through multiple time windows
        events = []
        current_ts = int(end_date.timestamp())
        start_ts = int(start_date.timestamp())
        
        keyword_lower = keyword.lower()
        
        while current_ts > start_ts and len(events) < limit:
            result = await self.coindesk_service._request(
                "/news/v1/article/list",
                {"limit": 100, "to_ts": current_ts, "lang": "EN"}
            )
            
            for article in result.get("Data", []):
                title = article.get("TITLE", "").lower()
                body = article.get("BODY", "").lower()
                
                if keyword_lower in title or keyword_lower in body:
                    pub_ts = article.get("PUBLISHED_ON", 0)
                    classification = self.classify_event(title, body[:500])
                    
                    events.append({
                        "title": article.get("TITLE", ""),
                        "published_at": datetime.fromtimestamp(pub_ts, tz=timezone.utc).isoformat(),
                        "timestamp": pub_ts,
                        "sentiment": article.get("SENTIMENT", "NEUTRAL"),
                        "source": article.get("SOURCE_DATA", {}).get("NAME", "Unknown"),
                        "url": article.get("URL", ""),
                        "classification": classification,
                        "match_context": title if keyword_lower in title else body[:200]
                    })
            
            # Move back in time
            if result.get("Data"):
                oldest = min(a.get("PUBLISHED_ON", current_ts) for a in result["Data"])
                current_ts = oldest - 1
            else:
                break
            
            await asyncio.sleep(0.2)
        
        return sorted(events, key=lambda x: x["timestamp"], reverse=True)[:limit]


# Global instance
_correlation_engine = None

def get_correlation_engine(db: AsyncIOMotorDatabase = None, coindesk_service=None, cryptocompare_service=None):
    """Get or create correlation engine instance"""
    global _correlation_engine
    if _correlation_engine is None and db is not None:
        _correlation_engine = EventCorrelationEngine(db, coindesk_service, cryptocompare_service)
    return _correlation_engine

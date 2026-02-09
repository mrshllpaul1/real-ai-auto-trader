"""
Unified News Aggregator Service
Consolidates multiple news sources with persistent storage and sentiment analysis.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import hashlib
import logging

logger = logging.getLogger(__name__)


class NewsAggregator:
    """
    Unified news aggregator that combines multiple sources with:
    - Persistent storage
    - Deduplication
    - Multi-source sentiment aggregation
    - Historical archival
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.crypto_news
        
        # Source weights for sentiment aggregation (higher = more trusted)
        self.source_weights = {
            'cryptopanic': 1.0,
            'coindesk': 0.9,
            'cointelegraph': 0.8,
            'news_service': 0.6,
            'social': 0.5
        }
        
        # Ensure indexes
        asyncio.create_task(self._ensure_indexes())
    
    async def _ensure_indexes(self):
        """Create database indexes for efficient querying"""
        try:
            await self.collection.create_index([("news_id", 1)], unique=True)
            await self.collection.create_index([("published_at", -1)])
            await self.collection.create_index([("coins", 1)])
            await self.collection.create_index([("sentiment.final", 1)])
            await self.collection.create_index([("source", 1)])
            logger.info("News collection indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    async def fetch_and_store_news(
        self,
        coins: Optional[List[str]] = None,
        limit: int = 50,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Fetch news from all sources and store in database.
        
        Args:
            coins: List of coin symbols to filter (None = all)
            limit: Max news items per source
            force_refresh: Skip cache and fetch fresh data
            
        Returns:
            Dict with fetched news count and summary
        """
        if coins is None:
            coins = ["BTC", "ETH", "SOL", "XRP", "ADA"]
        
        all_news = []
        source_counts = {}
        
        # Fetch from CryptoPanic
        try:
            from services.cryptopanic_service import CryptoPanicService
            cryptopanic = CryptoPanicService()
            
            if cryptopanic.is_available:
                for coin in coins:
                    news = await cryptopanic.get_news_for_coin(coin, limit=limit // len(coins))
                    if "results" in news:
                        for item in news["results"]:
                            all_news.append(self._normalize_cryptopanic(item, coin))
                
                source_counts['cryptopanic'] = len([n for n in all_news if n['source'] == 'cryptopanic'])
                logger.info(f"Fetched {source_counts['cryptopanic']} news from CryptoPanic")
        except Exception as e:
            logger.warning(f"CryptoPanic fetch failed: {e}")
        
        # Fetch from News Service (fallback)
        try:
            from services.news_service import NewsService
            news_service = NewsService()
            
            news_data = await news_service.get_latest_news(limit=limit)
            if news_data and "articles" in news_data:
                for item in news_data["articles"]:
                    all_news.append(self._normalize_news_service(item, coins))
                
                source_counts['news_service'] = len([n for n in all_news if n['source'] == 'news_service'])
                logger.info(f"Fetched {source_counts['news_service']} news from NewsService")
        except Exception as e:
            logger.warning(f"NewsService fetch failed: {e}")
        
        # Deduplicate and store
        stored_count = await self._deduplicate_and_store(all_news)
        
        return {
            "fetched": len(all_news),
            "stored": stored_count,
            "by_source": source_counts,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _normalize_cryptopanic(self, item: Dict, coin: str) -> Dict[str, Any]:
        """Normalize CryptoPanic news format"""
        # Generate unique ID from URL or title
        news_id = self._generate_news_id(item.get("url", item.get("title", "")))
        
        # Extract sentiment from votes
        votes = item.get("votes", {})
        sentiment_score = self._calculate_sentiment_from_votes(votes)
        
        return {
            "news_id": news_id,
            "source": "cryptopanic",
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "published_at": self._parse_timestamp(item.get("published_at")),
            "coins": [c.get("code", coin) for c in item.get("currencies", [{"code": coin}])],
            "sentiment": {
                "vote_based": sentiment_score,
                "source": "cryptopanic",
                "votes": votes
            },
            "metadata": {
                "domain": item.get("domain", ""),
                "kind": item.get("kind", "news"),
                "source_id": item.get("id")
            },
            "fetched_at": datetime.now(timezone.utc)
        }
    
    def _normalize_news_service(self, item: Dict, coins: List[str]) -> Dict[str, Any]:
        """Normalize generic news service format"""
        news_id = self._generate_news_id(item.get("url", item.get("title", "")))
        
        # Extract mentioned coins from title/description
        mentioned_coins = []
        text = f"{item.get('title', '')} {item.get('description', '')}".upper()
        for coin in coins:
            if coin in text or self._get_coin_name(coin) in text:
                mentioned_coins.append(coin)
        
        return {
            "news_id": news_id,
            "source": "news_service",
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "published_at": self._parse_timestamp(item.get("publishedAt", item.get("published_at"))),
            "coins": mentioned_coins if mentioned_coins else ["BTC"],  # Default to BTC
            "sentiment": {
                "ai_based": item.get("sentiment", 0.0),
                "source": "news_service"
            },
            "metadata": {
                "source_name": item.get("source", {}).get("name", ""),
                "author": item.get("author", ""),
                "description": item.get("description", "")[:500]  # Limit length
            },
            "fetched_at": datetime.now(timezone.utc)
        }
    
    def _calculate_sentiment_from_votes(self, votes: Dict) -> float:
        """Calculate sentiment score from CryptoPanic votes (-1 to 1)"""
        positive = votes.get("positive", 0) + votes.get("liked", 0)
        negative = votes.get("negative", 0) + votes.get("disliked", 0) + votes.get("toxic", 0)
        
        total = positive + negative
        if total == 0:
            return 0.0
        
        # Normalize to -1 to 1
        return (positive - negative) / total
    
    def _generate_news_id(self, text: str) -> str:
        """Generate unique hash ID for news item"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> datetime:
        """Parse various timestamp formats to datetime"""
        if not timestamp_str:
            return datetime.now(timezone.utc)
        
        try:
            # Try ISO format first
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            try:
                # Try common formats
                return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                return datetime.now(timezone.utc)
    
    def _get_coin_name(self, symbol: str) -> str:
        """Get coin name from symbol"""
        names = {
            "BTC": "BITCOIN",
            "ETH": "ETHEREUM",
            "SOL": "SOLANA",
            "XRP": "RIPPLE",
            "ADA": "CARDANO",
            "DOGE": "DOGECOIN"
        }
        return names.get(symbol, symbol)
    
    async def _deduplicate_and_store(self, news_items: List[Dict]) -> int:
        """Deduplicate and store news items in database"""
        stored_count = 0
        
        for item in news_items:
            try:
                # Calculate final sentiment (weighted average of all sources)
                final_sentiment = self._calculate_final_sentiment(item)
                item["sentiment"]["final"] = final_sentiment
                
                # Upsert (update if exists, insert if not)
                result = await self.collection.update_one(
                    {"news_id": item["news_id"]},
                    {
                        "$set": item,
                        "$setOnInsert": {"created_at": datetime.now(timezone.utc)}
                    },
                    upsert=True
                )
                
                if result.upserted_id or result.modified_count > 0:
                    stored_count += 1
            except Exception as e:
                logger.error(f"Failed to store news item: {e}")
        
        logger.info(f"Stored {stored_count} news items in database")
        return stored_count
    
    def _calculate_final_sentiment(self, item: Dict) -> float:
        """Calculate final weighted sentiment score"""
        sentiment = item.get("sentiment", {})
        source = item.get("source", "unknown")
        weight = self.source_weights.get(source, 0.5)
        
        # Get available sentiment score
        score = (
            sentiment.get("final") or
            sentiment.get("vote_based") or
            sentiment.get("ai_based") or
            0.0
        )
        
        return score * weight
    
    async def get_news(
        self,
        coins: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sentiment: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> Dict[str, Any]:
        """
        Get news from database with filtering.
        
        Args:
            coins: Filter by coin symbols
            start_date: Filter news after this date
            end_date: Filter news before this date
            sentiment: Filter by sentiment ("bullish", "bearish", "neutral")
            limit: Max results to return
            skip: Number of results to skip (pagination)
            
        Returns:
            Dict with news items and metadata
        """
        try:
            # Build query
            query = {}
            
            if coins:
                query["coins"] = {"$in": [c.upper() for c in coins]}
            
            if start_date or end_date:
                query["published_at"] = {}
                if start_date:
                    query["published_at"]["$gte"] = start_date
                if end_date:
                    query["published_at"]["$lte"] = end_date
            
            if sentiment:
                if sentiment == "bullish":
                    query["sentiment.final"] = {"$gte": 0.2}
                elif sentiment == "bearish":
                    query["sentiment.final"] = {"$lte": -0.2}
                elif sentiment == "neutral":
                    query["sentiment.final"] = {"$gte": -0.2, "$lte": 0.2}
            
            # Execute query
            cursor = self.collection.find(query).sort("published_at", -1).skip(skip).limit(limit)
            news_items = await cursor.to_list(length=limit)
            
            # Get total count
            total_count = await self.collection.count_documents(query)
            
            # Format response
            formatted_news = []
            for item in news_items:
                formatted_news.append({
                    "id": item.get("news_id"),
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "published_at": item.get("published_at").isoformat() if item.get("published_at") else None,
                    "coins": item.get("coins", []),
                    "sentiment": item.get("sentiment", {}).get("final", 0.0),
                    "sentiment_label": self._get_sentiment_label(item.get("sentiment", {}).get("final", 0.0)),
                    "source": item.get("source"),
                    "metadata": item.get("metadata", {})
                })
            
            return {
                "news": formatted_news,
                "count": len(formatted_news),
                "total": total_count,
                "has_more": (skip + len(formatted_news)) < total_count
            }
        except Exception as e:
            logger.error(f"Error querying news: {e}")
            return {
                "news": [],
                "count": 0,
                "total": 0,
                "error": str(e)
            }
    
    def _get_sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score >= 0.2:
            return "bullish"
        elif score <= -0.2:
            return "bearish"
        else:
            return "neutral"
    
    async def get_sentiment_summary(
        self,
        coin: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get sentiment summary for a coin over time period.
        
        Args:
            coin: Coin symbol
            days: Number of days to analyze
            
        Returns:
            Dict with sentiment metrics
        """
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = {
                "coins": coin.upper(),
                "published_at": {"$gte": start_date}
            }
            
            cursor = self.collection.find(query)
            news_items = await cursor.to_list(length=None)
            
            if not news_items:
                return {
                    "coin": coin,
                    "period_days": days,
                    "news_count": 0,
                    "sentiment": "neutral",
                    "score": 0.0
                }
            
            # Calculate metrics
            sentiments = [item.get("sentiment", {}).get("final", 0.0) for item in news_items]
            avg_sentiment = sum(sentiments) / len(sentiments)
            
            bullish_count = sum(1 for s in sentiments if s >= 0.2)
            bearish_count = sum(1 for s in sentiments if s <= -0.2)
            neutral_count = len(sentiments) - bullish_count - bearish_count
            
            return {
                "coin": coin,
                "period_days": days,
                "news_count": len(news_items),
                "sentiment": self._get_sentiment_label(avg_sentiment),
                "score": round(avg_sentiment, 3),
                "distribution": {
                    "bullish": bullish_count,
                    "bearish": bearish_count,
                    "neutral": neutral_count
                },
                "latest_news": [{
                    "title": item.get("title"),
                    "published_at": item.get("published_at").isoformat() if item.get("published_at") else None,
                    "sentiment": round(item.get("sentiment", {}).get("final", 0.0), 3)
                } for item in news_items[:5]]
            }
        except Exception as e:
            logger.error(f"Error getting sentiment summary: {e}")
            return {"error": str(e)}


# Singleton instance
_news_aggregator = None


def get_news_aggregator(db: AsyncIOMotorDatabase) -> NewsAggregator:
    """Get or create news aggregator instance"""
    global _news_aggregator
    if _news_aggregator is None:
        _news_aggregator = NewsAggregator(db)
    return _news_aggregator

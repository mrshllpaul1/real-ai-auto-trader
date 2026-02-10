"""
Historical Media Data Service
==============================
Persistent storage and retrieval of news, social media, and sentiment data.
Enables long-term analysis and ML model training on media+price correlations.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class HistoricalMediaService:
    """
    Service for archiving and managing historical news and media data.
    Stores data persistently for long-term analysis and ML training.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize the historical media service.
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.news_archive = db.news_archive
        self.sentiment_history = db.sentiment_history
        self.news_price_correlations = db.news_price_correlations
        self.media_events = db.media_events
        
        logger.info("✅ Historical Media Service initialized")
    
    async def ensure_indexes(self):
        """Create necessary database indexes for efficient queries"""
        try:
            # News archive indexes
            await self.news_archive.create_index([("published_at", -1)])
            await self.news_archive.create_index([("fetched_at", -1)])
            await self.news_archive.create_index([("currencies", 1), ("published_at", -1)])
            await self.news_archive.create_index([("sentiment_score", -1)])
            await self.news_archive.create_index([("source", 1), ("article_id", 1)], unique=True)
            await self.news_archive.create_index([("is_market_moving", 1), ("published_at", -1)])
            
            # Sentiment history indexes
            await self.sentiment_history.create_index([("timestamp", -1)])
            await self.sentiment_history.create_index([("coin_symbol", 1), ("timestamp", -1)])
            await self.sentiment_history.create_index([("resolution", 1), ("coin_symbol", 1), ("timestamp", -1)])
            
            # News-price correlation indexes
            await self.news_price_correlations.create_index([("published_at", -1)])
            await self.news_price_correlations.create_index([("coin_symbol", 1), ("published_at", -1)])
            await self.news_price_correlations.create_index([("is_correlated", 1), ("correlation_strength", -1)])
            
            # Media events indexes
            await self.media_events.create_index([("date", -1)])
            await self.media_events.create_index([("coins_affected", 1), ("date", -1)])
            await self.media_events.create_index([("type", 1), ("date", -1)])
            
            logger.info("✅ Historical media indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    async def archive_news_article(
        self,
        article: Dict[str, Any],
        source: str = "unknown"
    ) -> Optional[str]:
        """
        Archive a single news article for historical analysis.
        
        Args:
            article: News article data
            source: Source identifier (cryptopanic, free_news, etc.)
        
        Returns:
            Inserted document ID or None if duplicate
        """
        try:
            # Generate unique article ID
            article_id = article.get('id') or f"{source}_{article.get('url', '')}_{article.get('published_at', '')}"
            
            # Prepare document
            doc = {
                "article_id": article_id,
                "title": article.get('title', ''),
                "description": article.get('description', ''),
                "url": article.get('url', ''),
                "source": source,
                "published_at": self._parse_datetime(article.get('published_at')),
                "fetched_at": datetime.utcnow(),
                "sentiment": article.get('sentiment', 'neutral'),
                "sentiment_score": self._calculate_sentiment_score(article.get('sentiment', 'neutral')),
                "currencies": article.get('currencies', []),
                "impact_keywords": self._extract_impact_keywords(article.get('title', '') + ' ' + article.get('description', '')),
                "votes": article.get('votes', {}),
                "is_market_moving": self._is_market_moving(article),
                "indexed_at": datetime.utcnow()
            }
            
            # Insert or update
            result = await self.news_archive.update_one(
                {"source": source, "article_id": article_id},
                {"$set": doc},
                upsert=True
            )
            
            if result.upserted_id:
                logger.debug(f"Archived new article: {article_id}")
                return str(result.upserted_id)
            else:
                logger.debug(f"Updated existing article: {article_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error archiving article: {e}")
            return None
    
    async def archive_news_batch(
        self,
        articles: List[Dict[str, Any]],
        source: str = "unknown"
    ) -> Dict[str, int]:
        """
        Archive multiple news articles in batch.
        
        Args:
            articles: List of article data
            source: Source identifier
        
        Returns:
            Dictionary with counts of new and updated articles
        """
        new_count = 0
        updated_count = 0
        error_count = 0
        
        for article in articles:
            result = await self.archive_news_article(article, source)
            if result:
                new_count += 1
            elif result is None:
                error_count += 1
            else:
                updated_count += 1
        
        logger.info(f"Batch archive complete: {new_count} new, {updated_count} updated, {error_count} errors")
        
        return {
            "new": new_count,
            "updated": len(articles) - new_count - error_count,
            "errors": error_count,
            "total_processed": len(articles)
        }
    
    async def get_historical_news(
        self,
        coin_symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sentiment: Optional[str] = None,
        min_impact_score: Optional[int] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical news articles with filtering.
        
        Args:
            coin_symbol: Filter by cryptocurrency symbol
            start_date: Start of date range
            end_date: End of date range
            sentiment: Filter by sentiment (positive/negative/neutral)
            min_impact_score: Minimum impact score
            limit: Maximum results to return
            skip: Number of results to skip (pagination)
        
        Returns:
            List of news articles
        """
        try:
            # Build query
            query = {}
            
            if coin_symbol:
                query["currencies"] = coin_symbol.upper()
            
            if start_date or end_date:
                query["published_at"] = {}
                if start_date:
                    query["published_at"]["$gte"] = start_date
                if end_date:
                    query["published_at"]["$lte"] = end_date
            
            if sentiment:
                query["sentiment"] = sentiment.lower()
            
            if min_impact_score:
                query["sentiment_score"] = {"$gte": min_impact_score}
            
            # Execute query
            cursor = self.news_archive.find(query).sort("published_at", -1).skip(skip).limit(limit)
            articles = await cursor.to_list(length=limit)
            
            # Remove MongoDB _id for API response
            for article in articles:
                article['_id'] = str(article['_id'])
            
            return articles
            
        except Exception as e:
            logger.error(f"Error retrieving historical news: {e}")
            return []
    
    async def get_news_count(
        self,
        coin_symbol: Optional[str] = None,
        days: int = 30
    ) -> int:
        """
        Get count of archived news articles.
        
        Args:
            coin_symbol: Optional filter by coin
            days: Number of days to look back
        
        Returns:
            Count of articles
        """
        try:
            query = {}
            
            if coin_symbol:
                query["currencies"] = coin_symbol.upper()
            
            if days:
                query["published_at"] = {"$gte": datetime.utcnow() - timedelta(days=days)}
            
            count = await self.news_archive.count_documents(query)
            return count
            
        except Exception as e:
            logger.error(f"Error counting news: {e}")
            return 0
    
    async def get_sentiment_timeseries(
        self,
        coin_symbol: str,
        resolution: str = "daily",  # hourly, daily, weekly
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get aggregated sentiment time-series data.
        
        Args:
            coin_symbol: Cryptocurrency symbol
            resolution: Time resolution (hourly/daily/weekly)
            days: Number of days to retrieve
        
        Returns:
            List of sentiment data points
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = {
                "coin_symbol": coin_symbol.upper(),
                "resolution": resolution,
                "timestamp": {"$gte": start_date}
            }
            
            cursor = self.sentiment_history.find(query).sort("timestamp", 1)
            data = await cursor.to_list(length=days * 24 if resolution == "hourly" else days)
            
            for item in data:
                item['_id'] = str(item['_id'])
            
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving sentiment timeseries: {e}")
            return []
    
    async def calculate_news_statistics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate statistics about archived news data.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with statistics
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Total articles
            total_count = await self.news_archive.count_documents(
                {"published_at": {"$gte": start_date}}
            )
            
            # Sentiment breakdown
            sentiment_pipeline = [
                {"$match": {"published_at": {"$gte": start_date}}},
                {"$group": {
                    "_id": "$sentiment",
                    "count": {"$sum": 1}
                }}
            ]
            sentiment_results = await self.news_archive.aggregate(sentiment_pipeline).to_list(10)
            sentiment_breakdown = {item['_id']: item['count'] for item in sentiment_results}
            
            # Top currencies mentioned
            currency_pipeline = [
                {"$match": {"published_at": {"$gte": start_date}}},
                {"$unwind": "$currencies"},
                {"$group": {
                    "_id": "$currencies",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            currency_results = await self.news_archive.aggregate(currency_pipeline).to_list(10)
            top_currencies = {item['_id']: item['count'] for item in currency_results}
            
            # Market-moving news count
            market_moving_count = await self.news_archive.count_documents({
                "published_at": {"$gte": start_date},
                "is_market_moving": True
            })
            
            return {
                "total_articles": total_count,
                "sentiment_breakdown": sentiment_breakdown,
                "top_currencies": top_currencies,
                "market_moving_count": market_moving_count,
                "days_analyzed": days,
                "oldest_article": start_date.isoformat(),
                "data_coverage_pct": (total_count / (days * 50)) * 100 if days > 0 else 0  # Assuming ~50 articles/day
            }
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}
    
    # Helper methods
    
    def _parse_datetime(self, date_str: Any) -> datetime:
        """Parse datetime from various formats"""
        if isinstance(date_str, datetime):
            return date_str
        
        if not date_str:
            return datetime.utcnow()
        
        try:
            # Try ISO format
            return datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
        except:
            # Fallback to current time
            return datetime.utcnow()
    
    def _calculate_sentiment_score(self, sentiment: str) -> int:
        """Convert sentiment to numeric score (0-100)"""
        sentiment_map = {
            'positive': 75,
            'bullish': 75,
            'neutral': 50,
            'negative': 25,
            'bearish': 25
        }
        return sentiment_map.get(sentiment.lower(), 50)
    
    def _extract_impact_keywords(self, text: str) -> List[str]:
        """Extract high-impact keywords from text"""
        text_lower = text.lower()
        impact_keywords = []
        
        high_impact_words = [
            'sec', 'lawsuit', 'hack', 'hacked', 'exploit', 'scam',
            'etf', 'approved', 'regulation', 'ban', 'banned',
            'partnership', 'acquisition', 'merger', 'listing',
            'halted', 'suspended', 'investigation', 'fraud',
            'upgrade', 'mainnet', 'launch', 'release'
        ]
        
        for keyword in high_impact_words:
            if keyword in text_lower:
                impact_keywords.append(keyword)
        
        return impact_keywords
    
    def _is_market_moving(self, article: Dict[str, Any]) -> bool:
        """Determine if article is likely market-moving"""
        # Check for high-impact keywords
        impact_keywords = self._extract_impact_keywords(
            article.get('title', '') + ' ' + article.get('description', '')
        )
        
        if len(impact_keywords) >= 2:
            return True
        
        # Check sentiment strength
        sentiment = article.get('sentiment', 'neutral')
        if sentiment in ['very_positive', 'very_negative']:
            return True
        
        # Check votes (CryptoPanic)
        votes = article.get('votes', {})
        if votes.get('positive', 0) > 100 or votes.get('negative', 0) > 50:
            return True
        
        return False

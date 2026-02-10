"""
News-Price Correlation Service
===============================
Analyzes correlation between news events and price movements.
Generates datasets for ML model training on news+price relationships.
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class NewsPriceCorrelationService:
    """
    Service for analyzing correlations between news and price movements.
    Enables ML models to learn news→price relationships.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, historical_media_service):
        """
        Initialize correlation service.
        
        Args:
            db: MongoDB database instance
            historical_media_service: Historical media service for news data
        """
        self.db = db
        self.historical_media = historical_media_service
        self.news_price_correlations = db.news_price_correlations
        self.historical_ohlcv = db.historical_ohlcv
        
        logger.info("✅ News-Price Correlation Service initialized")
    
    async def analyze_news_impact(
        self,
        article: Dict[str, Any],
        coin_symbol: str,
        time_windows: List[int] = [1, 4, 12, 24]  # Hours
    ) -> Dict[str, Any]:
        """
        Analyze price impact of a news article.
        
        Args:
            article: News article data
            coin_symbol: Cryptocurrency symbol
            time_windows: Time windows to analyze (in hours)
        
        Returns:
            Dictionary with correlation analysis
        """
        try:
            published_at = article.get('published_at')
            if isinstance(published_at, str):
                published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            
            # Get price data around the news event
            price_before = await self._get_price_at_time(coin_symbol, published_at - timedelta(hours=1))
            
            if not price_before:
                return {"error": "No price data available"}
            
            # Calculate price changes for each time window
            price_changes = {}
            volume_changes = {}
            
            for hours in time_windows:
                price_after = await self._get_price_at_time(coin_symbol, published_at + timedelta(hours=hours))
                
                if price_after:
                    price_change = ((price_after['close'] - price_before['close']) / price_before['close']) * 100
                    volume_change = ((price_after['volume'] - price_before['volume']) / price_before['volume']) * 100 if price_before['volume'] > 0 else 0
                    
                    price_changes[f"{hours}h"] = round(price_change, 2)
                    volume_changes[f"{hours}h"] = round(volume_change, 2)
            
            # Calculate correlation strength
            sentiment_score = article.get('sentiment_score', 50)
            avg_price_change = sum(price_changes.values()) / len(price_changes) if price_changes else 0
            
            # Correlation: positive sentiment should align with price increase
            correlation_strength = self._calculate_correlation_strength(
                sentiment_score, avg_price_change
            )
            
            return {
                "article_id": article.get('article_id'),
                "coin_symbol": coin_symbol,
                "published_at": published_at,
                "sentiment_score": sentiment_score,
                "price_before": round(price_before['close'], 2),
                "price_changes": price_changes,
                "volume_changes": volume_changes,
                "correlation_strength": correlation_strength,
                "is_correlated": correlation_strength > 0.5,
                "analyzed_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing news impact: {e}")
            return {"error": str(e)}
    
    async def store_correlation(
        self,
        correlation_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Store news-price correlation analysis.
        
        Args:
            correlation_data: Correlation analysis result
        
        Returns:
            Inserted document ID or None
        """
        try:
            result = await self.news_price_correlations.insert_one(correlation_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error storing correlation: {e}")
            return None
    
    async def analyze_batch_correlations(
        self,
        coin_symbol: str,
        days: int = 7,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Analyze correlations for a batch of news articles.
        
        Args:
            coin_symbol: Cryptocurrency symbol
            days: Number of days to analyze
            limit: Maximum articles to analyze
        
        Returns:
            Batch analysis results
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get recent news for the coin
            news_articles = await self.historical_media.get_historical_news(
                coin_symbol=coin_symbol,
                start_date=start_date,
                limit=limit
            )
            
            analyzed_count = 0
            correlated_count = 0
            errors = 0
            
            for article in news_articles:
                # Check if already analyzed
                existing = await self.news_price_correlations.find_one({
                    "article_id": article.get('article_id'),
                    "coin_symbol": coin_symbol
                })
                
                if existing:
                    continue
                
                # Analyze correlation
                correlation = await self.analyze_news_impact(article, coin_symbol)
                
                if "error" not in correlation:
                    # Store correlation
                    await self.store_correlation(correlation)
                    analyzed_count += 1
                    
                    if correlation.get('is_correlated'):
                        correlated_count += 1
                else:
                    errors += 1
                
                # Throttle to avoid overloading
                await asyncio.sleep(0.1)
            
            return {
                "status": "completed",
                "coin_symbol": coin_symbol,
                "days_analyzed": days,
                "total_articles": len(news_articles),
                "analyzed_count": analyzed_count,
                "correlated_count": correlated_count,
                "correlation_rate": round(correlated_count / analyzed_count * 100, 1) if analyzed_count > 0 else 0,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error in batch analysis: {e}")
            return {"error": str(e)}
    
    async def get_correlations(
        self,
        coin_symbol: Optional[str] = None,
        days: int = 30,
        min_correlation: float = 0.5,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get stored news-price correlations.
        
        Args:
            coin_symbol: Optional filter by coin
            days: Number of days to look back
            min_correlation: Minimum correlation strength
            limit: Maximum results
        
        Returns:
            List of correlation records
        """
        try:
            query = {
                "analyzed_at": {"$gte": datetime.utcnow() - timedelta(days=days)},
                "correlation_strength": {"$gte": min_correlation}
            }
            
            if coin_symbol:
                query["coin_symbol"] = coin_symbol.upper()
            
            cursor = self.news_price_correlations.find(query).sort("analyzed_at", -1).limit(limit)
            correlations = await cursor.to_list(length=limit)
            
            for item in correlations:
                item['_id'] = str(item['_id'])
            
            return correlations
            
        except Exception as e:
            logger.error(f"Error retrieving correlations: {e}")
            return []
    
    async def get_correlation_statistics(
        self,
        coin_symbol: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get statistics about news-price correlations.
        
        Args:
            coin_symbol: Optional filter by coin
            days: Number of days to analyze
        
        Returns:
            Dictionary with statistics
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            query = {"analyzed_at": {"$gte": start_date}}
            
            if coin_symbol:
                query["coin_symbol"] = coin_symbol.upper()
            
            # Total correlations
            total_count = await self.news_price_correlations.count_documents(query)
            
            # Correlated vs non-correlated
            correlated_count = await self.news_price_correlations.count_documents({
                **query,
                "is_correlated": True
            })
            
            # Average correlation strength
            pipeline = [
                {"$match": query},
                {"$group": {
                    "_id": None,
                    "avg_correlation": {"$avg": "$correlation_strength"},
                    "max_correlation": {"$max": "$correlation_strength"},
                    "min_correlation": {"$min": "$correlation_strength"}
                }}
            ]
            
            stats_result = await self.news_price_correlations.aggregate(pipeline).to_list(1)
            stats = stats_result[0] if stats_result else {}
            
            return {
                "total_analyzed": total_count,
                "correlated_count": correlated_count,
                "non_correlated_count": total_count - correlated_count,
                "correlation_rate": round(correlated_count / total_count * 100, 1) if total_count > 0 else 0,
                "avg_correlation_strength": round(stats.get('avg_correlation', 0), 3),
                "max_correlation_strength": round(stats.get('max_correlation', 0), 3),
                "min_correlation_strength": round(stats.get('min_correlation', 0), 3),
                "days_analyzed": days,
                "coin_symbol": coin_symbol if coin_symbol else "all"
            }
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}
    
    async def generate_ml_training_dataset(
        self,
        coin_symbol: str,
        days: int = 365,
        min_correlation: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Generate ML training dataset with news+price features.
        
        Args:
            coin_symbol: Cryptocurrency symbol
            days: Number of days of historical data
            min_correlation: Minimum correlation to include
        
        Returns:
            List of training samples with features and labels
        """
        try:
            correlations = await self.get_correlations(
                coin_symbol=coin_symbol,
                days=days,
                min_correlation=min_correlation,
                limit=10000
            )
            
            training_data = []
            
            for corr in correlations:
                # Features
                features = {
                    "sentiment_score": corr.get('sentiment_score', 50),
                    "is_market_moving": 1 if corr.get('is_market_moving', False) else 0,
                    "price_before": corr.get('price_before', 0),
                    "hour_of_day": corr.get('published_at').hour if isinstance(corr.get('published_at'), datetime) else 0,
                    "day_of_week": corr.get('published_at').weekday() if isinstance(corr.get('published_at'), datetime) else 0,
                }
                
                # Labels (price changes at different time horizons)
                labels = corr.get('price_changes', {})
                
                training_data.append({
                    "features": features,
                    "labels": labels,
                    "correlation_strength": corr.get('correlation_strength', 0),
                    "timestamp": corr.get('published_at')
                })
            
            return training_data
            
        except Exception as e:
            logger.error(f"Error generating training dataset: {e}")
            return []
    
    # Helper methods
    
    async def _get_price_at_time(
        self,
        symbol: str,
        timestamp: datetime,
        tolerance_hours: int = 2
    ) -> Optional[Dict[str, Any]]:
        """Get price data closest to the specified timestamp"""
        try:
            # Try to find OHLCV data within tolerance window
            query = {
                "symbol": symbol.upper(),
                "timestamp": {
                    "$gte": timestamp - timedelta(hours=tolerance_hours),
                    "$lte": timestamp + timedelta(hours=tolerance_hours)
                }
            }
            
            # Find closest timestamp
            result = await self.historical_ohlcv.find_one(
                query,
                sort=[("timestamp", 1)]
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting price at time: {e}")
            return None
    
    def _calculate_correlation_strength(
        self,
        sentiment_score: float,
        price_change_pct: float
    ) -> float:
        """
        Calculate correlation strength between sentiment and price change.
        
        Returns:
            Correlation strength (0-1)
        """
        # Normalize sentiment to -1 to 1 scale (from 0-100)
        sentiment_normalized = (sentiment_score - 50) / 50
        
        # Normalize price change to -1 to 1 scale (assuming max ±20% move)
        price_normalized = max(-1, min(1, price_change_pct / 20))
        
        # Calculate correlation (1 = perfect alignment, 0 = no correlation, -1 = inverse)
        correlation = sentiment_normalized * price_normalized
        
        # Convert to 0-1 scale (absolute value)
        return abs(correlation)

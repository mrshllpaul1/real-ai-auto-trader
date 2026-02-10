"""
Historical Sentiment Tracker Service
Stores and retrieves historical sentiment data for enhanced backtesting and analysis.
Complements ai_news_sentiment.py by providing persistent storage and historical queries.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class HistoricalSentimentTracker:
    """
    Tracks and stores sentiment data over time for historical analysis.
    Provides daily sentiment snapshots and aggregation capabilities.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.historical_sentiment
        self.daily_snapshots = db.daily_sentiment_snapshots
        
    async def initialize_indexes(self):
        """Create indexes for efficient queries"""
        try:
            # Index for coin_id and timestamp queries
            await self.collection.create_index([("coin_id", 1), ("timestamp", -1)])
            await self.collection.create_index([("timestamp", -1)])
            
            # Index for daily snapshots
            await self.daily_snapshots.create_index([("coin_id", 1), ("date", -1)], unique=True)
            await self.daily_snapshots.create_index([("date", -1)])
            
            logger.info("✅ Historical sentiment indexes created")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    async def store_sentiment(
        self,
        coin_id: str,
        sentiment_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store a sentiment reading with timestamp.
        
        Args:
            coin_id: Cryptocurrency identifier (e.g., 'bitcoin')
            sentiment_data: Sentiment analysis result
            metadata: Optional additional context (price, volume, etc.)
        
        Returns:
            Stored document with _id
        """
        document = {
            "coin_id": coin_id,
            "symbol": sentiment_data.get("symbol"),
            "score": sentiment_data.get("score", 50),
            "label": sentiment_data.get("label", "neutral"),
            "confidence": sentiment_data.get("confidence", 50),
            "summary": sentiment_data.get("summary", ""),
            "key_factors": sentiment_data.get("key_factors", []),
            "bullish_signals": sentiment_data.get("bullish_signals", []),
            "bearish_signals": sentiment_data.get("bearish_signals", []),
            "news_count": sentiment_data.get("news_count", 0),
            "timestamp": datetime.utcnow(),
            "date": datetime.utcnow().date().isoformat(),
            "metadata": metadata or {}
        }
        
        result = await self.collection.insert_one(document)
        document["_id"] = str(result.inserted_id)
        
        return document
    
    async def get_coin_sentiment_history(
        self,
        coin_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get historical sentiment data for a coin.
        
        Args:
            coin_id: Cryptocurrency identifier
            start_date: Start of time range (optional)
            end_date: End of time range (optional)
            limit: Maximum records to return
        
        Returns:
            List of sentiment records ordered by timestamp descending
        """
        query = {"coin_id": coin_id}
        
        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date
            if end_date:
                query["timestamp"]["$lte"] = end_date
        
        cursor = self.collection.find(query).sort("timestamp", -1).limit(limit)
        
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        
        return results
    
    async def create_daily_snapshot(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Create daily sentiment snapshots for all tracked coins.
        Aggregates sentiment readings from the past 24 hours.
        
        Args:
            date: ISO date string (YYYY-MM-DD), defaults to today
        
        Returns:
            Summary of snapshot creation
        """
        if date is None:
            date = datetime.utcnow().date().isoformat()
        
        snapshot_date = datetime.fromisoformat(date)
        start_time = snapshot_date
        end_time = snapshot_date + timedelta(days=1)
        
        # Get all coins with sentiment data in this time range
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start_time, "$lt": end_time}
                }
            },
            {
                "$group": {
                    "_id": "$coin_id",
                    "avg_score": {"$avg": "$score"},
                    "avg_confidence": {"$avg": "$confidence"},
                    "total_readings": {"$sum": 1},
                    "total_news": {"$sum": "$news_count"},
                    "labels": {"$push": "$label"},
                    "bullish_count": {
                        "$sum": {
                            "$cond": [
                                {"$in": ["$label", ["bullish", "very_bullish"]]},
                                1,
                                0
                            ]
                        }
                    },
                    "bearish_count": {
                        "$sum": {
                            "$cond": [
                                {"$in": ["$label", ["bearish", "very_bearish"]]},
                                1,
                                0
                            ]
                        }
                    },
                    "neutral_count": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$label", "neutral"]},
                                1,
                                0
                            ]
                        }
                    },
                    "all_key_factors": {"$push": "$key_factors"},
                    "all_bullish_signals": {"$push": "$bullish_signals"},
                    "all_bearish_signals": {"$push": "$bearish_signals"}
                }
            }
        ]
        
        snapshots_created = 0
        async for result in self.collection.aggregate(pipeline):
            coin_id = result["_id"]
            
            # Flatten and count key factors
            all_factors = []
            for factors in result.get("all_key_factors", []):
                all_factors.extend(factors)
            
            # Count factor frequency
            factor_counts = {}
            for factor in all_factors:
                factor_counts[factor] = factor_counts.get(factor, 0) + 1
            
            # Get top 5 most mentioned factors
            top_factors = sorted(
                factor_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            # Determine overall label based on average score
            avg_score = result.get("avg_score", 50)
            if avg_score >= 70:
                overall_label = "bullish"
            elif avg_score >= 55:
                overall_label = "slightly_bullish"
            elif avg_score >= 45:
                overall_label = "neutral"
            elif avg_score >= 30:
                overall_label = "slightly_bearish"
            else:
                overall_label = "bearish"
            
            snapshot = {
                "coin_id": coin_id,
                "date": date,
                "avg_score": round(avg_score, 2),
                "avg_confidence": round(result.get("avg_confidence", 50), 2),
                "overall_label": overall_label,
                "total_readings": result.get("total_readings", 0),
                "total_news": result.get("total_news", 0),
                "bullish_count": result.get("bullish_count", 0),
                "bearish_count": result.get("bearish_count", 0),
                "neutral_count": result.get("neutral_count", 0),
                "top_factors": [{"factor": f, "count": c} for f, c in top_factors],
                "created_at": datetime.utcnow()
            }
            
            # Upsert snapshot (update if exists for this coin/date)
            await self.daily_snapshots.update_one(
                {"coin_id": coin_id, "date": date},
                {"$set": snapshot},
                upsert=True
            )
            
            snapshots_created += 1
        
        return {
            "date": date,
            "snapshots_created": snapshots_created,
            "status": "success"
        }
    
    async def get_daily_snapshots(
        self,
        coin_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 365
    ) -> List[Dict[str, Any]]:
        """
        Get daily sentiment snapshots.
        
        Args:
            coin_id: Filter by specific coin (optional)
            start_date: Start date (ISO format, optional)
            end_date: End date (ISO format, optional)
            limit: Maximum snapshots to return
        
        Returns:
            List of daily snapshots
        """
        query = {}
        
        if coin_id:
            query["coin_id"] = coin_id
        
        if start_date or end_date:
            query["date"] = {}
            if start_date:
                query["date"]["$gte"] = start_date
            if end_date:
                query["date"]["$lte"] = end_date
        
        cursor = self.daily_snapshots.find(query).sort("date", -1).limit(limit)
        
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        
        return results
    
    async def get_sentiment_trend(
        self,
        coin_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze sentiment trend over time.
        
        Args:
            coin_id: Cryptocurrency identifier
            days: Number of days to analyze
        
        Returns:
            Trend analysis including direction, momentum, and volatility
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        snapshots = await self.get_daily_snapshots(
            coin_id=coin_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        if not snapshots:
            return {
                "coin_id": coin_id,
                "days": days,
                "error": "No sentiment data available for this period"
            }
        
        # Reverse to chronological order
        snapshots.reverse()
        
        scores = [s["avg_score"] for s in snapshots]
        
        # Calculate trend metrics
        if len(scores) >= 2:
            # Simple linear trend
            trend_direction = "rising" if scores[-1] > scores[0] else "falling"
            if abs(scores[-1] - scores[0]) < 5:
                trend_direction = "stable"
            
            # Momentum (recent vs. older average)
            mid_point = len(scores) // 2
            recent_avg = sum(scores[mid_point:]) / len(scores[mid_point:])
            older_avg = sum(scores[:mid_point]) / len(scores[:mid_point])
            momentum = recent_avg - older_avg
            
            # Volatility (standard deviation)
            mean_score = sum(scores) / len(scores)
            variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
            volatility = variance ** 0.5
            
        else:
            trend_direction = "insufficient_data"
            momentum = 0
            volatility = 0
        
        return {
            "coin_id": coin_id,
            "days": days,
            "data_points": len(snapshots),
            "current_score": scores[-1] if scores else None,
            "trend_direction": trend_direction,
            "momentum": round(momentum, 2),
            "volatility": round(volatility, 2),
            "score_range": {
                "min": min(scores) if scores else None,
                "max": max(scores) if scores else None,
                "avg": round(sum(scores) / len(scores), 2) if scores else None
            },
            "snapshots": snapshots[-7:]  # Last 7 days
        }
    
    async def get_multi_coin_sentiment(
        self,
        coin_ids: List[str],
        date: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get sentiment for multiple coins on a specific date.
        
        Args:
            coin_ids: List of coin identifiers
            date: ISO date string (defaults to latest available)
        
        Returns:
            Dictionary mapping coin_id to sentiment snapshot
        """
        query = {"coin_id": {"$in": coin_ids}}
        
        if date:
            query["date"] = date
        else:
            # Get latest snapshot for each coin
            # This is done in multiple queries for simplicity
            pass
        
        results = {}
        
        if date:
            cursor = self.daily_snapshots.find(query)
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                results[doc["coin_id"]] = doc
        else:
            # Get latest for each coin
            for coin_id in coin_ids:
                snapshot = await self.daily_snapshots.find_one(
                    {"coin_id": coin_id},
                    sort=[("date", -1)]
                )
                if snapshot:
                    snapshot["_id"] = str(snapshot["_id"])
                    results[coin_id] = snapshot
        
        return results
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about stored sentiment data"""
        total_records = await self.collection.count_documents({})
        total_snapshots = await self.daily_snapshots.count_documents({})
        
        # Count unique coins
        unique_coins = await self.collection.distinct("coin_id")
        
        # Get date range
        oldest = await self.collection.find_one({}, sort=[("timestamp", 1)])
        newest = await self.collection.find_one({}, sort=[("timestamp", -1)])
        
        return {
            "total_sentiment_records": total_records,
            "total_daily_snapshots": total_snapshots,
            "unique_coins_tracked": len(unique_coins),
            "coins": unique_coins,
            "date_range": {
                "oldest": oldest.get("timestamp").isoformat() if oldest else None,
                "newest": newest.get("timestamp").isoformat() if newest else None
            }
        }
    
    async def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """
        Remove sentiment records older than specified days.
        Daily snapshots are preserved longer.
        
        Args:
            days_to_keep: Keep records from the last N days
        
        Returns:
            Cleanup summary
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        result = await self.collection.delete_many({
            "timestamp": {"$lt": cutoff_date}
        })
        
        return {
            "deleted_records": result.deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "status": "success"
        }

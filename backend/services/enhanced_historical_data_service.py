"""
Enhanced Historical Data Service
Provides advanced historical market data features:
- Extended retention for intraday data (1h/4h up to 1+ year)
- Volume profile and depth metrics
- Data quality validation and scoring
- Historical event markers
- Cross-exchange validation
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from httpx import AsyncClient
import asyncio
import numpy as np

logger = logging.getLogger(__name__)


class EnhancedHistoricalDataService:
    """
    Enhanced historical data service with advanced features:
    - Persistent intraday storage (1h/4h for 1+ year)
    - Volume profile calculation
    - Data quality scoring
    - Historical event markers
    """
    
    # Extended retention periods (in days)
    EXTENDED_RETENTION = {
        "1m": 30,      # Extended from 7 to 30 days
        "5m": 60,      # Extended from 14 to 60 days
        "15m": 90,     # Extended from 30 to 90 days
        "30m": 180,    # Extended from 60 to 180 days
        "1h": 730,     # Extended from 180 to 2 years
        "4h": 1095,    # Extended from 365 to 3 years
        "1D": 3650,    # Keep 10 years
        "1W": 3650     # Keep 10 years
    }
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection_ohlcv = "enhanced_ohlcv"
        self.collection_events = "historical_events"
        self.collection_volume_profile = "volume_profile"
        self.collection_quality = "data_quality"
        
    async def store_enhanced_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        candles: List[Dict[str, Any]],
        source: str = "kraken"
    ) -> Dict[str, Any]:
        """
        Store OHLCV data with enhanced metrics.
        
        Args:
            symbol: Coin symbol (BTC, ETH, etc.)
            timeframe: Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1D, 1W)
            candles: List of OHLCV candles
            source: Data source name
            
        Returns:
            Storage result with statistics
        """
        try:
            if not candles:
                return {"error": "No candles provided"}
            
            collection = self.db[self.collection_ohlcv]
            documents = []
            
            for candle in candles:
                # Calculate enhanced metrics
                enhanced_candle = self._enhance_candle(candle, symbol, timeframe)
                enhanced_candle.update({
                    "symbol": symbol.upper(),
                    "timeframe": timeframe,
                    "source": source,
                    "stored_at": datetime.now(timezone.utc)
                })
                documents.append(enhanced_candle)
            
            # Upsert to avoid duplicates
            from pymongo import UpdateOne
            operations = [
                UpdateOne(
                    {
                        "symbol": doc["symbol"],
                        "timeframe": doc["timeframe"],
                        "timestamp": doc["timestamp"]
                    },
                    {"$set": doc},
                    upsert=True
                )
                for doc in documents
            ]
            
            result = await collection.bulk_write(operations, ordered=False)
            
            # Create indexes
            await collection.create_index([("symbol", 1), ("timeframe", 1), ("timestamp", -1)])
            await collection.create_index("timestamp")
            await collection.create_index([("symbol", 1), ("quality_score", -1)])
            
            return {
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "inserted": result.upserted_count,
                "updated": result.modified_count,
                "total_processed": len(documents),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Failed to store enhanced OHLCV: {e}")
            return {"error": str(e)}
    
    def _enhance_candle(self, candle: Dict[str, Any], symbol: str, timeframe: str) -> Dict[str, Any]:
        """Add enhanced metrics to a candle"""
        try:
            open_price = float(candle.get("open", 0))
            high = float(candle.get("high", 0))
            low = float(candle.get("low", 0))
            close = float(candle.get("close", 0))
            volume = float(candle.get("volume", 0))
            
            # Price range and movement
            price_range = high - low if high > low else 0
            price_change = close - open_price if close > 0 and open_price > 0 else 0
            price_change_pct = (price_change / open_price * 100) if open_price > 0 else 0
            
            # Body vs wick analysis
            body = abs(close - open_price)
            upper_wick = high - max(open_price, close)
            lower_wick = min(open_price, close) - low
            
            # Volume analysis
            vwap = float(candle.get("vwap", (high + low + close) / 3))
            
            # Volatility (intraday range as % of close)
            volatility = (price_range / close * 100) if close > 0 else 0
            
            # Candle patterns
            is_bullish = close > open_price
            is_doji = body < (price_range * 0.1) if price_range > 0 else False
            is_hammer = (lower_wick > body * 2) and (upper_wick < body * 0.3) if body > 0 else False
            is_shooting_star = (upper_wick > body * 2) and (lower_wick < body * 0.3) if body > 0 else False
            
            # Quality scoring
            quality_score = self._calculate_quality_score(candle)
            
            enhanced = {
                "timestamp": candle.get("timestamp"),
                "datetime": candle.get("datetime"),
                "date": candle.get("date"),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "vwap": vwap,
                "trade_count": candle.get("trade_count", 0),
                # Enhanced metrics
                "price_range": price_range,
                "price_change": price_change,
                "price_change_pct": price_change_pct,
                "body_size": body,
                "upper_wick": upper_wick,
                "lower_wick": lower_wick,
                "volatility": volatility,
                "is_bullish": is_bullish,
                "is_doji": is_doji,
                "is_hammer": is_hammer,
                "is_shooting_star": is_shooting_star,
                "quality_score": quality_score
            }
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Failed to enhance candle: {e}")
            return candle
    
    def _calculate_quality_score(self, candle: Dict[str, Any]) -> float:
        """
        Calculate data quality score (0-100).
        Factors: completeness, consistency, reasonableness
        """
        score = 100.0
        
        # Check required fields
        required = ["open", "high", "low", "close", "volume"]
        for field in required:
            if field not in candle or candle[field] is None:
                score -= 20
        
        if score < 20:
            return score
        
        try:
            open_p = float(candle.get("open", 0))
            high = float(candle.get("high", 0))
            low = float(candle.get("low", 0))
            close = float(candle.get("close", 0))
            volume = float(candle.get("volume", 0))
            
            # Consistency checks
            if high < low:
                score -= 30  # Invalid: high should be >= low
            
            if high < max(open_p, close) or low > min(open_p, close):
                score -= 20  # Invalid: OHLC relationship
            
            # Reasonableness checks
            if volume == 0:
                score -= 10  # Suspicious: no volume
            
            # Check for extreme price movements (>50% in one candle - likely error)
            if open_p > 0:
                change_pct = abs((close - open_p) / open_p * 100)
                if change_pct > 50:
                    score -= 15  # Suspicious: extreme movement
            
            # Check for zero prices
            if any(p == 0 for p in [open_p, high, low, close]):
                score -= 25  # Invalid: zero prices
            
        except (ValueError, TypeError, ZeroDivisionError):
            score -= 20
        
        return max(0, min(100, score))
    
    async def calculate_volume_profile(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        price_bins: int = 50
    ) -> Dict[str, Any]:
        """
        Calculate volume profile for a time period.
        Shows volume distribution across price levels.
        
        Args:
            symbol: Coin symbol
            timeframe: Timeframe
            start_date: Start date
            end_date: End date
            price_bins: Number of price levels to group by
            
        Returns:
            Volume profile data
        """
        try:
            collection = self.db[self.collection_ohlcv]
            
            # Fetch candles
            candles = await collection.find({
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "timestamp": {
                    "$gte": int(start_date.timestamp()),
                    "$lte": int(end_date.timestamp())
                }
            }).sort("timestamp", 1).to_list(length=10000)
            
            if not candles:
                return {"error": "No data found"}
            
            # Extract prices and volumes
            prices = []
            volumes = []
            for candle in candles:
                # Use OHLC average weighted by volume
                avg_price = (candle["high"] + candle["low"] + candle["close"]) / 3
                prices.append(avg_price)
                volumes.append(candle["volume"])
            
            # Create price bins
            min_price = min(prices)
            max_price = max(prices)
            price_range = max_price - min_price
            
            if price_range == 0:
                return {"error": "No price variation"}
            
            bin_size = price_range / price_bins
            volume_profile = {}
            
            # Distribute volume into bins
            for i, price in enumerate(prices):
                bin_index = int((price - min_price) / bin_size)
                bin_index = min(bin_index, price_bins - 1)  # Ensure within bounds
                
                bin_price = min_price + (bin_index * bin_size) + (bin_size / 2)
                bin_key = f"{bin_price:.2f}"
                
                if bin_key not in volume_profile:
                    volume_profile[bin_key] = 0
                
                volume_profile[bin_key] += volumes[i]
            
            # Find Point of Control (POC) - price level with highest volume
            poc_price = max(volume_profile.items(), key=lambda x: x[1])
            
            # Sort by price
            sorted_profile = dict(sorted(volume_profile.items(), key=lambda x: float(x[0])))
            
            # Calculate value area (70% of volume)
            total_volume = sum(volumes)
            value_area_volume = total_volume * 0.70
            
            # Find value area high and low
            sorted_by_volume = sorted(volume_profile.items(), key=lambda x: x[1], reverse=True)
            va_volume = 0
            va_prices = []
            
            for price, vol in sorted_by_volume:
                va_volume += vol
                va_prices.append(float(price))
                if va_volume >= value_area_volume:
                    break
            
            va_high = max(va_prices) if va_prices else max_price
            va_low = min(va_prices) if va_prices else min_price
            
            # Store volume profile
            profile_doc = {
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "start_date": start_date,
                "end_date": end_date,
                "candle_count": len(candles),
                "total_volume": total_volume,
                "price_range": {
                    "min": min_price,
                    "max": max_price,
                    "range": price_range
                },
                "poc": {
                    "price": float(poc_price[0]),
                    "volume": poc_price[1]
                },
                "value_area": {
                    "high": va_high,
                    "low": va_low,
                    "range": va_high - va_low
                },
                "volume_profile": sorted_profile,
                "calculated_at": datetime.now(timezone.utc)
            }
            
            # Store in database
            await self.db[self.collection_volume_profile].insert_one(profile_doc)
            
            return profile_doc
            
        except Exception as e:
            logger.error(f"Failed to calculate volume profile: {e}")
            return {"error": str(e)}
    
    async def add_historical_event(
        self,
        symbol: str,
        timestamp: datetime,
        event_type: str,
        title: str,
        description: str,
        impact_score: float = 0.5,
        source: str = "manual",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Add a historical event marker.
        
        Args:
            symbol: Coin symbol (or "GLOBAL" for market-wide events)
            timestamp: Event timestamp
            event_type: Type (news, regulatory, technical, whale_movement, etc.)
            title: Event title
            description: Event description
            impact_score: Impact score 0-1 (0=low, 1=high)
            source: Event source
            metadata: Additional metadata
            
        Returns:
            Insert result
        """
        try:
            event_doc = {
                "symbol": symbol.upper(),
                "timestamp": int(timestamp.timestamp()),
                "datetime": timestamp,
                "event_type": event_type,
                "title": title,
                "description": description,
                "impact_score": max(0, min(1, impact_score)),
                "source": source,
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc)
            }
            
            result = await self.db[self.collection_events].insert_one(event_doc)
            
            # Create indexes
            await self.db[self.collection_events].create_index([("symbol", 1), ("timestamp", -1)])
            await self.db[self.collection_events].create_index("event_type")
            
            return {
                "event_id": str(result.inserted_id),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Failed to add historical event: {e}")
            return {"error": str(e)}
    
    async def get_events_for_period(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        event_types: List[str] = None
    ) -> Dict[str, Any]:
        """Get historical events for a time period"""
        try:
            query = {
                "symbol": {"$in": [symbol.upper(), "GLOBAL"]},
                "timestamp": {
                    "$gte": int(start_date.timestamp()),
                    "$lte": int(end_date.timestamp())
                }
            }
            
            if event_types:
                query["event_type"] = {"$in": event_types}
            
            events = await self.db[self.collection_events].find(
                query,
                {"_id": 0}
            ).sort("timestamp", -1).to_list(length=1000)
            
            return {
                "symbol": symbol.upper(),
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "count": len(events),
                "events": events
            }
            
        except Exception as e:
            logger.error(f"Failed to get historical events: {e}")
            return {"error": str(e)}
    
    async def get_data_quality_report(
        self,
        symbol: str,
        timeframe: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate data quality report for a symbol/timeframe.
        
        Args:
            symbol: Coin symbol
            timeframe: Timeframe
            days: Number of days to analyze
            
        Returns:
            Quality report with scores and issues
        """
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            collection = self.db[self.collection_ohlcv]
            
            candles = await collection.find({
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "timestamp": {
                    "$gte": int(start_date.timestamp()),
                    "$lte": int(end_date.timestamp())
                }
            }).to_list(length=10000)
            
            if not candles:
                return {"error": "No data found"}
            
            # Analyze quality
            total_candles = len(candles)
            quality_scores = [c.get("quality_score", 0) for c in candles]
            avg_quality = sum(quality_scores) / total_candles if total_candles > 0 else 0
            
            # Count issues
            low_quality = sum(1 for score in quality_scores if score < 70)
            zero_volume = sum(1 for c in candles if c.get("volume", 0) == 0)
            
            # Check for gaps in data
            timestamps = sorted([c["timestamp"] for c in candles])
            gaps = []
            
            # Expected interval in seconds
            interval_map = {
                "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
                "1h": 3600, "4h": 14400, "1D": 86400, "1W": 604800
            }
            expected_interval = interval_map.get(timeframe, 3600)
            
            for i in range(1, len(timestamps)):
                gap = timestamps[i] - timestamps[i-1]
                if gap > expected_interval * 1.5:  # Allow 50% tolerance
                    gaps.append({
                        "from": datetime.fromtimestamp(timestamps[i-1], tz=timezone.utc).isoformat(),
                        "to": datetime.fromtimestamp(timestamps[i], tz=timezone.utc).isoformat(),
                        "gap_seconds": gap,
                        "missing_candles": int(gap / expected_interval) - 1
                    })
            
            report = {
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": days
                },
                "summary": {
                    "total_candles": total_candles,
                    "average_quality_score": round(avg_quality, 2),
                    "low_quality_candles": low_quality,
                    "zero_volume_candles": zero_volume,
                    "data_gaps": len(gaps)
                },
                "quality_distribution": {
                    "excellent (90-100)": sum(1 for s in quality_scores if s >= 90),
                    "good (80-89)": sum(1 for s in quality_scores if 80 <= s < 90),
                    "fair (70-79)": sum(1 for s in quality_scores if 70 <= s < 80),
                    "poor (<70)": sum(1 for s in quality_scores if s < 70)
                },
                "gaps": gaps[:10],  # First 10 gaps
                "recommendation": self._get_quality_recommendation(avg_quality, low_quality, total_candles),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Store report
            await self.db[self.collection_quality].insert_one(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate quality report: {e}")
            return {"error": str(e)}
    
    def _get_quality_recommendation(self, avg_quality: float, low_quality: int, total: int) -> str:
        """Generate quality recommendation"""
        if avg_quality >= 90:
            return "Excellent data quality. Suitable for all trading strategies."
        elif avg_quality >= 80:
            return "Good data quality. Minor issues detected but generally reliable."
        elif avg_quality >= 70:
            return "Fair data quality. Consider re-downloading data or using alternative source."
        else:
            pct = (low_quality / total * 100) if total > 0 else 0
            return f"Poor data quality ({pct:.1f}% low quality candles). Re-download recommended."
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        try:
            stats = {}
            
            # OHLCV stats
            ohlcv_count = await self.db[self.collection_ohlcv].count_documents({})
            symbols = await self.db[self.collection_ohlcv].distinct("symbol")
            timeframes = await self.db[self.collection_ohlcv].distinct("timeframe")
            
            # Events stats
            events_count = await self.db[self.collection_events].count_documents({})
            event_types = await self.db[self.collection_events].distinct("event_type")
            
            # Volume profiles
            profiles_count = await self.db[self.collection_volume_profile].count_documents({})
            
            # Quality reports
            reports_count = await self.db[self.collection_quality].count_documents({})
            
            return {
                "ohlcv": {
                    "total_candles": ohlcv_count,
                    "unique_symbols": len(symbols),
                    "symbols": symbols[:30],
                    "timeframes": timeframes
                },
                "events": {
                    "total_events": events_count,
                    "event_types": event_types
                },
                "volume_profiles": {
                    "total_profiles": profiles_count
                },
                "quality_reports": {
                    "total_reports": reports_count
                },
                "status": "operational"
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}


# Singleton
_enhanced_service = None

def get_enhanced_historical_service(db: AsyncIOMotorDatabase = None) -> EnhancedHistoricalDataService:
    """Get or create enhanced historical data service"""
    global _enhanced_service
    if _enhanced_service is None and db is not None:
        _enhanced_service = EnhancedHistoricalDataService(db)
    return _enhanced_service

"""
Unified Historical Data Manager
Consolidates multiple data sources (CoinGecko, CoinDesk, Kraken) into a single interface
with persistent storage, quality validation, and automatic updates.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class HistoricalDataManager:
    """
    Unified manager for historical OHLCV data across multiple sources.
    Provides persistent storage, quality validation, and source prioritization.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.historical_ohlcv
        
        # Source priority (higher is better)
        self.source_priority = {
            'coindesk': 3,
            'kraken': 2,
            'coingecko': 1
        }
        
        # Data quality thresholds
        self.quality_thresholds = {
            'max_price_deviation': 0.05,  # 5% max deviation from adjacent candles
            'min_volume_ratio': 0.01,     # Min volume relative to average
            'max_gap_days': 1             # Max allowed gap in days
        }
    
    async def get_historical_ohlcv(
        self,
        symbol: str,
        quote: str = "USD",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "daily",
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get historical OHLCV data with automatic source fallback.
        
        Args:
            symbol: Coin symbol (BTC, ETH, etc.)
            quote: Quote currency (USD, EUR, etc.)
            start_date: Start date (default: 1 year ago)
            end_date: End date (default: now)
            interval: Timeframe (daily, hourly, 4h, weekly)
            force_refresh: Skip cache and fetch fresh data
            
        Returns:
            Dict with OHLCV data, metadata, and quality info
        """
        if start_date is None:
            start_date = datetime.now(timezone.utc) - timedelta(days=365)
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        
        # Try to get from local database first
        if not force_refresh:
            cached_data = await self._get_from_database(
                symbol, quote, start_date, end_date, interval
            )
            
            if cached_data and self._is_data_complete(cached_data, start_date, end_date):
                logger.info(f"Retrieved {symbol} data from local database")
                return self._format_response(cached_data, "database")
        
        # Fetch from external sources with prioritized fallback
        data = await self._fetch_from_sources(symbol, quote, start_date, end_date, interval)
        
        if data:
            # Validate and store the data
            validated_data = await self._validate_and_store(data, symbol, quote, interval)
            return self._format_response(validated_data, data.get('source', 'unknown'))
        
        # Return empty result if all sources fail
        return {
            "symbol": symbol,
            "quote": quote,
            "interval": interval,
            "data": [],
            "count": 0,
            "source": "none",
            "error": "Failed to fetch data from all sources"
        }
    
    async def _get_from_database(
        self,
        symbol: str,
        quote: str,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> List[Dict[str, Any]]:
        """Retrieve data from local database"""
        try:
            query = {
                "symbol": symbol.upper(),
                "quote": quote.upper(),
                "interval": interval,
                "timestamp": {
                    "$gte": int(start_date.timestamp()),
                    "$lte": int(end_date.timestamp())
                }
            }
            
            cursor = self.collection.find(query).sort("timestamp", 1)
            data = await cursor.to_list(length=None)
            
            return data
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return []
    
    async def _fetch_from_sources(
        self,
        symbol: str,
        quote: str,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch data from external sources with prioritized fallback"""
        
        # Try CoinDesk first (highest quality)
        try:
            from services.coindesk_historical import get_historical_service
            coindesk = get_historical_service()
            
            days = (end_date - start_date).days
            result = await coindesk.get_daily_ohlcv(
                symbol=symbol,
                quote=quote,
                market="kraken",
                limit=min(days, 2000)
            )
            
            if result and "data" in result and result["data"]:
                logger.info(f"Fetched {symbol} from CoinDesk")
                result['source'] = 'coindesk'
                return result
        except Exception as e:
            logger.warning(f"CoinDesk fetch failed: {e}")
        
        # Try Kraken API
        try:
            from services.market_data_service import MarketDataService
            market_service = MarketDataService()
            
            days = (end_date - start_date).days
            result = await market_service.get_historical_from_kraken(
                f"{symbol.lower()}",
                days=days
            )
            
            if result and "prices" in result:
                # Convert to standard format
                data = self._convert_kraken_format(result)
                logger.info(f"Fetched {symbol} from Kraken")
                return {
                    "symbol": symbol,
                    "quote": quote,
                    "data": data,
                    "source": "kraken"
                }
        except Exception as e:
            logger.warning(f"Kraken fetch failed: {e}")
        
        # Try CoinGecko as last resort
        try:
            from services.market_data_service import MarketDataService
            market_service = MarketDataService()
            
            days = (end_date - start_date).days
            result = await market_service.get_historical_data(
                f"{symbol.lower()}",
                days=min(days, 365)
            )
            
            if result and "prices" in result:
                data = self._convert_coingecko_format(result)
                logger.info(f"Fetched {symbol} from CoinGecko")
                return {
                    "symbol": symbol,
                    "quote": quote,
                    "data": data,
                    "source": "coingecko"
                }
        except Exception as e:
            logger.warning(f"CoinGecko fetch failed: {e}")
        
        return None
    
    def _convert_kraken_format(self, kraken_data: Dict) -> List[Dict]:
        """Convert Kraken format to standard OHLCV format"""
        data = []
        prices = kraken_data.get("prices", [])
        volumes = kraken_data.get("total_volumes", [])
        
        for i, item in enumerate(prices):
            volume = volumes[i][1] if i < len(volumes) else 0
            data.append({
                "timestamp": item[0] // 1000,  # Convert ms to seconds
                "open": item[1],
                "high": item[1],  # Kraken historical doesn't provide OHLC
                "low": item[1],
                "close": item[1],
                "volume": volume
            })
        
        return data
    
    def _convert_coingecko_format(self, coingecko_data: Dict) -> List[Dict]:
        """Convert CoinGecko format to standard OHLCV format"""
        data = []
        prices = coingecko_data.get("prices", [])
        volumes = coingecko_data.get("total_volumes", [])
        
        for i, price_point in enumerate(prices):
            volume = volumes[i][1] if i < len(volumes) else 0
            data.append({
                "timestamp": price_point[0] // 1000,  # Convert ms to seconds
                "open": price_point[1],
                "high": price_point[1],
                "low": price_point[1],
                "close": price_point[1],
                "volume": volume
            })
        
        return data
    
    async def _validate_and_store(
        self,
        data: Dict[str, Any],
        symbol: str,
        quote: str,
        interval: str
    ) -> List[Dict[str, Any]]:
        """Validate data quality and store in database"""
        ohlcv_data = data.get("data", [])
        source = data.get("source", "unknown")
        
        # Validate data quality
        validated_data = []
        for i, candle in enumerate(ohlcv_data):
            quality_issues = []
            
            # Check for price anomalies
            if i > 0:
                prev_close = validated_data[-1]["close"]
                price_change = abs(candle["close"] - prev_close) / prev_close
                if price_change > self.quality_thresholds["max_price_deviation"]:
                    quality_issues.append("high_price_deviation")
            
            # Check for volume anomalies
            if candle.get("volume", 0) == 0:
                quality_issues.append("zero_volume")
            
            # Add quality metadata
            candle_with_meta = {
                **candle,
                "symbol": symbol.upper(),
                "quote": quote.upper(),
                "interval": interval,
                "source": source,
                "source_priority": self.source_priority.get(source, 0),
                "quality_issues": quality_issues,
                "validated_at": datetime.now(timezone.utc),
                "date": datetime.fromtimestamp(candle["timestamp"], tz=timezone.utc).strftime("%Y-%m-%d")
            }
            
            validated_data.append(candle_with_meta)
        
        # Store in database (upsert to avoid duplicates)
        if validated_data:
            try:
                operations = []
                for candle in validated_data:
                    operations.append({
                        "filter": {
                            "symbol": candle["symbol"],
                            "quote": candle["quote"],
                            "interval": candle["interval"],
                            "timestamp": candle["timestamp"]
                        },
                        "update": {"$set": candle},
                        "upsert": True
                    })
                
                # Batch update
                if operations:
                    # Use update_many approach for efficiency
                    for op in operations:
                        await self.collection.update_one(
                            op["filter"],
                            op["update"],
                            upsert=op["upsert"]
                        )
                
                logger.info(f"Stored {len(validated_data)} candles for {symbol}/{quote}")
            except Exception as e:
                logger.error(f"Failed to store data: {e}")
        
        return validated_data
    
    def _is_data_complete(
        self,
        data: List[Dict],
        start_date: datetime,
        end_date: datetime
    ) -> bool:
        """Check if data covers the requested time range without major gaps"""
        if not data:
            return False
        
        # Check if we have data at the boundaries
        first_timestamp = data[0]["timestamp"]
        last_timestamp = data[-1]["timestamp"]
        
        start_ts = int(start_date.timestamp())
        end_ts = int(end_date.timestamp())
        
        # Allow 2-day tolerance
        tolerance = 2 * 86400
        
        return (
            first_timestamp <= start_ts + tolerance and
            last_timestamp >= end_ts - tolerance
        )
    
    def _format_response(
        self,
        data: List[Dict[str, Any]],
        source: str
    ) -> Dict[str, Any]:
        """Format data into standard response structure"""
        if not data:
            return {
                "data": [],
                "count": 0,
                "source": source
            }
        
        # Remove metadata fields for response
        clean_data = []
        for candle in data:
            clean_data.append({
                "timestamp": candle["timestamp"],
                "date": candle.get("date", datetime.fromtimestamp(candle["timestamp"], tz=timezone.utc).strftime("%Y-%m-%d")),
                "open": candle["open"],
                "high": candle["high"],
                "low": candle["low"],
                "close": candle["close"],
                "volume": candle.get("volume", 0)
            })
        
        return {
            "symbol": data[0].get("symbol", ""),
            "quote": data[0].get("quote", "USD"),
            "interval": data[0].get("interval", "daily"),
            "data": clean_data,
            "count": len(clean_data),
            "source": source,
            "earliest_date": clean_data[0]["date"],
            "latest_date": clean_data[-1]["date"],
            "quality_summary": self._get_quality_summary(data)
        }
    
    def _get_quality_summary(self, data: List[Dict]) -> Dict[str, Any]:
        """Generate quality summary for the dataset"""
        total_issues = 0
        issue_types = {}
        
        for candle in data:
            issues = candle.get("quality_issues", [])
            total_issues += len(issues)
            for issue in issues:
                issue_types[issue] = issue_types.get(issue, 0) + 1
        
        return {
            "total_candles": len(data),
            "candles_with_issues": sum(1 for c in data if c.get("quality_issues")),
            "issue_breakdown": issue_types,
            "quality_score": max(0, 100 - (total_issues / len(data) * 100)) if data else 0
        }
    
    async def get_data_gaps(
        self,
        symbol: str,
        quote: str = "USD",
        interval: str = "daily"
    ) -> List[Dict[str, Any]]:
        """Identify gaps in historical data"""
        try:
            query = {
                "symbol": symbol.upper(),
                "quote": quote.upper(),
                "interval": interval
            }
            
            cursor = self.collection.find(query).sort("timestamp", 1)
            data = await cursor.to_list(length=None)
            
            if len(data) < 2:
                return []
            
            gaps = []
            expected_interval = 86400 if interval == "daily" else 3600  # seconds
            
            for i in range(1, len(data)):
                time_diff = data[i]["timestamp"] - data[i-1]["timestamp"]
                if time_diff > expected_interval * 1.5:  # Allow 50% tolerance
                    gaps.append({
                        "gap_start": datetime.fromtimestamp(data[i-1]["timestamp"], tz=timezone.utc).isoformat(),
                        "gap_end": datetime.fromtimestamp(data[i]["timestamp"], tz=timezone.utc).isoformat(),
                        "gap_duration_days": time_diff / 86400,
                        "missing_candles": int(time_diff / expected_interval) - 1
                    })
            
            return gaps
        except Exception as e:
            logger.error(f"Error finding gaps: {e}")
            return []
    
    async def get_quality_report(
        self,
        symbol: str,
        quote: str = "USD",
        interval: str = "daily"
    ) -> Dict[str, Any]:
        """Get comprehensive quality report for a symbol"""
        try:
            query = {
                "symbol": symbol.upper(),
                "quote": quote.upper(),
                "interval": interval
            }
            
            cursor = self.collection.find(query)
            data = await cursor.to_list(length=None)
            
            if not data:
                return {
                    "symbol": symbol,
                    "error": "No data available"
                }
            
            # Find gaps
            gaps = await self.get_data_gaps(symbol, quote, interval)
            
            # Quality metrics
            issues_by_type = {}
            for candle in data:
                for issue in candle.get("quality_issues", []):
                    issues_by_type[issue] = issues_by_type.get(issue, 0) + 1
            
            # Source breakdown
            sources = {}
            for candle in data:
                source = candle.get("source", "unknown")
                sources[source] = sources.get(source, 0) + 1
            
            return {
                "symbol": symbol,
                "quote": quote,
                "interval": interval,
                "total_candles": len(data),
                "date_range": {
                    "earliest": datetime.fromtimestamp(data[0]["timestamp"], tz=timezone.utc).isoformat(),
                    "latest": datetime.fromtimestamp(data[-1]["timestamp"], tz=timezone.utc).isoformat()
                },
                "gaps": {
                    "count": len(gaps),
                    "details": gaps[:10]  # Limit to first 10 gaps
                },
                "quality_issues": {
                    "total": sum(issues_by_type.values()),
                    "by_type": issues_by_type
                },
                "sources": sources,
                "quality_score": max(0, 100 - (sum(issues_by_type.values()) / len(data) * 100))
            }
        except Exception as e:
            logger.error(f"Error generating quality report: {e}")
            return {"error": str(e)}


# Singleton instance
_historical_data_manager = None


def get_historical_data_manager(db: AsyncIOMotorDatabase) -> HistoricalDataManager:
    """Get or create historical data manager instance"""
    global _historical_data_manager
    if _historical_data_manager is None:
        _historical_data_manager = HistoricalDataManager(db)
    return _historical_data_manager

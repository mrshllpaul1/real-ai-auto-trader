"""
CoinDesk Historical Data Service
Provides comprehensive historical OHLCV data for AI training.
Uses the same API key as the news service (11,000 credits/month).
"""

import os
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from httpx import AsyncClient
import time

COINDESK_API_KEY = os.getenv('COINDESK_API_KEY', '')
COINDESK_DATA_URL = "https://data-api.coindesk.com"

# Cache for historical data (longer TTL since historical data doesn't change)
_historical_cache = {}
_cache_ttl = 3600  # 1 hour cache for historical data


class CoinDeskHistoricalService:
    """
    CoinDesk Historical Data API client for AI training.
    Provides OHLCV data from 2010+ for 10,000+ coins.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or COINDESK_API_KEY
        self.base_url = COINDESK_DATA_URL
        
    async def _request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make authenticated request to CoinDesk Data API"""
        if not self.api_key:
            return {"error": "CoinDesk API key not configured"}
        
        url = f"{self.base_url}{endpoint}"
        
        if params is None:
            params = {}
        params["api_key"] = self.api_key
        
        try:
            async with AsyncClient(timeout=60) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    return {"error": "Rate limit exceeded", "status": 429}
                else:
                    return {"error": f"API error: {response.status_code}", "status": response.status_code}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_daily_ohlcv(
        self,
        symbol: str = "BTC",
        quote: str = "USD",
        market: str = "kraken",
        limit: int = 2000,
        to_timestamp: int = None
    ) -> Dict[str, Any]:
        """
        Get daily OHLCV candlestick data.
        
        Args:
            symbol: Base asset (BTC, ETH, SOL, etc.)
            quote: Quote currency (USD, EUR, etc.)
            market: Exchange (kraken, coinbase, binance, etc.)
            limit: Number of days (max 2000)
            to_timestamp: Unix timestamp to get data up to (default: now)
        
        Returns:
            Dict with OHLCV data array
        """
        cache_key = f"daily_{market}_{symbol}_{quote}_{limit}_{to_timestamp}"
        
        # Check cache
        if cache_key in _historical_cache:
            cached = _historical_cache[cache_key]
            if time.time() - cached["timestamp"] < _cache_ttl:
                return cached["data"]
        
        instrument = f"{symbol}-{quote}"
        params = {
            "market": market,
            "instrument": instrument,
            "limit": min(limit, 2000),
            "aggregate": 1,
            "fill": "true",
            "apply_mapping": "true",
            "response_format": "JSON"
        }
        
        if to_timestamp:
            params["to_ts"] = to_timestamp
        
        result = await self._request("/spot/v1/historical/days", params)
        
        if "Data" in result:
            ohlcv_data = []
            for candle in result.get("Data", []):
                ohlcv_data.append({
                    "timestamp": candle.get("TIMESTAMP"),
                    "date": datetime.fromtimestamp(candle.get("TIMESTAMP", 0), tz=timezone.utc).strftime("%Y-%m-%d"),
                    "open": candle.get("OPEN", 0),
                    "high": candle.get("HIGH", 0),
                    "low": candle.get("LOW", 0),
                    "close": candle.get("CLOSE", 0),
                    "volume": candle.get("VOLUME", 0),
                    "quote_volume": candle.get("QUOTE_VOLUME", 0),
                    "trades": candle.get("TOTAL_TRADES", 0)
                })
            
            response = {
                "symbol": symbol,
                "quote": quote,
                "market": market,
                "interval": "daily",
                "count": len(ohlcv_data),
                "data": ohlcv_data,
                "earliest_date": ohlcv_data[-1]["date"] if ohlcv_data else None,
                "latest_date": ohlcv_data[0]["date"] if ohlcv_data else None
            }
            
            # Cache the response
            _historical_cache[cache_key] = {
                "data": response,
                "timestamp": time.time()
            }
            
            return response
        
        return result
    
    async def get_hourly_ohlcv(
        self,
        symbol: str = "BTC",
        quote: str = "USD",
        market: str = "kraken",
        limit: int = 2000,
        to_timestamp: int = None
    ) -> Dict[str, Any]:
        """Get hourly OHLCV candlestick data"""
        instrument = f"{symbol}-{quote}"
        params = {
            "market": market,
            "instrument": instrument,
            "limit": min(limit, 2000),
            "aggregate": 1,
            "fill": "true",
            "apply_mapping": "true",
            "response_format": "JSON"
        }
        
        if to_timestamp:
            params["to_ts"] = to_timestamp
        
        result = await self._request("/spot/v1/historical/hours", params)
        
        if "Data" in result:
            ohlcv_data = []
            for candle in result.get("Data", []):
                ohlcv_data.append({
                    "timestamp": candle.get("TIMESTAMP"),
                    "datetime": datetime.fromtimestamp(candle.get("TIMESTAMP", 0), tz=timezone.utc).isoformat(),
                    "open": candle.get("OPEN", 0),
                    "high": candle.get("HIGH", 0),
                    "low": candle.get("LOW", 0),
                    "close": candle.get("CLOSE", 0),
                    "volume": candle.get("VOLUME", 0),
                    "quote_volume": candle.get("QUOTE_VOLUME", 0),
                    "trades": candle.get("TOTAL_TRADES", 0)
                })
            
            return {
                "symbol": symbol,
                "quote": quote,
                "market": market,
                "interval": "hourly",
                "count": len(ohlcv_data),
                "data": ohlcv_data
            }
        
        return result
    
    async def get_full_history(
        self,
        symbol: str = "BTC",
        quote: str = "USD",
        market: str = "kraken",
        start_year: int = 2010
    ) -> Dict[str, Any]:
        """
        Get complete historical data from start_year to present.
        Chains multiple requests to get full history.
        
        WARNING: This uses multiple API calls. Use sparingly.
        """
        all_data = []
        to_ts = None
        batch_count = 0
        max_batches = 10  # Safety limit
        
        while batch_count < max_batches:
            batch = await self.get_daily_ohlcv(
                symbol=symbol,
                quote=quote,
                market=market,
                limit=2000,
                to_timestamp=to_ts
            )
            
            if "error" in batch or not batch.get("data"):
                break
            
            data = batch.get("data", [])
            all_data.extend(data)
            
            # Check if we've reached the start year
            if data:
                earliest = data[-1]
                earliest_date = datetime.fromtimestamp(earliest["timestamp"], tz=timezone.utc)
                
                if earliest_date.year <= start_year:
                    break
                
                # Set to_ts for next batch (subtract 1 day to avoid overlap)
                to_ts = earliest["timestamp"] - 86400
            
            batch_count += 1
            await asyncio.sleep(0.5)  # Rate limiting
        
        # Remove duplicates and sort by date
        seen = set()
        unique_data = []
        for d in all_data:
            if d["timestamp"] not in seen:
                seen.add(d["timestamp"])
                unique_data.append(d)
        
        unique_data.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "symbol": symbol,
            "quote": quote,
            "market": market,
            "interval": "daily",
            "count": len(unique_data),
            "batches_fetched": batch_count,
            "data": unique_data,
            "earliest_date": unique_data[-1]["date"] if unique_data else None,
            "latest_date": unique_data[0]["date"] if unique_data else None,
            "years_covered": (
                datetime.strptime(unique_data[0]["date"], "%Y-%m-%d").year - 
                datetime.strptime(unique_data[-1]["date"], "%Y-%m-%d").year + 1
            ) if unique_data else 0
        }
    
    async def get_training_dataset(
        self,
        symbols: List[str] = None,
        quote: str = "USD",
        market: str = "kraken",
        days: int = 365
    ) -> Dict[str, Any]:
        """
        Get training dataset for multiple coins.
        Returns OHLCV data formatted for ML training.
        
        Args:
            symbols: List of coin symbols (default: top coins)
            quote: Quote currency
            market: Exchange
            days: Number of days of history
        
        Returns:
            Dict with training data for each coin
        """
        if symbols is None:
            symbols = ["BTC", "ETH", "SOL", "XRP", "DOT", "ADA", "AVAX", "LINK", "UNI", "AAVE"]
        
        training_data = {}
        
        for symbol in symbols:
            try:
                data = await self.get_daily_ohlcv(
                    symbol=symbol,
                    quote=quote,
                    market=market,
                    limit=min(days, 2000)
                )
                
                if "data" in data and data["data"]:
                    # Extract features for ML
                    prices = [d["close"] for d in data["data"]]
                    volumes = [d["volume"] for d in data["data"]]
                    
                    training_data[symbol] = {
                        "ohlcv": data["data"],
                        "prices": prices,
                        "volumes": volumes,
                        "count": len(prices),
                        "date_range": {
                            "start": data.get("earliest_date"),
                            "end": data.get("latest_date")
                        }
                    }
                
                await asyncio.sleep(0.3)  # Rate limiting
                
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                continue
        
        return {
            "coins": list(training_data.keys()),
            "coin_count": len(training_data),
            "days_requested": days,
            "market": market,
            "data": training_data,
            "ready_for_training": len(training_data) > 0
        }


# Singleton instance
_historical_service = None

def get_historical_service() -> CoinDeskHistoricalService:
    """Get or create historical data service instance"""
    global _historical_service
    if _historical_service is None:
        _historical_service = CoinDeskHistoricalService()
    return _historical_service

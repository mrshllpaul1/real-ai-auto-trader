"""
Multi-Timeframe Historical Data Service
Extended historical data with multiple timeframes for comprehensive AI training.

Timeframes supported:
- 1m, 5m, 15m, 30m (recent data only - last 7 days)
- 1h, 4h (last 30 days)
- 1D (full history - up to 10+ years)
- 1W (full history)

Data sources:
- Kraken API (primary for Kraken pairs)
- CryptoCompare API (backup/extended history)
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from httpx import AsyncClient
import logging

logger = logging.getLogger(__name__)

# API endpoints
KRAKEN_API_URL = "https://api.kraken.com"


class MultiTimeframeHistoricalService:
    """
    Multi-timeframe historical data service.
    
    Provides:
    - Extended historical data (10+ years where available)
    - Multiple timeframe analysis (1m to 1W)
    - Kraken-specific OHLCV data
    - Automatic backfilling
    """
    
    # Kraken interval mappings (in minutes)
    KRAKEN_INTERVALS = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "4h": 240,
        "1D": 1440,
        "1W": 10080
    }
    
    # Maximum history per timeframe (in days)
    MAX_HISTORY = {
        "1m": 7,       # 7 days of minute data
        "5m": 14,      # 14 days
        "15m": 30,     # 30 days
        "30m": 60,     # 60 days
        "1h": 180,     # 6 months
        "4h": 365,     # 1 year
        "1D": 3650,    # 10 years
        "1W": 3650     # 10 years
    }
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection_prefix = "ohlcv_"
        self._cache: Dict[str, Any] = {}
        
    def _get_collection_name(self, timeframe: str) -> str:
        """Get collection name for a timeframe"""
        return f"{self.collection_prefix}{timeframe.replace('m', 'min').replace('h', 'hour').replace('D', 'day').replace('W', 'week')}"
    
    async def fetch_kraken_ohlc(
        self,
        pair: str,
        interval: int,
        since: int = None
    ) -> Dict[str, Any]:
        """
        Fetch OHLC data from Kraken public API.
        
        Args:
            pair: Trading pair (e.g., XBTUSD, ETHUSD)
            interval: Candle interval in minutes
            since: Unix timestamp to fetch data from
        
        Returns:
            Dict with OHLC data
        """
        params = {
            "pair": pair,
            "interval": interval
        }
        if since:
            params["since"] = since
        
        try:
            async with AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{KRAKEN_API_URL}/0/public/OHLC",
                    params=params,
                    headers={"User-Agent": "CryptoTradingBot/1.0"}
                )
                data = response.json()
                
                if data.get("error") and len(data["error"]) > 0:
                    return {"error": data["error"]}
                
                result = data.get("result", {})
                
                # Extract OHLC data (key is the pair name, might be different format)
                ohlc_data = None
                for key, value in result.items():
                    if key != "last":
                        ohlc_data = value
                        break
                
                if ohlc_data:
                    return {
                        "pair": pair,
                        "interval": interval,
                        "data": ohlc_data,
                        "last": result.get("last"),
                        "count": len(ohlc_data)
                    }
                
                return {"error": "No OHLC data in response"}
                
        except Exception as e:
            return {"error": str(e)}
    
    async def download_timeframe_data(
        self,
        symbol: str,
        timeframe: str,
        kraken_pair: str = None
    ) -> Dict[str, Any]:
        """
        Download and store OHLC data for a specific timeframe.
        
        Args:
            symbol: Coin symbol (e.g., BTC, ETH)
            timeframe: Timeframe string (1m, 5m, 15m, 30m, 1h, 4h, 1D, 1W)
            kraken_pair: Kraken pair name (optional, will be constructed)
        
        Returns:
            Dict with download results
        """
        interval = self.KRAKEN_INTERVALS.get(timeframe)
        if not interval:
            return {"error": f"Invalid timeframe: {timeframe}"}
        
        # Construct Kraken pair if not provided
        if not kraken_pair:
            # Try common formats
            if symbol.upper() == "BTC":
                kraken_pair = "XBTUSD"
            else:
                kraken_pair = f"{symbol.upper()}USD"
        
        logger.info(f"📊 Downloading {symbol} {timeframe} data from Kraken...")
        
        # Calculate since timestamp based on max history
        max_days = self.MAX_HISTORY.get(timeframe, 30)
        since_ts = int((datetime.now(timezone.utc) - timedelta(days=max_days)).timestamp())
        
        # Fetch data from Kraken
        result = await self.fetch_kraken_ohlc(kraken_pair, interval, since_ts)
        
        if "error" in result:
            # Try alternative pair format
            alt_pair = f"X{symbol.upper()}ZUSD" if symbol.upper() != "BTC" else "XXBTZUSD"
            result = await self.fetch_kraken_ohlc(alt_pair, interval, since_ts)
            
            if "error" in result:
                return result
        
        ohlc_data = result.get("data", [])
        
        if not ohlc_data:
            return {"error": "No data returned"}
        
        # Parse OHLC data
        # Kraken format: [timestamp, open, high, low, close, vwap, volume, count]
        documents = []
        for candle in ohlc_data:
            try:
                ts = int(candle[0])
                documents.append({
                    "symbol": symbol.upper(),
                    "timeframe": timeframe,
                    "timestamp": ts,
                    "datetime": datetime.fromtimestamp(ts, tz=timezone.utc),
                    "date": datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d"),
                    "open": float(candle[1]),
                    "high": float(candle[2]),
                    "low": float(candle[3]),
                    "close": float(candle[4]),
                    "vwap": float(candle[5]),
                    "volume": float(candle[6]),
                    "trade_count": int(candle[7]),
                    "source": "kraken"
                })
            except (IndexError, ValueError) as e:
                continue
        
        if not documents:
            return {"error": "Failed to parse OHLC data"}
        
        # Store in database
        collection = self.db[self._get_collection_name(timeframe)]
        
        # Remove existing data for this symbol/timeframe
        await collection.delete_many({
            "symbol": symbol.upper(),
            "timeframe": timeframe
        })
        
        # Insert new data
        await collection.insert_many(documents)
        
        # Create indexes
        await collection.create_index([("symbol", 1), ("timestamp", 1)])
        await collection.create_index([("symbol", 1), ("timeframe", 1), ("timestamp", 1)])
        
        return {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "kraken_pair": kraken_pair,
            "records_stored": len(documents),
            "date_range": {
                "from": documents[0]["date"] if documents else None,
                "to": documents[-1]["date"] if documents else None
            },
            "source": "kraken",
            "status": "success"
        }
    
    async def download_all_timeframes(
        self,
        symbol: str,
        kraken_pair: str = None,
        timeframes: List[str] = None
    ) -> Dict[str, Any]:
        """
        Download all timeframes for a symbol.
        
        Args:
            symbol: Coin symbol
            kraken_pair: Kraken pair name (optional)
            timeframes: List of timeframes to download (default: all)
        
        Returns:
            Dict with results per timeframe
        """
        if timeframes is None:
            timeframes = list(self.KRAKEN_INTERVALS.keys())
        
        results = {
            "symbol": symbol.upper(),
            "timeframes": {},
            "errors": []
        }
        
        for tf in timeframes:
            try:
                result = await self.download_timeframe_data(symbol, tf, kraken_pair)
                results["timeframes"][tf] = result
                
                if "error" in result:
                    results["errors"].append({"timeframe": tf, "error": result["error"]})
                
                # Brief delay between requests
                await asyncio.sleep(0.5)
                
            except Exception as e:
                results["errors"].append({"timeframe": tf, "error": str(e)})
        
        results["success_count"] = len([tf for tf, r in results["timeframes"].items() if "error" not in r])
        results["error_count"] = len(results["errors"])
        results["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        return results
    
    async def get_ohlc_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = None
    ) -> Dict[str, Any]:
        """
        Get stored OHLC data for a symbol and timeframe.
        
        Args:
            symbol: Coin symbol
            timeframe: Timeframe string
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum records to return
        
        Returns:
            Dict with OHLC data
        """
        collection = self.db[self._get_collection_name(timeframe)]
        
        query = {
            "symbol": symbol.upper(),
            "timeframe": timeframe
        }
        
        if start_date:
            query["timestamp"] = {"$gte": int(start_date.timestamp())}
        
        if end_date:
            if "timestamp" in query:
                query["timestamp"]["$lte"] = int(end_date.timestamp())
            else:
                query["timestamp"] = {"$lte": int(end_date.timestamp())}
        
        cursor = collection.find(query, {"_id": 0}).sort("timestamp", 1)
        
        if limit:
            cursor = cursor.limit(limit)
        
        data = await cursor.to_list(length=limit or 10000)
        
        return {
            "symbol": symbol.upper(),
            "timeframe": timeframe,
            "count": len(data),
            "data": data,
            "date_range": {
                "from": data[0]["date"] if data else None,
                "to": data[-1]["date"] if data else None
            }
        }
    
    async def get_multi_timeframe_data(
        self,
        symbol: str,
        timeframes: List[str] = None,
        limit_per_tf: int = 100
    ) -> Dict[str, Any]:
        """
        Get data for multiple timeframes at once.
        Useful for multi-timeframe analysis in ML models.
        """
        if timeframes is None:
            timeframes = ["1h", "4h", "1D"]
        
        results = {
            "symbol": symbol.upper(),
            "timeframes": {}
        }
        
        for tf in timeframes:
            data = await self.get_ohlc_data(symbol, tf, limit=limit_per_tf)
            results["timeframes"][tf] = data
        
        results["timestamp"] = datetime.now(timezone.utc).isoformat()
        return results
    
    async def get_training_features(
        self,
        symbol: str,
        timeframes: List[str] = None
    ) -> Dict[str, Any]:
        """
        Get multi-timeframe features formatted for ML training.
        Includes technical indicators calculated at each timeframe.
        """
        import numpy as np
        
        if timeframes is None:
            timeframes = ["1h", "4h", "1D"]
        
        features = {
            "symbol": symbol.upper(),
            "timeframes": {}
        }
        
        for tf in timeframes:
            data_result = await self.get_ohlc_data(symbol, tf, limit=200)
            data = data_result.get("data", [])
            
            if len(data) < 50:
                continue
            
            closes = [d["close"] for d in data]
            highs = [d["high"] for d in data]
            lows = [d["low"] for d in data]
            volumes = [d["volume"] for d in data]
            
            # Calculate indicators
            closes_arr = np.array(closes)
            
            # SMAs
            sma_7 = np.convolve(closes_arr, np.ones(7)/7, mode='valid')[-1] if len(closes) >= 7 else closes[-1]
            sma_20 = np.convolve(closes_arr, np.ones(20)/20, mode='valid')[-1] if len(closes) >= 20 else closes[-1]
            sma_50 = np.convolve(closes_arr, np.ones(50)/50, mode='valid')[-1] if len(closes) >= 50 else closes[-1]
            
            # Returns
            returns = np.diff(closes_arr) / closes_arr[:-1] * 100
            
            # Volatility
            volatility = np.std(returns[-20:]) if len(returns) >= 20 else 0
            
            # RSI (14-period)
            gains = returns[returns > 0]
            losses = -returns[returns < 0]
            avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else 0
            avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else 0.001
            rsi = 100 - (100 / (1 + avg_gain / avg_loss))
            
            # Volume ratio
            vol_arr = np.array(volumes)
            vol_sma = np.mean(vol_arr[-20:]) if len(vol_arr) >= 20 else vol_arr[-1]
            vol_ratio = vol_arr[-1] / vol_sma if vol_sma > 0 else 1
            
            features["timeframes"][tf] = {
                "close": closes[-1],
                "sma_7": float(sma_7),
                "sma_20": float(sma_20),
                "sma_50": float(sma_50),
                "rsi": float(rsi),
                "volatility": float(volatility),
                "volume_ratio": float(vol_ratio),
                "return_1": float(returns[-1]) if len(returns) > 0 else 0,
                "return_5": float(np.sum(returns[-5:])) if len(returns) >= 5 else 0,
                "return_10": float(np.sum(returns[-10:])) if len(returns) >= 10 else 0,
                "high_low_range": (highs[-1] - lows[-1]) / closes[-1] * 100,
                "data_points": len(data)
            }
        
        features["timestamp"] = datetime.now(timezone.utc).isoformat()
        return features
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about stored multi-timeframe data"""
        stats = {
            "timeframes": {},
            "total_records": 0
        }
        
        for tf in self.KRAKEN_INTERVALS.keys():
            collection = self.db[self._get_collection_name(tf)]
            
            count = await collection.count_documents({})
            symbols = await collection.distinct("symbol")
            
            stats["timeframes"][tf] = {
                "collection": self._get_collection_name(tf),
                "total_records": count,
                "symbols": symbols,
                "symbol_count": len(symbols)
            }
            stats["total_records"] += count
        
        stats["timestamp"] = datetime.now(timezone.utc).isoformat()
        return stats
    
    async def backfill_all_kraken_coins(
        self,
        coins: List[str] = None,
        timeframes: List[str] = None
    ) -> Dict[str, Any]:
        """
        Backfill historical data for all Kraken coins.
        
        Args:
            coins: List of coin symbols (optional, will use all from universe)
            timeframes: List of timeframes to backfill
        """
        from services.kraken_universe_manager import get_kraken_universe_manager
        
        if coins is None:
            # Get all coins from Kraken universe
            universe_mgr = get_kraken_universe_manager(self.db)
            if universe_mgr:
                coins = await universe_mgr.get_training_coin_list()
            else:
                coins = ["BTC", "ETH", "SOL", "ADA", "DOT", "AVAX", "LINK", "MATIC"]
        
        if timeframes is None:
            timeframes = ["1h", "4h", "1D"]  # Most useful for training
        
        results = {
            "coins_processed": [],
            "errors": [],
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
        for coin in coins:
            try:
                logger.info(f"📊 Backfilling {coin}...")
                coin_result = await self.download_all_timeframes(coin, timeframes=timeframes)
                results["coins_processed"].append({
                    "symbol": coin,
                    "success_count": coin_result["success_count"],
                    "error_count": coin_result["error_count"]
                })
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                results["errors"].append({"symbol": coin, "error": str(e)})
        
        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        results["total_coins"] = len(coins)
        results["successful_coins"] = len([c for c in results["coins_processed"] if c["success_count"] > 0])
        
        return results


# Global instance
_mtf_service: Optional[MultiTimeframeHistoricalService] = None


def get_multitimeframe_service(db: AsyncIOMotorDatabase = None) -> Optional[MultiTimeframeHistoricalService]:
    """Get or create Multi-Timeframe Historical Service instance"""
    global _mtf_service
    if _mtf_service is None and db is not None:
        _mtf_service = MultiTimeframeHistoricalService(db)
    return _mtf_service

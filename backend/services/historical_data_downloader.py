"""
Historical Data Downloader Service
Downloads and stores historical OHLCV data from CryptoCompare for AI training.
"""

import os
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import numpy as np
import talib

from services.coindesk_service import get_cryptocompare_service


# Download status tracking
_download_status = {
    "running": False,
    "started_at": None,
    "progress": 0,
    "current_coin": None,
    "coins_completed": 0,
    "coins_total": 0,
    "message": "",
    "error": None,
    "result": None
}


def get_download_status() -> Dict[str, Any]:
    """Get current download status"""
    return _download_status.copy()


class HistoricalDataDownloader:
    """
    Downloads and stores historical OHLCV data for AI training.
    Uses CryptoCompare API via the user's CoinDesk API key.
    """
    
    # MASTER LIST: All AI favorite coins (200+ coins for comprehensive training)
    ALL_AI_COINS = [
        # Tier 1: Major cryptocurrencies (50)
        "BTC", "ETH", "XRP", "SOL", "ADA", "DOGE", "DOT", "AVAX", "LINK", "MATIC",
        "UNI", "ATOM", "LTC", "BCH", "NEAR", "APT", "SUI", "ICP", "FIL", "ARB",
        "OP", "IMX", "AAVE", "MKR", "CRV", "SNX", "COMP", "YFI", "SUSHI", "1INCH",
        "XMR", "ZEC", "DASH", "ETC", "XLM", "VET", "ALGO", "HBAR", "EOS", "XTZ",
        "SAND", "MANA", "AXS", "ENJ", "GALA", "APE", "SHIB", "PEPE", "FLOKI", "WIF",
        
        # Tier 2: DeFi & Layer 2 (50)
        "FTM", "RUNE", "INJ", "SEI", "TIA", "PYTH", "JUP", "W", "STRK", "BLUR",
        "BONK", "RNDR", "FET", "AGIX", "OCEAN", "GRT", "LDO", "RPL", "SSV", "PENDLE",
        "GMX", "DYDX", "CAKE", "JOE", "QUICK", "BAL", "KNC", "PERP", "LQTY", "SPELL",
        "CVX", "FXS", "FRAX", "LUSD", "RAI", "MIM", "ALCX", "OHM", "TOKE", "BTRFLY",
        "RBN", "JONES", "DPX", "LYRA", "PREMIA", "HEGIC", "OPYN", "RIBBON", "PODS", "SIREN",
        
        # Tier 3: Gaming & Metaverse (50)
        "IMX", "GODS", "ILV", "YGG", "MC", "ALICE", "TLM", "STARL", "WAXP", "UFO",
        "ATLAS", "POLIS", "GENE", "DFL", "SLP", "AXS", "MBOX", "HERO", "PYR", "REVV",
        "TOWER", "SKILL", "WILD", "NAKA", "CEEK", "HIGH", "VOXEL", "GHST", "RACA", "DPET",
        "BAKE", "BURGER", "MANA", "SAND", "GALA", "ENJ", "CHZ", "FLOW", "THETA", "TFUEL",
        "AUDIO", "LPT", "LIVEPEER", "RAD", "GTC", "API3", "BAND", "TRB", "DIA", "UMA",
        
        # Tier 4: Infrastructure & Scaling (50)
        "MATIC", "ARB", "OP", "ZK", "STRK", "MANTA", "BLAST", "SCROLL", "LINEA", "BASE",
        "CELO", "KAVA", "ONE", "FTM", "GLMR", "MOVR", "ASTR", "SDN", "AURORA", "BOBA",
        "METIS", "EVMOS", "OSMO", "JUNO", "SCRT", "AKASH", "REGEN", "DVPN", "BAND", "KAVA",
        "ROSE", "MINA", "CKB", "KDA", "FLUX", "HNT", "IOT", "MOBILE", "QNT", "LINK",
        "API3", "BAND", "TRB", "DIA", "UMA", "NEST", "DOS", "BNT", "LRC", "ZRX",
        
        # Tier 5: AI & Data (30)
        "FET", "AGIX", "OCEAN", "NMR", "GRT", "RNDR", "THETA", "TFUEL", "LPT", "AR",
        "FIL", "STORJ", "SIA", "ANKR", "POKT", "AIOZ", "PHB", "MDT", "DBC", "NKN",
        "CTSI", "TRU", "GLM", "RLC", "iEXEC", "SONM", "GNO", "COW", "BAL", "DODO",
        
        # Tier 6: Meme & Community (20)
        "DOGE", "SHIB", "PEPE", "FLOKI", "WIF", "BONK", "BOME", "MEW", "POPCAT", "BRETT",
        "WOJAK", "TURBO", "LADYS", "AIDOGE", "BABYDOGE", "ELON", "SAMO", "CATE", "HOGE", "AKITA"
    ]
    
    # Top coins to download historical data for (prioritized by importance)
    TOP_COINS = ALL_AI_COINS[:50]  # First 50 for quick access
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.crypto_service = get_cryptocompare_service()
        self.collection_name = "historical_ohlcv"
    
    def _compute_technical_indicators(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compute technical indicators for the historical data.
        
        Args:
            data: List of OHLCV candles
        
        Returns:
            List of candles with added technical indicators
        """
        if not data or len(data) < 50:  # Need at least 50 data points for indicators
            return data
        
        try:
            # Convert to numpy arrays for TA-Lib
            closes = np.array([float(d.get("close", 0)) for d in data])
            highs = np.array([float(d.get("high", 0)) for d in data])
            lows = np.array([float(d.get("low", 0)) for d in data])
            opens = np.array([float(d.get("open", 0)) for d in data])
            volumes = np.array([float(d.get("volume_from", 0)) for d in data])
            
            # Compute RSI (14-period)
            rsi = talib.RSI(closes, timeperiod=14)
            
            # Compute MACD
            macd, macd_signal, macd_hist = talib.MACD(closes, fastperiod=12, slowperiod=26, signalperiod=9)
            
            # Compute Moving Averages
            sma_7 = talib.SMA(closes, timeperiod=7)
            sma_14 = talib.SMA(closes, timeperiod=14)
            sma_20 = talib.SMA(closes, timeperiod=20)
            sma_30 = talib.SMA(closes, timeperiod=30)
            sma_50 = talib.SMA(closes, timeperiod=50)
            
            ema_7 = talib.EMA(closes, timeperiod=7)
            ema_14 = talib.EMA(closes, timeperiod=14)
            ema_20 = talib.EMA(closes, timeperiod=20)
            ema_30 = talib.EMA(closes, timeperiod=30)
            ema_50 = talib.EMA(closes, timeperiod=50)
            
            # Compute Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(closes, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
            
            # Compute ATR (Average True Range)
            atr = talib.ATR(highs, lows, closes, timeperiod=14)
            
            # Compute returns and volatility
            returns = np.zeros(len(closes))
            returns[1:] = (closes[1:] - closes[:-1]) / closes[:-1] * 100  # Percentage returns
            
            # Rolling volatility (7-day and 14-day standard deviation of returns)
            volatility_7d = np.zeros(len(closes))
            volatility_14d = np.zeros(len(closes))
            
            for i in range(7, len(returns)):
                volatility_7d[i] = np.std(returns[i-7:i])
            
            for i in range(14, len(returns)):
                volatility_14d[i] = np.std(returns[i-14:i])
            
            # Price momentum (1d, 7d, 14d, 30d)
            momentum_1d = np.zeros(len(closes))
            momentum_7d = np.zeros(len(closes))
            momentum_14d = np.zeros(len(closes))
            momentum_30d = np.zeros(len(closes))
            
            for i in range(1, len(closes)):
                momentum_1d[i] = (closes[i] - closes[i-1]) / closes[i-1] * 100
            
            for i in range(7, len(closes)):
                momentum_7d[i] = (closes[i] - closes[i-7]) / closes[i-7] * 100
            
            for i in range(14, len(closes)):
                momentum_14d[i] = (closes[i] - closes[i-14]) / closes[i-14] * 100
            
            for i in range(30, len(closes)):
                momentum_30d[i] = (closes[i] - closes[i-30]) / closes[i-30] * 100
            
            # Volume surge ratio (current volume / 7-day average volume)
            volume_surge = np.zeros(len(volumes))
            for i in range(7, len(volumes)):
                avg_volume = np.mean(volumes[i-7:i])
                volume_surge[i] = volumes[i] / avg_volume if avg_volume > 0 else 1.0
            
            # VWAP (Volume-Weighted Average Price) - simplified daily calculation
            typical_price = (highs + lows + closes) / 3
            vwap = np.zeros(len(closes))
            for i in range(len(closes)):
                if volumes[i] > 0:
                    vwap[i] = typical_price[i]  # Simplified: just using typical price
                else:
                    vwap[i] = closes[i]
            
            # Add computed indicators to each candle
            for i, candle in enumerate(data):
                # Convert NaN to None for MongoDB storage
                candle["rsi"] = float(rsi[i]) if not np.isnan(rsi[i]) else None
                candle["macd"] = float(macd[i]) if not np.isnan(macd[i]) else None
                candle["macd_signal"] = float(macd_signal[i]) if not np.isnan(macd_signal[i]) else None
                candle["macd_hist"] = float(macd_hist[i]) if not np.isnan(macd_hist[i]) else None
                
                candle["sma_7"] = float(sma_7[i]) if not np.isnan(sma_7[i]) else None
                candle["sma_14"] = float(sma_14[i]) if not np.isnan(sma_14[i]) else None
                candle["sma_20"] = float(sma_20[i]) if not np.isnan(sma_20[i]) else None
                candle["sma_30"] = float(sma_30[i]) if not np.isnan(sma_30[i]) else None
                candle["sma_50"] = float(sma_50[i]) if not np.isnan(sma_50[i]) else None
                
                candle["ema_7"] = float(ema_7[i]) if not np.isnan(ema_7[i]) else None
                candle["ema_14"] = float(ema_14[i]) if not np.isnan(ema_14[i]) else None
                candle["ema_20"] = float(ema_20[i]) if not np.isnan(ema_20[i]) else None
                candle["ema_30"] = float(ema_30[i]) if not np.isnan(ema_30[i]) else None
                candle["ema_50"] = float(ema_50[i]) if not np.isnan(ema_50[i]) else None
                
                candle["bb_upper"] = float(bb_upper[i]) if not np.isnan(bb_upper[i]) else None
                candle["bb_middle"] = float(bb_middle[i]) if not np.isnan(bb_middle[i]) else None
                candle["bb_lower"] = float(bb_lower[i]) if not np.isnan(bb_lower[i]) else None
                
                candle["atr"] = float(atr[i]) if not np.isnan(atr[i]) else None
                
                candle["returns_pct"] = float(returns[i]) if not np.isnan(returns[i]) else None
                candle["volatility_7d"] = float(volatility_7d[i]) if not np.isnan(volatility_7d[i]) else None
                candle["volatility_14d"] = float(volatility_14d[i]) if not np.isnan(volatility_14d[i]) else None
                
                candle["momentum_1d"] = float(momentum_1d[i]) if not np.isnan(momentum_1d[i]) else None
                candle["momentum_7d"] = float(momentum_7d[i]) if not np.isnan(momentum_7d[i]) else None
                candle["momentum_14d"] = float(momentum_14d[i]) if not np.isnan(momentum_14d[i]) else None
                candle["momentum_30d"] = float(momentum_30d[i]) if not np.isnan(momentum_30d[i]) else None
                
                candle["volume_surge"] = float(volume_surge[i]) if not np.isnan(volume_surge[i]) else None
                candle["vwap"] = float(vwap[i]) if not np.isnan(vwap[i]) else None
            
            return data
            
        except Exception as e:
            print(f"Error computing technical indicators: {e}")
            # Return data without indicators if computation fails
            return data
        
    async def download_coin_history(
        self,
        coin_symbol: str,
        max_days: int = 5000
    ) -> Dict[str, Any]:
        """
        Download and store historical data for a single coin.
        
        Args:
            coin_symbol: Cryptocurrency symbol (e.g., BTC)
            max_days: Maximum days of history to fetch
        
        Returns:
            Dict with download result
        """
        try:
            # Fetch full history
            result = await self.crypto_service.get_full_history(
                coin_symbol=coin_symbol,
                max_days=max_days
            )
            
            if "error" in result:
                return result
            
            data = result.get("data", [])
            if not data:
                return {"error": f"No data found for {coin_symbol}"}
            
            # Compute technical indicators for the data
            data_with_indicators = self._compute_technical_indicators(data)
            
            # Prepare documents for MongoDB
            documents = []
            for candle in data_with_indicators:
                doc = {
                    "symbol": coin_symbol.upper(),
                    "timestamp": candle["timestamp"],
                    "date": candle["date"],
                    "open": candle["open"],
                    "high": candle["high"],
                    "low": candle["low"],
                    "close": candle["close"],
                    "volume_from": candle["volume_from"],
                    "volume_to": candle["volume_to"],
                    # Technical Indicators
                    "rsi": candle.get("rsi"),
                    "macd": candle.get("macd"),
                    "macd_signal": candle.get("macd_signal"),
                    "macd_hist": candle.get("macd_hist"),
                    "sma_7": candle.get("sma_7"),
                    "sma_14": candle.get("sma_14"),
                    "sma_20": candle.get("sma_20"),
                    "sma_30": candle.get("sma_30"),
                    "sma_50": candle.get("sma_50"),
                    "ema_7": candle.get("ema_7"),
                    "ema_14": candle.get("ema_14"),
                    "ema_20": candle.get("ema_20"),
                    "ema_30": candle.get("ema_30"),
                    "ema_50": candle.get("ema_50"),
                    "bb_upper": candle.get("bb_upper"),
                    "bb_middle": candle.get("bb_middle"),
                    "bb_lower": candle.get("bb_lower"),
                    "atr": candle.get("atr"),
                    "returns_pct": candle.get("returns_pct"),
                    "volatility_7d": candle.get("volatility_7d"),
                    "volatility_14d": candle.get("volatility_14d"),
                    "momentum_1d": candle.get("momentum_1d"),
                    "momentum_7d": candle.get("momentum_7d"),
                    "momentum_14d": candle.get("momentum_14d"),
                    "momentum_30d": candle.get("momentum_30d"),
                    "volume_surge": candle.get("volume_surge"),
                    "vwap": candle.get("vwap"),
                    # Metadata
                    "source": "cryptocompare",
                    "updated_at": datetime.now(timezone.utc)
                }
                documents.append(doc)
            
            # Upsert data (replace if exists based on symbol+timestamp)
            collection = self.db[self.collection_name]
            
            # Delete existing data for this coin and insert fresh
            await collection.delete_many({"symbol": coin_symbol.upper()})
            
            if documents:
                await collection.insert_many(documents)
            
            # Create index for efficient queries
            await collection.create_index([("symbol", 1), ("timestamp", 1)])
            
            # Count how many records have valid indicators (non-null RSI as proxy)
            records_with_indicators = sum(1 for doc in documents if doc.get("rsi") is not None)
            
            return {
                "symbol": coin_symbol.upper(),
                "records_stored": len(documents),
                "records_with_indicators": records_with_indicators,
                "date_range": {
                    "from": data[0]["date"] if data else None,
                    "to": data[-1]["date"] if data else None
                },
                "source": "cryptocompare",
                "indicators_computed": True,
                "status": "success"
            }
            
        except Exception as e:
            return {"error": str(e), "symbol": coin_symbol}
    
    async def download_all_coins(
        self,
        coins: List[str] = None,
        max_days: int = 3000
    ) -> Dict[str, Any]:
        """
        Download historical data for multiple coins.
        Runs as a background task with progress tracking.
        
        Args:
            coins: List of coin symbols (default: TOP_COINS)
            max_days: Maximum days of history per coin
        
        Returns:
            Dict with overall result
        """
        global _download_status
        
        coins = coins or self.TOP_COINS
        total_coins = len(coins)
        
        _download_status.update({
            "running": True,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "progress": 0,
            "current_coin": None,
            "coins_completed": 0,
            "coins_total": total_coins,
            "message": f"Starting download for {total_coins} coins...",
            "error": None,
            "result": None
        })
        
        results = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "coins_requested": total_coins,
            "coins_completed": 0,
            "coins_failed": 0,
            "total_records": 0,
            "coin_results": [],
            "errors": []
        }
        
        try:
            for i, coin in enumerate(coins):
                _download_status["current_coin"] = coin
                _download_status["message"] = f"Downloading {coin} ({i+1}/{total_coins})..."
                _download_status["progress"] = int((i / total_coins) * 100)
                
                # Download coin data
                coin_result = await self.download_coin_history(coin, max_days)
                
                if "error" in coin_result:
                    results["coins_failed"] += 1
                    results["errors"].append({
                        "coin": coin,
                        "error": coin_result["error"]
                    })
                else:
                    results["coins_completed"] += 1
                    results["total_records"] += coin_result.get("records_stored", 0)
                    results["coin_results"].append(coin_result)
                
                _download_status["coins_completed"] = i + 1
                
                # Brief delay to respect rate limits
                await asyncio.sleep(0.5)
            
            results["completed_at"] = datetime.now(timezone.utc).isoformat()
            results["status"] = "completed"
            
            _download_status["progress"] = 100
            _download_status["message"] = f"Download complete! {results['coins_completed']}/{total_coins} coins, {results['total_records']} records"
            _download_status["result"] = results
            
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            _download_status["error"] = str(e)
            _download_status["message"] = f"Error: {str(e)}"
        finally:
            _download_status["running"] = False
        
        return results
    
    async def get_coin_data(
        self,
        coin_symbol: str,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = None
    ) -> Dict[str, Any]:
        """
        Retrieve stored historical data for a coin.
        
        Args:
            coin_symbol: Cryptocurrency symbol
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            limit: Maximum records to return (optional)
        
        Returns:
            Dict with historical OHLCV data
        """
        collection = self.db[self.collection_name]
        
        query = {"symbol": coin_symbol.upper()}
        
        if start_date:
            start_ts = int(start_date.timestamp())
            query["timestamp"] = {"$gte": start_ts}
        
        if end_date:
            end_ts = int(end_date.timestamp())
            if "timestamp" in query:
                query["timestamp"]["$lte"] = end_ts
            else:
                query["timestamp"] = {"$lte": end_ts}
        
        cursor = collection.find(query, {"_id": 0}).sort("timestamp", 1)
        
        if limit:
            cursor = cursor.limit(limit)
        
        data = await cursor.to_list(length=limit or 10000)
        
        return {
            "symbol": coin_symbol.upper(),
            "count": len(data),
            "data": data,
            "date_range": {
                "from": data[0]["date"] if data else None,
                "to": data[-1]["date"] if data else None
            } if data else {}
        }
    
    async def get_training_data(
        self,
        coins: List[str] = None,
        min_records: int = 365
    ) -> Dict[str, Any]:
        """
        Get historical data formatted for AI training.
        
        Args:
            coins: List of coin symbols (default: all stored)
            min_records: Minimum records required per coin
        
        Returns:
            Dict with training-ready data
        """
        collection = self.db[self.collection_name]
        
        if coins:
            query = {"symbol": {"$in": [c.upper() for c in coins]}}
        else:
            query = {}
        
        # Get all unique symbols
        symbols = await collection.distinct("symbol", query)
        
        training_data = {
            "coins": {},
            "stats": {
                "total_coins": 0,
                "total_records": 0,
                "coins_with_sufficient_data": 0
            }
        }
        
        for symbol in symbols:
            data = await self.get_coin_data(symbol)
            count = data.get("count", 0)
            
            if count >= min_records:
                training_data["coins"][symbol] = {
                    "records": count,
                    "date_range": data.get("date_range", {}),
                    "data": data.get("data", [])
                }
                training_data["stats"]["coins_with_sufficient_data"] += 1
            
            training_data["stats"]["total_records"] += count
        
        training_data["stats"]["total_coins"] = len(symbols)
        
        return training_data
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about stored historical data"""
        collection = self.db[self.collection_name]
        
        # Get counts per symbol
        pipeline = [
            {"$group": {
                "_id": "$symbol",
                "count": {"$sum": 1},
                "min_date": {"$min": "$date"},
                "max_date": {"$max": "$date"}
            }},
            {"$sort": {"count": -1}}
        ]
        
        results = await collection.aggregate(pipeline).to_list(length=1000)
        
        total_records = sum(r["count"] for r in results)
        
        return {
            "total_coins": len(results),
            "total_records": total_records,
            "coins": [
                {
                    "symbol": r["_id"],
                    "records": r["count"],
                    "date_range": {
                        "from": r["min_date"],
                        "to": r["max_date"]
                    }
                }
                for r in results
            ],
            "collection": self.collection_name,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_next_batch_to_download(self, batch_size: int = 50) -> Dict[str, Any]:
        """
        Get the next batch of coins that haven't been downloaded yet.
        Used by the weekly expansion job.
        
        Returns:
            Dict with coins to download and progress stats
        """
        # Get currently stored coins
        stored_coins = await self.db[self.collection_name].distinct("symbol")
        stored_set = set(stored_coins)
        
        # Find coins not yet downloaded
        all_coins = self.ALL_AI_COINS
        missing_coins = [c for c in all_coins if c.upper() not in stored_set and c not in stored_set]
        
        # Get unique coins (remove duplicates from ALL_AI_COINS)
        seen = set()
        unique_missing = []
        for coin in missing_coins:
            if coin.upper() not in seen:
                seen.add(coin.upper())
                unique_missing.append(coin)
        
        # Get next batch
        next_batch = unique_missing[:batch_size]
        
        return {
            "total_ai_coins": len(set(c.upper() for c in all_coins)),
            "coins_downloaded": len(stored_set),
            "coins_remaining": len(unique_missing),
            "next_batch": next_batch,
            "batch_size": len(next_batch),
            "is_complete": len(unique_missing) == 0,
            "progress_pct": round(len(stored_set) / len(set(c.upper() for c in all_coins)) * 100, 1)
        }
    
    async def download_next_batch(self, batch_size: int = 50, max_days: int = 3000) -> Dict[str, Any]:
        """
        Download the next batch of coins automatically.
        Used by the weekly scheduled job.
        """
        batch_info = await self.get_next_batch_to_download(batch_size)
        
        if batch_info["is_complete"]:
            return {
                "status": "complete",
                "message": "All AI coins have been downloaded!",
                "total_coins": batch_info["coins_downloaded"],
                "progress_pct": 100
            }
        
        next_batch = batch_info["next_batch"]
        
        if not next_batch:
            return {
                "status": "complete",
                "message": "No more coins to download",
                "total_coins": batch_info["coins_downloaded"]
            }
        
        # Download the batch
        result = await self.download_all_coins(coins=next_batch, max_days=max_days)
        
        # Get updated stats
        updated_info = await self.get_next_batch_to_download(batch_size)
        
        result["expansion_progress"] = {
            "coins_downloaded": updated_info["coins_downloaded"],
            "coins_remaining": updated_info["coins_remaining"],
            "progress_pct": updated_info["progress_pct"],
            "is_complete": updated_info["is_complete"]
        }
        
        return result


# Factory function
_downloader_instance = None

def get_historical_downloader(db: AsyncIOMotorDatabase) -> HistoricalDataDownloader:
    """Get or create historical data downloader instance"""
    global _downloader_instance
    if _downloader_instance is None:
        _downloader_instance = HistoricalDataDownloader(db)
    return _downloader_instance

"""
Consolidated Data Service
=========================
Combines all data fetching and management:
- Market data from multiple sources
- Historical data
- OHLCV management
- Data caching
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

__all__ = [
    'DataService',
    'get_data_service'
]


class DataService:
    """
    Unified data service that consolidates:
    - market_data_service
    - ohlcv_data_manager
    - historical_data_downloader
    - coindesk_service
    - coinstats_service
    - twelvedata_service
    - coincodex_service
    """
    
    def __init__(self, db=None):
        self.db = db
        self._market_data = None
        self._ohlcv_manager = None
        self._historical = None
        self._cache = {}
        self._cache_ttl = 60  # seconds
        logger.info("📊 Data Service initialized")
    
    @property
    def market_data(self):
        """Lazy load market data service"""
        if self._market_data is None:
            try:
                from services.market_data_service import MarketDataService
                self._market_data = MarketDataService(self.db)
            except Exception as e:
                logger.warning(f"Could not load market data service: {e}")
        return self._market_data
    
    @property
    def ohlcv_manager(self):
        """Lazy load OHLCV manager"""
        if self._ohlcv_manager is None:
            try:
                from services.ohlcv_data_manager import OHLCVDataManager
                self._ohlcv_manager = OHLCVDataManager(self.db)
            except Exception as e:
                logger.warning(f"Could not load OHLCV manager: {e}")
        return self._ohlcv_manager
    
    # === Market Data ===
    async def get_price(self, symbol: str) -> Dict[str, Any]:
        """Get current price for a symbol"""
        cache_key = f"price_{symbol}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        if self.market_data:
            try:
                result = await self.market_data.get_price(symbol)
                self._set_cached(cache_key, result)
                return result
            except Exception as e:
                logger.error(f"Get price error: {e}")
        
        return {"error": "Market data not available"}
    
    async def get_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """Get prices for multiple symbols"""
        results = {}
        for symbol in symbols:
            results[symbol] = await self.get_price(symbol)
        return results
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """Get overall market overview"""
        if self.market_data:
            try:
                return await self.market_data.get_overview()
            except Exception as e:
                logger.error(f"Market overview error: {e}")
        
        return {
            "total_market_cap": 0,
            "btc_dominance": 0,
            "error": "Market data not available"
        }
    
    # === OHLCV Data ===
    async def get_ohlcv(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get OHLCV candles"""
        if self.ohlcv_manager:
            try:
                return await self.ohlcv_manager.get(symbol, interval, limit)
            except Exception as e:
                logger.error(f"OHLCV error: {e}")
        
        return []
    
    async def get_historical(
        self,
        symbol: str,
        start_date: str,
        end_date: str = None,
        interval: str = "1d"
    ) -> List[Dict[str, Any]]:
        """Get historical data for a date range"""
        if self._historical is None:
            try:
                from services.historical_data_downloader import HistoricalDataDownloader
                self._historical = HistoricalDataDownloader(self.db)
            except Exception as e:
                logger.warning(f"Could not load historical service: {e}")
                return []
        
        try:
            return await self._historical.download(symbol, start_date, end_date, interval)
        except Exception as e:
            logger.error(f"Historical data error: {e}")
            return []
    
    # === Aggregated Data ===
    async def get_symbol_data(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive data for a symbol"""
        price_data = await self.get_price(symbol)
        ohlcv = await self.get_ohlcv(symbol, "1h", 24)
        
        # Calculate basic stats
        if ohlcv:
            prices = [c.get("close", 0) for c in ohlcv]
            high_24h = max(c.get("high", 0) for c in ohlcv)
            low_24h = min(c.get("low", 0) for c in ohlcv)
            volume_24h = sum(c.get("volume", 0) for c in ohlcv)
            
            change_24h = ((prices[-1] - prices[0]) / prices[0] * 100) if prices[0] > 0 else 0
        else:
            high_24h = low_24h = volume_24h = change_24h = 0
        
        return {
            "symbol": symbol,
            "price": price_data.get("price", 0),
            "high_24h": high_24h,
            "low_24h": low_24h,
            "volume_24h": volume_24h,
            "change_24h": round(change_24h, 2),
            "ohlcv_count": len(ohlcv),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # === Universe Data ===
    async def get_tradeable_symbols(self) -> List[str]:
        """Get list of tradeable symbols"""
        if self.market_data:
            try:
                return await self.market_data.get_tradeable_symbols()
            except Exception as e:
                logger.error(f"Get symbols error: {e}")
        
        # Default symbols
        return ["BTC", "ETH", "SOL", "DOT", "AAVE", "UNI", "LINK", "AVAX"]
    
    # === Caching ===
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if (datetime.now() - timestamp).total_seconds() < self._cache_ttl:
                return data
        return None
    
    def _set_cached(self, key: str, value: Any):
        """Set cached value"""
        self._cache[key] = (value, datetime.now())
    
    def clear_cache(self):
        """Clear all cached data"""
        self._cache = {}
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service": "data",
            "market_data": self._market_data is not None,
            "ohlcv_manager": self._ohlcv_manager is not None,
            "historical": self._historical is not None,
            "cache_size": len(self._cache),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Singleton
_data_service = None

def get_data_service(db=None) -> DataService:
    """Get or create data service singleton"""
    global _data_service
    if _data_service is None:
        _data_service = DataService(db)
    return _data_service

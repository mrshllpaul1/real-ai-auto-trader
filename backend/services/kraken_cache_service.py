"""
Kraken API Caching Service
===========================
Provides caching layer for Kraken API to reduce rate limiting.
Caches:
- Balance data (30 second TTL)
- Ticker data (5 second TTL)
- Asset pairs (1 hour TTL - rarely changes)
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry with TTL tracking"""
    data: Any
    timestamp: datetime
    ttl_seconds: int
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        age = (datetime.now(timezone.utc) - self.timestamp).total_seconds()
        return age > self.ttl_seconds


class KrakenCacheService:
    """
    Caching layer for Kraken API calls.
    Reduces API rate limiting by caching frequently accessed data.
    """
    
    # Cache TTL settings (in seconds)
    TTL_BALANCE = 30        # Balance changes with trades, cache for 30s
    TTL_TICKER = 5          # Prices change frequently, cache for 5s
    TTL_TICKER_BATCH = 5    # Batch ticker data
    TTL_ASSET_PAIRS = 3600  # Asset pairs rarely change, cache for 1 hour
    TTL_TRADE_HISTORY = 60  # Trade history for entry price lookups
    
    def __init__(self, kraken_service):
        """
        Initialize cache with reference to actual Kraken service.
        
        Args:
            kraken_service: The actual KrakenTradeService for API calls
        """
        self._kraken = kraken_service
        self._cache: Dict[str, CacheEntry] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "api_calls_saved": 0
        }
        logger.info("📦 Kraken Cache Service initialized")
    
    def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create lock for a cache key to prevent thundering herd"""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]
    
    def _get_cache(self, key: str) -> Optional[Any]:
        """Get cached data if not expired"""
        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired():
                self._stats["hits"] += 1
                self._stats["api_calls_saved"] += 1
                return entry.data
            else:
                # Remove expired entry
                del self._cache[key]
        self._stats["misses"] += 1
        return None
    
    def _set_cache(self, key: str, data: Any, ttl: int):
        """Set cache entry with TTL"""
        self._cache[key] = CacheEntry(
            data=data,
            timestamp=datetime.now(timezone.utc),
            ttl_seconds=ttl
        )
    
    def invalidate(self, key: str = None):
        """
        Invalidate cache entries.
        If key is None, invalidate all. Otherwise invalidate specific key.
        """
        if key is None:
            self._cache.clear()
            logger.info("🗑️ Cache cleared completely")
        elif key in self._cache:
            del self._cache[key]
            logger.debug(f"🗑️ Cache entry '{key}' invalidated")
    
    def invalidate_balance(self):
        """Invalidate balance cache after trades"""
        self.invalidate("balance")
        # Also invalidate any ticker caches that might show old holdings
        keys_to_remove = [k for k in self._cache.keys() if k.startswith("ticker_")]
        for k in keys_to_remove:
            del self._cache[k]
    
    async def get_balance(self) -> Dict[str, float]:
        """
        Get account balance with caching.
        Uses 30-second TTL to balance freshness with rate limits.
        """
        cache_key = "balance"
        
        # Check cache first
        cached = self._get_cache(cache_key)
        if cached is not None:
            logger.debug("💾 Balance cache HIT")
            return cached
        
        # Use lock to prevent multiple simultaneous API calls
        async with self._get_lock(cache_key):
            # Double-check cache after acquiring lock
            cached = self._get_cache(cache_key)
            if cached is not None:
                return cached
            
            # Make API call
            logger.debug("🌐 Balance cache MISS - calling API")
            balance = await self._kraken.get_balance()
            self._set_cache(cache_key, balance, self.TTL_BALANCE)
            return balance
    
    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get ticker for a single symbol with caching.
        Uses 5-second TTL for price data.
        """
        cache_key = f"ticker_{symbol}"
        
        cached = self._get_cache(cache_key)
        if cached is not None:
            logger.debug(f"💾 Ticker cache HIT for {symbol}")
            return cached
        
        async with self._get_lock(cache_key):
            cached = self._get_cache(cache_key)
            if cached is not None:
                return cached
            
            logger.debug(f"🌐 Ticker cache MISS for {symbol}")
            ticker = await self._kraken.get_ticker(symbol)
            if ticker:
                self._set_cache(cache_key, ticker, self.TTL_TICKER)
            return ticker
    
    async def get_tickers_batch(self, pairs: List[str]) -> Dict[str, Any]:
        """
        Get multiple tickers with caching.
        Checks cache for each pair and only fetches missing ones.
        """
        result = {}
        pairs_to_fetch = []
        
        # Check cache for each pair
        for pair in pairs:
            cache_key = f"ticker_{pair}"
            cached = self._get_cache(cache_key)
            if cached is not None:
                result[pair] = cached
            else:
                pairs_to_fetch.append(pair)
        
        if not pairs_to_fetch:
            logger.debug(f"💾 Batch ticker cache HIT - all {len(pairs)} pairs cached")
            return result
        
        logger.debug(f"🌐 Batch ticker: {len(result)} cached, fetching {len(pairs_to_fetch)}")
        
        # Fetch missing pairs from API
        if hasattr(self._kraken, 'get_tickers_batch'):
            fetched = await self._kraken.get_tickers_batch(pairs_to_fetch)
            
            # Cache fetched data
            for pair, ticker in fetched.items():
                self._set_cache(f"ticker_{pair}", ticker, self.TTL_TICKER_BATCH)
                result[pair] = ticker
        else:
            # Fallback: fetch individually with rate limiting
            for pair in pairs_to_fetch:
                ticker = await self.get_ticker(pair)
                if ticker:
                    result[pair] = ticker
                await asyncio.sleep(0.1)  # Small delay between calls
        
        return result
    
    async def get_trade_history(self, start: int = None, end: int = None) -> Dict[str, Any]:
        """
        Get trade history with caching.
        Used for entry price tracking.
        """
        cache_key = f"trades_{start}_{end}"
        
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached
        
        async with self._get_lock(cache_key):
            cached = self._get_cache(cache_key)
            if cached is not None:
                return cached
            
            if hasattr(self._kraken, 'get_trades_history'):
                trades = await self._kraken.get_trades_history(start=start, end=end)
            else:
                # Use authenticated request
                params = {}
                if start:
                    params['start'] = start
                if end:
                    params['end'] = end
                trades = await self._kraken.auth.request("TradesHistory", params=params)
            
            if trades and not trades.get("error"):
                self._set_cache(cache_key, trades, self.TTL_TRADE_HISTORY)
            return trades
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "api_calls_saved": self._stats["api_calls_saved"],
            "cache_entries": len(self._cache),
            "cache_keys": list(self._cache.keys())
        }
    
    # Passthrough methods for non-cached operations
    async def create_order(self, *args, **kwargs):
        """Pass through to actual service - orders should never be cached"""
        result = await self._kraken.create_order(*args, **kwargs)
        # Invalidate balance cache after order
        self.invalidate_balance()
        return result
    
    async def cancel_order(self, *args, **kwargs):
        """Pass through to actual service"""
        result = await self._kraken.cancel_order(*args, **kwargs)
        self.invalidate_balance()
        return result
    
    async def get_open_orders(self, *args, **kwargs):
        """Pass through - open orders should always be fresh"""
        return await self._kraken.get_open_orders(*args, **kwargs)
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get portfolio summary with cached balance and ticker data.
        Combines balance data with current prices for total value calculation.
        """
        cache_key = "portfolio_summary"
        
        cached = self._get_cache(cache_key)
        if cached is not None:
            logger.debug("💾 Portfolio summary cache HIT")
            return cached
        
        async with self._get_lock(cache_key):
            cached = self._get_cache(cache_key)
            if cached is not None:
                return cached
            
            try:
                # Get balance
                balance = await self.get_balance()
                
                if not balance:
                    return {"total_usd": 0, "holdings": [], "error": "No balance data"}
                
                holdings = []
                total_usd = 0
                
                # Get tickers for all holdings
                for asset, amount in balance.items():
                    if amount <= 0:
                        continue
                    
                    # USD/USDT/USDC are 1:1
                    if asset.upper() in ['USD', 'ZUSD', 'USDT', 'USDC']:
                        value_usd = float(amount)
                        price = 1.0
                    else:
                        # Try to get ticker
                        symbol = f"{asset}USD"
                        ticker = await self.get_ticker(symbol)
                        if ticker and 'c' in ticker:
                            price = float(ticker['c'][0]) if isinstance(ticker['c'], list) else float(ticker['c'])
                            value_usd = float(amount) * price
                        else:
                            # Fallback: try USDT pair
                            symbol = f"{asset}USDT"
                            ticker = await self.get_ticker(symbol)
                            if ticker and 'c' in ticker:
                                price = float(ticker['c'][0]) if isinstance(ticker['c'], list) else float(ticker['c'])
                                value_usd = float(amount) * price
                            else:
                                price = 0
                                value_usd = 0
                    
                    holdings.append({
                        "asset": asset,
                        "amount": float(amount),
                        "price_usd": price,
                        "value_usd": value_usd
                    })
                    total_usd += value_usd
                
                # Sort by value
                holdings.sort(key=lambda x: x['value_usd'], reverse=True)
                
                result = {
                    "total_usd": round(total_usd, 2),
                    "holdings": holdings,
                    "asset_count": len(holdings),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                self._set_cache(cache_key, result, self.TTL_BALANCE)
                return result
                
            except Exception as e:
                logger.error(f"Error getting portfolio summary: {e}")
                return {"total_usd": 0, "holdings": [], "error": str(e)}
    
    async def get_portfolio(self) -> Dict[str, Any]:
        """
        Alias for get_portfolio_summary for compatibility with consolidated services.
        """
        return await self.get_portfolio_summary()

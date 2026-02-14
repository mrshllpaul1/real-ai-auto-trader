"""
Consolidated Exchange Service
=============================
Combines all exchange-related functionality:
- Kraken API interactions
- Order execution
- WebSocket connections
- Order book analysis
- Cache management
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Re-export from existing services for backwards compatibility
try:
    from services.kraken_service import KrakenTradeService as KrakenService
except ImportError:
    KrakenService = None
    
try:
    from services.kraken_cache_service import KrakenCacheService
except ImportError:
    KrakenCacheService = None
    
try:
    from services.kraken_executor import KrakenExecutor
except ImportError:
    KrakenExecutor = None
    
try:
    from services.kraken_orderbook_ws import KrakenOrderBookWS
except ImportError:
    KrakenOrderBookWS = None
    
try:
    from services.order_book_analyzer import OrderBookAnalyzer
except ImportError:
    OrderBookAnalyzer = None

__all__ = [
    'KrakenService',
    'KrakenCacheService', 
    'KrakenExecutor',
    'KrakenOrderBookWS',
    'OrderBookAnalyzer',
    'ExchangeService',
    'get_exchange_service'
]


class ExchangeService:
    """
    Unified exchange service that consolidates:
    - kraken_service
    - kraken_cache_service
    - kraken_executor
    - kraken_orderbook_ws
    - order_book_analyzer
    - multi_exchange (future)
    """
    
    def __init__(self, db=None):
        self.db = db
        self._kraken = None
        self._cache = None
        self._executor = None
        self._orderbook_ws = None
        self._orderbook_analyzer = None
        logger.info("📊 Exchange Service initialized")
    
    @property
    def kraken(self):
        """Lazy load Kraken service"""
        if self._kraken is None:
            if KrakenService is not None:
                try:
                    # KrakenTradeService needs an authenticator
                    from services.kraken_service import KrakenAuthenticator
                    import os
                    api_key = os.environ.get("KRAKEN_API_KEY", "")
                    api_secret = os.environ.get("KRAKEN_API_SECRET", "")
                    if api_key and api_secret:
                        auth = KrakenAuthenticator(api_key, api_secret)
                        self._kraken = KrakenService(auth)
                    else:
                        logger.warning("Kraken API keys not configured")
                except Exception as e:
                    logger.warning(f"Could not initialize KrakenService: {e}")
        return self._kraken
    
    @property
    def cache(self):
        """Lazy load cache service"""
        if self._cache is None:
            if KrakenCacheService is not None and self.kraken is not None:
                try:
                    self._cache = KrakenCacheService(self.kraken)
                except Exception as e:
                    logger.warning(f"Could not initialize cache: {e}")
        return self._cache
    
    @property
    def executor(self) -> KrakenExecutor:
        """Lazy load executor"""
        if self._executor is None:
            self._executor = KrakenExecutor()
        return self._executor
    
    # === Portfolio Methods ===
    async def get_portfolio(self) -> Dict[str, Any]:
        """Get current portfolio from cache or fresh"""
        return await self.cache.get_portfolio()
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary"""
        return await self.cache.get_portfolio_summary()
    
    async def get_balance(self) -> Dict[str, float]:
        """Get account balances"""
        return await self.kraken.get_balance()
    
    # === Market Data Methods ===
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker data for symbol"""
        return await self.cache.get_ticker(symbol)
    
    async def get_ohlcv(self, symbol: str, interval: int = 60, limit: int = 100) -> List[Dict]:
        """Get OHLCV candles"""
        return await self.kraken.get_ohlcv(symbol, interval, limit)
    
    async def get_orderbook(self, symbol: str, depth: int = 25) -> Dict[str, Any]:
        """Get order book"""
        return await self.kraken.get_orderbook(symbol, depth)
    
    # === Trading Methods ===
    async def place_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        order_type: str = "market",
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Place a trade order"""
        return await self.executor.place_order(
            symbol=symbol,
            side=side,
            amount=amount,
            order_type=order_type,
            price=price
        )
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        return await self.executor.cancel_order(order_id)
    
    async def get_open_orders(self) -> List[Dict[str, Any]]:
        """Get all open orders"""
        return await self.kraken.get_open_orders()
    
    async def get_trade_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trade history"""
        return await self.kraken.get_trade_history(limit)
    
    # === Status Methods ===
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service": "exchange",
            "exchange": "kraken",
            "kraken_initialized": self._kraken is not None,
            "cache_initialized": self._cache is not None,
            "executor_initialized": self._executor is not None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Singleton instance
_exchange_service = None

def get_exchange_service(db=None) -> ExchangeService:
    """Get or create exchange service singleton"""
    global _exchange_service
    if _exchange_service is None:
        _exchange_service = ExchangeService(db)
    return _exchange_service

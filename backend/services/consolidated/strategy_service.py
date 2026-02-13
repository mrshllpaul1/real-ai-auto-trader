"""
Consolidated Strategy Service
=============================
Combines all trading strategies:
- Adaptive strategies
- Custom strategies
- Backtesting
- Strategy optimization
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

__all__ = [
    'StrategyService',
    'get_strategy_service'
]


# Strategy definitions
AVAILABLE_STRATEGIES = {
    "momentum": {
        "name": "Momentum",
        "description": "Follows price momentum using RSI and MACD",
        "risk_level": "medium",
        "timeframes": ["1h", "4h", "1d"]
    },
    "mean_reversion": {
        "name": "Mean Reversion",
        "description": "Trades reversions to moving averages",
        "risk_level": "low",
        "timeframes": ["4h", "1d"]
    },
    "breakout": {
        "name": "Breakout",
        "description": "Identifies and trades price breakouts",
        "risk_level": "high",
        "timeframes": ["1h", "4h"]
    },
    "trend_following": {
        "name": "Trend Following",
        "description": "Follows established trends with trailing stops",
        "risk_level": "medium",
        "timeframes": ["4h", "1d", "1w"]
    },
    "scalping": {
        "name": "Scalping",
        "description": "Quick trades on small price movements",
        "risk_level": "high",
        "timeframes": ["1m", "5m", "15m"]
    },
    "swing": {
        "name": "Swing Trading",
        "description": "Multi-day trades capturing larger moves",
        "risk_level": "medium",
        "timeframes": ["4h", "1d"]
    },
    "dca": {
        "name": "Dollar Cost Averaging",
        "description": "Systematic buying at regular intervals",
        "risk_level": "low",
        "timeframes": ["1d", "1w"]
    },
    "grid": {
        "name": "Grid Trading",
        "description": "Places orders at price intervals",
        "risk_level": "medium",
        "timeframes": ["1h", "4h"]
    },
    "arbitrage": {
        "name": "Arbitrage",
        "description": "Exploits price differences across markets",
        "risk_level": "low",
        "timeframes": ["1m", "5m"]
    },
    "ai_ensemble": {
        "name": "AI Ensemble",
        "description": "Uses multiple AI models for signals",
        "risk_level": "medium",
        "timeframes": ["1h", "4h", "1d"]
    }
}


class StrategyService:
    """
    Unified strategy service that consolidates:
    - adaptive_strategy
    - adaptive_strategy_service
    - custom_strategy_builder
    - strategy_engine
    - backtest_service
    - backtesting
    - gem_backtester
    """
    
    def __init__(self, db=None):
        self.db = db
        self._adaptive = None
        self._backtest = None
        self._custom_builder = None
        self._active_strategies = {}
        logger.info("📋 Strategy Service initialized")
    
    @property
    def adaptive(self):
        """Lazy load adaptive strategy"""
        if self._adaptive is None:
            try:
                from services.adaptive_strategy_service import AdaptiveStrategyService
                self._adaptive = AdaptiveStrategyService(self.db)
            except Exception as e:
                logger.warning(f"Could not load adaptive strategy: {e}")
        return self._adaptive
    
    @property
    def backtest(self):
        """Lazy load backtest service"""
        if self._backtest is None:
            try:
                from services.backtest_service import BacktestService
                self._backtest = BacktestService(self.db)
            except Exception as e:
                logger.warning(f"Could not load backtest service: {e}")
        return self._backtest
    
    # === Strategy Management ===
    def get_available_strategies(self) -> Dict[str, Any]:
        """Get all available strategies"""
        return AVAILABLE_STRATEGIES
    
    def get_strategy_info(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Get info about a specific strategy"""
        return AVAILABLE_STRATEGIES.get(strategy_id)
    
    async def activate_strategy(
        self,
        strategy_id: str,
        symbol: str,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Activate a strategy for a symbol"""
        if strategy_id not in AVAILABLE_STRATEGIES:
            return {"error": f"Unknown strategy: {strategy_id}"}
        
        key = f"{strategy_id}_{symbol}"
        self._active_strategies[key] = {
            "strategy_id": strategy_id,
            "symbol": symbol,
            "params": params or {},
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "status": "active"
        }
        
        return {
            "activated": True,
            "strategy": strategy_id,
            "symbol": symbol
        }
    
    async def deactivate_strategy(self, strategy_id: str, symbol: str) -> Dict[str, Any]:
        """Deactivate a strategy"""
        key = f"{strategy_id}_{symbol}"
        if key in self._active_strategies:
            del self._active_strategies[key]
            return {"deactivated": True}
        return {"deactivated": False, "reason": "Strategy not active"}
    
    def get_active_strategies(self) -> List[Dict[str, Any]]:
        """Get all active strategies"""
        return list(self._active_strategies.values())
    
    # === Strategy Signals ===
    async def get_strategy_signal(
        self,
        strategy_id: str,
        symbol: str,
        ohlcv: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get signal from a strategy"""
        if strategy_id not in AVAILABLE_STRATEGIES:
            return {"error": f"Unknown strategy: {strategy_id}"}
        
        # Use adaptive strategy service if available
        if self.adaptive:
            try:
                return await self.adaptive.get_signal(strategy_id, symbol, ohlcv)
            except Exception as e:
                logger.error(f"Strategy signal error: {e}")
        
        # Fallback to basic signal
        return self._basic_signal(strategy_id, ohlcv)
    
    def _basic_signal(self, strategy_id: str, ohlcv: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate basic signal without full strategy service"""
        if not ohlcv or len(ohlcv) < 2:
            return {"signal": "hold", "confidence": 0.5}
        
        prices = [c.get("close", 0) for c in ohlcv]
        
        # Simple momentum check
        short_ma = sum(prices[-5:]) / min(5, len(prices))
        long_ma = sum(prices[-20:]) / min(20, len(prices))
        
        if short_ma > long_ma * 1.02:
            signal = "buy"
            confidence = 0.6
        elif short_ma < long_ma * 0.98:
            signal = "sell"
            confidence = 0.6
        else:
            signal = "hold"
            confidence = 0.5
        
        return {
            "signal": signal,
            "confidence": confidence,
            "strategy": strategy_id,
            "short_ma": short_ma,
            "long_ma": long_ma
        }
    
    # === Backtesting ===
    async def run_backtest(
        self,
        strategy_id: str,
        symbol: str,
        start_date: str,
        end_date: str = None,
        initial_capital: float = 10000
    ) -> Dict[str, Any]:
        """Run backtest for a strategy"""
        if not self.backtest:
            return {"error": "Backtest service not available"}
        
        try:
            return await self.backtest.run(
                strategy_id=strategy_id,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital
            )
        except Exception as e:
            return {"error": str(e)}
    
    async def get_backtest_results(self, backtest_id: str) -> Dict[str, Any]:
        """Get results of a backtest"""
        if not self.backtest:
            return {"error": "Backtest service not available"}
        
        try:
            return await self.backtest.get_results(backtest_id)
        except Exception as e:
            return {"error": str(e)}
    
    # === Custom Strategies ===
    async def create_custom_strategy(
        self,
        name: str,
        rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a custom strategy"""
        if self._custom_builder is None:
            try:
                from services.custom_strategy_builder import CustomStrategyBuilder
                self._custom_builder = CustomStrategyBuilder(self.db)
            except Exception as e:
                return {"error": f"Could not load strategy builder: {e}"}
        
        try:
            return await self._custom_builder.create(name, rules)
        except Exception as e:
            return {"error": str(e)}
    
    async def get_custom_strategies(self) -> List[Dict[str, Any]]:
        """Get all custom strategies"""
        if self._custom_builder:
            try:
                return await self._custom_builder.list_all()
            except Exception as e:
                logger.error(f"List custom strategies error: {e}")
        return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service": "strategy",
            "available_strategies": len(AVAILABLE_STRATEGIES),
            "active_strategies": len(self._active_strategies),
            "adaptive": self._adaptive is not None,
            "backtest": self._backtest is not None,
            "custom_builder": self._custom_builder is not None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Singleton
_strategy_service = None

def get_strategy_service(db=None) -> StrategyService:
    """Get or create strategy service singleton"""
    global _strategy_service
    if _strategy_service is None:
        _strategy_service = StrategyService(db)
    return _strategy_service

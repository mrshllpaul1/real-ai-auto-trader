"""
Consolidated Trading Service
============================
Combines all trading execution and strategy:
- Automated trading
- Strategy execution
- Risk management
- Position sizing
- Stop loss automation
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

__all__ = [
    'TradingService',
    'get_trading_service'
]


class TradingService:
    """
    Unified trading service that consolidates:
    - automated_trader
    - trading_engine
    - strategy_engine
    - risk_manager
    - position_sizing
    - stop_loss_automation
    - trailing_stop_service
    - circuit_breaker
    """
    
    def __init__(self, db=None):
        self.db = db
        self._automated_trader = None
        self._risk_manager = None
        self._position_sizing = None
        self._circuit_breaker = None
        self._trading_engine = None
        logger.info("💹 Trading Service initialized")
    
    @property
    def circuit_breaker(self):
        """Lazy load circuit breaker"""
        if self._circuit_breaker is None:
            try:
                from services.circuit_breaker import CircuitBreaker
                self._circuit_breaker = CircuitBreaker(self.db)
            except Exception as e:
                logger.warning(f"Could not load circuit breaker: {e}")
        return self._circuit_breaker
    
    @property
    def position_sizing(self):
        """Lazy load position sizing"""
        if self._position_sizing is None:
            try:
                from services.position_sizing import PositionSizer
                self._position_sizing = PositionSizer(self.db)
            except Exception as e:
                logger.warning(f"Could not load position sizing: {e}")
        return self._position_sizing
    
    @property
    def risk_manager(self):
        """Lazy load risk manager"""
        if self._risk_manager is None:
            try:
                from services.risk_manager import RiskManager
                self._risk_manager = RiskManager(self.db)
            except Exception as e:
                logger.warning(f"Could not load risk manager: {e}")
        return self._risk_manager
    
    # === Safety Checks ===
    async def can_trade(self) -> Dict[str, Any]:
        """Check if trading is allowed"""
        if self.circuit_breaker:
            status = await self.circuit_breaker.get_status()
            if status.get("kill_switch_active"):
                return {
                    "allowed": False,
                    "reason": "Kill switch is active",
                    "circuit_breaker": status
                }
            if status.get("circuit_open"):
                return {
                    "allowed": False,
                    "reason": "Circuit breaker triggered",
                    "circuit_breaker": status
                }
        
        return {"allowed": True, "reason": None}
    
    async def activate_kill_switch(self, reason: str = "Manual activation") -> Dict[str, Any]:
        """Activate the trading kill switch"""
        if self.circuit_breaker:
            return await self.circuit_breaker.activate_kill_switch(reason)
        return {"error": "Circuit breaker not available"}
    
    async def deactivate_kill_switch(self) -> Dict[str, Any]:
        """Deactivate the trading kill switch"""
        if self.circuit_breaker:
            return await self.circuit_breaker.deactivate_kill_switch()
        return {"error": "Circuit breaker not available"}
    
    # === Position Sizing ===
    async def calculate_position_size(
        self,
        symbol: str,
        signal: str,
        confidence: float,
        portfolio_value: float
    ) -> Dict[str, Any]:
        """Calculate optimal position size"""
        if not self.position_sizing:
            # Default conservative sizing
            return {
                "position_size": portfolio_value * 0.02,
                "method": "default_2%",
                "symbol": symbol
            }
        
        try:
            return await self.position_sizing.calculate(
                symbol=symbol,
                signal=signal,
                confidence=confidence,
                portfolio_value=portfolio_value
            )
        except Exception as e:
            logger.error(f"Position sizing error: {e}")
            return {"position_size": 0, "error": str(e)}
    
    # === Risk Assessment ===
    async def assess_trade_risk(
        self,
        symbol: str,
        side: str,
        amount: float
    ) -> Dict[str, Any]:
        """Assess risk of a potential trade"""
        if not self.risk_manager:
            return {"risk_level": "unknown", "approved": True}
        
        try:
            return await self.risk_manager.assess(symbol, side, amount)
        except Exception as e:
            return {"risk_level": "error", "approved": False, "error": str(e)}
    
    async def get_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics"""
        if not self.risk_manager:
            return {"error": "Risk manager not available"}
        
        try:
            return await self.risk_manager.get_metrics()
        except Exception as e:
            return {"error": str(e)}
    
    # === Strategy Execution ===
    async def execute_strategy(
        self,
        strategy_id: str,
        symbol: str,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute a trading strategy"""
        # Check if trading is allowed
        can_trade = await self.can_trade()
        if not can_trade["allowed"]:
            return {
                "executed": False,
                "reason": can_trade["reason"]
            }
        
        if self._trading_engine is None:
            try:
                from services.trading_engine import TradingEngine
                self._trading_engine = TradingEngine(self.db)
            except Exception as e:
                return {"executed": False, "error": str(e)}
        
        try:
            return await self._trading_engine.execute(strategy_id, symbol, params)
        except Exception as e:
            return {"executed": False, "error": str(e)}
    
    # === Automated Trading ===
    async def start_automated_trading(self) -> Dict[str, Any]:
        """Start automated trading"""
        can_trade = await self.can_trade()
        if not can_trade["allowed"]:
            return {"started": False, "reason": can_trade["reason"]}
        
        if self._automated_trader is None:
            try:
                from services.automated_trader import AutomatedTrader
                self._automated_trader = AutomatedTrader(self.db)
            except Exception as e:
                return {"started": False, "error": str(e)}
        
        try:
            await self._automated_trader.start()
            return {"started": True}
        except Exception as e:
            return {"started": False, "error": str(e)}
    
    async def stop_automated_trading(self) -> Dict[str, Any]:
        """Stop automated trading"""
        if self._automated_trader:
            try:
                await self._automated_trader.stop()
                return {"stopped": True}
            except Exception as e:
                return {"stopped": False, "error": str(e)}
        return {"stopped": True, "note": "Was not running"}
    
    async def get_automated_status(self) -> Dict[str, Any]:
        """Get automated trading status"""
        return {
            "running": self._automated_trader is not None and getattr(self._automated_trader, 'running', False),
            "can_trade": (await self.can_trade())["allowed"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service": "trading",
            "circuit_breaker": self._circuit_breaker is not None,
            "position_sizing": self._position_sizing is not None,
            "risk_manager": self._risk_manager is not None,
            "trading_engine": self._trading_engine is not None,
            "automated_trader": self._automated_trader is not None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Singleton
_trading_service = None

def get_trading_service(db=None) -> TradingService:
    """Get or create trading service singleton"""
    global _trading_service
    if _trading_service is None:
        _trading_service = TradingService(db)
    return _trading_service

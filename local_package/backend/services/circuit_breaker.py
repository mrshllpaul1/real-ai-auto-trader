"""
Circuit Breaker Service
=======================
Implements trading halts and emergency stops based on risk conditions.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class CircuitBreakerState(Enum):
    OPEN = "open"          # Trading allowed
    TRIPPED = "tripped"    # Trading halted
    COOLDOWN = "cooldown"  # In cooldown period

@dataclass
class CircuitBreakerStatus:
    state: CircuitBreakerState = CircuitBreakerState.OPEN
    reason: str = ""
    tripped_at: Optional[datetime] = None
    cooldown_until: Optional[datetime] = None
    consecutive_losses: int = 0
    daily_trades: int = 0
    daily_loss_percent: float = 0.0
    
class CircuitBreakerService:
    """
    Monitors trading conditions and trips circuit breakers when limits are exceeded.
    """
    
    def __init__(self, db, risk_config=None):
        self.db = db
        
        # Import risk config
        if risk_config is None:
            from config.risk_config import DEFAULT_RISK_CONFIG
            risk_config = DEFAULT_RISK_CONFIG
        
        self.config = risk_config
        self.status = CircuitBreakerStatus()
        self._kill_switch_active = False
        self._trade_timestamps: List[datetime] = []
        
        logger.info("🔌 Circuit Breaker Service initialized")
    
    # ==================== KILL SWITCH ====================
    
    def activate_kill_switch(self, reason: str = "Manual activation"):
        """
        EMERGENCY: Immediately halt all trading
        """
        self._kill_switch_active = True
        self.status.state = CircuitBreakerState.TRIPPED
        self.status.reason = f"KILL SWITCH: {reason}"
        self.status.tripped_at = datetime.now(timezone.utc)
        
        logger.critical(f"🚨 KILL SWITCH ACTIVATED: {reason}")
        
        return {
            "status": "activated",
            "reason": reason,
            "timestamp": self.status.tripped_at.isoformat()
        }
    
    def deactivate_kill_switch(self):
        """Deactivate the kill switch and resume trading"""
        self._kill_switch_active = False
        self.status.state = CircuitBreakerState.OPEN
        self.status.reason = ""
        self.status.tripped_at = None
        
        logger.info("✅ Kill switch deactivated - Trading resumed")
        
        return {"status": "deactivated"}
    
    def is_kill_switch_active(self) -> bool:
        return self._kill_switch_active
    
    # ==================== CIRCUIT BREAKER CHECKS ====================
    
    def can_trade(self) -> Dict[str, Any]:
        """
        Check if trading is allowed based on all circuit breaker conditions.
        Returns dict with allowed status and reason if blocked.
        """
        # Kill switch takes priority
        if self._kill_switch_active:
            return {
                "allowed": False,
                "reason": "Kill switch is active",
                "state": CircuitBreakerState.TRIPPED.value
            }
        
        # Check cooldown
        if self.status.state == CircuitBreakerState.COOLDOWN:
            if self.status.cooldown_until and datetime.now(timezone.utc) < self.status.cooldown_until:
                remaining = (self.status.cooldown_until - datetime.now(timezone.utc)).seconds
                return {
                    "allowed": False,
                    "reason": f"In cooldown period ({remaining}s remaining)",
                    "state": CircuitBreakerState.COOLDOWN.value
                }
            else:
                # Cooldown expired
                self._reset_status()
        
        # Check if already tripped
        if self.status.state == CircuitBreakerState.TRIPPED:
            return {
                "allowed": False,
                "reason": self.status.reason,
                "state": CircuitBreakerState.TRIPPED.value
            }
        
        # Check trade rate limits
        rate_check = self._check_trade_rate()
        if not rate_check["allowed"]:
            return rate_check
        
        return {
            "allowed": True,
            "reason": "",
            "state": CircuitBreakerState.OPEN.value
        }
    
    def _check_trade_rate(self) -> Dict[str, Any]:
        """Check if trade rate limits are exceeded"""
        now = datetime.now(timezone.utc)
        
        # Clean old timestamps
        self._trade_timestamps = [
            ts for ts in self._trade_timestamps
            if ts > now - timedelta(hours=24)
        ]
        
        # Check hourly limit
        hour_ago = now - timedelta(hours=1)
        trades_last_hour = sum(1 for ts in self._trade_timestamps if ts > hour_ago)
        
        if trades_last_hour >= self.config.max_trades_per_hour:
            return {
                "allowed": False,
                "reason": f"Hourly trade limit reached ({trades_last_hour}/{self.config.max_trades_per_hour})",
                "state": CircuitBreakerState.COOLDOWN.value
            }
        
        # Check daily limit
        if len(self._trade_timestamps) >= self.config.max_trades_per_day:
            return {
                "allowed": False,
                "reason": f"Daily trade limit reached ({len(self._trade_timestamps)}/{self.config.max_trades_per_day})",
                "state": CircuitBreakerState.TRIPPED.value
            }
        
        # Check minimum interval
        if self._trade_timestamps:
            last_trade = max(self._trade_timestamps)
            seconds_since_last = (now - last_trade).total_seconds()
            if seconds_since_last < self.config.min_trade_interval_seconds:
                return {
                    "allowed": False,
                    "reason": f"Minimum trade interval not met ({int(seconds_since_last)}s < {self.config.min_trade_interval_seconds}s)",
                    "state": CircuitBreakerState.COOLDOWN.value
                }
        
        return {"allowed": True}
    
    # ==================== EVENT HANDLERS ====================
    
    def record_trade(self, trade_result: Dict[str, Any]):
        """Record a trade and check for circuit breaker conditions"""
        self._trade_timestamps.append(datetime.now(timezone.utc))
        
        # Check if it was a loss
        pnl = trade_result.get("pnl", 0)
        if pnl < 0:
            self.status.consecutive_losses += 1
            logger.warning(f"📉 Trade loss recorded. Consecutive losses: {self.status.consecutive_losses}")
            
            # Check consecutive loss limit
            if self.status.consecutive_losses >= self.config.max_consecutive_losses:
                self._trip_breaker(
                    f"Max consecutive losses reached ({self.status.consecutive_losses})"
                )
        else:
            # Reset consecutive losses on win
            self.status.consecutive_losses = 0
    
    def check_portfolio_drawdown(self, current_value: float, peak_value: float) -> bool:
        """Check if portfolio drawdown exceeds limit"""
        if peak_value <= 0:
            return True
        
        drawdown_percent = ((peak_value - current_value) / peak_value) * 100
        
        if drawdown_percent >= self.config.max_portfolio_drawdown_percent:
            self._trip_breaker(
                f"Portfolio drawdown limit exceeded ({drawdown_percent:.1f}% > {self.config.max_portfolio_drawdown_percent}%)"
            )
            return False
        
        return True
    
    def check_daily_loss(self, daily_pnl_percent: float) -> bool:
        """Check if daily loss exceeds limit"""
        self.status.daily_loss_percent = daily_pnl_percent
        
        if daily_pnl_percent <= -self.config.max_daily_loss_percent:
            self._trip_breaker(
                f"Daily loss limit exceeded ({daily_pnl_percent:.1f}% > -{self.config.max_daily_loss_percent}%)"
            )
            return False
        
        return True
    
    def check_market_conditions(self, btc_24h_change: float, volatility: float) -> bool:
        """Check market conditions for emergency halts"""
        # Check market crash
        if btc_24h_change <= self.config.market_crash_threshold_percent:
            self._trip_breaker(
                f"Market crash detected (BTC {btc_24h_change:.1f}%)"
            )
            return False
        
        # Check volatility
        if volatility >= self.config.volatility_halt_threshold:
            self._trip_breaker(
                f"High volatility detected ({volatility*100:.1f}% > {self.config.volatility_halt_threshold*100}%)"
            )
            return False
        
        return True
    
    def check_confidence(self, confidence: float) -> bool:
        """Check if AI confidence meets minimum threshold"""
        if confidence < self.config.min_confidence_threshold:
            return False
        return True
    
    # ==================== INTERNAL METHODS ====================
    
    def _trip_breaker(self, reason: str):
        """Trip the circuit breaker"""
        self.status.state = CircuitBreakerState.TRIPPED
        self.status.reason = reason
        self.status.tripped_at = datetime.now(timezone.utc)
        
        logger.warning(f"⚠️ CIRCUIT BREAKER TRIPPED: {reason}")
    
    def _enter_cooldown(self, minutes: int = None):
        """Enter cooldown period"""
        if minutes is None:
            minutes = self.config.cooldown_after_loss_minutes
        
        self.status.state = CircuitBreakerState.COOLDOWN
        self.status.cooldown_until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        
        logger.info(f"⏳ Entering cooldown for {minutes} minutes")
    
    def _reset_status(self):
        """Reset circuit breaker status"""
        self.status = CircuitBreakerStatus()
        logger.info("✅ Circuit breaker reset")
    
    def reset(self):
        """Manual reset of circuit breaker"""
        if self._kill_switch_active:
            return {"status": "error", "message": "Cannot reset while kill switch is active"}
        
        self._reset_status()
        return {"status": "success", "message": "Circuit breaker reset"}
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        return {
            "state": self.status.state.value,
            "kill_switch_active": self._kill_switch_active,
            "reason": self.status.reason,
            "tripped_at": self.status.tripped_at.isoformat() if self.status.tripped_at else None,
            "cooldown_until": self.status.cooldown_until.isoformat() if self.status.cooldown_until else None,
            "consecutive_losses": self.status.consecutive_losses,
            "daily_loss_percent": self.status.daily_loss_percent,
            "trades_today": len(self._trade_timestamps),
            "config": {
                "max_daily_loss": self.config.max_daily_loss_percent,
                "max_drawdown": self.config.max_portfolio_drawdown_percent,
                "max_consecutive_losses": self.config.max_consecutive_losses,
                "max_trades_per_day": self.config.max_trades_per_day,
            }
        }


# Singleton instance
_circuit_breaker = None

def get_circuit_breaker(db=None) -> CircuitBreakerService:
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = CircuitBreakerService(db)
    return _circuit_breaker

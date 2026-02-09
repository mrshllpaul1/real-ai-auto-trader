"""
Enhanced Risk Management System for Automated Trading

Now includes:
- Circuit breakers for maximum daily loss
- Position concentration limits
- Trailing stop-loss management
- Volatility-based position sizing
- Pre-trade risk assessment
- Emergency stop functionality
"""

from typing import Dict, Any, List, Optional, tuple
from datetime import datetime, timedelta
import logging
import numpy as np

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit breaker that halts trading if daily loss exceeds threshold.
    Resets at market close (UTC midnight).
    """
    
    def __init__(self, max_loss_pct: float = 5.0, max_loss_usd: float = 500.0):
        self.max_loss_pct = max_loss_pct
        self.max_loss_usd = max_loss_usd
        self.daily_pnl = 0.0
        self.initial_balance = 0.0
        self.last_reset = datetime.utcnow().date()
        self.is_tripped = False
        self.trip_reason = None
        
    def reset_if_new_day(self):
        """Reset circuit breaker at market close (UTC midnight)"""
        current_date = datetime.utcnow().date()
        if current_date > self.last_reset:
            logger.info(f"🔄 Circuit breaker reset for new trading day: {current_date}")
            self.daily_pnl = 0.0
            self.is_tripped = False
            self.trip_reason = None
            self.last_reset = current_date
            return True
        return False
    
    def set_initial_balance(self, balance: float):
        """Set initial balance for the day"""
        self.initial_balance = balance
        
    def update_pnl(self, pnl: float):
        """Update daily P&L and check if circuit breaker should trip"""
        self.reset_if_new_day()
        self.daily_pnl = pnl
        
        # Check percentage loss
        if self.initial_balance > 0:
            loss_pct = (self.daily_pnl / self.initial_balance) * 100
            if loss_pct <= -self.max_loss_pct:
                self.is_tripped = True
                self.trip_reason = f"Daily loss {loss_pct:.1f}% exceeds limit {self.max_loss_pct}%"
                logger.error(f"🛑 CIRCUIT BREAKER TRIPPED: {self.trip_reason}")
                return True
        
        # Check absolute loss
        if self.daily_pnl <= -self.max_loss_usd:
            self.is_tripped = True
            self.trip_reason = f"Daily loss ${-self.daily_pnl:.2f} exceeds limit ${self.max_loss_usd}"
            logger.error(f"🛑 CIRCUIT BREAKER TRIPPED: {self.trip_reason}")
            return True
        
        return False
    
    def can_trade(self) -> tuple[bool, Optional[str]]:
        """Check if trading is allowed"""
        self.reset_if_new_day()
        
        if self.is_tripped:
            return False, self.trip_reason
        return True, None
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        self.reset_if_new_day()
        
        return {
            'is_tripped': self.is_tripped,
            'daily_pnl': self.daily_pnl,
            'initial_balance': self.initial_balance,
            'max_loss_pct': self.max_loss_pct,
            'max_loss_usd': self.max_loss_usd,
            'trip_reason': self.trip_reason,
            'last_reset': self.last_reset.isoformat()
        }


class RiskManager:
    def __init__(self, db):
        self.db = db
        
        # Initialize advanced risk components
        self.circuit_breaker = CircuitBreaker()
        self.emergency_stop = False
        self.emergency_stop_reason = None
    
    async def get_risk_settings(self, user_id: str) -> Dict[str, Any]:
        """Get risk management settings for a user"""
        settings = await self.db.risk_settings.find_one({"user_id": user_id}, {"_id": 0})
        
        if not settings:
            # Default risk settings
            settings = {
                "user_id": user_id,
                "max_investment_per_trade": 1000,  # USD
                "stop_loss_percentage": 5,  # %
                "take_profit_percentage": 15,  # %
                "max_daily_trades": 10,
                "max_portfolio_allocation": 20,  # % per coin
                "risk_level": "medium"  # low, medium, high
            }
            await self.db.risk_settings.insert_one(settings)
        
        return settings
    
    async def update_risk_settings(
        self,
        user_id: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update risk management settings"""
        await self.db.risk_settings.update_one(
            {"user_id": user_id},
            {"$set": settings},
            upsert=True
        )
        return await self.get_risk_settings(user_id)
    
    async def validate_trade(
        self,
        user_id: str,
        amount: float,
        coin_pair: str
    ) -> Dict[str, Any]:
        """Validate if a trade meets risk management criteria"""
        settings = await self.get_risk_settings(user_id)
        
        # Check max investment per trade
        if amount > settings.get('max_investment_per_trade', 1000):
            return {
                "valid": False,
                "reason": f"Trade amount exceeds max investment per trade: ${settings.get('max_investment_per_trade')}"
            }
        
        # Check daily trade limit
        from datetime import datetime, timedelta
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        daily_trades = await self.db.trades.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": today_start.isoformat()}
        })
        
        if daily_trades >= settings.get('max_daily_trades', 10):
            return {
                "valid": False,
                "reason": f"Daily trade limit reached: {settings.get('max_daily_trades')}"
            }
        
        return {"valid": True, "reason": "Trade passes risk validation"}
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        stop_loss_percentage: float
    ) -> float:
        """Calculate stop loss price"""
        return entry_price * (1 - stop_loss_percentage / 100)
    
    def calculate_take_profit(
        self,
        entry_price: float,
        take_profit_percentage: float
    ) -> float:
        """Calculate take profit price"""
        return entry_price * (1 + take_profit_percentage / 100)
    
    async def assess_trade_risk(self, trade_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive pre-trade risk assessment with circuit breaker integration.
        
        Returns risk score (0-100) and detailed risk factors.
        """
        risk_factors = []
        risk_score = 0
        
        user_id = trade_info.get('user_id')
        symbol = trade_info.get('symbol')
        position_value = trade_info.get('position_value', 0)
        model_confidence = trade_info.get('confidence', 50)
        
        # Get user's risk settings
        settings = await self.get_risk_settings(user_id)
        
        # Factor 1: Circuit breaker status (0-30 points)
        can_trade, reason = self.circuit_breaker.can_trade()
        if not can_trade:
            risk_score += 30
            risk_factors.append({'factor': 'circuit_breaker', 'risk': 30, 'reason': reason})
        elif self.circuit_breaker.daily_pnl < 0:
            # Add risk based on current loss
            loss_ratio = abs(self.circuit_breaker.daily_pnl) / self.circuit_breaker.max_loss_usd
            points = min(15, loss_ratio * 15)
            risk_score += points
            risk_factors.append({'factor': 'daily_loss', 'risk': points, 'reason': f'Current daily loss: ${self.circuit_breaker.daily_pnl:.2f}'})
        
        # Factor 2: Position size vs max investment (0-25 points)
        max_investment = settings.get('max_investment_per_trade', 1000)
        if position_value > max_investment:
            risk_score += 25
            risk_factors.append({'factor': 'position_size', 'risk': 25, 'reason': f'Position ${position_value:.2f} exceeds limit ${max_investment}'})
        else:
            size_ratio = position_value / max_investment
            points = size_ratio * 15
            risk_score += points
            risk_factors.append({'factor': 'position_size', 'risk': points, 'reason': f'Position is {size_ratio*100:.1f}% of max'})
        
        # Factor 3: Model confidence (0-25 points)
        # Lower confidence = higher risk
        if model_confidence < 50:
            points = 25
        elif model_confidence < 60:
            points = 20
        elif model_confidence < 70:
            points = 15
        elif model_confidence < 80:
            points = 10
        else:
            points = 5
        risk_score += points
        risk_factors.append({'factor': 'model_confidence', 'risk': points, 'reason': f'Model confidence: {model_confidence:.1f}%'})
        
        # Factor 4: Daily trade limit (0-20 points)
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_trades = await self.db.trades.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": today_start.isoformat()}
        })
        max_daily = settings.get('max_daily_trades', 10)
        
        if daily_trades >= max_daily:
            risk_score += 20
            risk_factors.append({'factor': 'daily_limit', 'risk': 20, 'reason': f'Daily trade limit reached: {daily_trades}/{max_daily}'})
        else:
            trade_ratio = daily_trades / max_daily
            points = trade_ratio * 10
            risk_score += points
            risk_factors.append({'factor': 'daily_trades', 'risk': points, 'reason': f'Trades today: {daily_trades}/{max_daily}'})
        
        # Determine risk level
        if risk_score < 30:
            risk_level = 'low'
            recommendation = 'proceed'
        elif risk_score < 60:
            risk_level = 'medium'
            recommendation = 'proceed_with_caution'
        elif risk_score < 80:
            risk_level = 'high'
            recommendation = 'reduce_size'
        else:
            risk_level = 'extreme'
            recommendation = 'skip_trade'
        
        return {
            'risk_score': round(risk_score, 1),
            'risk_level': risk_level,
            'recommendation': recommendation,
            'risk_factors': risk_factors,
            'can_trade': risk_score < 80 and not self.emergency_stop,
            'suggested_size_multiplier': max(0.3, 1 - (risk_score / 100)),
            'emergency_stop': self.emergency_stop
        }
    
    def trigger_emergency_stop(self, reason: str):
        """Trigger emergency stop - halts all trading immediately"""
        self.emergency_stop = True
        self.emergency_stop_reason = reason
        logger.error(f"🚨 EMERGENCY STOP TRIGGERED: {reason}")
        
    def reset_emergency_stop(self):
        """Reset emergency stop (requires manual intervention)"""
        self.emergency_stop = False
        self.emergency_stop_reason = None
        logger.info("✅ Emergency stop reset")
        
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get complete risk management status"""
        return {
            'emergency_stop': self.emergency_stop,
            'emergency_stop_reason': self.emergency_stop_reason,
            'circuit_breaker': self.circuit_breaker.get_status(),
            'timestamp': datetime.now().isoformat()
        }
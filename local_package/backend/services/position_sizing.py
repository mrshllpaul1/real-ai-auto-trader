"""
Position Sizing Service
=======================
Implements Kelly Criterion and risk-adjusted position sizing.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)

@dataclass
class PositionSizeResult:
    """Result of position size calculation"""
    recommended_size_usd: float
    position_percent: float
    kelly_fraction: float
    risk_adjusted: bool
    max_allowed: float
    reasoning: str

class PositionSizingService:
    """
    Calculate optimal position sizes using Kelly Criterion and risk management.
    """
    
    def __init__(self, risk_config=None):
        if risk_config is None:
            from config.risk_config import DEFAULT_RISK_CONFIG
            risk_config = DEFAULT_RISK_CONFIG
        
        self.config = risk_config
        logger.info("📊 Position Sizing Service initialized")
    
    def kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        fraction: float = 0.25
    ) -> float:
        """
        Calculate Kelly Criterion position size.
        
        Kelly formula: f* = (p * b - q) / b
        where:
            f* = fraction of bankroll to bet
            p = probability of winning
            q = probability of losing (1 - p)
            b = odds (win/loss ratio)
        
        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average winning trade size
            avg_loss: Average losing trade size (positive number)
            fraction: Kelly fraction to use (0.25 = quarter Kelly, safer)
        
        Returns:
            Recommended position size as fraction of portfolio
        """
        if avg_loss == 0:
            return 0
        
        p = win_rate
        q = 1 - win_rate
        b = avg_win / avg_loss  # Win/loss ratio
        
        # Full Kelly
        kelly = (p * b - q) / b
        
        # Apply fraction for safety (quarter Kelly is common)
        fractional_kelly = kelly * fraction
        
        # Clamp to reasonable range
        return max(0, min(fractional_kelly, 0.25))  # Never more than 25%
    
    def calculate_position_size(
        self,
        portfolio_value: float,
        signal_confidence: float,
        win_rate: float = 0.55,
        avg_win: float = 1.5,
        avg_loss: float = 1.0,
        volatility: float = 0.02,
        asset: str = None
    ) -> PositionSizeResult:
        """
        Calculate recommended position size based on multiple factors.
        
        Args:
            portfolio_value: Current portfolio value in USD
            signal_confidence: AI signal confidence (0-1)
            win_rate: Historical win rate
            avg_win: Average winning trade multiplier
            avg_loss: Average losing trade multiplier
            volatility: Current market volatility
            asset: Asset being traded (for concentration limits)
        
        Returns:
            PositionSizeResult with recommendation
        """
        reasoning_parts = []
        
        # 1. Base Kelly calculation
        kelly_fraction = self.kelly_criterion(win_rate, avg_win, avg_loss)
        reasoning_parts.append(f"Kelly suggests {kelly_fraction*100:.1f}%")
        
        # 2. Confidence adjustment
        # Scale position by confidence (higher confidence = larger position)
        confidence_multiplier = signal_confidence  # Linear scaling
        adjusted_fraction = kelly_fraction * confidence_multiplier
        reasoning_parts.append(f"Confidence ({signal_confidence*100:.0f}%) adjusted to {adjusted_fraction*100:.1f}%")
        
        # 3. Volatility adjustment
        # Reduce position in high volatility
        if volatility > 0.03:  # High volatility
            vol_multiplier = 0.5
            reasoning_parts.append("High volatility: reducing by 50%")
        elif volatility > 0.02:  # Medium volatility
            vol_multiplier = 0.75
            reasoning_parts.append("Medium volatility: reducing by 25%")
        else:
            vol_multiplier = 1.0
        
        adjusted_fraction *= vol_multiplier
        
        # 4. Apply risk limits
        max_trade_percent = self.config.max_single_trade_percent / 100
        if adjusted_fraction > max_trade_percent:
            adjusted_fraction = max_trade_percent
            reasoning_parts.append(f"Capped at max {self.config.max_single_trade_percent}%")
        
        # 5. Calculate USD amount
        position_usd = portfolio_value * adjusted_fraction
        
        # 6. Apply max position size limit
        if position_usd > self.config.max_position_size_usd:
            position_usd = self.config.max_position_size_usd
            adjusted_fraction = position_usd / portfolio_value if portfolio_value > 0 else 0
            reasoning_parts.append(f"Capped at max ${self.config.max_position_size_usd}")
        
        # 7. Minimum viable trade
        min_trade = 10  # $10 minimum
        if position_usd < min_trade:
            position_usd = 0
            adjusted_fraction = 0
            reasoning_parts.append("Below minimum trade size - no trade")
        
        return PositionSizeResult(
            recommended_size_usd=round(position_usd, 2),
            position_percent=round(adjusted_fraction * 100, 2),
            kelly_fraction=round(kelly_fraction, 4),
            risk_adjusted=True,
            max_allowed=self.config.max_position_size_usd,
            reasoning=" → ".join(reasoning_parts)
        )
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        volatility: float,
        risk_percent: float = 2.0,
        use_atr: bool = True,
        atr_multiplier: float = 2.0
    ) -> Dict[str, float]:
        """
        Calculate dynamic stop loss levels.
        
        Args:
            entry_price: Entry price of the trade
            volatility: Current volatility (as decimal, e.g., 0.02 for 2%)
            risk_percent: Maximum risk per trade as percent
            use_atr: Whether to use ATR-based stop
            atr_multiplier: ATR multiplier for stop distance
        
        Returns:
            Dict with stop loss price and percent from entry
        """
        if use_atr:
            # ATR-based stop loss
            stop_distance = entry_price * volatility * atr_multiplier
        else:
            # Fixed percentage stop
            stop_distance = entry_price * (risk_percent / 100)
        
        stop_price = entry_price - stop_distance
        stop_percent = (stop_distance / entry_price) * 100
        
        return {
            "stop_price": round(stop_price, 8),
            "stop_percent": round(stop_percent, 2),
            "risk_usd_per_unit": round(stop_distance, 8)
        }
    
    def calculate_take_profit(
        self,
        entry_price: float,
        stop_loss: float,
        risk_reward_ratio: float = 2.0
    ) -> Dict[str, Any]:
        """
        Calculate take profit levels based on risk/reward ratio.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_reward_ratio: Desired risk/reward ratio (2.0 = 2:1)
        
        Returns:
            Dict with take profit levels
        """
        risk = entry_price - stop_loss
        reward = risk * risk_reward_ratio
        
        # Multiple take profit levels (scale out)
        tp1 = entry_price + (reward * 0.5)   # 50% of target
        tp2 = entry_price + reward            # Full target
        tp3 = entry_price + (reward * 1.5)   # Extended target
        
        return {
            "tp1": {
                "price": round(tp1, 8),
                "percent": round(((tp1 - entry_price) / entry_price) * 100, 2),
                "close_percent": 33  # Close 33% of position
            },
            "tp2": {
                "price": round(tp2, 8),
                "percent": round(((tp2 - entry_price) / entry_price) * 100, 2),
                "close_percent": 33
            },
            "tp3": {
                "price": round(tp3, 8),
                "percent": round(((tp3 - entry_price) / entry_price) * 100, 2),
                "close_percent": 34  # Remaining position
            },
            "risk_reward_ratio": risk_reward_ratio
        }
    
    def scale_in_strategy(
        self,
        total_position_usd: float,
        num_entries: int = 3
    ) -> list:
        """
        Generate scale-in entry strategy.
        
        Args:
            total_position_usd: Total position size to build
            num_entries: Number of entries to scale in
        
        Returns:
            List of entry amounts
        """
        if num_entries <= 1:
            return [total_position_usd]
        
        # Pyramid: larger first entry, smaller subsequent
        # Example for 3 entries: 50%, 30%, 20%
        if num_entries == 2:
            weights = [0.6, 0.4]
        elif num_entries == 3:
            weights = [0.5, 0.3, 0.2]
        elif num_entries == 4:
            weights = [0.4, 0.3, 0.2, 0.1]
        else:
            # Equal weighting for more entries
            weights = [1/num_entries] * num_entries
        
        return [
            {
                "entry_num": i + 1,
                "amount_usd": round(total_position_usd * w, 2),
                "percent_of_total": round(w * 100, 1)
            }
            for i, w in enumerate(weights)
        ]


# Singleton
_position_sizing = None

def get_position_sizing_service() -> PositionSizingService:
    global _position_sizing
    if _position_sizing is None:
        _position_sizing = PositionSizingService()
    return _position_sizing

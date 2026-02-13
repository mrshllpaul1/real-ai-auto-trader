"""
Risk Management Configuration
=============================
Centralized risk limits and circuit breakers for the trading system.
"""

from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum

class RiskLevel(Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

@dataclass
class RiskConfig:
    """Risk configuration parameters"""
    
    # Portfolio Limits
    max_portfolio_drawdown_percent: float = 15.0      # Stop all trading if down 15%
    max_daily_loss_percent: float = 5.0               # Halt trading for day if down 5%
    max_single_trade_percent: float = 5.0             # Max 5% of portfolio per trade
    
    # Position Limits
    max_position_size_usd: float = 500.0              # No single position > $500
    max_positions_count: int = 10                      # Max 10 open positions
    max_leverage: float = 1.0                          # No leverage initially
    max_concentration_percent: float = 25.0            # Max 25% in single asset
    
    # Circuit Breakers
    max_consecutive_losses: int = 5                    # Pause after 5 consecutive losses
    min_confidence_threshold: float = 0.7              # Only trade with >70% AI confidence
    cooldown_after_loss_minutes: int = 30              # Wait 30min after loss
    
    # Emergency Stops
    market_crash_threshold_percent: float = -10.0      # Halt if BTC drops 10% in 24h
    volatility_halt_threshold: float = 0.05            # Halt if volatility > 5%
    
    # Trade Limits
    max_trades_per_day: int = 20                       # Max 20 trades per day
    max_trades_per_hour: int = 5                       # Max 5 trades per hour
    min_trade_interval_seconds: int = 60               # At least 1 min between trades
    
    # Slippage & Fees
    max_slippage_percent: float = 1.0                  # Cancel if slippage > 1%
    include_fees_in_calculations: bool = True


# Preset configurations
RISK_PRESETS: Dict[RiskLevel, RiskConfig] = {
    RiskLevel.CONSERVATIVE: RiskConfig(
        max_portfolio_drawdown_percent=10.0,
        max_daily_loss_percent=3.0,
        max_single_trade_percent=2.0,
        max_position_size_usd=200.0,
        max_positions_count=5,
        min_confidence_threshold=0.8,
        max_trades_per_day=10,
    ),
    RiskLevel.MODERATE: RiskConfig(
        max_portfolio_drawdown_percent=15.0,
        max_daily_loss_percent=5.0,
        max_single_trade_percent=5.0,
        max_position_size_usd=500.0,
        max_positions_count=10,
        min_confidence_threshold=0.7,
        max_trades_per_day=20,
    ),
    RiskLevel.AGGRESSIVE: RiskConfig(
        max_portfolio_drawdown_percent=25.0,
        max_daily_loss_percent=10.0,
        max_single_trade_percent=10.0,
        max_position_size_usd=1000.0,
        max_positions_count=15,
        min_confidence_threshold=0.6,
        max_trades_per_day=50,
    ),
}

# Default configuration
DEFAULT_RISK_CONFIG = RISK_PRESETS[RiskLevel.MODERATE]


def get_risk_config(level: RiskLevel = RiskLevel.MODERATE) -> RiskConfig:
    """Get risk configuration for a specific level"""
    return RISK_PRESETS.get(level, DEFAULT_RISK_CONFIG)

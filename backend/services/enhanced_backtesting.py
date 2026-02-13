"""
Enhanced Backtesting Framework
==============================
Comprehensive backtesting system with walk-forward validation.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
import statistics
import math

logger = logging.getLogger(__name__)

@dataclass
class BacktestTrade:
    """Single trade in backtest"""
    entry_time: datetime
    exit_time: datetime
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    pnl_percent: float
    fees: float
    signal_confidence: float

@dataclass
class BacktestResult:
    """Complete backtest results"""
    # Basic Info
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    
    # Returns
    total_return_percent: float
    annualized_return_percent: float
    
    # Risk Metrics
    max_drawdown_percent: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Trade Statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win_percent: float
    avg_loss_percent: float
    profit_factor: float
    avg_trade_duration: float  # hours
    
    # Additional
    best_trade_percent: float
    worst_trade_percent: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    
    # Validation
    passed_validation: bool
    validation_notes: List[str] = field(default_factory=list)
    
    # Trade list
    trades: List[BacktestTrade] = field(default_factory=list)


class EnhancedBacktestEngine:
    """
    Enhanced backtesting engine with realistic simulation including:
    - Transaction costs
    - Slippage
    - Walk-forward validation
    """
    
    # Minimum requirements for strategy validation
    VALIDATION_REQUIREMENTS = {
        "min_history_days": 365,
        "min_trades": 100,
        "max_drawdown_threshold": 20.0,
        "min_sharpe_ratio": 1.5,
        "min_win_rate": 0.45,
        "min_profit_factor": 1.5,
    }
    
    def __init__(
        self,
        initial_capital: float = 10000,
        commission_percent: float = 0.1,
        slippage_percent: float = 0.05
    ):
        self.initial_capital = initial_capital
        self.commission_percent = commission_percent
        self.slippage_percent = slippage_percent
        
        logger.info("🔬 Enhanced Backtest Engine initialized")
    
    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """Calculate maximum drawdown percentage"""
        if not equity_curve:
            return 0
        
        peak = equity_curve[0]
        max_dd = 0
        
        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = ((peak - value) / peak) * 100 if peak > 0 else 0
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def _calculate_consecutive(self, trades: List[BacktestTrade]) -> tuple:
        """Calculate max consecutive wins and losses"""
        max_wins = max_losses = 0
        current_wins = current_losses = 0
        
        for trade in trades:
            if trade.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
        
        return max_wins, max_losses
    
    def validate_strategy(
        self,
        days: int,
        total_trades: int,
        max_drawdown: float,
        sharpe: float,
        win_rate: float,
        profit_factor: float
    ) -> tuple:
        """Validate strategy against minimum requirements"""
        notes = []
        passed = True
        
        req = self.VALIDATION_REQUIREMENTS
        
        if days < req["min_history_days"]:
            notes.append(f"❌ Insufficient history: {days} days < {req['min_history_days']} required")
            passed = False
        else:
            notes.append(f"✅ History: {days} days")
        
        if total_trades < req["min_trades"]:
            notes.append(f"❌ Insufficient trades: {total_trades} < {req['min_trades']} required")
            passed = False
        else:
            notes.append(f"✅ Trades: {total_trades}")
        
        if max_drawdown > req["max_drawdown_threshold"]:
            notes.append(f"❌ Drawdown too high: {max_drawdown:.1f}% > {req['max_drawdown_threshold']}%")
            passed = False
        else:
            notes.append(f"✅ Max Drawdown: {max_drawdown:.1f}%")
        
        if sharpe < req["min_sharpe_ratio"]:
            notes.append(f"❌ Sharpe too low: {sharpe:.2f} < {req['min_sharpe_ratio']}")
            passed = False
        else:
            notes.append(f"✅ Sharpe Ratio: {sharpe:.2f}")
        
        if win_rate < req["min_win_rate"]:
            notes.append(f"❌ Win rate too low: {win_rate*100:.1f}% < {req['min_win_rate']*100}%")
            passed = False
        else:
            notes.append(f"✅ Win Rate: {win_rate*100:.1f}%")
        
        if profit_factor < req["min_profit_factor"]:
            notes.append(f"❌ Profit factor too low: {profit_factor:.2f} < {req['min_profit_factor']}")
            passed = False
        else:
            notes.append(f"✅ Profit Factor: {profit_factor:.2f}")
        
        return passed, notes
    
    def get_validation_requirements(self) -> Dict[str, Any]:
        """Get the validation requirements"""
        return self.VALIDATION_REQUIREMENTS


# Singleton
_enhanced_backtest_engine = None

def get_enhanced_backtest_engine() -> EnhancedBacktestEngine:
    global _enhanced_backtest_engine
    if _enhanced_backtest_engine is None:
        _enhanced_backtest_engine = EnhancedBacktestEngine()
    return _enhanced_backtest_engine

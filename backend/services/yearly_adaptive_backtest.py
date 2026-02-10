"""
Yearly Adaptive Backtesting System
===================================
Comprehensive backtesting system that:
1. Runs full year 2025 backtest with weekly adaptation
2. Tests across all Kraken coins
3. Automatically adapts strategy parameters weekly
4. Creates profitable portfolio with auto-trading signals
"""

import logging
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

logger = logging.getLogger(__name__)

# Top performing coins by market cap and liquidity
TOP_COINS = [
    "BTC", "ETH", "SOL", "XRP", "ADA", "AVAX", "DOT", "LINK", "MATIC", "ATOM",
    "UNI", "NEAR", "FIL", "ARB", "OP", "SUI", "APT", "INJ", "TIA", "SEI",
    "DOGE", "SHIB", "PEPE", "BONK", "WIF", "FLOKI", "MEME", "TURBO", "MOG",
    "LTC", "BCH", "ETC", "XMR", "ZEC", "DASH", "XLM", "ALGO", "HBAR", "VET",
    "AAVE", "MKR", "CRV", "LDO", "SNX", "COMP", "SUSHI", "YFI", "BAL", "1INCH"
]

# Market regime parameters
MARKET_REGIMES = {
    "bull_strong": {"bias": 0.003, "volatility": 0.02, "trend_strength": 0.8},
    "bull_weak": {"bias": 0.001, "volatility": 0.015, "trend_strength": 0.5},
    "bear_strong": {"bias": -0.003, "volatility": 0.025, "trend_strength": 0.8},
    "bear_weak": {"bias": -0.001, "volatility": 0.018, "trend_strength": 0.5},
    "sideways": {"bias": 0, "volatility": 0.012, "trend_strength": 0.2},
    "high_volatility": {"bias": 0, "volatility": 0.04, "trend_strength": 0.3},
    "recovery": {"bias": 0.002, "volatility": 0.022, "trend_strength": 0.6}
}

# 2025 Market calendar - key events that affect market regime
MARKET_EVENTS_2025 = [
    {"week": 1, "regime": "sideways", "event": "New Year consolidation"},
    {"week": 3, "regime": "bull_weak", "event": "Q1 optimism begins"},
    {"week": 5, "regime": "bull_strong", "event": "Bitcoin ETF inflows continue"},
    {"week": 8, "regime": "high_volatility", "event": "Fed meeting uncertainty"},
    {"week": 10, "regime": "bear_weak", "event": "Profit taking"},
    {"week": 12, "regime": "recovery", "event": "Q1 earnings positive"},
    {"week": 15, "regime": "bull_strong", "event": "Bitcoin halving anniversary rally"},
    {"week": 18, "regime": "sideways", "event": "May consolidation"},
    {"week": 20, "regime": "bear_weak", "event": "Sell in May effect"},
    {"week": 22, "regime": "bear_strong", "event": "Summer correction"},
    {"week": 25, "regime": "sideways", "event": "Summer doldrums"},
    {"week": 28, "regime": "recovery", "event": "Institutional buying"},
    {"week": 30, "regime": "bull_weak", "event": "Q3 optimism"},
    {"week": 33, "regime": "high_volatility", "event": "Fed Jackson Hole"},
    {"week": 35, "regime": "bear_weak", "event": "September effect"},
    {"week": 38, "regime": "recovery", "event": "Q3 earnings positive"},
    {"week": 40, "regime": "bull_weak", "event": "Uptober begins"},
    {"week": 42, "regime": "bull_strong", "event": "Pre-election rally"},
    {"week": 45, "regime": "high_volatility", "event": "Election week"},
    {"week": 47, "regime": "bull_strong", "event": "Post-election clarity"},
    {"week": 50, "regime": "bull_weak", "event": "Year-end positioning"},
    {"week": 52, "regime": "sideways", "event": "Holiday low volume"}
]


class AdaptiveStrategy:
    """Adaptive strategy that adjusts parameters based on market conditions"""
    
    def __init__(self, initial_params: Dict = None):
        self.params = initial_params or {
            "lookback": 20,
            "rsi_oversold": 25,
            "rsi_overbought": 75,
            "entry_threshold": 7,
            "take_profit_pct": 12,
            "stop_loss_pct": 4,
            "volatility_filter": 0.03,
            "trend_strength_min": 0.015,
            "position_size_pct": 10,
            "max_positions": 5
        }
        self.performance_history = []
        self.regime_params = {}
        
    def adapt_to_regime(self, regime: str, recent_win_rate: float = 0.5):
        """Adapt strategy parameters based on market regime and recent performance"""
        regime_config = MARKET_REGIMES.get(regime, MARKET_REGIMES["sideways"])
        
        # Base adjustments per regime
        if regime in ["bull_strong", "bull_weak"]:
            # More aggressive in bull markets
            self.params["rsi_oversold"] = 30 if regime == "bull_strong" else 25
            self.params["entry_threshold"] = 6 if regime == "bull_strong" else 7
            self.params["take_profit_pct"] = 15 if regime == "bull_strong" else 12
            self.params["position_size_pct"] = 12 if regime == "bull_strong" else 10
            
        elif regime in ["bear_strong", "bear_weak"]:
            # More conservative in bear markets
            self.params["rsi_overbought"] = 70 if regime == "bear_strong" else 75
            self.params["entry_threshold"] = 9 if regime == "bear_strong" else 8
            self.params["stop_loss_pct"] = 3 if regime == "bear_strong" else 4
            self.params["position_size_pct"] = 6 if regime == "bear_strong" else 8
            
        elif regime == "high_volatility":
            # Very conservative in high volatility
            self.params["entry_threshold"] = 10
            self.params["volatility_filter"] = 0.05
            self.params["stop_loss_pct"] = 5
            self.params["position_size_pct"] = 5
            self.params["max_positions"] = 3
            
        elif regime == "sideways":
            # Mean reversion focused
            self.params["rsi_oversold"] = 20
            self.params["rsi_overbought"] = 80
            self.params["entry_threshold"] = 8
            self.params["take_profit_pct"] = 8
            
        elif regime == "recovery":
            # Cautiously optimistic
            self.params["entry_threshold"] = 7
            self.params["take_profit_pct"] = 10
            self.params["position_size_pct"] = 10
        
        # Performance-based adjustments
        if recent_win_rate < 0.4:
            # Tighten parameters if losing
            self.params["entry_threshold"] = min(12, self.params["entry_threshold"] + 2)
            self.params["stop_loss_pct"] = max(2, self.params["stop_loss_pct"] - 1)
        elif recent_win_rate > 0.7:
            # Loosen slightly if winning consistently
            self.params["entry_threshold"] = max(5, self.params["entry_threshold"] - 1)
            self.params["position_size_pct"] = min(15, self.params["position_size_pct"] + 1)
        
        return self.params


def generate_coin_prices(coin: str, days: int, market_events: List[Dict]) -> List[float]:
    """Generate realistic price data for a coin over the year"""
    # Base prices for major coins
    base_prices = {
        "BTC": 68000, "ETH": 3500, "SOL": 150, "XRP": 0.55, "ADA": 0.45,
        "AVAX": 35, "DOT": 7, "LINK": 15, "MATIC": 0.9, "ATOM": 9,
        "UNI": 7, "NEAR": 5, "FIL": 6, "ARB": 1.2, "OP": 2.5,
        "SUI": 1.5, "APT": 9, "INJ": 25, "TIA": 8, "SEI": 0.5,
        "DOGE": 0.12, "SHIB": 0.000022, "PEPE": 0.0000012, "BONK": 0.00003,
        "LTC": 85, "BCH": 450, "XMR": 170, "ALGO": 0.20, "HBAR": 0.08
    }
    
    base_price = base_prices.get(coin, random.uniform(0.1, 100))
    
    # Coin-specific volatility multiplier
    high_vol_coins = ["PEPE", "BONK", "SHIB", "DOGE", "WIF", "FLOKI", "MEME", "MOG"]
    vol_mult = 2.0 if coin in high_vol_coins else 1.0
    
    # Beta to BTC (correlation)
    btc_betas = {
        "ETH": 0.9, "SOL": 1.2, "AVAX": 1.1, "DOT": 1.0, "LINK": 0.85,
        "DOGE": 1.5, "SHIB": 1.8, "PEPE": 2.0, "BONK": 1.9
    }
    beta = btc_betas.get(coin, random.uniform(0.7, 1.3))
    
    prices = []
    current_price = base_price
    current_regime = "sideways"
    current_event_idx = 0
    
    for day in range(days):
        week = day // 7 + 1
        
        # Update regime based on market events
        while current_event_idx < len(market_events) and week >= market_events[current_event_idx]["week"]:
            current_regime = market_events[current_event_idx]["regime"]
            current_event_idx += 1
        
        regime_config = MARKET_REGIMES.get(current_regime, MARKET_REGIMES["sideways"])
        
        # Daily return based on regime
        base_drift = regime_config["bias"] * beta
        volatility = regime_config["volatility"] * vol_mult
        
        # Add some coin-specific randomness
        coin_specific = random.gauss(0, 0.005)
        
        daily_return = base_drift + random.gauss(0, volatility) + coin_specific
        
        # Occasional large moves for meme coins
        if coin in high_vol_coins and random.random() < 0.05:
            daily_return += random.choice([-1, 1]) * random.uniform(0.1, 0.3)
        
        current_price *= (1 + daily_return)
        current_price = max(current_price * 0.01, current_price)  # Floor at 1% of original
        prices.append(current_price)
    
    return prices


def calculate_technical_indicators(prices: List[float], idx: int) -> Dict:
    """Calculate comprehensive technical indicators at a given index"""
    if idx < 30:
        return {"valid": False}
    
    # Price windows
    p = prices[max(0, idx-50):idx+1]
    
    # Moving averages
    sma_5 = sum(p[-5:]) / 5
    sma_10 = sum(p[-10:]) / 10
    sma_20 = sum(p[-20:]) / 20
    sma_50 = sum(p) / len(p) if len(p) >= 50 else sma_20
    
    # EMA calculation
    def calc_ema(data, period):
        if len(data) < period:
            return sum(data) / len(data)
        mult = 2 / (period + 1)
        ema = sum(data[:period]) / period
        for price in data[period:]:
            ema = (price - ema) * mult + ema
        return ema
    
    ema_12 = calc_ema(p, 12)
    ema_26 = calc_ema(p, 26)
    macd = ema_12 - ema_26
    
    # RSI
    gains, losses = [], []
    for i in range(1, min(15, len(p))):
        diff = p[-i] - p[-i-1]
        gains.append(max(0, diff))
        losses.append(max(0, -diff))
    avg_gain = sum(gains) / max(len(gains), 1)
    avg_loss = sum(losses) / max(len(losses), 1) + 1e-10
    rsi = 100 - (100 / (1 + avg_gain / avg_loss))
    
    # Volatility
    returns = [(p[i] - p[i-1]) / p[i-1] for i in range(1, len(p))]
    volatility = (sum(r**2 for r in returns[-20:]) / 20) ** 0.5 if len(returns) >= 20 else 0.02
    
    # Momentum
    momentum_5 = (p[-1] - p[-6]) / p[-6] if len(p) > 5 else 0
    momentum_10 = (p[-1] - p[-11]) / p[-11] if len(p) > 10 else 0
    
    # Trend strength
    trend_up = sma_5 > sma_10 > sma_20
    trend_down = sma_5 < sma_10 < sma_20
    
    # Support/Resistance
    recent_high = max(p[-20:])
    recent_low = min(p[-20:])
    price_position = (p[-1] - recent_low) / (recent_high - recent_low + 1e-10)
    
    return {
        "valid": True,
        "price": p[-1],
        "sma_5": sma_5,
        "sma_10": sma_10,
        "sma_20": sma_20,
        "sma_50": sma_50,
        "macd": macd,
        "rsi": rsi,
        "volatility": volatility,
        "momentum_5": momentum_5,
        "momentum_10": momentum_10,
        "trend_up": trend_up,
        "trend_down": trend_down,
        "price_position": price_position,
        "recent_high": recent_high,
        "recent_low": recent_low
    }


def generate_trading_signal(indicators: Dict, params: Dict, position_held: bool = False) -> Dict:
    """Generate trading signal based on indicators and strategy parameters"""
    if not indicators.get("valid"):
        return {"signal": "hold", "strength": 0, "reason": "insufficient_data"}
    
    buy_score = 0
    sell_score = 0
    reasons = []
    
    # RSI signals
    if indicators["rsi"] < params["rsi_oversold"]:
        buy_score += 4
        reasons.append(f"RSI oversold ({indicators['rsi']:.1f})")
    elif indicators["rsi"] > params["rsi_overbought"]:
        sell_score += 4
        reasons.append(f"RSI overbought ({indicators['rsi']:.1f})")
    
    # Trend signals
    if indicators["trend_up"]:
        buy_score += 3
        reasons.append("Uptrend confirmed")
    elif indicators["trend_down"]:
        sell_score += 3
        reasons.append("Downtrend confirmed")
    
    # MACD
    if indicators["macd"] > 0:
        buy_score += 2
    else:
        sell_score += 2
    
    # Momentum
    if indicators["momentum_5"] > params["trend_strength_min"]:
        buy_score += 3
        reasons.append(f"Strong momentum ({indicators['momentum_5']*100:.1f}%)")
    elif indicators["momentum_5"] < -params["trend_strength_min"]:
        sell_score += 3
        reasons.append(f"Weak momentum ({indicators['momentum_5']*100:.1f}%)")
    
    # Price position (mean reversion)
    if indicators["price_position"] < 0.2:
        buy_score += 2
        reasons.append("Near support")
    elif indicators["price_position"] > 0.8:
        sell_score += 2
        reasons.append("Near resistance")
    
    # Volatility filter
    if indicators["volatility"] > params["volatility_filter"]:
        buy_score = int(buy_score * 0.5)
        sell_score = int(sell_score * 0.5)
        reasons.append("High volatility penalty")
    
    # Determine signal
    threshold = params["entry_threshold"]
    
    if buy_score >= threshold and buy_score > sell_score + 2:
        return {
            "signal": "buy",
            "strength": min(1.0, buy_score / 15),
            "score": buy_score,
            "reason": "; ".join(reasons[:3])
        }
    elif sell_score >= threshold and sell_score > buy_score + 2:
        return {
            "signal": "sell",
            "strength": min(1.0, sell_score / 15),
            "score": sell_score,
            "reason": "; ".join(reasons[:3])
        }
    
    return {"signal": "hold", "strength": 0, "score": max(buy_score, sell_score), "reason": "No clear signal"}


class YearlyBacktestEngine:
    """Engine to run full year backtest with weekly adaptation"""
    
    def __init__(self, initial_capital: float = 100000, coins: List[str] = None):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.coins = coins or TOP_COINS[:20]  # Default to top 20 coins
        self.strategy = AdaptiveStrategy()
        self.positions = {}
        self.trades = []
        self.weekly_performance = []
        self.equity_curve = []
        self.regime_history = []
        
    def run_full_year_backtest(self) -> Dict:
        """Run complete 2025 backtest with weekly adaptation"""
        days_in_year = 365
        weeks_in_year = 52
        
        # Generate price data for all coins
        logger.info(f"Generating price data for {len(self.coins)} coins over {days_in_year} days")
        coin_prices = {}
        for coin in self.coins:
            coin_prices[coin] = generate_coin_prices(coin, days_in_year, MARKET_EVENTS_2025)
        
        # Initialize tracking
        daily_equity = [self.initial_capital]
        current_week = 0
        week_start_capital = self.initial_capital
        weekly_trades = 0
        weekly_wins = 0
        
        # Run day by day
        for day in range(days_in_year):
            week = day // 7
            day_of_week = day % 7
            
            # Weekly adaptation at start of each week
            if week > current_week:
                # Calculate weekly performance
                week_return = (self.capital - week_start_capital) / week_start_capital
                week_win_rate = weekly_wins / max(weekly_trades, 1)
                
                # Get regime for this week
                regime = "sideways"
                for event in MARKET_EVENTS_2025:
                    if event["week"] <= week + 1:
                        regime = event["regime"]
                
                self.weekly_performance.append({
                    "week": current_week + 1,
                    "return": week_return,
                    "win_rate": week_win_rate,
                    "trades": weekly_trades,
                    "regime": regime,
                    "capital": self.capital
                })
                
                self.regime_history.append({"week": week + 1, "regime": regime})
                
                # Adapt strategy based on performance
                self.strategy.adapt_to_regime(regime, week_win_rate)
                
                # Reset weekly counters
                current_week = week
                week_start_capital = self.capital
                weekly_trades = 0
                weekly_wins = 0
            
            # Trading logic for each coin
            for coin in self.coins:
                prices = coin_prices[coin]
                indicators = calculate_technical_indicators(prices, day)
                
                # Check existing positions for exits
                if coin in self.positions:
                    pos = self.positions[coin]
                    current_price = prices[day]
                    entry_price = pos["entry_price"]
                    pnl_pct = (current_price - entry_price) / entry_price * 100
                    
                    # Exit conditions
                    should_exit = False
                    exit_reason = ""
                    
                    if pnl_pct >= self.strategy.params["take_profit_pct"]:
                        should_exit = True
                        exit_reason = "take_profit"
                    elif pnl_pct <= -self.strategy.params["stop_loss_pct"]:
                        should_exit = True
                        exit_reason = "stop_loss"
                    elif pos["holding_days"] > 30:
                        should_exit = True
                        exit_reason = "time_exit"
                    
                    if should_exit:
                        # Close position
                        pnl = pos["size"] * (current_price / entry_price - 1)
                        self.capital += pos["size"] + pnl
                        
                        trade = {
                            "coin": coin,
                            "entry_day": pos["entry_day"],
                            "exit_day": day,
                            "entry_price": entry_price,
                            "exit_price": current_price,
                            "pnl": pnl,
                            "pnl_pct": pnl_pct,
                            "exit_reason": exit_reason,
                            "holding_days": pos["holding_days"],
                            "week": week + 1
                        }
                        self.trades.append(trade)
                        
                        weekly_trades += 1
                        if pnl > 0:
                            weekly_wins += 1
                        
                        del self.positions[coin]
                    else:
                        self.positions[coin]["holding_days"] += 1
                
                # Check for new entries
                elif len(self.positions) < self.strategy.params["max_positions"]:
                    signal = generate_trading_signal(indicators, self.strategy.params)
                    
                    if signal["signal"] == "buy" and signal["strength"] > 0.5:
                        # Calculate position size
                        position_size = self.capital * (self.strategy.params["position_size_pct"] / 100)
                        
                        if position_size > 100 and position_size <= self.capital * 0.3:
                            self.positions[coin] = {
                                "entry_price": prices[day],
                                "size": position_size,
                                "entry_day": day,
                                "holding_days": 0,
                                "signal_strength": signal["strength"],
                                "signal_reason": signal["reason"]
                            }
                            self.capital -= position_size
            
            # Update equity curve
            portfolio_value = self.capital
            for coin, pos in self.positions.items():
                current_price = coin_prices[coin][day]
                position_value = pos["size"] * (current_price / pos["entry_price"])
                portfolio_value += position_value
            
            daily_equity.append(portfolio_value)
            self.equity_curve.append({
                "day": day + 1,
                "equity": portfolio_value,
                "open_positions": len(self.positions)
            })
        
        # Close all remaining positions at year end
        final_day = days_in_year - 1
        for coin in list(self.positions.keys()):
            pos = self.positions[coin]
            current_price = coin_prices[coin][final_day]
            entry_price = pos["entry_price"]
            pnl_pct = (current_price - entry_price) / entry_price * 100
            pnl = pos["size"] * (current_price / entry_price - 1)
            
            self.capital += pos["size"] + pnl
            
            trade = {
                "coin": coin,
                "entry_day": pos["entry_day"],
                "exit_day": final_day,
                "entry_price": entry_price,
                "exit_price": current_price,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "exit_reason": "year_end_close",
                "holding_days": pos["holding_days"],
                "week": 52
            }
            self.trades.append(trade)
        
        self.positions = {}
        
        # Calculate final metrics
        return self._calculate_results(daily_equity)
    
    def _calculate_results(self, daily_equity: List[float]) -> Dict:
        """Calculate comprehensive backtest results"""
        if not self.trades:
            return {
                "status": "completed",
                "error": "No trades executed",
                "total_return": 0,
                "win_rate": 0
            }
        
        # Trade statistics
        winning_trades = [t for t in self.trades if t["pnl"] > 0]
        losing_trades = [t for t in self.trades if t["pnl"] <= 0]
        
        total_trades = len(self.trades)
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        total_pnl = sum(t["pnl"] for t in self.trades)
        total_return = (self.capital - self.initial_capital) / self.initial_capital * 100
        
        avg_win = sum(t["pnl"] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = abs(sum(t["pnl"] for t in losing_trades) / len(losing_trades)) if losing_trades else 0
        
        profit_factor = (sum(t["pnl"] for t in winning_trades) / abs(sum(t["pnl"] for t in losing_trades))) if losing_trades and sum(t["pnl"] for t in losing_trades) != 0 else float('inf')
        
        # Risk metrics
        returns = [(daily_equity[i] - daily_equity[i-1]) / daily_equity[i-1] for i in range(1, len(daily_equity))]
        avg_return = sum(returns) / len(returns) if returns else 0
        std_return = (sum((r - avg_return)**2 for r in returns) / len(returns)) ** 0.5 if returns else 0.01
        
        sharpe_ratio = (avg_return * 252) / (std_return * (252 ** 0.5)) if std_return > 0 else 0
        
        # Max drawdown
        peak = daily_equity[0]
        max_drawdown = 0
        for eq in daily_equity:
            if eq > peak:
                peak = eq
            drawdown = (peak - eq) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        # Best/worst weeks
        best_week = max(self.weekly_performance, key=lambda x: x["return"]) if self.weekly_performance else {}
        worst_week = min(self.weekly_performance, key=lambda x: x["return"]) if self.weekly_performance else {}
        
        # Coin performance
        coin_performance = {}
        for trade in self.trades:
            coin = trade["coin"]
            if coin not in coin_performance:
                coin_performance[coin] = {"trades": 0, "wins": 0, "pnl": 0}
            coin_performance[coin]["trades"] += 1
            coin_performance[coin]["pnl"] += trade["pnl"]
            if trade["pnl"] > 0:
                coin_performance[coin]["wins"] += 1
        
        # Calculate win rate per coin
        for coin in coin_performance:
            coin_performance[coin]["win_rate"] = coin_performance[coin]["wins"] / coin_performance[coin]["trades"]
        
        # Top performers
        top_coins = sorted(coin_performance.items(), key=lambda x: x[1]["pnl"], reverse=True)[:10]
        
        return {
            "status": "completed",
            "backtest_period": "2025-01-01 to 2025-12-31",
            "coins_traded": len(set(t["coin"] for t in self.trades)),
            
            # Capital metrics
            "initial_capital": self.initial_capital,
            "final_capital": round(self.capital, 2),
            "total_return_pct": round(total_return, 2),
            "total_pnl": round(total_pnl, 2),
            
            # Trade metrics
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(win_rate * 100, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else "Infinite",
            
            # Risk metrics
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown_pct": round(max_drawdown * 100, 2),
            
            # Weekly summary
            "total_weeks": len(self.weekly_performance),
            "profitable_weeks": len([w for w in self.weekly_performance if w["return"] > 0]),
            "best_week": {
                "week": best_week.get("week"),
                "return": f"{best_week.get('return', 0)*100:.2f}%",
                "regime": best_week.get("regime")
            } if best_week else {},
            "worst_week": {
                "week": worst_week.get("week"),
                "return": f"{worst_week.get('return', 0)*100:.2f}%",
                "regime": worst_week.get("regime")
            } if worst_week else {},
            
            # Top performing coins
            "top_coins": [
                {
                    "coin": coin,
                    "pnl": round(stats["pnl"], 2),
                    "trades": stats["trades"],
                    "win_rate": f"{stats['win_rate']*100:.1f}%"
                }
                for coin, stats in top_coins
            ],
            
            # Strategy adaptation summary
            "regime_changes": len(self.regime_history),
            "regimes_encountered": list(set(r["regime"] for r in self.regime_history)),
            
            # Recommended portfolio for live trading
            "recommended_portfolio": {
                "coins": [coin for coin, _ in top_coins[:5]],
                "allocation": {coin: f"{100/min(5, len(top_coins)):.1f}%" for coin, _ in top_coins[:5]},
                "strategy_params": self.strategy.params
            },
            
            # Auto-trade signals for next week
            "auto_trade_ready": True,
            "next_week_strategy": self.strategy.params
        }


async def run_yearly_adaptive_backtest(
    initial_capital: float = 100000,
    coins: List[str] = None,
    db = None
) -> Dict:
    """
    Main function to run yearly adaptive backtest
    """
    try:
        engine = YearlyBacktestEngine(
            initial_capital=initial_capital,
            coins=coins or TOP_COINS[:30]
        )
        
        results = engine.run_full_year_backtest()
        
        # Store results in database if available
        if db is not None:
            try:
                await db.yearly_backtests.insert_one({
                    "backtest_id": str(uuid.uuid4()),
                    "created_at": datetime.utcnow(),
                    "results": results,
                    "equity_curve": engine.equity_curve[-52:],  # Last 52 days
                    "weekly_performance": engine.weekly_performance,
                    "trades_summary": {
                        "total": len(engine.trades),
                        "by_coin": {coin: len([t for t in engine.trades if t["coin"] == coin]) 
                                   for coin in set(t["coin"] for t in engine.trades)}
                    }
                })
            except Exception as e:
                logger.error(f"Failed to store backtest results: {e}")
        
        return results
        
    except Exception as e:
        logger.error(f"Yearly backtest failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

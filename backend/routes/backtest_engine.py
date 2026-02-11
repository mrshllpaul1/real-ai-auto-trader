"""
Backtesting Engine API Routes
==============================
Comprehensive backtesting engine for testing trading strategies on historical data.
Uses REAL Kraken OHLC data when available, falls back to synthetic data only when necessary.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import random
import math
from httpx import AsyncClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backtest-engine", tags=["Backtesting Engine"])

# Global state
_db = None
_running_backtests = {}

# Kraken pair mapping for OHLC
KRAKEN_OHLC_PAIRS = {
    'BTC': 'XXBTZUSD',
    'ETH': 'XETHZUSD',
    'SOL': 'SOLUSD',
    'ADA': 'ADAUSD',
    'DOT': 'DOTUSD',
    'AVAX': 'AVAXUSD',
    'LINK': 'LINKUSD',
    'MATIC': 'MATICUSD',
    'UNI': 'UNIUSD',
    'LTC': 'XLTCZUSD',
    'DOGE': 'XDGUSD',
    'XRP': 'XXRPZUSD',
    'ATOM': 'ATOMUSD',
    'NEAR': 'NEARUSD',
    'APT': 'APTUSD',
    'SUI': 'SUIUSD',
    'ARB': 'ARBUSD',
    'OP': 'OPUSD',
    'SHIB': 'SHIBUSD',
}


async def _fetch_real_ohlc_data(symbol: str, days: int) -> List[float]:
    """
    Fetch REAL historical OHLC data from Kraken API.
    Returns list of closing prices for the requested days.
    
    Args:
        symbol: Asset symbol (e.g., 'BTC', 'ETH')
        days: Number of days of historical data needed
        
    Returns:
        List of closing prices, or empty list if unavailable
    """
    pair = KRAKEN_OHLC_PAIRS.get(symbol.upper())
    if not pair:
        # Try constructing the pair
        pair = f"{symbol.upper()}USD"
    
    # Calculate interval - Kraken supports: 1, 5, 15, 30, 60, 240, 1440 (daily), 10080 (weekly)
    interval = 1440  # Daily candles
    
    try:
        async with AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://api.kraken.com/0/public/OHLC",
                params={
                    "pair": pair,
                    "interval": interval
                },
                headers={"User-Agent": "CryptoTradingBot/1.0"}
            )
            data = response.json()
            
            if data.get("error") and len(data["error"]) > 0:
                logger.warning(f"Kraken OHLC error for {pair}: {data['error']}")
                return []
            
            result = data.get("result", {})
            # Remove 'last' key and get the OHLC data
            result.pop('last', None)
            
            if not result:
                return []
            
            # Get the first (and only) pair's data
            ohlc_data = list(result.values())[0] if result else []
            
            if not ohlc_data:
                return []
            
            # Extract closing prices (index 4 in Kraken OHLC: time, open, high, low, close, vwap, volume, count)
            prices = [float(candle[4]) for candle in ohlc_data]
            
            # Return most recent 'days' of data
            if len(prices) > days:
                prices = prices[-days:]
            
            logger.info(f"Fetched {len(prices)} REAL OHLC data points for {symbol}")
            return prices
            
    except Exception as e:
        logger.error(f"Failed to fetch OHLC data for {symbol}: {e}")
        return []


def set_db(db):
    global _db
    _db = db


async def get_database():
    global _db
    if _db is None:
        from server import db
        _db = db
    return _db


# =============================================================================
# MODELS
# =============================================================================

class BacktestConfig(BaseModel):
    name: str
    strategy_type: str  # momentum, mean_reversion, trend_following, ml_based, custom
    symbols: List[str] = ["BTC/USD"]
    start_date: str  # ISO format
    end_date: str  # ISO format
    initial_capital: float = 10000
    position_size_pct: float = 10  # % of capital per trade
    max_positions: int = 5
    stop_loss_pct: Optional[float] = 5
    take_profit_pct: Optional[float] = 15
    commission_pct: float = 0.1
    slippage_pct: float = 0.05
    # Strategy parameters
    strategy_params: Dict[str, Any] = {}


class StrategySignal(BaseModel):
    symbol: str
    signal: str  # buy, sell, hold
    strength: float  # 0-1
    reason: str


# =============================================================================
# STRATEGY IMPLEMENTATIONS
# =============================================================================

def generate_momentum_signals(prices: List[float], lookback: int = 14) -> List[str]:
    """Generate momentum-based signals"""
    signals = []
    for i in range(len(prices)):
        if i < lookback:
            signals.append("hold")
            continue
        
        returns = (prices[i] - prices[i-lookback]) / prices[i-lookback]
        if returns > 0.05:
            signals.append("buy")
        elif returns < -0.05:
            signals.append("sell")
        else:
            signals.append("hold")
    
    return signals


def generate_mean_reversion_signals(prices: List[float], lookback: int = 20, threshold: float = 2) -> List[str]:
    """Generate mean reversion signals based on standard deviation"""
    signals = []
    for i in range(len(prices)):
        if i < lookback:
            signals.append("hold")
            continue
        
        window = prices[i-lookback:i]
        mean = sum(window) / len(window)
        std = (sum((x - mean)**2 for x in window) / len(window)) ** 0.5
        
        if std == 0:
            signals.append("hold")
            continue
        
        z_score = (prices[i] - mean) / std
        
        if z_score < -threshold:
            signals.append("buy")  # Oversold
        elif z_score > threshold:
            signals.append("sell")  # Overbought
        else:
            signals.append("hold")
    
    return signals


def generate_trend_following_signals(prices: List[float], fast_ma: int = 10, slow_ma: int = 30) -> List[str]:
    """Generate trend following signals using moving average crossover"""
    signals = []
    for i in range(len(prices)):
        if i < slow_ma:
            signals.append("hold")
            continue
        
        fast = sum(prices[i-fast_ma:i]) / fast_ma
        slow = sum(prices[i-slow_ma:i]) / slow_ma
        
        prev_fast = sum(prices[i-fast_ma-1:i-1]) / fast_ma
        prev_slow = sum(prices[i-slow_ma-1:i-1]) / slow_ma
        
        # Crossover detection
        if fast > slow and prev_fast <= prev_slow:
            signals.append("buy")
        elif fast < slow and prev_fast >= prev_slow:
            signals.append("sell")
        else:
            signals.append("hold")
    
    return signals


async def generate_ml_based_signals(prices: List[float], symbol: str, db, strategy_params: Dict = None) -> List[str]:
    """
    Generate ML-based signals using the trained Enhanced MTF model combined
    with technical analysis for high win rate and Sharpe ratio.
    
    Strategy v8 - ULTRA HIGH WIN RATE Optimized:
    1. Uses Enhanced MTF model predictions when available
    2. Multi-factor trend-following with VERY STRICT confirmation
    3. RSI extremes + mean reversion for high-probability entries
    4. Volatility filtering to avoid choppy markets
    5. ADX trend strength filter for quality setups
    6. MACD divergence confirmation
    7. Dynamic trailing stops with profit locking
    8. Wait for trend confirmation before entry
    """
    signals = []
    n = len(prices)
    params = strategy_params or {}
    
    # Strategy parameters - ULTRA optimized for higher win rate
    lookback = params.get("lookback", 20)
    min_trend_strength = params.get("min_trend_strength", 0.02)  # Increased
    rsi_oversold = params.get("rsi_oversold", 20)  # More extreme
    rsi_overbought = params.get("rsi_overbought", 80)  # More extreme
    entry_threshold = params.get("entry_threshold", 8)  # Much higher threshold
    adx_threshold = params.get("adx_threshold", 25)  # ADX filter
    
    # Get ML prediction from Enhanced MTF service
    ml_signal = 0  # -1 sell, 0 hold, 1 buy
    ml_confidence = 0.5
    
    try:
        from services.enhanced_mtf_training_service import get_enhanced_mtf_service
        enhanced_mtf_service = get_enhanced_mtf_service(db)
        if enhanced_mtf_service:
            coin_symbol = symbol.replace("/USD", "").replace("USD", "")
            prediction = await enhanced_mtf_service.predict(coin_symbol)
            if prediction and "prediction" in prediction:
                ml_signal = prediction.get("prediction", 0)
                ml_confidence = prediction.get("confidence", 0.5)
                logger.info(f"ML Prediction for {coin_symbol}: signal={ml_signal}, confidence={ml_confidence:.2f}")
    except Exception as e:
        logger.debug(f"ML prediction not available: {e}")
    
    # State tracking for position management
    position_held = False
    entry_price = 0
    position_type = None
    holding_days = 0
    highest_since_entry = 0
    lowest_since_entry = float('inf')
    consecutive_trend_days = 0
    prev_trend = None
    
    # Historical tracking for divergence detection
    rsi_history = []
    price_highs = []
    price_lows = []
    
    for i in range(n):
        if i < lookback + 20:  # Need more data for reliable signals
            signals.append("hold")
            continue
        
        # Calculate technical indicators with multiple timeframes
        short_window = prices[i-5:i+1]
        medium_window = prices[i-lookback:i+1]
        long_window = prices[max(0, i-50):i+1]
        extra_long_window = prices[max(0, i-100):i+1]
        
        # Moving averages - multiple timeframes
        sma_5 = sum(short_window) / len(short_window)
        sma_10 = sum(prices[i-10:i+1]) / 11 if i >= 10 else sma_5
        sma_20 = sum(medium_window) / len(medium_window)
        sma_50 = sum(long_window) / len(long_window)
        sma_100 = sum(extra_long_window) / len(extra_long_window) if len(extra_long_window) >= 50 else sma_50
        
        # EMA calculation for MACD
        ema_12 = _calc_ema(prices[max(0, i-26):i+1], 12)
        ema_26 = _calc_ema(prices[max(0, i-26):i+1], 26)
        macd_line = ema_12 - ema_26
        
        # Previous MACD for crossover detection
        prev_ema_12 = _calc_ema(prices[max(0, i-27):i], 12)
        prev_ema_26 = _calc_ema(prices[max(0, i-27):i], 26)
        prev_macd = prev_ema_12 - prev_ema_26
        
        # MACD histogram
        signal_line = _calc_ema([macd_line], 9) if i > 35 else macd_line
        macd_hist = macd_line - signal_line
        
        # Momentum calculations
        momentum_3 = (prices[i] - prices[i-3]) / prices[i-3] if i >= 3 else 0
        momentum_5 = (prices[i] - prices[i-5]) / prices[i-5]
        momentum_10 = (prices[i] - prices[i-10]) / prices[i-10] if i >= 10 else 0
        momentum_20 = (prices[i] - prices[i-20]) / prices[i-20] if i >= 20 else 0
        
        # RSI calculation with proper smoothing
        gains, losses = [], []
        for j in range(1, min(15, i+1)):
            diff = prices[i-j+1] - prices[i-j]
            gains.append(max(0, diff))
            losses.append(max(0, -diff))
        avg_gain = sum(gains) / max(len(gains), 1)
        avg_loss = sum(losses) / max(len(losses), 1) + 1e-10
        rsi = 100 - (100 / (1 + avg_gain / avg_loss))
        rsi_history.append(rsi)
        if len(rsi_history) > 20:
            rsi_history.pop(0)
        
        # Stochastic RSI for oversold/overbought
        if len(rsi_history) >= 14:
            rsi_min = min(rsi_history[-14:])
            rsi_max = max(rsi_history[-14:])
            stoch_rsi = (rsi - rsi_min) / (rsi_max - rsi_min + 1e-10) * 100
        else:
            stoch_rsi = 50
        
        # Volatility with ATR-style calculation
        returns = [(prices[j] - prices[j-1]) / prices[j-1] for j in range(max(1, i-20), i+1)]
        volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5 if returns else 0.02
        avg_volatility = sum(abs(r) for r in returns) / len(returns) if returns else 0.015
        
        # ADX calculation (simplified)
        tr_list = []
        dm_plus_list = []
        dm_minus_list = []
        for j in range(max(1, i-14), i+1):
            high_low = abs(max(prices[j-1:j+1]) - min(prices[j-1:j+1]))
            tr_list.append(high_low)
            
            up_move = prices[j] - prices[j-1] if j > 0 else 0
            down_move = prices[j-1] - prices[j] if j > 0 else 0
            
            dm_plus_list.append(max(0, up_move) if up_move > down_move else 0)
            dm_minus_list.append(max(0, down_move) if down_move > up_move else 0)
        
        atr = sum(tr_list) / len(tr_list) if tr_list else 0.01
        di_plus = sum(dm_plus_list) / (atr * len(dm_plus_list) + 1e-10) * 100
        di_minus = sum(dm_minus_list) / (atr * len(dm_minus_list) + 1e-10) * 100
        dx = abs(di_plus - di_minus) / (di_plus + di_minus + 1e-10) * 100
        adx = dx  # Simplified ADX
        
        # Trend detection - more stringent
        ma_aligned_up = sma_5 > sma_10 > sma_20 > sma_50
        ma_aligned_down = sma_5 < sma_10 < sma_20 < sma_50
        
        strong_uptrend = ma_aligned_up and momentum_5 > min_trend_strength and adx > adx_threshold
        strong_downtrend = ma_aligned_down and momentum_5 < -min_trend_strength and adx > adx_threshold
        uptrend = sma_5 > sma_20 and sma_20 > sma_50 and prices[i] > sma_20
        downtrend = sma_5 < sma_20 and sma_20 < sma_50 and prices[i] < sma_20
        
        # Track trend consistency
        current_trend = "up" if uptrend else ("down" if downtrend else "neutral")
        if current_trend == prev_trend:
            consecutive_trend_days += 1
        else:
            consecutive_trend_days = 1
        prev_trend = current_trend
        
        # Support/Resistance levels
        recent_10_high = max(prices[max(0, i-10):i])
        recent_10_low = min(prices[max(0, i-10):i])
        recent_20_high = max(prices[max(0, i-20):i])
        recent_20_low = min(prices[max(0, i-20):i])
        
        # Breakout detection with confirmation
        confirmed_breakout_up = prices[i] > recent_20_high * 1.005 and prices[i-1] > recent_10_high
        confirmed_breakout_down = prices[i] < recent_20_low * 0.995 and prices[i-1] < recent_10_low
        
        # RSI divergence detection
        bullish_divergence = False
        bearish_divergence = False
        if len(rsi_history) >= 10 and len(prices) > i - 10:
            # Bullish divergence: price lower low, RSI higher low
            if prices[i] < min(prices[i-5:i]) and rsi > min(rsi_history[-5:]):
                bullish_divergence = True
            # Bearish divergence: price higher high, RSI lower high
            if prices[i] > max(prices[i-5:i]) and rsi < max(rsi_history[-5:]):
                bearish_divergence = True
        
        # Mean reversion signals
        price_distance_from_sma20 = (prices[i] - sma_20) / sma_20 * 100
        mean_reversion_buy = price_distance_from_sma20 < -3 and rsi < 35
        mean_reversion_sell = price_distance_from_sma20 > 3 and rsi > 65
        
        signal = "hold"
        
        # Position management for existing positions - TIGHT RISK MANAGEMENT
        if position_held:
            holding_days += 1
            current_price = prices[i]
            
            if position_type == "long":
                highest_since_entry = max(highest_since_entry, current_price)
                pnl_pct = (current_price - entry_price) / entry_price * 100
                drawdown_from_high = (highest_since_entry - current_price) / highest_since_entry * 100
                
                exit_signal = False
                exit_reason = ""
                
                # Dynamic take profit based on volatility
                take_profit_target = max(8, min(20, 100 * avg_volatility * 5))
                
                # Exit conditions for long - STRICT
                if pnl_pct >= take_profit_target:  # Dynamic take profit
                    exit_signal = True
                    exit_reason = "take_profit"
                elif pnl_pct <= -3:  # Tight stop loss
                    exit_signal = True
                    exit_reason = "stop_loss"
                elif pnl_pct > 5 and drawdown_from_high > 2:  # Lock profits early
                    exit_signal = True
                    exit_reason = "trailing_stop"
                elif pnl_pct > 2 and drawdown_from_high > 1.5:  # Very tight trailing
                    exit_signal = True
                    exit_reason = "tight_trailing"
                elif strong_downtrend and pnl_pct > 1:  # Exit on trend reversal
                    exit_signal = True
                    exit_reason = "trend_reversal"
                elif rsi > 85:  # Extreme overbought
                    exit_signal = True
                    exit_reason = "overbought"
                elif bearish_divergence and pnl_pct > 0:  # Divergence exit
                    exit_signal = True
                    exit_reason = "divergence"
                elif holding_days > 20 and pnl_pct < 3:  # Time-based exit
                    exit_signal = True
                    exit_reason = "time_decay"
                elif macd_hist < 0 and prev_macd > 0 and pnl_pct > 0:  # MACD cross
                    exit_signal = True
                    exit_reason = "macd_cross"
                
                if exit_signal:
                    signal = "sell"
                    position_held = False
                    position_type = None
                    holding_days = 0
                    highest_since_entry = 0
            
            elif position_type == "short":
                lowest_since_entry = min(lowest_since_entry, current_price)
                pnl_pct = (entry_price - current_price) / entry_price * 100
                drawup_from_low = (current_price - lowest_since_entry) / lowest_since_entry * 100 if lowest_since_entry > 0 else 0
                
                exit_signal = False
                take_profit_target = max(8, min(20, 100 * avg_volatility * 5))
                
                if pnl_pct >= take_profit_target:
                    exit_signal = True
                elif pnl_pct <= -3:
                    exit_signal = True
                elif pnl_pct > 5 and drawup_from_low > 2:
                    exit_signal = True
                elif pnl_pct > 2 and drawup_from_low > 1.5:
                    exit_signal = True
                elif strong_uptrend and pnl_pct > 1:
                    exit_signal = True
                elif rsi < 15:
                    exit_signal = True
                elif bullish_divergence and pnl_pct > 0:
                    exit_signal = True
                elif holding_days > 20 and pnl_pct < 3:
                    exit_signal = True
                elif macd_hist > 0 and prev_macd < 0 and pnl_pct > 0:
                    exit_signal = True
                
                if exit_signal:
                    signal = "buy"
                    position_held = False
                    position_type = None
                    holding_days = 0
                    lowest_since_entry = float('inf')
        
        # Entry logic for new positions - ULTRA STRICT CONFIRMATION
        if not position_held:
            buy_score = 0
            sell_score = 0
            
            # ML model signal (high weight if confident)
            if ml_signal == 1 and ml_confidence > 0.75:
                buy_score += 5
            elif ml_signal == -1 and ml_confidence > 0.75:
                sell_score += 5
            
            # Strong trend with ADX confirmation (high weight)
            if strong_uptrend and adx > 30:
                buy_score += 5
            elif strong_downtrend and adx > 30:
                sell_score += 5
            elif strong_uptrend:
                buy_score += 3
            elif strong_downtrend:
                sell_score += 3
            
            # RSI extremes with stochastic confirmation
            if rsi < rsi_oversold and stoch_rsi < 20:
                buy_score += 5
            elif rsi > rsi_overbought and stoch_rsi > 80:
                sell_score += 5
            elif rsi < 30:
                buy_score += 2
            elif rsi > 70:
                sell_score += 2
            
            # MACD crossover confirmation
            if macd_line > 0 and prev_macd <= 0:  # Bullish crossover
                buy_score += 3
            elif macd_line < 0 and prev_macd >= 0:  # Bearish crossover
                sell_score += 3
            
            # RSI divergence signals (high probability)
            if bullish_divergence and rsi < 40:
                buy_score += 4
            elif bearish_divergence and rsi > 60:
                sell_score += 4
            
            # Mean reversion at extremes
            if mean_reversion_buy and uptrend:
                buy_score += 3
            elif mean_reversion_sell and downtrend:
                sell_score += 3
            
            # Confirmed breakouts
            if confirmed_breakout_up and uptrend and adx > 20:
                buy_score += 3
            elif confirmed_breakout_down and downtrend and adx > 20:
                sell_score += 3
            
            # Momentum confirmation - multiple timeframes
            if momentum_3 > 0.01 and momentum_5 > 0.015 and momentum_10 > 0.02:
                buy_score += 3
            elif momentum_3 < -0.01 and momentum_5 < -0.015 and momentum_10 < -0.02:
                sell_score += 3
            
            # Trend consistency bonus
            if consecutive_trend_days >= 3 and uptrend:
                buy_score += 2
            elif consecutive_trend_days >= 3 and downtrend:
                sell_score += 2
            
            # Volatility filter - STRICT
            if volatility > 0.035:  # High volatility penalty
                buy_score = int(buy_score * 0.4)
                sell_score = int(sell_score * 0.4)
            elif volatility < 0.01:  # Low volatility penalty
                buy_score = int(buy_score * 0.7)
                sell_score = int(sell_score * 0.7)
            
            # Price position filter - don't buy at highs, don't sell at lows
            if prices[i] > recent_20_high * 0.98:  # Near recent high
                buy_score = int(buy_score * 0.6)
            if prices[i] < recent_20_low * 1.02:  # Near recent low
                sell_score = int(sell_score * 0.6)
            
            # Entry decision - ULTRA STRICT threshold
            if buy_score >= entry_threshold and buy_score > sell_score + 3:
                signal = "buy"
                position_held = True
                position_type = "long"
                entry_price = prices[i]
                holding_days = 0
                highest_since_entry = prices[i]
            elif sell_score >= entry_threshold and sell_score > buy_score + 3:
                signal = "sell"
                position_held = True
                position_type = "short"
                entry_price = prices[i]
                holding_days = 0
                lowest_since_entry = prices[i]
        
        signals.append(signal)
    
    return signals


def _calc_ema(prices: List[float], period: int) -> float:
    """Calculate Exponential Moving Average"""
    if not prices:
        return 0
    if len(prices) < period:
        return sum(prices) / len(prices)
    
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    
    return ema


# =============================================================================
# BACKTESTING ENGINE
# =============================================================================

async def run_backtest(backtest_id: str, config: BacktestConfig, db):
    """Execute backtest simulation"""
    global _running_backtests
    
    try:
        _running_backtests[backtest_id] = {"status": "running", "progress": 0}
        
        # Parse dates
        start = datetime.fromisoformat(config.start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(config.end_date.replace('Z', '+00:00'))
        days = (end - start).days
        
        # Generate simulated price data
        base_prices = {"BTC/USD": 45000, "ETH/USD": 2500, "SOL/USD": 100}
        
        results = {
            "backtest_id": backtest_id,
            "config": config.dict(),
            "trades": [],
            "equity_curve": [],
            "daily_returns": [],
            "positions": [],
            "data_sources": {}  # Track which data sources were used
        }
        
        capital = config.initial_capital
        positions = {}
        
        for symbol in config.symbols:
            base_price = base_prices.get(symbol, 1000)
            
            # Try to fetch REAL historical data from Kraken
            prices = await _fetch_real_ohlc_data(symbol, days)
            
            # Use real data if we have at least 100 data points (enough for most strategies)
            # Kraken provides max ~720 daily candles
            min_required = min(100, days)  # Need at least 100 or the requested days if smaller
            
            # If we have sufficient real data, use it; otherwise fall back to synthetic
            if prices and len(prices) >= min_required:
                # Real data was successfully fetched
                results["data_sources"][symbol] = f"kraken_ohlc ({len(prices)} candles)"
                logger.info(f"Using REAL Kraken data for {symbol}")
                days = len(prices)  # Adjust days to match available data
            else:
                # No real data available, generate synthetic (with warning)
                logger.warning(f"Using synthetic data for {symbol} - real OHLC not available or insufficient ({len(prices) if prices else 0} records)")
                results["data_sources"][symbol] = "synthetic (fallback)"
                prices = []
                current_price = base_price
                
                # Generate trending price data with cycles
                trend_duration = random.randint(20, 60)
                trend_direction = random.choice([1, -1])
                trend_strength = random.uniform(0.002, 0.005)
                trend_counter = 0
                
                for day in range(days):
                    # Change trend periodically
                    trend_counter += 1
                    if trend_counter >= trend_duration:
                        trend_counter = 0
                        trend_duration = random.randint(20, 60)
                        trend_direction = -trend_direction if random.random() < 0.6 else trend_direction
                        trend_strength = random.uniform(0.002, 0.005)
                    
                    # Base drift follows trend
                    drift = trend_direction * trend_strength
                    
                    # Add volatility with clustering
                    base_vol = 0.015
                    volatility_mult = 1 + abs(random.gauss(0, 0.5))
                    vol = base_vol * volatility_mult
                    
                    # Daily return combines trend + noise
                    daily_return = drift + random.gauss(0, vol)
                    current_price *= (1 + daily_return)
                    prices.append(current_price)
            
            # Generate signals based on strategy
            if config.strategy_type == "momentum":
                lookback = config.strategy_params.get("lookback", 14)
                signals = generate_momentum_signals(prices, lookback)
            elif config.strategy_type == "mean_reversion":
                lookback = config.strategy_params.get("lookback", 20)
                threshold = config.strategy_params.get("threshold", 2)
                signals = generate_mean_reversion_signals(prices, lookback, threshold)
            elif config.strategy_type == "trend_following":
                fast = config.strategy_params.get("fast_ma", 10)
                slow = config.strategy_params.get("slow_ma", 30)
                signals = generate_trend_following_signals(prices, fast, slow)
            elif config.strategy_type == "ml_based":
                # Use ML-based signals with improved strategy
                signals = await generate_ml_based_signals(prices, symbol, db, config.strategy_params)
            else:
                # Random signals for other strategies
                signals = [random.choice(["buy", "sell", "hold"]) for _ in range(days)]
            
            # Execute trades
            position = None
            for i, (price, signal) in enumerate(zip(prices, signals)):
                date = (start + timedelta(days=i)).isoformat()
                
                # Check stop loss / take profit
                if position:
                    pnl_pct = (price - position["entry_price"]) / position["entry_price"] * 100
                    
                    if config.stop_loss_pct and pnl_pct < -config.stop_loss_pct:
                        # Stop loss triggered
                        exit_value = position["quantity"] * price * (1 - config.commission_pct/100 - config.slippage_pct/100)
                        pnl = exit_value - position["cost"]
                        capital += exit_value
                        
                        results["trades"].append({
                            "symbol": symbol,
                            "type": "sell (stop loss)",
                            "entry_date": position["entry_date"],
                            "exit_date": date,
                            "entry_price": position["entry_price"],
                            "exit_price": price,
                            "quantity": position["quantity"],
                            "pnl": round(pnl, 2),
                            "pnl_pct": round(pnl_pct, 2)
                        })
                        position = None
                    
                    elif config.take_profit_pct and pnl_pct > config.take_profit_pct:
                        # Take profit triggered
                        exit_value = position["quantity"] * price * (1 - config.commission_pct/100 - config.slippage_pct/100)
                        pnl = exit_value - position["cost"]
                        capital += exit_value
                        
                        results["trades"].append({
                            "symbol": symbol,
                            "type": "sell (take profit)",
                            "entry_date": position["entry_date"],
                            "exit_date": date,
                            "entry_price": position["entry_price"],
                            "exit_price": price,
                            "quantity": position["quantity"],
                            "pnl": round(pnl, 2),
                            "pnl_pct": round(pnl_pct, 2)
                        })
                        position = None
                
                # Execute signal
                if signal == "buy" and not position and capital > 100:
                    # Open position
                    trade_value = capital * (config.position_size_pct / 100)
                    cost = trade_value * (1 + config.commission_pct/100 + config.slippage_pct/100)
                    quantity = trade_value / price
                    
                    position = {
                        "symbol": symbol,
                        "entry_date": date,
                        "entry_price": price,
                        "quantity": quantity,
                        "cost": cost
                    }
                    capital -= cost
                    
                elif signal == "sell" and position:
                    # Close position
                    exit_value = position["quantity"] * price * (1 - config.commission_pct/100 - config.slippage_pct/100)
                    pnl = exit_value - position["cost"]
                    pnl_pct = (price - position["entry_price"]) / position["entry_price"] * 100
                    capital += exit_value
                    
                    results["trades"].append({
                        "symbol": symbol,
                        "type": "sell",
                        "entry_date": position["entry_date"],
                        "exit_date": date,
                        "entry_price": position["entry_price"],
                        "exit_price": price,
                        "quantity": position["quantity"],
                        "pnl": round(pnl, 2),
                        "pnl_pct": round(pnl_pct, 2)
                    })
                    position = None
                
                # Record equity
                position_value = position["quantity"] * price if position else 0
                total_equity = capital + position_value
                
                results["equity_curve"].append({
                    "date": date,
                    "equity": round(total_equity, 2),
                    "price": round(price, 2)
                })
                
                # Update progress
                progress = int((i + 1) / days * 100)
                _running_backtests[backtest_id]["progress"] = progress
        
        # Close any remaining positions at end
        if position:
            final_price = prices[-1]
            exit_value = position["quantity"] * final_price * (1 - config.commission_pct/100)
            pnl = exit_value - position["cost"]
            capital += exit_value
            
            results["trades"].append({
                "symbol": symbol,
                "type": "sell (end)",
                "entry_date": position["entry_date"],
                "exit_date": end.isoformat(),
                "entry_price": position["entry_price"],
                "exit_price": final_price,
                "quantity": position["quantity"],
                "pnl": round(pnl, 2)
            })
        
        # Calculate metrics
        total_trades = len(results["trades"])
        winning_trades = sum(1 for t in results["trades"] if t["pnl"] > 0)
        total_pnl = sum(t["pnl"] for t in results["trades"])
        
        # Calculate drawdown
        peak = config.initial_capital
        max_drawdown = 0
        for point in results["equity_curve"]:
            if point["equity"] > peak:
                peak = point["equity"]
            drawdown = (peak - point["equity"]) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        # Calculate Sharpe ratio (simplified)
        if len(results["equity_curve"]) > 1:
            returns = []
            for i in range(1, len(results["equity_curve"])):
                r = (results["equity_curve"][i]["equity"] - results["equity_curve"][i-1]["equity"]) / results["equity_curve"][i-1]["equity"]
                returns.append(r)
            
            avg_return = sum(returns) / len(returns) if returns else 0
            std_return = (sum((r - avg_return)**2 for r in returns) / len(returns)) ** 0.5 if returns else 0
            sharpe = (avg_return * 252) / (std_return * math.sqrt(252)) if std_return > 0 else 0
        else:
            sharpe = 0
        
        final_capital = capital
        total_return = (final_capital - config.initial_capital) / config.initial_capital * 100
        
        results["metrics"] = {
            "initial_capital": config.initial_capital,
            "final_capital": round(final_capital, 2),
            "total_return_pct": round(total_return, 2),
            "total_pnl": round(total_pnl, 2),
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": total_trades - winning_trades,
            "win_rate": round(winning_trades / total_trades * 100, 1) if total_trades > 0 else 0,
            "max_drawdown_pct": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe, 2),
            "profit_factor": round(sum(t["pnl"] for t in results["trades"] if t["pnl"] > 0) / 
                                   abs(sum(t["pnl"] for t in results["trades"] if t["pnl"] < 0) or 1), 2)
        }
        
        results["status"] = "completed"
        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Save to database
        await db.backtest_results.replace_one(
            {"backtest_id": backtest_id},
            results,
            upsert=True
        )
        
        _running_backtests[backtest_id] = {"status": "completed", "progress": 100}
        
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        _running_backtests[backtest_id] = {"status": "failed", "error": str(e)}


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/run")
async def start_backtest(
    config: BacktestConfig,
    background_tasks: BackgroundTasks,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Start a new backtest"""
    backtest_id = str(uuid.uuid4())
    
    # Save initial record
    record = {
        "backtest_id": backtest_id,
        "user_id": user_id,
        "config": config.dict(),
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.backtest_results.insert_one(record)
    
    # Start backtest in background
    background_tasks.add_task(run_backtest, backtest_id, config, db)
    
    return {
        "status": "started",
        "backtest_id": backtest_id,
        "message": "Backtest started in background"
    }


@router.get("/status/{backtest_id}")
async def get_backtest_status(backtest_id: str, db = Depends(get_database)):
    """Get status of a running backtest"""
    if backtest_id in _running_backtests:
        return _running_backtests[backtest_id]
    
    result = await db.backtest_results.find_one(
        {"backtest_id": backtest_id},
        {"_id": 0, "status": 1, "completed_at": 1}
    )
    
    if result:
        return {"status": result.get("status", "unknown"), "progress": 100 if result.get("status") == "completed" else 0}
    
    return {"status": "not_found"}


@router.get("/results/{backtest_id}")
async def get_backtest_results(backtest_id: str, db = Depends(get_database)):
    """Get results of a completed backtest"""
    result = await db.backtest_results.find_one(
        {"backtest_id": backtest_id},
        {"_id": 0}
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    return result


@router.get("/history")
async def get_backtest_history(
    user_id: str = "default_user",
    limit: int = 20,
    db = Depends(get_database)
):
    """Get user's backtest history"""
    results = await db.backtest_results.find(
        {"user_id": user_id},
        {"_id": 0, "backtest_id": 1, "config.name": 1, "config.strategy_type": 1, 
         "status": 1, "metrics": 1, "created_at": 1, "completed_at": 1}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"history": results}


@router.delete("/{backtest_id}")
async def delete_backtest(
    backtest_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Delete a backtest result"""
    result = await db.backtest_results.delete_one({
        "backtest_id": backtest_id,
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    return {"status": "deleted", "backtest_id": backtest_id}


@router.get("/strategies")
async def get_available_strategies():
    """Get available backtesting strategies"""
    return {
        "strategies": [
            {
                "id": "momentum",
                "name": "Momentum Strategy",
                "description": "Buy assets with positive momentum, sell those with negative momentum",
                "params": {
                    "lookback": {"type": "int", "default": 14, "min": 5, "max": 50, "description": "Lookback period in days"}
                }
            },
            {
                "id": "mean_reversion",
                "name": "Mean Reversion Strategy",
                "description": "Buy oversold assets, sell overbought based on standard deviation",
                "params": {
                    "lookback": {"type": "int", "default": 20, "min": 10, "max": 50, "description": "Lookback period"},
                    "threshold": {"type": "float", "default": 2.0, "min": 1.0, "max": 3.0, "description": "Z-score threshold"}
                }
            },
            {
                "id": "trend_following",
                "name": "Trend Following Strategy",
                "description": "Follow trends using moving average crossovers",
                "params": {
                    "fast_ma": {"type": "int", "default": 10, "min": 5, "max": 20, "description": "Fast MA period"},
                    "slow_ma": {"type": "int", "default": 30, "min": 20, "max": 100, "description": "Slow MA period"}
                }
            },
            {
                "id": "ml_based",
                "name": "ML-Based Strategy",
                "description": "Use machine learning predictions for trading signals",
                "params": {
                    "model": {"type": "string", "default": "random_forest", "options": ["random_forest", "gradient_boost", "lstm"]}
                }
            }
        ]
    }


@router.get("/templates")
async def get_backtest_templates():
    """Get pre-configured backtest templates"""
    return {
        "templates": [
            {
                "name": "BTC Momentum 30D",
                "description": "30-day momentum strategy on Bitcoin",
                "config": {
                    "name": "BTC Momentum",
                    "strategy_type": "momentum",
                    "symbols": ["BTC/USD"],
                    "initial_capital": 10000,
                    "position_size_pct": 20,
                    "stop_loss_pct": 5,
                    "take_profit_pct": 15,
                    "strategy_params": {"lookback": 14}
                }
            },
            {
                "name": "Multi-Coin Mean Reversion",
                "description": "Mean reversion across major cryptocurrencies",
                "config": {
                    "name": "Multi Mean Reversion",
                    "strategy_type": "mean_reversion",
                    "symbols": ["BTC/USD", "ETH/USD", "SOL/USD"],
                    "initial_capital": 10000,
                    "position_size_pct": 10,
                    "max_positions": 3,
                    "stop_loss_pct": 8,
                    "strategy_params": {"lookback": 20, "threshold": 2}
                }
            },
            {
                "name": "ETH Trend Following",
                "description": "Trend following on Ethereum using MA crossover",
                "config": {
                    "name": "ETH Trend",
                    "strategy_type": "trend_following",
                    "symbols": ["ETH/USD"],
                    "initial_capital": 10000,
                    "position_size_pct": 25,
                    "stop_loss_pct": 10,
                    "take_profit_pct": 25,
                    "strategy_params": {"fast_ma": 10, "slow_ma": 30}
                }
            }
        ]
    }


@router.post("/compare")
async def compare_backtests(
    backtest_ids: List[str],
    db = Depends(get_database)
):
    """Compare multiple backtest results"""
    results = []
    for bid in backtest_ids:
        result = await db.backtest_results.find_one(
            {"backtest_id": bid},
            {"_id": 0, "backtest_id": 1, "config.name": 1, "config.strategy_type": 1, "metrics": 1}
        )
        if result:
            results.append(result)
    
    if not results:
        raise HTTPException(status_code=404, detail="No backtests found")
    
    # Sort by total return
    results.sort(key=lambda x: x.get("metrics", {}).get("total_return_pct", 0), reverse=True)
    
    return {
        "comparison": results,
        "best_performer": results[0] if results else None,
        "metrics_summary": {
            "avg_return": round(sum(r.get("metrics", {}).get("total_return_pct", 0) for r in results) / len(results), 2),
            "avg_win_rate": round(sum(r.get("metrics", {}).get("win_rate", 0) for r in results) / len(results), 1),
            "avg_sharpe": round(sum(r.get("metrics", {}).get("sharpe_ratio", 0) for r in results) / len(results), 2)
        }
    }

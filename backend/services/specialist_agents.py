"""
Specialist Trading Agents for Different Market Regimes
========================================================
Ensemble of agents specialized for:
- Bull markets (momentum-focused)
- Bear markets (defensive/short-focused)
- Sideways/Range-bound markets (mean-reversion)

Includes market regime detection and dynamic agent switching.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from collections import deque
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classification"""
    STRONG_BULL = "strong_bull"
    BULL = "bull"
    SIDEWAYS = "sideways"
    BEAR = "bear"
    STRONG_BEAR = "strong_bear"
    HIGH_VOLATILITY = "high_volatility"
    UNKNOWN = "unknown"


class MarketRegimeDetector:
    """
    Detects current market regime using multiple indicators:
    - Trend analysis (SMA crossovers, ADX)
    - Volatility analysis (ATR, Bollinger Band width)
    - Momentum analysis (RSI, MACD)
    - Market breadth (advance/decline ratio)
    """
    
    def __init__(self):
        self.regime_history = deque(maxlen=100)
        self.current_regime = MarketRegime.UNKNOWN
        self.regime_confidence = 0.0
        self.regime_duration = 0  # Number of periods in current regime
        
    def detect_regime(
        self, 
        prices: List[float],
        volumes: Optional[List[float]] = None,
        market_breadth: Optional[Dict] = None
    ) -> Tuple[MarketRegime, float]:
        """
        Detect current market regime from price data.
        
        Returns:
            Tuple of (regime, confidence_score)
        """
        if len(prices) < 50:
            return MarketRegime.UNKNOWN, 0.0
        
        prices = np.array(prices)
        
        # Calculate indicators
        trend_score = self._calculate_trend_score(prices)
        volatility_score = self._calculate_volatility_score(prices)
        momentum_score = self._calculate_momentum_score(prices)
        
        # Combine scores to determine regime
        regime, confidence = self._classify_regime(
            trend_score, volatility_score, momentum_score
        )
        
        # Update tracking
        if regime == self.current_regime:
            self.regime_duration += 1
        else:
            self.current_regime = regime
            self.regime_duration = 1
        
        self.regime_confidence = confidence
        self.regime_history.append({
            "regime": regime.value,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trend_score": trend_score,
            "volatility_score": volatility_score,
            "momentum_score": momentum_score
        })
        
        return regime, confidence
    
    def _calculate_trend_score(self, prices: np.ndarray) -> float:
        """Calculate trend strength and direction (-100 to 100)"""
        # SMA crossovers
        sma_20 = np.mean(prices[-20:])
        sma_50 = np.mean(prices[-50:])
        sma_200 = np.mean(prices[-200:]) if len(prices) >= 200 else sma_50
        
        score = 0
        
        # Price vs SMAs
        if prices[-1] > sma_20:
            score += 20
        else:
            score -= 20
        
        if prices[-1] > sma_50:
            score += 20
        else:
            score -= 20
        
        if prices[-1] > sma_200:
            score += 15
        else:
            score -= 15
        
        # SMA alignment (golden/death cross)
        if sma_20 > sma_50 > sma_200:
            score += 25  # Perfect bull alignment
        elif sma_20 < sma_50 < sma_200:
            score -= 25  # Perfect bear alignment
        elif sma_20 > sma_50:
            score += 10
        else:
            score -= 10
        
        # Linear regression slope
        x = np.arange(20)
        slope = np.polyfit(x, prices[-20:], 1)[0]
        slope_pct = (slope / np.mean(prices[-20:])) * 100
        score += np.clip(slope_pct * 5, -20, 20)
        
        return np.clip(score, -100, 100)
    
    def _calculate_volatility_score(self, prices: np.ndarray) -> float:
        """Calculate volatility level (0 to 100, higher = more volatile)"""
        # Calculate returns
        returns = np.diff(prices) / prices[:-1]
        
        # Historical volatility (20-period)
        volatility_20 = np.std(returns[-20:]) * np.sqrt(252) * 100
        
        # ATR approximation
        high_low_range = np.max(prices[-20:]) - np.min(prices[-20:])
        atr_pct = (high_low_range / np.mean(prices[-20:])) * 100
        
        # Bollinger Band width
        sma = np.mean(prices[-20:])
        std = np.std(prices[-20:])
        bb_width = (2 * std / sma) * 100
        
        # Combine metrics
        volatility_score = (
            volatility_20 * 0.4 +
            atr_pct * 0.3 +
            bb_width * 0.3
        )
        
        # Normalize to 0-100
        return np.clip(volatility_score * 5, 0, 100)
    
    def _calculate_momentum_score(self, prices: np.ndarray) -> float:
        """Calculate momentum score (-100 to 100)"""
        score = 0
        
        # RSI
        gains = []
        losses = []
        for i in range(1, min(15, len(prices))):
            diff = prices[-i] - prices[-i-1]
            if diff > 0:
                gains.append(diff)
            else:
                losses.append(abs(diff))
        
        avg_gain = np.mean(gains) if gains else 0.0001
        avg_loss = np.mean(losses) if losses else 0.0001
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        if rsi > 70:
            score -= 20  # Overbought
        elif rsi < 30:
            score += 20  # Oversold
        elif rsi > 50:
            score += 10
        else:
            score -= 10
        
        # Rate of change
        roc_7 = ((prices[-1] - prices[-7]) / prices[-7]) * 100 if len(prices) >= 7 else 0
        roc_14 = ((prices[-1] - prices[-14]) / prices[-14]) * 100 if len(prices) >= 14 else 0
        
        score += np.clip(roc_7 * 2, -30, 30)
        score += np.clip(roc_14, -20, 20)
        
        # MACD-like calculation
        ema_12 = self._ema(prices, 12)
        ema_26 = self._ema(prices, 26)
        macd = ema_12 - ema_26
        macd_pct = (macd / prices[-1]) * 100
        
        score += np.clip(macd_pct * 10, -20, 20)
        
        return np.clip(score, -100, 100)
    
    def _ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate EMA using vectorized pandas computation"""
        if len(prices) < period:
            return np.mean(prices)
        
        # Use pandas ewm for efficient vectorized EMA calculation
        return pd.Series(prices[-period:]).ewm(span=period, adjust=False).mean().iloc[-1]
    
    def _classify_regime(
        self, 
        trend: float, 
        volatility: float, 
        momentum: float
    ) -> Tuple[MarketRegime, float]:
        """Classify market regime from indicator scores"""
        
        # High volatility overrides other regimes
        if volatility > 70:
            return MarketRegime.HIGH_VOLATILITY, volatility
        
        # Combined score
        combined = (trend * 0.4 + momentum * 0.4 + (50 - volatility) * 0.2)
        
        if combined > 60:
            regime = MarketRegime.STRONG_BULL
            confidence = min(95, 60 + combined * 0.35)
        elif combined > 30:
            regime = MarketRegime.BULL
            confidence = 55 + combined * 0.4
        elif combined > -30:
            regime = MarketRegime.SIDEWAYS
            confidence = 60 + abs(combined) * 0.3
        elif combined > -60:
            regime = MarketRegime.BEAR
            confidence = 55 + abs(combined) * 0.4
        else:
            regime = MarketRegime.STRONG_BEAR
            confidence = min(95, 60 + abs(combined) * 0.35)
        
        return regime, confidence
    
    def get_regime_summary(self) -> Dict:
        """Get summary of regime detection"""
        return {
            "current_regime": self.current_regime.value,
            "confidence": self.regime_confidence,
            "duration_periods": self.regime_duration,
            "recent_history": list(self.regime_history)[-10:]
        }


class SpecialistAgent:
    """Base class for specialist trading agents"""
    
    def __init__(self, name: str, regime: MarketRegime):
        self.name = name
        self.target_regime = regime
        self.performance_history = deque(maxlen=100)
        self.total_trades = 0
        self.winning_trades = 0
        
    def get_signal(self, prices: List[float], **kwargs) -> Dict:
        """Get trading signal - to be implemented by subclasses"""
        raise NotImplementedError
    
    def record_trade_result(self, profit_pct: float):
        """Record trade result for performance tracking"""
        self.total_trades += 1
        if profit_pct > 0:
            self.winning_trades += 1
        self.performance_history.append({
            "profit_pct": profit_pct,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def get_win_rate(self) -> float:
        """Get win rate"""
        if self.total_trades == 0:
            return 0.5
        return self.winning_trades / self.total_trades
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        profits = [p["profit_pct"] for p in self.performance_history]
        return {
            "name": self.name,
            "target_regime": self.target_regime.value,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate": self.get_win_rate(),
            "avg_profit": np.mean(profits) if profits else 0,
            "sharpe": (np.mean(profits) / (np.std(profits) + 0.0001)) * np.sqrt(252) if profits else 0
        }


class BullMarketAgent(SpecialistAgent):
    """
    Specialist for bull markets.
    Strategy: Momentum-following, buy dips, ride trends.
    """
    
    def __init__(self):
        super().__init__("Bull Market Specialist", MarketRegime.BULL)
        
    def get_signal(self, prices: List[float], **kwargs) -> Dict:
        if len(prices) < 20:
            return {"signal": "HOLD", "confidence": 30, "reason": "Insufficient data"}
        
        prices = np.array(prices)
        current_price = prices[-1]
        
        # Calculate indicators
        sma_20 = np.mean(prices[-20:])
        rsi = self._calculate_rsi(prices)
        
        # Bull market strategy: Buy pullbacks to SMA, hold strong trends
        pullback_pct = ((sma_20 - current_price) / sma_20) * 100
        
        signal = "HOLD"
        confidence = 50
        reason = ""
        
        # Buy on pullback to SMA (2-5% below)
        if 2 < pullback_pct < 5 and rsi < 45:
            signal = "BUY"
            confidence = 75
            reason = "Pullback to SMA20 in uptrend"
        
        # Strong buy on larger pullback with oversold RSI
        elif pullback_pct > 5 and rsi < 35:
            signal = "STRONG_BUY"
            confidence = 85
            reason = "Deep pullback with oversold RSI"
        
        # Take profit if overbought
        elif rsi > 75 and current_price > sma_20 * 1.1:
            signal = "SELL"
            confidence = 65
            reason = "Overbought - take partial profits"
        
        # Hold if in uptrend
        elif current_price > sma_20:
            signal = "HOLD"
            confidence = 60
            reason = "In uptrend - maintain position"
        
        return {
            "signal": signal,
            "confidence": confidence,
            "reason": reason,
            "agent": self.name,
            "indicators": {
                "sma_20": sma_20,
                "rsi": rsi,
                "pullback_pct": pullback_pct
            }
        }
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        gains = []
        losses = []
        for i in range(1, min(period + 1, len(prices))):
            diff = prices[-i] - prices[-i-1]
            if diff > 0:
                gains.append(diff)
            else:
                losses.append(abs(diff))
        
        avg_gain = np.mean(gains) if gains else 0.0001
        avg_loss = np.mean(losses) if losses else 0.0001
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))


class BearMarketAgent(SpecialistAgent):
    """
    Specialist for bear markets.
    Strategy: Defensive, short rallies, preserve capital.
    """
    
    def __init__(self):
        super().__init__("Bear Market Specialist", MarketRegime.BEAR)
        
    def get_signal(self, prices: List[float], **kwargs) -> Dict:
        if len(prices) < 20:
            return {"signal": "HOLD", "confidence": 30, "reason": "Insufficient data"}
        
        prices = np.array(prices)
        current_price = prices[-1]
        
        sma_20 = np.mean(prices[-20:])
        sma_50 = np.mean(prices[-50:]) if len(prices) >= 50 else sma_20
        rsi = self._calculate_rsi(prices)
        
        # Bear market strategy: Short rallies, cash is king
        rally_pct = ((current_price - sma_20) / sma_20) * 100
        
        signal = "HOLD"
        confidence = 50
        reason = ""
        
        # Short opportunity on rally to resistance
        if rally_pct > 5 and rsi > 55 and current_price < sma_50:
            signal = "SELL"
            confidence = 75
            reason = "Rally to resistance in downtrend"
        
        # Strong sell on overbought rally
        elif rally_pct > 10 and rsi > 65:
            signal = "STRONG_SELL"
            confidence = 85
            reason = "Overbought rally - high probability reversal"
        
        # Potential bounce trade (risky)
        elif rsi < 25 and rally_pct < -10:
            signal = "BUY"
            confidence = 55
            reason = "Oversold bounce opportunity (high risk)"
        
        # Stay defensive
        elif current_price < sma_20:
            signal = "HOLD"
            confidence = 60
            reason = "Downtrend - stay defensive/cash"
        
        return {
            "signal": signal,
            "confidence": confidence,
            "reason": reason,
            "agent": self.name,
            "indicators": {
                "sma_20": sma_20,
                "sma_50": sma_50,
                "rsi": rsi,
                "rally_pct": rally_pct
            }
        }
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        gains = []
        losses = []
        for i in range(1, min(period + 1, len(prices))):
            diff = prices[-i] - prices[-i-1]
            if diff > 0:
                gains.append(diff)
            else:
                losses.append(abs(diff))
        
        avg_gain = np.mean(gains) if gains else 0.0001
        avg_loss = np.mean(losses) if losses else 0.0001
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))


class SidewaysMarketAgent(SpecialistAgent):
    """
    Specialist for sideways/range-bound markets.
    Strategy: Mean reversion, buy support, sell resistance.
    """
    
    def __init__(self):
        super().__init__("Range Trading Specialist", MarketRegime.SIDEWAYS)
        
    def get_signal(self, prices: List[float], **kwargs) -> Dict:
        if len(prices) < 30:
            return {"signal": "HOLD", "confidence": 30, "reason": "Insufficient data"}
        
        prices = np.array(prices)
        current_price = prices[-1]
        
        # Calculate range
        high_20 = np.max(prices[-20:])
        low_20 = np.min(prices[-20:])
        range_mid = (high_20 + low_20) / 2
        
        # Position in range (0 = at low, 100 = at high)
        range_position = ((current_price - low_20) / (high_20 - low_20)) * 100 if high_20 != low_20 else 50
        
        # Bollinger Bands
        sma_20 = np.mean(prices[-20:])
        std_20 = np.std(prices[-20:])
        upper_bb = sma_20 + 2 * std_20
        lower_bb = sma_20 - 2 * std_20
        
        signal = "HOLD"
        confidence = 50
        reason = ""
        
        # Buy at support (lower band / range low)
        if range_position < 20 or current_price <= lower_bb:
            signal = "BUY"
            confidence = 70
            reason = "At range support / lower Bollinger Band"
        
        # Strong buy if oversold at support
        elif range_position < 10:
            signal = "STRONG_BUY"
            confidence = 80
            reason = "Extreme oversold at range support"
        
        # Sell at resistance (upper band / range high)
        elif range_position > 80 or current_price >= upper_bb:
            signal = "SELL"
            confidence = 70
            reason = "At range resistance / upper Bollinger Band"
        
        # Strong sell if overbought at resistance
        elif range_position > 90:
            signal = "STRONG_SELL"
            confidence = 80
            reason = "Extreme overbought at range resistance"
        
        # Near middle - wait
        else:
            signal = "HOLD"
            confidence = 55
            reason = "Mid-range - wait for extremes"
        
        return {
            "signal": signal,
            "confidence": confidence,
            "reason": reason,
            "agent": self.name,
            "indicators": {
                "range_position": range_position,
                "range_high": high_20,
                "range_low": low_20,
                "upper_bb": upper_bb,
                "lower_bb": lower_bb
            }
        }


class HighVolatilityAgent(SpecialistAgent):
    """
    Specialist for high volatility regimes.
    Strategy: Reduced position sizes, wider stops, capitalize on big moves.
    """
    
    def __init__(self):
        super().__init__("Volatility Specialist", MarketRegime.HIGH_VOLATILITY)
        
    def get_signal(self, prices: List[float], **kwargs) -> Dict:
        if len(prices) < 20:
            return {"signal": "HOLD", "confidence": 30, "reason": "Insufficient data"}
        
        prices = np.array(prices)
        
        # Calculate volatility
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns[-20:]) * np.sqrt(252) * 100
        
        # ATR for stop calculation
        atr = np.mean(np.abs(np.diff(prices[-20:])))
        atr_pct = (atr / prices[-1]) * 100
        
        # Trend in volatility
        short_trend = prices[-1] > prices[-5] if len(prices) >= 5 else True
        
        signal = "HOLD"
        confidence = 50
        reason = ""
        position_size_modifier = 0.5  # Reduce position size in high vol
        
        # Strong momentum move - follow it with reduced size
        recent_move = ((prices[-1] - prices[-3]) / prices[-3]) * 100 if len(prices) >= 3 else 0
        
        if recent_move > 10 and short_trend:
            signal = "BUY"
            confidence = 60
            reason = "Strong momentum breakout - follow with caution"
            position_size_modifier = 0.3
        
        elif recent_move < -10 and not short_trend:
            signal = "SELL"
            confidence = 60
            reason = "Strong breakdown - follow with caution"
            position_size_modifier = 0.3
        
        # Extreme volatility - stay out
        elif volatility > 100:
            signal = "HOLD"
            confidence = 70
            reason = "Extreme volatility - reduce exposure"
            position_size_modifier = 0.2
        
        else:
            signal = "HOLD"
            confidence = 55
            reason = "High volatility - be patient"
        
        return {
            "signal": signal,
            "confidence": confidence,
            "reason": reason,
            "agent": self.name,
            "position_size_modifier": position_size_modifier,
            "indicators": {
                "volatility_annualized": volatility,
                "atr_pct": atr_pct,
                "recent_move_pct": recent_move
            }
        }


class SpecialistEnsemble:
    """
    Ensemble that combines all specialist agents with regime-aware weighting.
    """
    
    def __init__(self, db=None):
        self.db = db
        
        # Initialize components
        self.regime_detector = MarketRegimeDetector()
        
        # Specialist agents
        self.agents = {
            MarketRegime.STRONG_BULL: BullMarketAgent(),
            MarketRegime.BULL: BullMarketAgent(),
            MarketRegime.SIDEWAYS: SidewaysMarketAgent(),
            MarketRegime.BEAR: BearMarketAgent(),
            MarketRegime.STRONG_BEAR: BearMarketAgent(),
            MarketRegime.HIGH_VOLATILITY: HighVolatilityAgent()
        }
        
        # Base weights for each regime
        self.regime_weights = {
            MarketRegime.STRONG_BULL: {"bull": 0.8, "sideways": 0.1, "bear": 0.05, "volatility": 0.05},
            MarketRegime.BULL: {"bull": 0.6, "sideways": 0.25, "bear": 0.1, "volatility": 0.05},
            MarketRegime.SIDEWAYS: {"bull": 0.2, "sideways": 0.6, "bear": 0.15, "volatility": 0.05},
            MarketRegime.BEAR: {"bull": 0.1, "sideways": 0.2, "bear": 0.6, "volatility": 0.1},
            MarketRegime.STRONG_BEAR: {"bull": 0.05, "sideways": 0.1, "bear": 0.75, "volatility": 0.1},
            MarketRegime.HIGH_VOLATILITY: {"bull": 0.1, "sideways": 0.1, "bear": 0.1, "volatility": 0.7}
        }
        
        logger.info("🎯 Specialist Ensemble initialized")
    
    async def get_ensemble_signal(
        self, 
        prices: List[float],
        volumes: Optional[List[float]] = None
    ) -> Dict:
        """
        Get ensemble signal from all specialists weighted by current regime.
        """
        if len(prices) < 50:
            return {
                "signal": "HOLD",
                "confidence": 30,
                "reason": "Insufficient data for regime detection",
                "regime": MarketRegime.UNKNOWN.value
            }
        
        # Detect current regime
        regime, regime_confidence = self.regime_detector.detect_regime(prices, volumes)
        
        # Get weights for current regime
        weights = self.regime_weights.get(regime, self.regime_weights[MarketRegime.SIDEWAYS])
        
        # Get signals from all agents
        agent_signals = {}
        
        bull_signal = self.agents[MarketRegime.BULL].get_signal(prices)
        bear_signal = self.agents[MarketRegime.BEAR].get_signal(prices)
        sideways_signal = self.agents[MarketRegime.SIDEWAYS].get_signal(prices)
        vol_signal = self.agents[MarketRegime.HIGH_VOLATILITY].get_signal(prices)
        
        agent_signals = {
            "bull": bull_signal,
            "bear": bear_signal,
            "sideways": sideways_signal,
            "volatility": vol_signal
        }
        
        # Combine signals with weights
        signal_scores = {"BUY": 0, "SELL": 0, "HOLD": 0}
        total_confidence = 0
        
        signal_mapping = {
            "STRONG_BUY": ("BUY", 1.5),
            "BUY": ("BUY", 1.0),
            "HOLD": ("HOLD", 1.0),
            "SELL": ("SELL", 1.0),
            "STRONG_SELL": ("SELL", 1.5)
        }
        
        for agent_type, signal_data in agent_signals.items():
            weight = weights.get(agent_type, 0.1)
            raw_signal = signal_data.get("signal", "HOLD")
            confidence = signal_data.get("confidence", 50)
            
            mapped_signal, multiplier = signal_mapping.get(raw_signal, ("HOLD", 1.0))
            signal_scores[mapped_signal] += weight * confidence * multiplier
            total_confidence += weight * confidence
        
        # Determine final signal
        max_signal = max(signal_scores, key=signal_scores.get)
        
        # Adjust for strength
        buy_score = signal_scores["BUY"]
        sell_score = signal_scores["SELL"]
        hold_score = signal_scores["HOLD"]
        
        if buy_score > sell_score * 1.5 and buy_score > hold_score:
            final_signal = "STRONG_BUY" if buy_score > sell_score * 2 else "BUY"
        elif sell_score > buy_score * 1.5 and sell_score > hold_score:
            final_signal = "STRONG_SELL" if sell_score > buy_score * 2 else "SELL"
        else:
            final_signal = "HOLD"
        
        # Calculate confidence
        total_score = buy_score + sell_score + hold_score
        final_confidence = (signal_scores[max_signal] / total_score) * 100 if total_score > 0 else 50
        
        # Get primary agent for this regime
        primary_agent = self.agents.get(regime)
        primary_signal = primary_agent.get_signal(prices) if primary_agent else {}
        
        return {
            "signal": final_signal,
            "confidence": min(95, final_confidence),
            "regime": regime.value,
            "regime_confidence": regime_confidence,
            "regime_duration": self.regime_detector.regime_duration,
            "primary_agent": primary_agent.name if primary_agent else "Unknown",
            "primary_agent_signal": primary_signal,
            "all_agent_signals": agent_signals,
            "signal_scores": signal_scores,
            "weights_used": weights,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_status(self) -> Dict:
        """Get ensemble status"""
        agent_metrics = {}
        for regime, agent in self.agents.items():
            metrics = agent.get_performance_metrics()
            agent_metrics[regime.value] = metrics
        
        return {
            "regime_summary": self.regime_detector.get_regime_summary(),
            "agent_performance": agent_metrics,
            "current_regime": self.regime_detector.current_regime.value,
            "regime_confidence": self.regime_detector.regime_confidence
        }


# Singleton
_specialist_ensemble: Optional[SpecialistEnsemble] = None


def get_specialist_ensemble(db=None) -> SpecialistEnsemble:
    """Get or create specialist ensemble singleton"""
    global _specialist_ensemble
    if _specialist_ensemble is None:
        _specialist_ensemble = SpecialistEnsemble(db)
    return _specialist_ensemble

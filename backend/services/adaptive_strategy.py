"""
Adaptive Strategy Engine for Real Money Trading
Dynamically adjusts trading strategies based on:
- Real-time market conditions (volatility, trend strength)
- Recent performance feedback
- News/event triggers
- Risk tolerance adjustments
- Multi-timeframe analysis
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import numpy as np
from enum import Enum


class MarketRegime(Enum):
    """Market regime classification"""
    STRONG_BULL = "strong_bull"      # >20% monthly gain, low volatility
    BULL = "bull"                     # 5-20% monthly gain
    SIDEWAYS = "sideways"            # -5% to +5%
    BEAR = "bear"                     # -20% to -5%
    STRONG_BEAR = "strong_bear"      # <-20% loss, high volatility
    HIGH_VOLATILITY = "high_volatility"  # >30% swings
    ACCUMULATION = "accumulation"    # Low volatility, range-bound


class RiskMode(Enum):
    """Risk tolerance modes"""
    AGGRESSIVE = "aggressive"        # Max growth, higher risk
    MODERATE = "moderate"            # Balanced
    CONSERVATIVE = "conservative"    # Capital preservation
    DEFENSIVE = "defensive"          # Minimize losses


class AdaptiveStrategyEngine:
    """
    Real-time adaptive strategy management system.
    Continuously monitors and adjusts trading parameters.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, kraken_service=None, alert_service=None):
        self.db = db
        self.kraken = kraken_service
        self.alert_service = alert_service
        
        # Default strategy parameters (will be adapted)
        self.base_params = {
            # Position sizing
            'max_position_pct': 15.0,      # Max % of portfolio per position
            'min_position_pct': 3.0,       # Min % per position
            'max_total_exposure': 90.0,    # Max % of portfolio invested
            
            # Risk management
            'stop_loss_pct': 15.0,         # Default stop loss
            'take_profit_pct': 30.0,       # Default take profit
            'trailing_stop_pct': 10.0,     # Trailing stop activation
            
            # Entry/Exit thresholds
            'min_confidence': 60.0,        # Min AI confidence to enter
            'exit_confidence': 40.0,       # Exit if confidence drops below
            
            # Rebalance frequency
            'rebalance_hours': 168,        # Weekly by default
            'emergency_rebalance_drop': 20.0,  # Trigger rebalance if drop >20%
        }
        
        # Current adaptive state
        self.current_regime = MarketRegime.SIDEWAYS
        self.current_risk_mode = RiskMode.MODERATE
        self.adapted_params = dict(self.base_params)
        
        # Performance tracking
        self.performance_window = []  # Last N trade results
        self.regime_history = []
        
        # Adaptation rules
        self.adaptation_rules = self._init_adaptation_rules()
    
    def _init_adaptation_rules(self) -> Dict[str, Any]:
        """Initialize regime-specific adaptation rules"""
        return {
            MarketRegime.STRONG_BULL: {
                'position_multiplier': 1.3,      # Increase positions
                'stop_loss_adjust': -5,          # Tighter stops (15->10%)
                'take_profit_adjust': +20,       # Higher targets (30->50%)
                'min_confidence_adjust': -10,    # Lower threshold (60->50%)
                'rebalance_multiplier': 0.5,     # More frequent rebalance
                'preferred_assets': ['momentum', 'growth', 'gems'],
            },
            MarketRegime.BULL: {
                'position_multiplier': 1.1,
                'stop_loss_adjust': -2,
                'take_profit_adjust': +10,
                'min_confidence_adjust': -5,
                'rebalance_multiplier': 0.75,
                'preferred_assets': ['large_cap', 'momentum'],
            },
            MarketRegime.SIDEWAYS: {
                'position_multiplier': 1.0,
                'stop_loss_adjust': 0,
                'take_profit_adjust': 0,
                'min_confidence_adjust': 0,
                'rebalance_multiplier': 1.0,
                'preferred_assets': ['yield', 'stable'],
            },
            MarketRegime.BEAR: {
                'position_multiplier': 0.7,      # Reduce positions
                'stop_loss_adjust': -3,          # Tighter stops
                'take_profit_adjust': -10,       # Lower targets
                'min_confidence_adjust': +10,    # Higher threshold
                'rebalance_multiplier': 1.5,     # Less frequent
                'preferred_assets': ['large_cap', 'btc', 'eth'],
            },
            MarketRegime.STRONG_BEAR: {
                'position_multiplier': 0.4,      # Minimal exposure
                'stop_loss_adjust': -5,
                'take_profit_adjust': -15,
                'min_confidence_adjust': +20,
                'rebalance_multiplier': 2.0,
                'preferred_assets': ['btc', 'stablecoins'],
                'max_exposure_override': 50.0,   # Cap at 50%
            },
            MarketRegime.HIGH_VOLATILITY: {
                'position_multiplier': 0.6,
                'stop_loss_adjust': +5,          # Wider stops for volatility
                'take_profit_adjust': +15,       # Higher targets
                'min_confidence_adjust': +5,
                'rebalance_multiplier': 0.5,     # Monitor more often
                'preferred_assets': ['large_cap'],
            },
            MarketRegime.ACCUMULATION: {
                'position_multiplier': 1.2,      # Good time to accumulate
                'stop_loss_adjust': 0,
                'take_profit_adjust': +5,
                'min_confidence_adjust': -5,
                'rebalance_multiplier': 1.25,
                'preferred_assets': ['oversold', 'high_potential'],
            },
        }
    
    async def detect_market_regime(self, btc_data: Dict = None) -> MarketRegime:
        """
        Detect current market regime based on BTC and overall market conditions.
        """
        try:
            # Get BTC price data if not provided
            if not btc_data and self.kraken:
                btc_data = await self.kraken.get_ticker('XXBTZUSD')
            
            if not btc_data:
                return MarketRegime.SIDEWAYS
            
            # Calculate metrics
            current_price = float(btc_data.get('last', btc_data.get('c', [0])[0]))
            
            # Get historical data for regime detection
            ohlcv = await self.db.historical_ohlcv.find(
                {'symbol': 'BTC'},
                {'_id': 0}
            ).sort('timestamp', -1).limit(30).to_list(30)
            
            if len(ohlcv) < 7:
                return MarketRegime.SIDEWAYS
            
            prices = [float(d.get('close', 0)) for d in ohlcv]
            
            # Calculate metrics
            week_change = ((prices[0] - prices[6]) / prices[6] * 100) if prices[6] else 0
            month_change = ((prices[0] - prices[-1]) / prices[-1] * 100) if prices[-1] else 0
            
            # Volatility (standard deviation of daily returns)
            returns = [(prices[i] - prices[i+1]) / prices[i+1] * 100 for i in range(len(prices)-1) if prices[i+1]]
            volatility = np.std(returns) if returns else 0
            
            # Determine regime
            if volatility > 8:  # High volatility
                regime = MarketRegime.HIGH_VOLATILITY
            elif month_change > 20:
                regime = MarketRegime.STRONG_BULL
            elif month_change > 5:
                regime = MarketRegime.BULL
            elif month_change < -20:
                regime = MarketRegime.STRONG_BEAR
            elif month_change < -5:
                regime = MarketRegime.BEAR
            elif abs(month_change) < 5 and volatility < 3:
                regime = MarketRegime.ACCUMULATION
            else:
                regime = MarketRegime.SIDEWAYS
            
            # Store regime detection
            await self.db.regime_detections.insert_one({
                'timestamp': datetime.now(timezone.utc),
                'regime': regime.value,
                'week_change': week_change,
                'month_change': month_change,
                'volatility': volatility,
                'btc_price': current_price
            })
            
            self.current_regime = regime
            return regime
            
        except Exception as e:
            print(f"Error detecting market regime: {e}")
            return MarketRegime.SIDEWAYS
    
    async def adapt_strategy(self, regime: MarketRegime = None, performance_data: Dict = None) -> Dict[str, Any]:
        """
        Adapt strategy parameters based on current market regime and performance.
        Returns the adapted parameters.
        """
        if regime is None:
            regime = await self.detect_market_regime()
        
        # Get adaptation rules for current regime
        rules = self.adaptation_rules.get(regime, {})
        
        # Start with base params
        adapted = dict(self.base_params)
        
        # Apply regime-based adaptations
        adapted['max_position_pct'] = self.base_params['max_position_pct'] * rules.get('position_multiplier', 1.0)
        adapted['stop_loss_pct'] = max(5, self.base_params['stop_loss_pct'] + rules.get('stop_loss_adjust', 0))
        adapted['take_profit_pct'] = max(10, self.base_params['take_profit_pct'] + rules.get('take_profit_adjust', 0))
        adapted['min_confidence'] = min(90, max(30, self.base_params['min_confidence'] + rules.get('min_confidence_adjust', 0)))
        adapted['rebalance_hours'] = self.base_params['rebalance_hours'] * rules.get('rebalance_multiplier', 1.0)
        
        # Apply max exposure override if present
        if 'max_exposure_override' in rules:
            adapted['max_total_exposure'] = rules['max_exposure_override']
        
        # Performance-based adjustments
        if performance_data:
            recent_accuracy = performance_data.get('recent_accuracy', 50)
            win_rate = performance_data.get('win_rate', 50)
            
            # If performing well, slightly increase exposure
            if recent_accuracy > 70 and win_rate > 60:
                adapted['max_position_pct'] *= 1.1
                adapted['min_confidence'] -= 5
            # If performing poorly, reduce exposure
            elif recent_accuracy < 40 or win_rate < 40:
                adapted['max_position_pct'] *= 0.8
                adapted['min_confidence'] += 10
                adapted['stop_loss_pct'] -= 3  # Tighter stops
        
        # Store adaptation
        adaptation_record = {
            'timestamp': datetime.now(timezone.utc),
            'regime': regime.value,
            'base_params': self.base_params,
            'adapted_params': adapted,
            'rules_applied': rules,
            'performance_input': performance_data
        }
        await self.db.strategy_adaptations.insert_one(adaptation_record)
        
        self.adapted_params = adapted
        
        return {
            'regime': regime.value,
            'adapted_params': adapted,
            'changes': {
                'position_size': f"{(adapted['max_position_pct'] / self.base_params['max_position_pct'] - 1) * 100:+.1f}%",
                'stop_loss': f"{adapted['stop_loss_pct'] - self.base_params['stop_loss_pct']:+.1f}%",
                'take_profit': f"{adapted['take_profit_pct'] - self.base_params['take_profit_pct']:+.1f}%",
                'confidence_threshold': f"{adapted['min_confidence'] - self.base_params['min_confidence']:+.1f}%",
            },
            'preferred_assets': rules.get('preferred_assets', [])
        }
    
    async def get_dynamic_position_size(
        self,
        coin_id: str,
        ai_confidence: float,
        portfolio_value: float,
        current_exposure: float = 0
    ) -> Dict[str, Any]:
        """
        Calculate dynamic position size based on confidence, regime, and risk.
        """
        params = self.adapted_params
        
        # Base position size
        base_size_pct = params['max_position_pct']
        
        # Confidence adjustment (higher confidence = larger position)
        confidence_factor = (ai_confidence - 50) / 50  # -1 to +1
        confidence_adjustment = 1 + (confidence_factor * 0.3)  # ±30% based on confidence
        
        # Calculate position
        position_pct = base_size_pct * confidence_adjustment
        position_pct = max(params['min_position_pct'], min(params['max_position_pct'], position_pct))
        
        # Check total exposure limit
        remaining_exposure = params['max_total_exposure'] - current_exposure
        position_pct = min(position_pct, remaining_exposure)
        
        position_usd = portfolio_value * (position_pct / 100)
        
        return {
            'coin_id': coin_id,
            'position_pct': round(position_pct, 2),
            'position_usd': round(position_usd, 2),
            'confidence_used': ai_confidence,
            'regime': self.current_regime.value,
            'stop_loss_pct': params['stop_loss_pct'],
            'take_profit_pct': params['take_profit_pct'],
        }
    
    async def should_exit_position(
        self,
        coin_id: str,
        entry_price: float,
        current_price: float,
        current_confidence: float,
        position_age_hours: float
    ) -> Dict[str, Any]:
        """
        Determine if a position should be exited based on adaptive rules.
        """
        params = self.adapted_params
        
        # Calculate P&L
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        exit_signal = False
        exit_reason = None
        urgency = "normal"
        
        # Stop loss hit
        if pnl_pct <= -params['stop_loss_pct']:
            exit_signal = True
            exit_reason = f"Stop loss triggered ({pnl_pct:.1f}%)"
            urgency = "high"
        
        # Take profit hit
        elif pnl_pct >= params['take_profit_pct']:
            exit_signal = True
            exit_reason = f"Take profit triggered ({pnl_pct:.1f}%)"
            urgency = "normal"
        
        # Trailing stop (if in profit)
        elif pnl_pct > params['trailing_stop_pct']:
            # Activate trailing stop
            trailing_threshold = pnl_pct - params['trailing_stop_pct']
            # This would need to track peak price - simplified here
            exit_signal = False
            exit_reason = f"Trailing stop active, lock in {trailing_threshold:.1f}%"
        
        # Confidence dropped significantly
        elif current_confidence < params['exit_confidence']:
            exit_signal = True
            exit_reason = f"AI confidence dropped to {current_confidence:.1f}%"
            urgency = "medium"
        
        # Regime change to bear while in profit
        elif self.current_regime in [MarketRegime.STRONG_BEAR, MarketRegime.BEAR] and pnl_pct > 5:
            exit_signal = True
            exit_reason = f"Market turned bearish, securing {pnl_pct:.1f}% profit"
            urgency = "medium"
        
        # Position too old with minimal gain
        elif position_age_hours > 336 and abs(pnl_pct) < 5:  # 2 weeks
            exit_signal = True
            exit_reason = "Position stagnant, reallocating capital"
            urgency = "low"
        
        return {
            'should_exit': exit_signal,
            'reason': exit_reason,
            'urgency': urgency,
            'pnl_pct': round(pnl_pct, 2),
            'current_regime': self.current_regime.value,
            'confidence': current_confidence
        }
    
    async def get_entry_signal(
        self,
        coin_id: str,
        ai_confidence: float,
        technical_signal: str,
        news_sentiment: str = "neutral"
    ) -> Dict[str, Any]:
        """
        Generate entry signal combining AI confidence, technicals, and sentiment.
        """
        params = self.adapted_params
        
        # Base entry decision
        should_enter = False
        entry_strength = 0
        reasons = []
        
        # AI Confidence check
        if ai_confidence >= params['min_confidence']:
            entry_strength += 40
            reasons.append(f"AI confidence {ai_confidence:.1f}% above threshold")
        else:
            reasons.append(f"AI confidence {ai_confidence:.1f}% below {params['min_confidence']:.1f}% threshold")
        
        # Technical signal
        if technical_signal == 'BUY':
            entry_strength += 30
            reasons.append("Technical indicators bullish")
        elif technical_signal == 'SELL':
            entry_strength -= 30
            reasons.append("Technical indicators bearish")
        else:
            reasons.append("Technical indicators neutral")
        
        # News sentiment
        if news_sentiment.lower() == 'positive':
            entry_strength += 20
            reasons.append("Positive news sentiment")
        elif news_sentiment.lower() == 'negative':
            entry_strength -= 20
            reasons.append("Negative news sentiment")
        
        # Regime bonus
        regime_bonus = {
            MarketRegime.STRONG_BULL: 15,
            MarketRegime.BULL: 10,
            MarketRegime.ACCUMULATION: 5,
            MarketRegime.SIDEWAYS: 0,
            MarketRegime.BEAR: -10,
            MarketRegime.STRONG_BEAR: -20,
            MarketRegime.HIGH_VOLATILITY: -5,
        }
        regime_adj = regime_bonus.get(self.current_regime, 0)
        entry_strength += regime_adj
        if regime_adj != 0:
            reasons.append(f"Regime adjustment: {regime_adj:+d}")
        
        # Final decision
        should_enter = entry_strength >= 50 and ai_confidence >= params['min_confidence']
        
        return {
            'should_enter': should_enter,
            'entry_strength': entry_strength,
            'reasons': reasons,
            'regime': self.current_regime.value,
            'position_params': await self.get_dynamic_position_size(
                coin_id, ai_confidence, 10000, 0
            ) if should_enter else None
        }
    
    async def trigger_emergency_adaptation(self, trigger_type: str, data: Dict = None) -> Dict[str, Any]:
        """
        Trigger immediate strategy adaptation based on urgent events.
        """
        adaptations = []
        
        if trigger_type == "flash_crash":
            # Immediate defensive mode
            self.current_risk_mode = RiskMode.DEFENSIVE
            self.adapted_params['max_position_pct'] *= 0.5
            self.adapted_params['stop_loss_pct'] = 5  # Very tight stops
            self.adapted_params['max_total_exposure'] = 30
            adaptations.append("Activated defensive mode - reduced exposure 50%")
            
        elif trigger_type == "major_news":
            # Wait for dust to settle
            self.adapted_params['min_confidence'] += 15
            self.adapted_params['rebalance_hours'] = 12  # Check more frequently
            adaptations.append("Increased confidence threshold, monitoring closely")
            
        elif trigger_type == "exchange_issue":
            # Reduce exchange-specific risk
            self.adapted_params['max_position_pct'] *= 0.7
            adaptations.append("Reduced position sizes due to exchange concerns")
            
        elif trigger_type == "performance_drop":
            # Getting consistently wrong, reduce exposure
            self.current_risk_mode = RiskMode.CONSERVATIVE
            self.adapted_params['max_position_pct'] *= 0.6
            self.adapted_params['min_confidence'] += 20
            adaptations.append("Performance-based reduction - waiting for better signals")
            
        elif trigger_type == "opportunity":
            # Strong opportunity detected, increase exposure
            self.adapted_params['max_position_pct'] *= 1.2
            self.adapted_params['min_confidence'] -= 5
            adaptations.append("Opportunity mode - increased exposure capacity")
        
        # Log emergency adaptation
        await self.db.emergency_adaptations.insert_one({
            'timestamp': datetime.now(timezone.utc),
            'trigger_type': trigger_type,
            'trigger_data': data,
            'adaptations': adaptations,
            'new_params': dict(self.adapted_params),
            'risk_mode': self.current_risk_mode.value
        })
        
        # Send alert
        if self.alert_service:
            await self.alert_service.send_alert(
                title=f"⚡ Strategy Adaptation: {trigger_type}",
                message="\n".join(adaptations),
                alert_type="strategy_adaptation",
                priority="high"
            )
        
        return {
            'trigger': trigger_type,
            'adaptations': adaptations,
            'new_params': self.adapted_params,
            'risk_mode': self.current_risk_mode.value
        }
    
    async def get_strategy_status(self) -> Dict[str, Any]:
        """Get current adaptive strategy status"""
        # Get recent adaptations
        recent_adaptations = await self.db.strategy_adaptations.find(
            {}, {'_id': 0}
        ).sort('timestamp', -1).limit(5).to_list(5)
        
        # Get regime history
        regime_history = await self.db.regime_detections.find(
            {}, {'_id': 0}
        ).sort('timestamp', -1).limit(24).to_list(24)
        
        return {
            'current_regime': self.current_regime.value,
            'risk_mode': self.current_risk_mode.value,
            'adapted_params': self.adapted_params,
            'base_params': self.base_params,
            'param_changes': {
                k: f"{((self.adapted_params.get(k, 0) / self.base_params.get(k, 1)) - 1) * 100:+.1f}%"
                for k in ['max_position_pct', 'stop_loss_pct', 'take_profit_pct', 'min_confidence']
            },
            'recent_adaptations': recent_adaptations,
            'regime_history': regime_history[:10],
            'adaptation_rules': {k.value: v for k, v in self.adaptation_rules.items()}
        }
    
    async def reset_to_base(self) -> Dict[str, Any]:
        """Reset strategy to base parameters"""
        self.adapted_params = dict(self.base_params)
        self.current_risk_mode = RiskMode.MODERATE
        
        await self.db.strategy_adaptations.insert_one({
            'timestamp': datetime.now(timezone.utc),
            'action': 'reset_to_base',
            'params': self.adapted_params
        })
        
        return {
            'status': 'reset',
            'params': self.adapted_params,
            'risk_mode': self.current_risk_mode.value
        }


# Global instance
_adaptive_strategy = None


def get_adaptive_strategy(
    db: AsyncIOMotorDatabase = None,
    kraken_service=None,
    alert_service=None
) -> AdaptiveStrategyEngine:
    """Get or create adaptive strategy instance"""
    global _adaptive_strategy
    if _adaptive_strategy is None and db is not None:
        _adaptive_strategy = AdaptiveStrategyEngine(db, kraken_service, alert_service)
    return _adaptive_strategy

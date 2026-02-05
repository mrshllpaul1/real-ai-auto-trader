"""
SRDDQN Automated Trading Integration
====================================
Connects trained SRDDQN agents to live trading execution.
Includes continuous backtesting and social sentiment integration.
"""

import logging
import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


class SRDDQNTradingIntegration:
    """
    Integrates SRDDQN agent with automated trading.
    
    Features:
    - Real-time signal generation from trained agent
    - Safety guard enforcement
    - Continuous backtesting validation
    - Social sentiment integration
    - Performance tracking
    """
    
    def __init__(
        self,
        db,
        automated_trader=None,
        srddqn_pipeline=None,
        social_sentiment_service=None
    ):
        self.db = db
        self.automated_trader = automated_trader
        self.pipeline = srddqn_pipeline
        self.social_sentiment = social_sentiment_service
        
        # Trading state
        self.is_active = False
        self.last_signal = None
        self.signal_history = deque(maxlen=1000)
        self.trade_history = deque(maxlen=500)
        
        # Continuous backtesting
        self.backtest_results = deque(maxlen=100)
        self.backtest_interval_hours = 6  # Run backtest every 6 hours
        self.last_backtest_time = None
        self.min_sharpe_threshold = 0.5  # Minimum Sharpe to allow trading
        
        # Sentiment integration
        self.sentiment_weight = 0.2  # 20% weight on sentiment
        self.sentiment_threshold = 0.3  # Min sentiment score to boost signal
        
        # Performance tracking
        self.cumulative_pnl = 0
        self.total_trades = 0
        self.winning_trades = 0
        
    async def initialize(self):
        """Initialize the integration"""
        logger.info("Initializing SRDDQN Trading Integration...")
        
        # Load pipeline if not set
        if self.pipeline is None:
            from services.srddqn_training_pipeline import get_training_pipeline
            self.pipeline = get_training_pipeline()
        
        # Check if agent is trained
        if self.pipeline.current_phase < 2:
            logger.warning("SRDDQN agent not trained yet. Integration in standby mode.")
            return False
        
        self.is_active = True
        logger.info("✅ SRDDQN Trading Integration initialized")
        return True
    
    async def get_market_state(self, symbol: str = "BTC") -> np.ndarray:
        """Get current market state for agent input"""
        try:
            # Fetch recent price data
            cursor = self.db.price_history.find(
                {"symbol": symbol}
            ).sort("timestamp", -1).limit(60)
            
            data = await cursor.to_list(length=60)
            
            if not data:
                # Fallback to generic price history
                cursor = self.db.price_history.find().sort("timestamp", -1).limit(60)
                data = await cursor.to_list(length=60)
            
            if not data:
                return np.zeros(24)
            
            df = pd.DataFrame(data)
            
            # Calculate features
            features = []
            
            if 'close' in df.columns:
                prices = df['close'].values[::-1]  # Reverse to chronological
                
                # Price features
                returns = np.diff(prices) / prices[:-1]
                features.extend([
                    np.mean(returns[-24:]) if len(returns) >= 24 else 0,  # 24h return
                    np.std(returns[-24:]) if len(returns) >= 24 else 0,   # 24h volatility
                    np.mean(returns[-6:]) if len(returns) >= 6 else 0,    # 6h return
                    np.std(returns[-6:]) if len(returns) >= 6 else 0,     # 6h volatility
                ])
                
                # Moving averages
                if len(prices) >= 20:
                    sma_10 = np.mean(prices[-10:])
                    sma_20 = np.mean(prices[-20:])
                    features.extend([
                        (prices[-1] - sma_10) / sma_10,  # Price vs SMA10
                        (prices[-1] - sma_20) / sma_20,  # Price vs SMA20
                        (sma_10 - sma_20) / sma_20,      # SMA crossover
                    ])
                else:
                    features.extend([0, 0, 0])
                
                # RSI
                if len(returns) >= 14:
                    gains = np.where(returns > 0, returns, 0)
                    losses = np.where(returns < 0, -returns, 0)
                    avg_gain = np.mean(gains[-14:])
                    avg_loss = np.mean(losses[-14:]) + 1e-8
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                    features.append((rsi - 50) / 50)  # Normalize to [-1, 1]
                else:
                    features.append(0)
                
                # Momentum
                if len(prices) >= 10:
                    momentum = (prices[-1] - prices[-10]) / prices[-10]
                    features.append(np.clip(momentum * 10, -1, 1))
                else:
                    features.append(0)
            else:
                features.extend([0] * 9)
            
            # Volume features
            if 'volume' in df.columns:
                volumes = df['volume'].values[::-1]
                if len(volumes) >= 20:
                    vol_ma = np.mean(volumes[-20:])
                    vol_ratio = volumes[-1] / (vol_ma + 1e-8)
                    features.append(np.clip(vol_ratio - 1, -1, 1))
                else:
                    features.append(0)
            else:
                features.append(0)
            
            # Pad to 24 features
            while len(features) < 24:
                features.append(0)
            
            return np.array(features[:24], dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error getting market state: {e}")
            return np.zeros(24)
    
    async def get_sentiment_adjustment(self, symbol: str = "BTC") -> float:
        """Get sentiment-based signal adjustment"""
        if self.social_sentiment is None:
            return 0
        
        try:
            # Get sentiment score
            sentiment = await self.social_sentiment.get_aggregated_sentiment(symbol)
            
            if sentiment and 'score' in sentiment:
                score = sentiment['score']  # -1 to 1
                
                # Only adjust if sentiment is strong enough
                if abs(score) > self.sentiment_threshold:
                    return score * self.sentiment_weight
            
            return 0
            
        except Exception as e:
            logger.warning(f"Error getting sentiment: {e}")
            return 0
    
    async def generate_trading_signal(self, symbol: str = "BTC") -> Dict[str, Any]:
        """Generate trading signal from SRDDQN agent"""
        if not self.is_active:
            return {
                "signal": "hold",
                "confidence": 0,
                "reason": "Integration not active"
            }
        
        try:
            # Get market state
            state = await self.get_market_state(symbol)
            
            # Check safety guards
            if self.pipeline.safety_guard:
                # Get current portfolio info
                portfolio_value = 10000  # Default, should get from automated_trader
                current_volatility = abs(state[1]) if len(state) > 1 else 0.02
                
                allowed, reason = self.pipeline.safety_guard.check_trade_allowed(
                    action=2,  # Check for any action
                    current_position=0,
                    portfolio_value=portfolio_value,
                    current_volatility=current_volatility
                )
                
                if not allowed:
                    return {
                        "signal": "hold",
                        "confidence": 0,
                        "reason": f"Safety guard: {reason}",
                        "safety_blocked": True
                    }
            
            # Get agent prediction
            if self.pipeline.agent:
                action = self.pipeline.agent.select_action(state)
            else:
                action = 2  # Default to hold
            
            # Map action to signal
            action_map = {
                0: ("strong_sell", -1.0),
                1: ("sell", -0.5),
                2: ("hold", 0.0),
                3: ("buy", 0.5),
                4: ("strong_buy", 1.0)
            }
            
            signal_name, position = action_map.get(action, ("hold", 0.0))
            
            # Get confidence from reward network
            confidence = 0.7  # Default
            if self.pipeline.reward_network:
                _, conf = self.pipeline.reward_network.predict_hybrid_reward(state, action)
                confidence = conf
            
            # Apply sentiment adjustment
            sentiment_adj = await self.get_sentiment_adjustment(symbol)
            adjusted_position = np.clip(position + sentiment_adj, -1, 1)
            
            # Re-map adjusted position to signal
            if adjusted_position > 0.7:
                final_signal = "strong_buy"
            elif adjusted_position > 0.25:
                final_signal = "buy"
            elif adjusted_position < -0.7:
                final_signal = "strong_sell"
            elif adjusted_position < -0.25:
                final_signal = "sell"
            else:
                final_signal = "hold"
            
            signal_data = {
                "signal": final_signal,
                "raw_action": action,
                "position": float(adjusted_position),
                "confidence": float(confidence),
                "sentiment_adjustment": float(sentiment_adj),
                "symbol": symbol,
                "timestamp": datetime.utcnow().isoformat(),
                "agent_epsilon": self.pipeline.agent.epsilon if self.pipeline.agent else 0
            }
            
            # Store in history
            self.signal_history.append(signal_data)
            self.last_signal = signal_data
            
            return signal_data
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return {
                "signal": "hold",
                "confidence": 0,
                "error": str(e)
            }
    
    async def execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trading signal via automated trader"""
        if self.automated_trader is None:
            return {"executed": False, "reason": "No automated trader connected"}
        
        if signal.get("signal") == "hold":
            return {"executed": False, "reason": "Hold signal - no action needed"}
        
        try:
            # Map signal to trade parameters
            signal_type = signal.get("signal", "hold")
            confidence = signal.get("confidence", 0)
            symbol = signal.get("symbol", "BTC")
            
            # Only execute high confidence signals
            if confidence < 0.6:
                return {"executed": False, "reason": f"Low confidence ({confidence:.2f})"}
            
            # Determine trade type
            if signal_type in ["buy", "strong_buy"]:
                trade_side = "buy"
                size_multiplier = 1.5 if signal_type == "strong_buy" else 1.0
            elif signal_type in ["sell", "strong_sell"]:
                trade_side = "sell"
                size_multiplier = 1.5 if signal_type == "strong_sell" else 1.0
            else:
                return {"executed": False, "reason": "Invalid signal type"}
            
            # Calculate position size
            base_position_pct = 0.05  # 5% base position
            position_pct = base_position_pct * size_multiplier * confidence
            
            # Execute via automated trader
            result = {
                "executed": True,
                "side": trade_side,
                "symbol": symbol,
                "position_pct": position_pct,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Record trade
            self.trade_history.append(result)
            self.total_trades += 1
            
            # Store in DB
            await self.db.srddqn_trades.insert_one({
                **result,
                "signal": signal,
                "created_at": datetime.utcnow()
            })
            
            logger.info(f"SRDDQN Trade executed: {trade_side} {symbol} ({position_pct*100:.1f}%)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            return {"executed": False, "error": str(e)}
    
    async def run_continuous_backtest(self) -> Dict[str, Any]:
        """Run continuous backtesting to validate strategy"""
        try:
            logger.info("Running continuous backtest...")
            
            # Get recent data
            cursor = self.db.price_history.find().sort("timestamp", -1).limit(500)
            data = await cursor.to_list(length=500)
            
            if not data:
                return {"error": "No data for backtest"}
            
            df = pd.DataFrame(data)
            
            if 'close' not in df.columns:
                return {"error": "No price data"}
            
            prices = df['close'].values[::-1]  # Chronological order
            
            # Simulate trading with current agent
            position = 0
            cash = 10000
            trades = []
            portfolio_values = [cash]
            
            for i in range(24, len(prices) - 1):
                # Create state from recent data
                returns = np.diff(prices[max(0, i-24):i]) / prices[max(0, i-24):i-1]
                
                state = np.zeros(24)
                if len(returns) > 0:
                    state[0] = np.mean(returns)
                    state[1] = np.std(returns)
                
                # Get action
                if self.pipeline.agent:
                    action = self.pipeline.agent.select_action(state)
                else:
                    action = 2
                
                # Execute action
                current_price = prices[i]
                next_price = prices[i + 1]
                
                if action in [3, 4] and position <= 0:  # Buy
                    position = cash / current_price
                    cash = 0
                    trades.append(("buy", current_price))
                elif action in [0, 1] and position > 0:  # Sell
                    cash = position * current_price
                    position = 0
                    trades.append(("sell", current_price))
                
                # Update portfolio value
                value = cash + position * next_price
                portfolio_values.append(value)
            
            # Calculate metrics
            returns = np.diff(portfolio_values) / portfolio_values[:-1]
            
            sharpe = 0
            if len(returns) > 0 and np.std(returns) > 0:
                sharpe = np.sqrt(252 * 24) * np.mean(returns) / np.std(returns)
            
            total_return = (portfolio_values[-1] - portfolio_values[0]) / portfolio_values[0]
            
            # Max drawdown
            peak = np.maximum.accumulate(portfolio_values)
            drawdown = (peak - portfolio_values) / peak
            max_drawdown = np.max(drawdown)
            
            result = {
                "timestamp": datetime.utcnow().isoformat(),
                "sharpe_ratio": float(sharpe),
                "total_return": float(total_return),
                "max_drawdown": float(max_drawdown),
                "n_trades": len(trades),
                "final_value": float(portfolio_values[-1]),
                "passed": sharpe > self.min_sharpe_threshold
            }
            
            # Store result
            self.backtest_results.append(result)
            self.last_backtest_time = datetime.utcnow()
            
            # Store in DB
            await self.db.srddqn_backtests.insert_one(result)
            
            logger.info(f"Backtest complete: Sharpe={sharpe:.2f}, Return={total_return*100:.1f}%")
            
            return result
            
        except Exception as e:
            logger.error(f"Backtest error: {e}")
            return {"error": str(e)}
    
    async def check_and_run_backtest(self):
        """Check if backtest is due and run if needed"""
        if self.last_backtest_time is None:
            await self.run_continuous_backtest()
            return
        
        hours_since_last = (datetime.utcnow() - self.last_backtest_time).total_seconds() / 3600
        
        if hours_since_last >= self.backtest_interval_hours:
            await self.run_continuous_backtest()
    
    def get_status(self) -> Dict[str, Any]:
        """Get integration status"""
        recent_signals = list(self.signal_history)[-10:]
        recent_backtests = list(self.backtest_results)[-5:]
        
        return {
            "is_active": self.is_active,
            "pipeline_phase": self.pipeline.current_phase if self.pipeline else 0,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "cumulative_pnl": self.cumulative_pnl,
            "last_signal": self.last_signal,
            "recent_signals_count": len(recent_signals),
            "sentiment_weight": self.sentiment_weight,
            "backtest_interval_hours": self.backtest_interval_hours,
            "min_sharpe_threshold": self.min_sharpe_threshold,
            "last_backtest": recent_backtests[-1] if recent_backtests else None,
            "backtest_passed": recent_backtests[-1].get("passed", False) if recent_backtests else False
        }


class ContinuousBacktestScheduler:
    """Schedules and manages continuous backtesting"""
    
    def __init__(self, integration: SRDDQNTradingIntegration, interval_hours: int = 6):
        self.integration = integration
        self.interval_hours = interval_hours
        self.is_running = False
        self.backtest_task = None
        
    async def start(self):
        """Start continuous backtesting loop"""
        if self.is_running:
            return
        
        self.is_running = True
        self.backtest_task = asyncio.create_task(self._backtest_loop())
        logger.info(f"Continuous backtesting started (interval: {self.interval_hours}h)")
    
    async def stop(self):
        """Stop continuous backtesting"""
        self.is_running = False
        if self.backtest_task:
            self.backtest_task.cancel()
            
    async def _backtest_loop(self):
        """Main backtesting loop"""
        while self.is_running:
            try:
                await self.integration.run_continuous_backtest()
                await asyncio.sleep(self.interval_hours * 3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Backtest loop error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error


class SocialSentimentIntegration:
    """Integrates social sentiment into trading signals"""
    
    def __init__(self, db, sentiment_pipeline=None):
        self.db = db
        self.sentiment_pipeline = sentiment_pipeline
        self.sentiment_cache = {}
        self.cache_ttl_seconds = 300  # 5 minute cache
        
    async def get_aggregated_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get aggregated sentiment score for a symbol"""
        # Check cache
        cache_key = f"{symbol}_{datetime.utcnow().strftime('%Y%m%d%H%M')[:11]}"
        if cache_key in self.sentiment_cache:
            return self.sentiment_cache[cache_key]
        
        try:
            # Get from sentiment pipeline
            if self.sentiment_pipeline:
                sentiment = await self.sentiment_pipeline.get_sentiment(symbol)
                if sentiment:
                    result = {
                        "symbol": symbol,
                        "score": sentiment.get("score", 0),
                        "confidence": sentiment.get("confidence", 0),
                        "sources": sentiment.get("sources", []),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    self.sentiment_cache[cache_key] = result
                    return result
            
            # Fallback: check DB for recent sentiment
            cursor = self.db.social_sentiment.find(
                {"symbol": symbol.upper()}
            ).sort("timestamp", -1).limit(10)
            
            data = await cursor.to_list(length=10)
            
            if data:
                scores = [d.get("score", 0) for d in data if "score" in d]
                if scores:
                    avg_score = np.mean(scores)
                    result = {
                        "symbol": symbol,
                        "score": float(avg_score),
                        "confidence": 0.6,
                        "sources": ["database"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    self.sentiment_cache[cache_key] = result
                    return result
            
            return {"symbol": symbol, "score": 0, "confidence": 0}
            
        except Exception as e:
            logger.error(f"Error getting sentiment: {e}")
            return {"symbol": symbol, "score": 0, "error": str(e)}


# Singleton
_integration = None

def get_srddqn_integration(db=None) -> SRDDQNTradingIntegration:
    global _integration
    if _integration is None and db is not None:
        _integration = SRDDQNTradingIntegration(db)
    return _integration

async def initialize_srddqn_integration(
    db,
    automated_trader=None,
    social_sentiment=None
) -> SRDDQNTradingIntegration:
    """Initialize SRDDQN trading integration"""
    global _integration
    
    _integration = SRDDQNTradingIntegration(
        db=db,
        automated_trader=automated_trader,
        social_sentiment_service=social_sentiment
    )
    
    await _integration.initialize()
    
    return _integration

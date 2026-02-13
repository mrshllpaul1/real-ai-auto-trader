"""
Master Trading Orchestrator
=============================
Central AI controller that coordinates all trading systems:
- News Monitor → Market sentiment
- Specialist Agents → Regime detection  
- Genetic Algorithm → Architecture optimization
- RLHF → Continuous learning
- Rainbow DQN → Trade execution

Supports hybrid auto-trading:
- Small trades: Auto-execute
- Large trades: Require confirmation
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timezone, timedelta
from collections import deque
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class TradeSize(Enum):
    """Trade size classification"""
    SMALL = "small"      # < 2% of portfolio
    MEDIUM = "medium"    # 2-5% of portfolio
    LARGE = "large"      # > 5% of portfolio


class TradeMode(Enum):
    """Auto-trading mode"""
    MANUAL = "manual"           # All trades require confirmation
    AUTO_SMALL = "auto_small"   # Small trades auto, others confirm (HYBRID)
    FULL_AUTO = "full_auto"     # All trades auto-execute


class TradingSignal:
    """Represents a trading signal from the AI"""
    
    def __init__(
        self,
        symbol: str,
        action: str,  # BUY, SELL, HOLD
        confidence: float,
        size_pct: float,
        source: str,
        reasoning: Dict = None
    ):
        self.id = f"sig_{datetime.now(timezone.utc).timestamp()}"
        self.symbol = symbol
        self.action = action
        self.confidence = confidence
        self.size_pct = size_pct
        self.source = source
        self.reasoning = reasoning or {}
        self.created_at = datetime.now(timezone.utc)
        self.status = "pending"  # pending, confirmed, executed, rejected, expired
        self.execution_result = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "action": self.action,
            "confidence": self.confidence,
            "size_pct": self.size_pct,
            "source": self.source,
            "reasoning": self.reasoning,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "execution_result": self.execution_result
        }
    
    def get_size_category(self) -> TradeSize:
        """Classify trade size"""
        if self.size_pct < 2:
            return TradeSize.SMALL
        elif self.size_pct <= 5:
            return TradeSize.MEDIUM
        return TradeSize.LARGE


class RiskManager:
    """
    Risk management system with safety limits.
    """
    
    def __init__(self, db=None):
        self.db = db
        
        # Risk limits
        self.max_position_pct = 10.0      # Max 10% in single position
        self.max_daily_loss_pct = 5.0     # Stop trading if down 5% today
        self.max_drawdown_pct = 15.0      # Max 15% drawdown from peak
        self.min_confidence = 60.0         # Min 60% confidence to trade
        self.max_trades_per_hour = 10      # Rate limit
        
        # Tracking
        self.daily_pnl = 0.0
        self.peak_portfolio = 0.0
        self.current_portfolio = 0.0
        self.trades_this_hour = 0
        self.hour_start = datetime.now(timezone.utc)
        
        # Position tracking
        self.positions: Dict[str, Dict] = {}
        
        logger.info("🛡️ Risk Manager initialized")
    
    def check_trade_allowed(self, signal: TradingSignal, portfolio_value: float) -> Dict:
        """
        Check if a trade is allowed based on risk rules.
        Returns approval status and reason.
        """
        self.current_portfolio = portfolio_value
        if self.peak_portfolio == 0:
            self.peak_portfolio = portfolio_value
        
        # Update peak
        if portfolio_value > self.peak_portfolio:
            self.peak_portfolio = portfolio_value
        
        # Check confidence
        if signal.confidence < self.min_confidence:
            return {
                "allowed": False,
                "reason": f"Confidence {signal.confidence:.1f}% below minimum {self.min_confidence}%",
                "risk_level": "low_confidence"
            }
        
        # Check position size
        if signal.size_pct > self.max_position_pct:
            return {
                "allowed": False,
                "reason": f"Position size {signal.size_pct:.1f}% exceeds max {self.max_position_pct}%",
                "risk_level": "oversized"
            }
        
        # Check daily loss limit
        if self.daily_pnl < -self.max_daily_loss_pct:
            return {
                "allowed": False,
                "reason": f"Daily loss {self.daily_pnl:.1f}% exceeds limit {self.max_daily_loss_pct}%",
                "risk_level": "daily_limit"
            }
        
        # Check drawdown
        current_drawdown = ((self.peak_portfolio - portfolio_value) / self.peak_portfolio) * 100
        if current_drawdown > self.max_drawdown_pct:
            return {
                "allowed": False,
                "reason": f"Drawdown {current_drawdown:.1f}% exceeds max {self.max_drawdown_pct}%",
                "risk_level": "drawdown_limit"
            }
        
        # Check rate limit
        now = datetime.now(timezone.utc)
        if (now - self.hour_start).total_seconds() > 3600:
            self.trades_this_hour = 0
            self.hour_start = now
        
        if self.trades_this_hour >= self.max_trades_per_hour:
            return {
                "allowed": False,
                "reason": f"Rate limit: {self.max_trades_per_hour} trades/hour exceeded",
                "risk_level": "rate_limit"
            }
        
        # All checks passed
        return {
            "allowed": True,
            "reason": "All risk checks passed",
            "risk_level": "acceptable",
            "current_drawdown": current_drawdown,
            "daily_pnl": self.daily_pnl
        }
    
    def record_trade(self, signal: TradingSignal, pnl: float = 0):
        """Record a completed trade"""
        self.trades_this_hour += 1
        self.daily_pnl += pnl
    
    def reset_daily(self):
        """Reset daily counters (call at midnight)"""
        self.daily_pnl = 0.0
        logger.info("📊 Daily risk counters reset")
    
    def get_status(self) -> Dict:
        """Get risk manager status"""
        current_drawdown = 0
        if self.peak_portfolio > 0:
            current_drawdown = ((self.peak_portfolio - self.current_portfolio) / self.peak_portfolio) * 100
        
        return {
            "daily_pnl_pct": self.daily_pnl,
            "current_drawdown_pct": current_drawdown,
            "peak_portfolio": self.peak_portfolio,
            "trades_this_hour": self.trades_this_hour,
            "limits": {
                "max_position_pct": self.max_position_pct,
                "max_daily_loss_pct": self.max_daily_loss_pct,
                "max_drawdown_pct": self.max_drawdown_pct,
                "min_confidence": self.min_confidence
            }
        }


class MasterTradingOrchestrator:
    """
    Central AI controller that coordinates all trading systems.
    """
    
    def __init__(self, db=None):
        self.db = db
        
        # Trading mode
        self.mode = TradeMode.AUTO_SMALL  # Default: hybrid
        self.is_active = False
        
        # Risk management
        self.risk_manager = RiskManager(db)
        
        # Signal queue
        self.pending_signals: List[TradingSignal] = []
        self.executed_signals: deque = deque(maxlen=100)
        self.rejected_signals: deque = deque(maxlen=50)
        
        # Performance tracking
        self.stats = {
            "total_signals": 0,
            "executed_trades": 0,
            "auto_executed": 0,
            "confirmed_executed": 0,
            "rejected": 0,
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "started_at": None
        }
        
        # AI system references (set during initialization)
        self.news_monitor = None
        self.specialist_ensemble = None
        self.rainbow_dqn = None
        
        # Callbacks
        self.on_signal_callback: Optional[Callable] = None
        self.on_trade_callback: Optional[Callable] = None
        
        # Portfolio value (fetched from Kraken)
        self.portfolio_value = 0.0
        
        # Small trade threshold (USD)
        self.small_trade_threshold = 100.0  # Trades under $100 are "small"
        
        logger.info("🎯 Master Trading Orchestrator initialized")
    
    def set_mode(self, mode: str):
        """Set trading mode"""
        mode_map = {
            "manual": TradeMode.MANUAL,
            "auto_small": TradeMode.AUTO_SMALL,
            "hybrid": TradeMode.AUTO_SMALL,
            "full_auto": TradeMode.FULL_AUTO
        }
        self.mode = mode_map.get(mode.lower(), TradeMode.AUTO_SMALL)
        logger.info(f"🔄 Trading mode set to: {self.mode.value}")
    
    async def start(self):
        """Start the orchestrator"""
        self.is_active = True
        self.stats["started_at"] = datetime.now(timezone.utc).isoformat()
        
        logger.info("🚀 Master Orchestrator started")
        
        # Start main loop
        while self.is_active:
            try:
                await self._orchestration_cycle()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Orchestration error: {e}")
                await asyncio.sleep(10)
    
    def stop(self):
        """Stop the orchestrator"""
        self.is_active = False
        logger.info("⏹️ Master Orchestrator stopped")
    
    async def _orchestration_cycle(self):
        """Main orchestration cycle"""
        # 1. Get market data
        market_data = await self._get_market_data()
        
        # 2. Get AI signals from all systems
        signals = await self._collect_ai_signals(market_data)
        
        # 3. Process signals
        for signal in signals:
            await self._process_signal(signal)
        
        # 4. Execute approved trades
        await self._execute_pending_trades()
    
    async def _get_market_data(self) -> Dict:
        """Fetch current market data"""
        try:
            # Get portfolio value from Kraken service
            from services.kraken_service import get_kraken_service
            kraken = get_kraken_service()
            
            if kraken:
                portfolio = await kraken.get_portfolio_summary()
                self.portfolio_value = portfolio.get("total_usd", 0)
            
            return {
                "portfolio_value": self.portfolio_value,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.warning(f"Error getting market data: {e}")
            return {"portfolio_value": self.portfolio_value}
    
    async def _collect_ai_signals(self, market_data: Dict) -> List[TradingSignal]:
        """Collect signals from all AI systems"""
        signals = []
        
        try:
            # 1. Get news sentiment signal
            if self.news_monitor:
                news_signal = await self._get_news_signal()
                if news_signal:
                    signals.append(news_signal)
            
            # 2. Get specialist agent signal
            if self.specialist_ensemble:
                specialist_signal = await self._get_specialist_signal()
                if specialist_signal:
                    signals.append(specialist_signal)
            
            # 3. Get Rainbow DQN signal
            if self.rainbow_dqn:
                dqn_signal = await self._get_dqn_signal()
                if dqn_signal:
                    signals.append(dqn_signal)
            
        except Exception as e:
            logger.error(f"Error collecting signals: {e}")
        
        return signals
    
    async def _get_news_signal(self) -> Optional[TradingSignal]:
        """Generate signal from news monitor"""
        try:
            from services.realtime_news_monitor import get_news_monitor
            monitor = get_news_monitor(self.db)
            
            trending = monitor.detector.get_trending_summary()
            
            # Check for significant trending keywords
            keywords = trending.get("top_keywords", [])
            if not keywords:
                return None
            
            top_keyword = keywords[0]
            if top_keyword["count"] < 3:
                return None  # Not trending enough
            
            # Check sentiment
            coin_sentiments = trending.get("coin_sentiments", {})
            
            # Get most mentioned coin
            top_coins = trending.get("top_coins", [])
            if not top_coins:
                return None
            
            coin = top_coins[0]["coin"]
            sentiment = coin_sentiments.get(coin, {})
            
            # Generate signal based on sentiment
            positive = sentiment.get("positive_pct", 33)
            negative = sentiment.get("negative_pct", 33)
            
            if positive > 50:
                action = "BUY"
                confidence = min(80, 50 + positive * 0.3)
            elif negative > 50:
                action = "SELL"
                confidence = min(80, 50 + negative * 0.3)
            else:
                return None  # Neutral, no signal
            
            return TradingSignal(
                symbol=f"{coin}/USD",
                action=action,
                confidence=confidence,
                size_pct=1.5,  # Conservative 1.5%
                source="news_monitor",
                reasoning={
                    "trending_keyword": top_keyword["keyword"],
                    "keyword_count": top_keyword["count"],
                    "sentiment": {"positive": positive, "negative": negative},
                    "mentions": top_coins[0]["mentions"]
                }
            )
            
        except Exception as e:
            logger.warning(f"News signal error: {e}")
            return None
    
    async def _get_specialist_signal(self) -> Optional[TradingSignal]:
        """Generate signal from specialist agents"""
        try:
            from services.specialist_agents import get_specialist_ensemble
            ensemble = get_specialist_ensemble(self.db)
            
            # Get recent prices (would come from market data service)
            # For now, return None if no price data
            status = ensemble.get_status()
            regime = status.get("regime_summary", {}).get("current_regime", "unknown")
            
            if regime == "unknown":
                return None
            
            # Map regime to signal
            regime_actions = {
                "strong_bull": ("BUY", 75, 3.0),
                "bull": ("BUY", 65, 2.0),
                "sideways": ("HOLD", 50, 0),
                "bear": ("SELL", 65, 2.0),
                "strong_bear": ("SELL", 75, 3.0),
            }
            
            if regime not in regime_actions:
                return None
            
            action, confidence, size = regime_actions[regime]
            
            if action == "HOLD":
                return None
            
            return TradingSignal(
                symbol="BTC/USD",  # Default to BTC
                action=action,
                confidence=confidence,
                size_pct=size,
                source="specialist_ensemble",
                reasoning={
                    "market_regime": regime,
                    "regime_confidence": status.get("regime_summary", {}).get("confidence", 0)
                }
            )
            
        except Exception as e:
            logger.warning(f"Specialist signal error: {e}")
            return None
    
    async def _get_dqn_signal(self) -> Optional[TradingSignal]:
        """Generate signal from Rainbow DQN"""
        try:
            from services.rainbow_dqn import get_rainbow_dqn
            dqn = get_rainbow_dqn()
            
            if not dqn or not dqn.is_trained:
                return None
            
            # Get latest state and predict
            # This would need actual market state data
            return None  # Placeholder until state data is available
            
        except Exception as e:
            logger.warning(f"DQN signal error: {e}")
            return None
    
    async def _process_signal(self, signal: TradingSignal):
        """Process a trading signal"""
        self.stats["total_signals"] += 1
        
        # Check risk limits
        risk_check = self.risk_manager.check_trade_allowed(signal, self.portfolio_value)
        
        if not risk_check["allowed"]:
            signal.status = "rejected"
            signal.execution_result = {"reason": risk_check["reason"]}
            self.rejected_signals.append(signal.to_dict())
            self.stats["rejected"] += 1
            logger.info(f"❌ Signal rejected: {risk_check['reason']}")
            return
        
        # Determine if auto-execute based on mode and size
        trade_value = self.portfolio_value * (signal.size_pct / 100)
        size_category = signal.get_size_category()
        
        auto_execute = False
        
        if self.mode == TradeMode.FULL_AUTO:
            auto_execute = True
        elif self.mode == TradeMode.AUTO_SMALL:
            # Hybrid mode: auto for small trades
            if size_category == TradeSize.SMALL or trade_value < self.small_trade_threshold:
                auto_execute = True
        # MANUAL mode: never auto-execute
        
        if auto_execute:
            signal.status = "approved_auto"
        else:
            signal.status = "pending_confirmation"
        
        self.pending_signals.append(signal)
        
        # Notify callbacks
        if self.on_signal_callback:
            try:
                await self.on_signal_callback(signal.to_dict())
            except Exception as e:
                logger.error(f"Signal callback error: {e}")
    
    async def _execute_pending_trades(self):
        """Execute approved trades"""
        for signal in self.pending_signals[:]:
            if signal.status == "approved_auto":
                result = await self._execute_trade(signal)
                
                if result["success"]:
                    signal.status = "executed"
                    signal.execution_result = result
                    self.stats["auto_executed"] += 1
                    self.stats["executed_trades"] += 1
                else:
                    signal.status = "failed"
                    signal.execution_result = result
                
                self.executed_signals.append(signal.to_dict())
                self.pending_signals.remove(signal)
                
                # Record trade in risk manager
                self.risk_manager.record_trade(signal, result.get("pnl", 0))
    
    async def _execute_trade(self, signal: TradingSignal) -> Dict:
        """Execute a trade via Kraken"""
        try:
            from services.kraken_service import get_kraken_service
            kraken = get_kraken_service()
            
            if not kraken:
                return {"success": False, "error": "Kraken service not available"}
            
            # Calculate order size
            trade_value = self.portfolio_value * (signal.size_pct / 100)
            
            # Get current price
            ticker = await kraken.get_ticker(signal.symbol.replace("/", ""))
            price = ticker.get("last", 0)
            
            if price == 0:
                return {"success": False, "error": "Could not get price"}
            
            quantity = trade_value / price
            
            # Place order
            order_result = await kraken.place_market_order(
                pair=signal.symbol.replace("/", ""),
                side=signal.action.lower(),
                volume=quantity
            )
            
            logger.info(f"✅ Trade executed: {signal.action} {quantity:.6f} {signal.symbol} @ ${price:.2f}")
            
            # Notify callback
            if self.on_trade_callback:
                try:
                    await self.on_trade_callback({
                        "signal": signal.to_dict(),
                        "order": order_result
                    })
                except Exception as e:
                    logger.error(f"Trade callback error: {e}")
            
            return {
                "success": True,
                "order_id": order_result.get("txid"),
                "price": price,
                "quantity": quantity,
                "value": trade_value
            }
            
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return {"success": False, "error": str(e)}
    
    async def confirm_signal(self, signal_id: str) -> Dict:
        """Manually confirm a pending signal"""
        for signal in self.pending_signals:
            if signal.id == signal_id:
                signal.status = "approved_auto"  # Mark for execution
                
                # Execute immediately
                result = await self._execute_trade(signal)
                
                if result["success"]:
                    signal.status = "executed"
                    signal.execution_result = result
                    self.stats["confirmed_executed"] += 1
                    self.stats["executed_trades"] += 1
                else:
                    signal.status = "failed"
                    signal.execution_result = result
                
                self.executed_signals.append(signal.to_dict())
                self.pending_signals.remove(signal)
                
                return {"success": True, "signal": signal.to_dict()}
        
        return {"success": False, "error": "Signal not found"}
    
    async def reject_signal(self, signal_id: str) -> Dict:
        """Manually reject a pending signal"""
        for signal in self.pending_signals:
            if signal.id == signal_id:
                signal.status = "rejected"
                signal.execution_result = {"reason": "Manual rejection"}
                self.rejected_signals.append(signal.to_dict())
                self.pending_signals.remove(signal)
                self.stats["rejected"] += 1
                
                return {"success": True, "signal": signal.to_dict()}
        
        return {"success": False, "error": "Signal not found"}
    
    def get_status(self) -> Dict:
        """Get orchestrator status"""
        return {
            "is_active": self.is_active,
            "mode": self.mode.value,
            "portfolio_value": self.portfolio_value,
            "small_trade_threshold": self.small_trade_threshold,
            "pending_signals": [s.to_dict() for s in self.pending_signals],
            "pending_count": len(self.pending_signals),
            "stats": self.stats,
            "risk_status": self.risk_manager.get_status(),
            "recent_trades": list(self.executed_signals)[-10:]
        }
    
    def get_pending_confirmations(self) -> List[Dict]:
        """Get signals waiting for confirmation"""
        return [
            s.to_dict() for s in self.pending_signals 
            if s.status == "pending_confirmation"
        ]


# Singleton
_master_orchestrator: Optional[MasterTradingOrchestrator] = None


def get_master_orchestrator(db=None) -> MasterTradingOrchestrator:
    """Get or create master orchestrator singleton"""
    global _master_orchestrator
    if _master_orchestrator is None:
        _master_orchestrator = MasterTradingOrchestrator(db)
    return _master_orchestrator

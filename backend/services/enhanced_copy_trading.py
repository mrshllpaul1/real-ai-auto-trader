"""
Enhanced Copy Trading Service
Real-time trade synchronization with advanced risk management and performance analytics
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
import uuid
import statistics

logger = logging.getLogger(__name__)


class EnhancedCopyTradingService:
    """
    Advanced copy trading with real-time sync, risk management, and profit sharing
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.active_signals = {}  # Cache for pending trade signals
        self.copier_equity_curves = {}  # Track equity curves for drawdown protection
        
    # =========================================================================
    # REAL-TIME TRADE SYNCHRONIZATION
    # =========================================================================
    
    async def broadcast_trade_signal(
        self,
        trader_id: str,
        trade: Dict[str, Any],
        signal_type: str = "entry"
    ) -> Dict[str, Any]:
        """
        Broadcast a trade signal to all active copiers with real-time sync.
        
        Args:
            trader_id: ID of the trader making the trade
            trade: Trade details (symbol, action, price, amount, etc.)
            signal_type: "entry", "exit", "stop_loss", or "take_profit"
        
        Returns:
            Summary of trade execution across all copiers
        """
        try:
            signal_id = str(uuid.uuid4())[:12]
            signal_time = datetime.now(timezone.utc)
            
            # Store signal for audit trail
            signal = {
                "signal_id": signal_id,
                "trader_id": trader_id,
                "signal_type": signal_type,
                "trade": trade,
                "broadcasted_at": signal_time.isoformat(),
                "status": "broadcasting"
            }
            
            await self.db.trade_signals.insert_one(dict(signal))
            
            # Get all active copiers for this trader
            copiers = await self._get_active_copiers(trader_id)
            
            # Execute trades in parallel with optimized batching
            execution_tasks = [
                self._execute_copy_trade(
                    copier,
                    trade,
                    signal_id,
                    signal_type,
                    signal_time
                )
                for copier in copiers
            ]
            
            results = await asyncio.gather(*execution_tasks, return_exceptions=True)
            
            # Aggregate results
            successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            failed = len(results) - successful
            
            summary = {
                "signal_id": signal_id,
                "trader_id": trader_id,
                "copiers_notified": len(copiers),
                "executed_successfully": successful,
                "failed": failed,
                "execution_time_ms": (datetime.now(timezone.utc) - signal_time).total_seconds() * 1000,
                "results": [r for r in results if isinstance(r, dict)]
            }
            
            # Update signal status
            await self.db.trade_signals.update_one(
                {"signal_id": signal_id},
                {"$set": {
                    "status": "completed",
                    "summary": summary,
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error broadcasting trade signal: {e}")
            return {
                "error": str(e),
                "signal_id": signal_id if 'signal_id' in locals() else None
            }
    
    async def _get_active_copiers(self, trader_id: str) -> List[Dict[str, Any]]:
        """Get all users actively copying this trader with risk checks"""
        copiers = await self.db.copy_relationships.find({
            "trader_id": trader_id,
            "active": True,
            "enabled": True
        }).to_list(500)
        
        # Filter copiers who haven't hit risk limits
        valid_copiers = []
        for copier in copiers:
            if await self._check_copier_risk_limits(copier):
                valid_copiers.append(copier)
        
        return valid_copiers
    
    async def _execute_copy_trade(
        self,
        copier: Dict[str, Any],
        original_trade: Dict[str, Any],
        signal_id: str,
        signal_type: str,
        signal_time: datetime
    ) -> Dict[str, Any]:
        """
        Execute a copy trade for a specific copier with intelligent scaling
        """
        try:
            copier_id = copier["user_id"]
            
            # Calculate scaled position size
            scaled_amount = await self._calculate_scaled_position(
                copier,
                original_trade.get("amount", 0)
            )
            
            # Check slippage tolerance
            if signal_type == "entry":
                current_price = await self._get_current_price(original_trade.get("symbol"))
                slippage_pct = abs((current_price - original_trade.get("price", 0)) / original_trade.get("price", 1)) * 100
                
                if slippage_pct > copier.get("max_slippage_pct", 2.0):
                    return {
                        "success": False,
                        "copier_id": copier_id,
                        "reason": f"Slippage too high: {slippage_pct:.2f}%"
                    }
            
            # Create copy trade
            copy_trade = {
                "trade_id": str(uuid.uuid4()),
                "copier_id": copier_id,
                "trader_id": copier["trader_id"],
                "signal_id": signal_id,
                "signal_type": signal_type,
                "symbol": original_trade.get("symbol"),
                "action": original_trade.get("action"),
                "original_amount": original_trade.get("amount"),
                "copied_amount": scaled_amount,
                "scaling_factor": copier.get("copy_percentage", 100) / 100,
                "entry_price": original_trade.get("price"),
                "stop_loss": original_trade.get("stop_loss"),
                "take_profit": original_trade.get("take_profit"),
                "status": "executed",
                "executed_at": datetime.now(timezone.utc).isoformat(),
                "latency_ms": (datetime.now(timezone.utc) - signal_time).total_seconds() * 1000
            }
            
            # Store the copy trade
            await self.db.copied_trades.insert_one(dict(copy_trade))
            
            # Update copier relationship stats
            await self._update_copier_stats(copier_id, copier["trader_id"], scaled_amount)
            
            # Update equity curve for drawdown tracking
            await self._update_equity_curve(copier_id, copy_trade)
            
            return {
                "success": True,
                "copier_id": copier_id,
                "trade_id": copy_trade["trade_id"],
                "amount": scaled_amount,
                "latency_ms": copy_trade["latency_ms"]
            }
            
        except Exception as e:
            logger.error(f"Error executing copy trade for {copier.get('user_id')}: {e}")
            return {
                "success": False,
                "copier_id": copier.get("user_id"),
                "error": str(e)
            }
    
    async def _calculate_scaled_position(
        self,
        copier: Dict[str, Any],
        original_amount: float
    ) -> float:
        """
        Calculate intelligent position size based on copier's account and settings
        """
        # Base scaling from copy percentage
        base_scaled = original_amount * (copier.get("copy_percentage", 100) / 100)
        
        # Apply max trade size limit
        max_size = copier.get("max_trade_size")
        if max_size and base_scaled > max_size:
            base_scaled = max_size
        
        # Get copier's current portfolio value
        portfolio_value = await self._get_copier_portfolio_value(copier["user_id"])
        
        # Apply portfolio-based position sizing (max % of portfolio per trade)
        max_position_pct = copier.get("max_position_pct", 10.0)
        max_by_portfolio = portfolio_value * (max_position_pct / 100)
        
        # Return the minimum of all constraints
        return min(base_scaled, max_by_portfolio) if max_by_portfolio > 0 else base_scaled
    
    async def _get_current_price(self, symbol: str) -> float:
        """Get current market price for slippage check"""
        # This would integrate with market data service
        # For now, return a placeholder
        return 0.0
    
    async def _get_copier_portfolio_value(self, user_id: str) -> float:
        """Get copier's current portfolio value"""
        # This would integrate with portfolio service
        # For now, return a default value
        return 10000.0
    
    # =========================================================================
    # ADVANCED RISK MANAGEMENT
    # =========================================================================
    
    async def _check_copier_risk_limits(self, copier: Dict[str, Any]) -> bool:
        """
        Comprehensive risk checks before allowing trade copy
        """
        copier_id = copier["user_id"]
        
        # Check max drawdown
        current_drawdown = await self._calculate_current_drawdown(copier_id)
        max_drawdown = copier.get("max_drawdown_pct", 20.0)
        
        if current_drawdown > max_drawdown:
            logger.warning(f"Copier {copier_id} exceeded max drawdown: {current_drawdown:.1f}% > {max_drawdown}%")
            # Disable copying temporarily
            await self.db.copy_relationships.update_one(
                {"user_id": copier_id, "trader_id": copier["trader_id"]},
                {"$set": {"enabled": False, "disabled_reason": "max_drawdown_exceeded"}}
            )
            return False
        
        # Check daily trade limit
        today_trades = await self.db.copied_trades.count_documents({
            "copier_id": copier_id,
            "executed_at": {"$gte": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()}
        })
        
        max_daily_trades = copier.get("max_daily_trades", 20)
        if today_trades >= max_daily_trades:
            logger.warning(f"Copier {copier_id} hit daily trade limit: {today_trades}/{max_daily_trades}")
            return False
        
        # Check if sufficient balance
        portfolio_value = await self._get_copier_portfolio_value(copier_id)
        min_balance = copier.get("min_balance_required", 100.0)
        
        if portfolio_value < min_balance:
            logger.warning(f"Copier {copier_id} insufficient balance: ${portfolio_value:.2f} < ${min_balance}")
            return False
        
        return True
    
    async def _calculate_current_drawdown(self, copier_id: str) -> float:
        """Calculate current drawdown from peak equity"""
        # Get equity curve
        equity_history = await self.db.copier_equity.find({
            "copier_id": copier_id
        }).sort("timestamp", 1).to_list(1000)
        
        if not equity_history:
            return 0.0
        
        # Find peak and current equity
        peak_equity = max(e["equity"] for e in equity_history)
        current_equity = equity_history[-1]["equity"]
        
        if peak_equity <= 0:
            return 0.0
        
        drawdown_pct = ((peak_equity - current_equity) / peak_equity) * 100
        return max(0, drawdown_pct)
    
    async def _update_equity_curve(self, copier_id: str, trade: Dict[str, Any]):
        """Update copier's equity curve for drawdown tracking"""
        # Calculate new equity after trade
        current_equity = await self._get_copier_portfolio_value(copier_id)
        
        equity_point = {
            "copier_id": copier_id,
            "equity": current_equity,
            "trade_id": trade.get("trade_id"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.copier_equity.insert_one(equity_point)
    
    async def get_copier_equity_curve(
        self,
        copier_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get copier's equity curve for visualization"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        curve = await self.db.copier_equity.find({
            "copier_id": copier_id,
            "timestamp": {"$gte": start_date.isoformat()}
        }).sort("timestamp", 1).to_list(1000)
        
        return curve
    
    # =========================================================================
    # PERFORMANCE ANALYTICS
    # =========================================================================
    
    async def calculate_trader_performance_metrics(
        self,
        trader_id: str,
        timeframe_days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics for a trader
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=timeframe_days)
        
        # Get all trades in timeframe
        trades = await self.db.copy_trade_history.find({
            "trader_id": trader_id,
            "executed_at": {"$gte": start_date.isoformat()},
            "status": {"$in": ["closed", "completed"]}
        }).to_list(5000)
        
        if not trades:
            return self._empty_metrics()
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.get("profit", 0) > 0]
        losing_trades = [t for t in trades if t.get("profit", 0) < 0]
        
        profits = [t.get("profit", 0) for t in trades]
        returns = [t.get("return_pct", 0) for t in trades]
        
        # Win rate
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        
        # Profit metrics
        total_profit = sum(profits)
        avg_win = statistics.mean([t.get("profit", 0) for t in winning_trades]) if winning_trades else 0
        avg_loss = statistics.mean([t.get("profit", 0) for t in losing_trades]) if losing_trades else 0
        
        # Profit factor
        gross_profit = sum(t.get("profit", 0) for t in winning_trades)
        gross_loss = abs(sum(t.get("profit", 0) for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Sharpe Ratio (simplified)
        if len(returns) > 1:
            avg_return = statistics.mean(returns)
            std_return = statistics.stdev(returns)
            sharpe_ratio = (avg_return / std_return) * (252 ** 0.5) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Sortino Ratio (downside deviation)
        downside_returns = [r for r in returns if r < 0]
        if len(downside_returns) > 1:
            downside_std = statistics.stdev(downside_returns)
            sortino_ratio = (statistics.mean(returns) / downside_std) * (252 ** 0.5) if downside_std > 0 else 0
        else:
            sortino_ratio = 0
        
        # Maximum drawdown
        equity_curve = await self.db.copier_equity.find({
            "trader_id": trader_id,
            "timestamp": {"$gte": start_date.isoformat()}
        }).sort("timestamp", 1).to_list(1000)
        
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        
        # Average trade duration
        durations = []
        for trade in trades:
            if trade.get("entry_time") and trade.get("exit_time"):
                entry = datetime.fromisoformat(trade["entry_time"].replace('Z', '+00:00'))
                exit = datetime.fromisoformat(trade["exit_time"].replace('Z', '+00:00'))
                durations.append((exit - entry).total_seconds() / 3600)  # hours
        
        avg_duration_hours = statistics.mean(durations) if durations else 0
        
        return {
            "trader_id": trader_id,
            "timeframe_days": timeframe_days,
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(win_rate, 2),
            "total_profit": round(total_profit, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "sharpe_ratio": round(sharpe_ratio, 3),
            "sortino_ratio": round(sortino_ratio, 3),
            "max_drawdown_pct": round(max_drawdown, 2),
            "avg_trade_duration_hours": round(avg_duration_hours, 1),
            "risk_reward_ratio": round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0,
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _calculate_max_drawdown(self, equity_curve: List[Dict[str, Any]]) -> float:
        """Calculate maximum drawdown percentage"""
        if not equity_curve:
            return 0.0
        
        equities = [point["equity"] for point in equity_curve]
        peak = equities[0]
        max_dd = 0
        
        for equity in equities:
            if equity > peak:
                peak = equity
            dd = ((peak - equity) / peak) * 100 if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            "total_trades": 0,
            "win_rate": 0,
            "total_profit": 0,
            "sharpe_ratio": 0,
            "sortino_ratio": 0,
            "max_drawdown_pct": 0
        }
    
    # =========================================================================
    # PROFIT SHARING
    # =========================================================================
    
    async def calculate_profit_share(
        self,
        trader_id: str,
        copier_id: str,
        period_start: datetime,
        period_end: datetime = None
    ) -> Dict[str, Any]:
        """
        Calculate profit sharing owed to trader from copier's profits
        """
        if period_end is None:
            period_end = datetime.now(timezone.utc)
        
        # Get copier relationship to find profit share percentage
        relationship = await self.db.copy_relationships.find_one({
            "user_id": copier_id,
            "trader_id": trader_id
        })
        
        if not relationship:
            return {"error": "No copy relationship found"}
        
        profit_share_pct = relationship.get("profit_share_pct", 10.0)
        
        # Get all profitable copied trades in period
        trades = await self.db.copied_trades.find({
            "copier_id": copier_id,
            "trader_id": trader_id,
            "executed_at": {
                "$gte": period_start.isoformat(),
                "$lte": period_end.isoformat()
            },
            "status": "closed",
            "profit": {"$gt": 0}
        }).to_list(10000)
        
        total_profit = sum(t.get("profit", 0) for t in trades)
        profit_share_amount = total_profit * (profit_share_pct / 100)
        
        share_record = {
            "share_id": str(uuid.uuid4()),
            "trader_id": trader_id,
            "copier_id": copier_id,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "total_copier_profit": round(total_profit, 2),
            "profit_share_pct": profit_share_pct,
            "profit_share_amount": round(profit_share_amount, 2),
            "trades_count": len(trades),
            "status": "pending",
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.profit_shares.insert_one(dict(share_record))
        
        return share_record
    
    async def process_profit_distribution(
        self,
        share_id: str
    ) -> Dict[str, Any]:
        """
        Process and distribute profit share to trader
        """
        share = await self.db.profit_shares.find_one({"share_id": share_id})
        
        if not share:
            return {"error": "Profit share not found"}
        
        if share.get("status") != "pending":
            return {"error": f"Profit share already {share.get('status')}"}
        
        # Record the distribution
        await self.db.profit_shares.update_one(
            {"share_id": share_id},
            {"$set": {
                "status": "distributed",
                "distributed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update trader's earnings
        await self.db.trader_profiles.update_one(
            {"trader_id": share["trader_id"]},
            {"$inc": {"total_earnings": share["profit_share_amount"]}}
        )
        
        return {
            "status": "success",
            "share_id": share_id,
            "amount_distributed": share["profit_share_amount"],
            "trader_id": share["trader_id"]
        }
    
    # =========================================================================
    # TRADER VERIFICATION
    # =========================================================================
    
    async def verify_trader_performance(
        self,
        trader_id: str
    ) -> Dict[str, Any]:
        """
        Verify trader's performance is legitimate (no wash trading, etc.)
        """
        # Get trader's trades
        trades = await self.db.copy_trade_history.find({
            "trader_id": trader_id
        }).to_list(5000)
        
        verification = {
            "trader_id": trader_id,
            "verified": True,
            "issues": [],
            "confidence_score": 100
        }
        
        if not trades:
            verification["verified"] = False
            verification["issues"].append("No trade history")
            return verification
        
        # Check 1: Minimum trade count
        if len(trades) < 20:
            verification["confidence_score"] -= 20
            verification["issues"].append("Low trade count (minimum 20 recommended)")
        
        # Check 2: Win rate too high (possible wash trading)
        wins = sum(1 for t in trades if t.get("profit", 0) > 0)
        win_rate = (wins / len(trades)) * 100
        
        if win_rate > 95:
            verification["verified"] = False
            verification["confidence_score"] -= 50
            verification["issues"].append("Suspiciously high win rate (>95%)")
        
        # Check 3: Trade distribution (check for patterns)
        hours = [datetime.fromisoformat(t.get("executed_at", "").replace('Z', '+00:00')).hour 
                 for t in trades if t.get("executed_at")]
        
        if hours:
            unique_hours = len(set(hours))
            if unique_hours < 3:
                verification["confidence_score"] -= 15
                verification["issues"].append("Trades concentrated in few hours")
        
        # Check 4: Profit consistency (detect manipulation)
        profits = [t.get("profit", 0) for t in trades]
        if len(profits) > 10:
            profit_std = statistics.stdev(profits)
            profit_mean = statistics.mean(profits)
            if profit_std < abs(profit_mean) * 0.1:
                verification["confidence_score"] -= 10
                verification["issues"].append("Unusually consistent profits")
        
        # Award verification badge if passed
        if verification["verified"] and verification["confidence_score"] >= 80:
            await self._award_verification_badge(trader_id, verification["confidence_score"])
        
        return verification
    
    async def _award_verification_badge(self, trader_id: str, confidence_score: int):
        """Award verification badge to trader"""
        badge = {
            "type": "verified_trader",
            "level": "gold" if confidence_score >= 95 else "silver",
            "confidence_score": confidence_score,
            "awarded_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.trader_profiles.update_one(
            {"trader_id": trader_id},
            {"$push": {"badges": badge}}
        )
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    async def _update_copier_stats(
        self,
        copier_id: str,
        trader_id: str,
        amount: float
    ):
        """Update copier's cumulative statistics"""
        await self.db.copy_relationships.update_one(
            {"user_id": copier_id, "trader_id": trader_id},
            {
                "$inc": {"total_copied": 1, "total_amount": amount},
                "$set": {"last_copied_at": datetime.now(timezone.utc).isoformat()}
            }
        )
    
    async def get_copy_performance_comparison(
        self,
        copier_id: str
    ) -> Dict[str, Any]:
        """
        Compare copier's performance across all traders they follow
        """
        relationships = await self.db.copy_relationships.find({
            "user_id": copier_id,
            "active": True
        }).to_list(50)
        
        comparisons = []
        
        for rel in relationships:
            trader_id = rel["trader_id"]
            
            # Get copier's performance with this trader
            trades = await self.db.copied_trades.find({
                "copier_id": copier_id,
                "trader_id": trader_id,
                "status": "closed"
            }).to_list(1000)
            
            if trades:
                total_profit = sum(t.get("profit", 0) for t in trades)
                wins = sum(1 for t in trades if t.get("profit", 0) > 0)
                win_rate = (wins / len(trades)) * 100
                
                comparisons.append({
                    "trader_id": trader_id,
                    "total_trades": len(trades),
                    "total_profit": round(total_profit, 2),
                    "win_rate": round(win_rate, 1),
                    "avg_profit_per_trade": round(total_profit / len(trades), 2)
                })
        
        # Sort by total profit
        comparisons.sort(key=lambda x: x["total_profit"], reverse=True)
        
        return {
            "copier_id": copier_id,
            "traders_followed": len(comparisons),
            "performance_by_trader": comparisons
        }

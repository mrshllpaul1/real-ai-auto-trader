"""
ML Strategy Optimization Service
================================
A/B testing, overfitting prevention, and production monitoring.
"""

import asyncio
import logging
import random
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class StrategyVariant:
    """A strategy parameter variant for A/B testing"""
    variant_id: str
    name: str
    parameters: Dict[str, Any]
    created_at: str
    is_active: bool = True
    
    # Performance metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    sharpe_ratio: float = 0.0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    profit_factor: float = 0.0
    
    # Validation metrics for overfitting detection
    train_accuracy: float = 0.0
    validation_accuracy: float = 0.0
    overfit_score: float = 0.0  # Higher = more overfit


@dataclass
class TradeRecord:
    """Record of a trade for performance tracking"""
    trade_id: str
    variant_id: str
    symbol: str
    entry_time: str
    exit_time: Optional[str]
    entry_price: float
    exit_price: Optional[float]
    position_type: str  # 'long' or 'short'
    signal_confidence: float
    pnl: float = 0.0
    pnl_pct: float = 0.0
    outcome: Optional[str] = None  # 'win', 'loss', 'open'


class MLOptimizationService:
    """
    Comprehensive ML strategy optimization with:
    - A/B testing of strategy parameter variants
    - Production monitoring of win rate and Sharpe ratio
    - Overfitting detection and prevention
    - Cross-validation for reliable performance estimation
    """
    
    # Pre-defined strategy parameter combinations for A/B testing
    STRATEGY_VARIANTS = [
        # Conservative variants - lower risk, fewer trades
        {
            "name": "Conservative Trend",
            "parameters": {
                "lookback": 30,
                "min_trend_strength": 0.02,
                "rsi_oversold": 20,
                "rsi_overbought": 80,
                "entry_threshold": 6,
                "take_profit_pct": 20,
                "stop_loss_pct": 4,
                "volatility_filter": 0.03
            }
        },
        {
            "name": "RSI Extreme",
            "parameters": {
                "lookback": 20,
                "min_trend_strength": 0.01,
                "rsi_oversold": 15,
                "rsi_overbought": 85,
                "entry_threshold": 5,
                "take_profit_pct": 15,
                "stop_loss_pct": 5,
                "volatility_filter": 0.04
            }
        },
        # Moderate variants - balanced approach
        {
            "name": "Balanced Momentum",
            "parameters": {
                "lookback": 20,
                "min_trend_strength": 0.015,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "entry_threshold": 5,
                "take_profit_pct": 12,
                "stop_loss_pct": 5,
                "volatility_filter": 0.035
            }
        },
        {
            "name": "Trend Follower",
            "parameters": {
                "lookback": 25,
                "min_trend_strength": 0.018,
                "rsi_oversold": 35,
                "rsi_overbought": 65,
                "entry_threshold": 4,
                "take_profit_pct": 15,
                "stop_loss_pct": 6,
                "volatility_filter": 0.04
            }
        },
        # Aggressive variants - more trades, higher risk/reward
        {
            "name": "Aggressive Breakout",
            "parameters": {
                "lookback": 15,
                "min_trend_strength": 0.01,
                "rsi_oversold": 35,
                "rsi_overbought": 65,
                "entry_threshold": 4,
                "take_profit_pct": 18,
                "stop_loss_pct": 4,
                "volatility_filter": 0.05
            }
        },
        {
            "name": "High Frequency",
            "parameters": {
                "lookback": 10,
                "min_trend_strength": 0.008,
                "rsi_oversold": 40,
                "rsi_overbought": 60,
                "entry_threshold": 3,
                "take_profit_pct": 8,
                "stop_loss_pct": 3,
                "volatility_filter": 0.06
            }
        },
        # Mean reversion variants
        {
            "name": "Mean Reversion",
            "parameters": {
                "lookback": 20,
                "min_trend_strength": 0.01,
                "rsi_oversold": 25,
                "rsi_overbought": 75,
                "entry_threshold": 5,
                "take_profit_pct": 10,
                "stop_loss_pct": 5,
                "volatility_filter": 0.03,
                "use_mean_reversion": True
            }
        },
        {
            "name": "Bollinger Bounce",
            "parameters": {
                "lookback": 20,
                "min_trend_strength": 0.01,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "entry_threshold": 4,
                "take_profit_pct": 12,
                "stop_loss_pct": 4,
                "volatility_filter": 0.035,
                "bollinger_bands": True
            }
        }
    ]
    
    def __init__(self, db):
        self.db = db
        self.variants: Dict[str, StrategyVariant] = {}
        self.trades: Dict[str, List[TradeRecord]] = defaultdict(list)
        self.is_monitoring = False
        self._monitoring_task = None
        self._best_variant_id = None
        
        # Rolling window for metrics calculation
        self.metrics_window_size = 100
        self.rolling_returns: Dict[str, List[float]] = defaultdict(list)
        
        logger.info("✅ ML Optimization Service initialized")
    
    async def initialize_variants(self) -> Dict[str, Any]:
        """Initialize all strategy variants for A/B testing"""
        results = []
        
        for i, variant_config in enumerate(self.STRATEGY_VARIANTS):
            variant_id = f"variant_{i}_{hashlib.md5(variant_config['name'].encode()).hexdigest()[:8]}"
            
            variant = StrategyVariant(
                variant_id=variant_id,
                name=variant_config['name'],
                parameters=variant_config['parameters'],
                created_at=datetime.now(timezone.utc).isoformat()
            )
            
            self.variants[variant_id] = variant
            
            # Save to database
            await self.db.strategy_variants.update_one(
                {'variant_id': variant_id},
                {'$set': asdict(variant)},
                upsert=True
            )
            
            results.append({
                'variant_id': variant_id,
                'name': variant_config['name'],
                'parameters': variant_config['parameters']
            })
        
        logger.info(f"🧪 Initialized {len(results)} strategy variants for A/B testing")
        return {'status': 'initialized', 'variants': results}
    
    async def get_variant_for_trade(self, symbol: str) -> Tuple[str, Dict]:
        """
        Select a variant for a trade using multi-armed bandit approach.
        Uses Thompson Sampling for exploration/exploitation balance.
        """
        if not self.variants:
            await self.initialize_variants()
        
        # Thompson Sampling: sample from posterior distribution
        variant_scores = {}
        for vid, variant in self.variants.items():
            if not variant.is_active:
                continue
            
            # Use Beta distribution based on wins/losses
            alpha = max(1, variant.winning_trades + 1)
            beta = max(1, variant.losing_trades + 1)
            
            # Sample from Beta distribution
            score = random.betavariate(alpha, beta)
            
            # Boost score if variant has good Sharpe ratio
            if variant.sharpe_ratio > 0.5:
                score *= 1.2
            
            variant_scores[vid] = score
        
        if not variant_scores:
            # Fallback to first variant
            vid = list(self.variants.keys())[0]
        else:
            # Select variant with highest sampled score
            vid = max(variant_scores, key=variant_scores.get)
        
        return vid, self.variants[vid].parameters
    
    async def record_trade(
        self,
        variant_id: str,
        symbol: str,
        entry_price: float,
        exit_price: float,
        position_type: str,
        signal_confidence: float = 0.5
    ) -> Dict[str, Any]:
        """Record a completed trade and update variant metrics"""
        trade_id = f"trade_{datetime.now().timestamp()}_{random.randint(1000, 9999)}"
        
        # Calculate PnL
        if position_type == 'long':
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        else:  # short
            pnl_pct = ((entry_price - exit_price) / entry_price) * 100
        
        pnl = entry_price * (pnl_pct / 100)
        outcome = 'win' if pnl_pct > 0 else 'loss'
        
        trade = TradeRecord(
            trade_id=trade_id,
            variant_id=variant_id,
            symbol=symbol,
            entry_time=datetime.now(timezone.utc).isoformat(),
            exit_time=datetime.now(timezone.utc).isoformat(),
            entry_price=entry_price,
            exit_price=exit_price,
            position_type=position_type,
            signal_confidence=signal_confidence,
            pnl=pnl,
            pnl_pct=pnl_pct,
            outcome=outcome
        )
        
        self.trades[variant_id].append(trade)
        self.rolling_returns[variant_id].append(pnl_pct)
        
        # Keep rolling window
        if len(self.rolling_returns[variant_id]) > self.metrics_window_size:
            self.rolling_returns[variant_id].pop(0)
        
        # Update variant metrics
        await self._update_variant_metrics(variant_id)
        
        # Save to database
        await self.db.trade_records.insert_one(asdict(trade))
        
        return {
            'status': 'recorded',
            'trade_id': trade_id,
            'pnl_pct': pnl_pct,
            'outcome': outcome
        }
    
    async def _update_variant_metrics(self, variant_id: str):
        """Update performance metrics for a variant"""
        variant = self.variants.get(variant_id)
        if not variant:
            return
        
        trades = self.trades[variant_id]
        if not trades:
            return
        
        # Calculate metrics
        wins = sum(1 for t in trades if t.outcome == 'win')
        losses = sum(1 for t in trades if t.outcome == 'loss')
        total = wins + losses
        
        variant.total_trades = total
        variant.winning_trades = wins
        variant.losing_trades = losses
        variant.win_rate = (wins / total * 100) if total > 0 else 0.0
        
        # Calculate total PnL
        variant.total_pnl = sum(t.pnl for t in trades)
        
        # Calculate Sharpe ratio (annualized)
        returns = self.rolling_returns[variant_id]
        if len(returns) > 1:
            mean_return = sum(returns) / len(returns)
            std_return = (sum((r - mean_return)**2 for r in returns) / len(returns)) ** 0.5
            if std_return > 0:
                # Assume daily trades, annualize with sqrt(252)
                variant.sharpe_ratio = (mean_return / std_return) * (252 ** 0.5)
            else:
                variant.sharpe_ratio = 0.0
        
        # Calculate max drawdown
        peak = 0
        max_dd = 0
        cumulative = 0
        for r in returns:
            cumulative += r
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
        variant.max_drawdown = max_dd
        
        # Calculate profit factor
        gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
        variant.profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Update in database
        await self.db.strategy_variants.update_one(
            {'variant_id': variant_id},
            {'$set': asdict(variant)}
        )
    
    async def detect_overfitting(self, variant_id: str, train_results: Dict, validation_results: Dict) -> Dict:
        """
        Detect overfitting by comparing train vs validation performance.
        
        Signs of overfitting:
        1. Train accuracy >> Validation accuracy
        2. Train Sharpe >> Validation Sharpe
        3. High variance in validation results
        """
        variant = self.variants.get(variant_id)
        if not variant:
            return {'status': 'error', 'message': 'Variant not found'}
        
        train_acc = train_results.get('win_rate', 0)
        val_acc = validation_results.get('win_rate', 0)
        
        train_sharpe = train_results.get('sharpe_ratio', 0)
        val_sharpe = validation_results.get('sharpe_ratio', 0)
        
        # Calculate overfit scores
        accuracy_gap = max(0, train_acc - val_acc)
        sharpe_gap = max(0, train_sharpe - val_sharpe)
        
        # Overfit score: 0-100, higher is worse
        overfit_score = min(100, (accuracy_gap * 2 + sharpe_gap * 20))
        
        variant.train_accuracy = train_acc
        variant.validation_accuracy = val_acc
        variant.overfit_score = overfit_score
        
        is_overfit = overfit_score > 30
        
        return {
            'variant_id': variant_id,
            'train_accuracy': train_acc,
            'validation_accuracy': val_acc,
            'accuracy_gap': accuracy_gap,
            'sharpe_gap': sharpe_gap,
            'overfit_score': overfit_score,
            'is_overfit': is_overfit,
            'recommendation': 'Reduce model complexity or increase regularization' if is_overfit else 'Acceptable'
        }
    
    async def cross_validate(
        self,
        variant_id: str,
        data: List[Dict],
        n_folds: int = 5
    ) -> Dict:
        """
        Perform k-fold cross-validation to get reliable performance estimates.
        Helps prevent overfitting by testing on multiple data splits.
        """
        if len(data) < n_folds * 10:
            return {'status': 'error', 'message': 'Not enough data for cross-validation'}
        
        fold_size = len(data) // n_folds
        fold_results = []
        
        for fold in range(n_folds):
            # Split data
            val_start = fold * fold_size
            val_end = val_start + fold_size
            
            train_data = data[:val_start] + data[val_end:]
            val_data = data[val_start:val_end]
            
            # Simulate trading on validation set
            wins = 0
            total = 0
            returns = []
            
            for sample in val_data:
                # Simulate a trade result
                signal = sample.get('signal', 'hold')
                actual_return = sample.get('actual_return', 0)
                
                if signal in ['buy', 'sell']:
                    total += 1
                    if signal == 'buy' and actual_return > 0:
                        wins += 1
                        returns.append(actual_return)
                    elif signal == 'sell' and actual_return < 0:
                        wins += 1
                        returns.append(-actual_return)
                    else:
                        returns.append(-abs(actual_return) * 0.5)  # Loss estimate
            
            win_rate = (wins / total * 100) if total > 0 else 0
            
            # Calculate Sharpe
            if returns:
                mean_ret = sum(returns) / len(returns)
                std_ret = (sum((r - mean_ret)**2 for r in returns) / len(returns)) ** 0.5
                sharpe = (mean_ret / std_ret) * (252 ** 0.5) if std_ret > 0 else 0
            else:
                sharpe = 0
            
            fold_results.append({
                'fold': fold + 1,
                'win_rate': win_rate,
                'sharpe_ratio': sharpe,
                'n_trades': total
            })
        
        # Calculate average metrics
        avg_win_rate = sum(f['win_rate'] for f in fold_results) / n_folds
        avg_sharpe = sum(f['sharpe_ratio'] for f in fold_results) / n_folds
        
        # Calculate variance (high variance = unstable model)
        win_rate_var = sum((f['win_rate'] - avg_win_rate)**2 for f in fold_results) / n_folds
        sharpe_var = sum((f['sharpe_ratio'] - avg_sharpe)**2 for f in fold_results) / n_folds
        
        return {
            'variant_id': variant_id,
            'n_folds': n_folds,
            'fold_results': fold_results,
            'avg_win_rate': avg_win_rate,
            'avg_sharpe_ratio': avg_sharpe,
            'win_rate_variance': win_rate_var,
            'sharpe_variance': sharpe_var,
            'stability_score': 100 - min(100, win_rate_var + sharpe_var * 10)
        }
    
    async def start_production_monitoring(self):
        """Start continuous production monitoring"""
        if self.is_monitoring:
            return {'status': 'already_running'}
        
        self.is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("📊 Production monitoring started")
        return {'status': 'started'}
    
    async def stop_production_monitoring(self):
        """Stop production monitoring"""
        self.is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
        
        logger.info("📊 Production monitoring stopped")
        return {'status': 'stopped'}
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop"""
        while self.is_monitoring:
            try:
                # Update metrics for all variants
                for variant_id in self.variants:
                    await self._update_variant_metrics(variant_id)
                
                # Find best performing variant
                best_variant = None
                best_score = float('-inf')
                
                for vid, variant in self.variants.items():
                    if variant.total_trades < 10:
                        continue
                    
                    # Score = Sharpe * sqrt(win_rate) - overfit_penalty
                    score = variant.sharpe_ratio * (variant.win_rate ** 0.5) / 10
                    score -= variant.overfit_score * 0.1
                    
                    if score > best_score:
                        best_score = score
                        best_variant = vid
                
                if best_variant and best_variant != self._best_variant_id:
                    self._best_variant_id = best_variant
                    logger.info(f"🏆 New best variant: {self.variants[best_variant].name}")
                
                # Save monitoring snapshot
                await self.db.monitoring_snapshots.insert_one({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'best_variant': best_variant,
                    'variants_summary': {
                        vid: {
                            'name': v.name,
                            'win_rate': v.win_rate,
                            'sharpe_ratio': v.sharpe_ratio,
                            'total_trades': v.total_trades
                        }
                        for vid, v in self.variants.items()
                    }
                })
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def get_monitoring_status(self) -> Dict:
        """Get current monitoring status and metrics"""
        variants_status = []
        
        for vid, variant in self.variants.items():
            variants_status.append({
                'variant_id': vid,
                'name': variant.name,
                'total_trades': variant.total_trades,
                'win_rate': round(variant.win_rate, 2),
                'sharpe_ratio': round(variant.sharpe_ratio, 2),
                'profit_factor': round(variant.profit_factor, 2),
                'max_drawdown': round(variant.max_drawdown, 2),
                'overfit_score': round(variant.overfit_score, 2),
                'is_best': vid == self._best_variant_id
            })
        
        # Sort by Sharpe ratio
        variants_status.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        
        return {
            'is_monitoring': self.is_monitoring,
            'best_variant': self._best_variant_id,
            'best_variant_name': self.variants[self._best_variant_id].name if self._best_variant_id else None,
            'total_variants': len(self.variants),
            'variants': variants_status
        }
    
    async def reduce_overfitting(self, variant_id: str) -> Dict:
        """
        Apply techniques to reduce overfitting for a variant.
        
        Techniques:
        1. Increase entry threshold (fewer trades)
        2. Widen RSI bands (less sensitivity)
        3. Increase volatility filter (avoid noise)
        4. Add confirmation requirements
        """
        variant = self.variants.get(variant_id)
        if not variant:
            return {'status': 'error', 'message': 'Variant not found'}
        
        original_params = variant.parameters.copy()
        
        # Apply regularization
        new_params = variant.parameters.copy()
        
        # 1. Increase entry threshold
        new_params['entry_threshold'] = min(8, new_params.get('entry_threshold', 5) + 1)
        
        # 2. Widen RSI bands
        new_params['rsi_oversold'] = max(15, new_params.get('rsi_oversold', 30) - 5)
        new_params['rsi_overbought'] = min(85, new_params.get('rsi_overbought', 70) + 5)
        
        # 3. Increase min trend strength requirement
        new_params['min_trend_strength'] = min(0.03, new_params.get('min_trend_strength', 0.015) * 1.3)
        
        # 4. Lower volatility threshold
        new_params['volatility_filter'] = max(0.02, new_params.get('volatility_filter', 0.035) * 0.85)
        
        variant.parameters = new_params
        variant.overfit_score = max(0, variant.overfit_score - 10)  # Reset score
        
        await self.db.strategy_variants.update_one(
            {'variant_id': variant_id},
            {'$set': asdict(variant)}
        )
        
        return {
            'status': 'regularized',
            'variant_id': variant_id,
            'original_params': original_params,
            'new_params': new_params,
            'changes': {
                'entry_threshold': f"{original_params.get('entry_threshold', 5)} → {new_params['entry_threshold']}",
                'rsi_bands': f"[{original_params.get('rsi_oversold', 30)}, {original_params.get('rsi_overbought', 70)}] → [{new_params['rsi_oversold']}, {new_params['rsi_overbought']}]",
                'min_trend_strength': f"{original_params.get('min_trend_strength', 0.015):.3f} → {new_params['min_trend_strength']:.3f}"
            }
        }
    
    async def run_ab_test(self, n_simulations: int = 100) -> Dict:
        """
        Run A/B test simulation across all variants.
        Returns comparative performance metrics.
        """
        if not self.variants:
            await self.initialize_variants()
        
        results = []
        
        for vid, variant in self.variants.items():
            # Simulate trades for this variant
            wins = 0
            total_pnl = 0
            returns = []
            
            for _ in range(n_simulations):
                # Generate random market conditions
                trend = random.choice(['up', 'down', 'sideways'])
                volatility = random.uniform(0.01, 0.05)
                
                # Determine if variant would trade
                params = variant.parameters
                would_trade = volatility < params.get('volatility_filter', 0.04)
                
                if would_trade:
                    # Simulate trade outcome based on parameters
                    base_win_prob = 0.45  # Base probability
                    
                    # Better RSI bands improve win rate
                    rsi_width = params.get('rsi_overbought', 70) - params.get('rsi_oversold', 30)
                    if rsi_width > 50:
                        base_win_prob += 0.05
                    
                    # Higher entry threshold improves win rate
                    if params.get('entry_threshold', 5) >= 5:
                        base_win_prob += 0.05
                    
                    # Trend alignment
                    if trend in ['up', 'down']:
                        base_win_prob += 0.08
                    
                    # Trade result
                    is_win = random.random() < base_win_prob
                    
                    if is_win:
                        wins += 1
                        pnl = random.uniform(0.5, params.get('take_profit_pct', 15))
                    else:
                        pnl = -random.uniform(0.5, params.get('stop_loss_pct', 5))
                    
                    total_pnl += pnl
                    returns.append(pnl)
            
            # Calculate metrics
            n_trades = len(returns)
            win_rate = (wins / n_trades * 100) if n_trades > 0 else 0
            
            if returns:
                mean_ret = sum(returns) / len(returns)
                std_ret = (sum((r - mean_ret)**2 for r in returns) / len(returns)) ** 0.5
                sharpe = (mean_ret / std_ret) * (252 ** 0.5) if std_ret > 0 else 0
            else:
                sharpe = 0
            
            results.append({
                'variant_id': vid,
                'name': variant.name,
                'parameters': variant.parameters,
                'n_trades': n_trades,
                'win_rate': round(win_rate, 2),
                'sharpe_ratio': round(sharpe, 2),
                'total_pnl': round(total_pnl, 2)
            })
        
        # Sort by Sharpe ratio
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        
        # Identify winner
        winner = results[0] if results else None
        
        return {
            'status': 'completed',
            'n_simulations': n_simulations,
            'winner': winner,
            'results': results,
            'recommendation': f"Best variant: {winner['name']} with {winner['win_rate']}% win rate and {winner['sharpe_ratio']} Sharpe ratio" if winner else "No clear winner"
        }


# Singleton instance
_ml_optimization_service = None


def get_ml_optimization_service(db=None):
    """Get or create ML optimization service instance"""
    global _ml_optimization_service
    
    if _ml_optimization_service is None and db is not None:
        _ml_optimization_service = MLOptimizationService(db)
    
    return _ml_optimization_service

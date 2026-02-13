"""
Performance Tracking & Auto-Tuning System
Tracks trading performance, regime prediction accuracy, and auto-tunes parameters.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import numpy as np
from collections import defaultdict


class PerformanceTracker:
    """
    Comprehensive performance tracking system that:
    1. Tracks trade outcomes and P&L
    2. Tracks regime prediction accuracy
    3. Tracks strategy parameter effectiveness
    4. Auto-tunes parameters based on performance
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = "performance_metrics"
        
        # Performance windows
        self.windows = {
            'short': 7,      # 7 days
            'medium': 30,    # 30 days
            'long': 90       # 90 days
        }
        
        # Parameter learning rates
        self.learning_rate = 0.1
        
        # Performance thresholds for auto-tuning
        self.thresholds = {
            'min_accuracy_for_increase': 65,  # Increase exposure if >65% accuracy
            'max_accuracy_for_decrease': 45,  # Decrease exposure if <45% accuracy
            'min_trades_for_tuning': 10,      # Need at least 10 trades to tune
        }
    
    async def record_trade_outcome(
        self,
        trade_id: str,
        coin_id: str,
        entry_price: float,
        exit_price: float,
        position_size: float,
        regime_at_entry: str,
        regime_at_exit: str,
        hold_hours: float,
        exit_reason: str,
        strategy_params: Dict[str, float]
    ) -> Dict[str, Any]:
        """Record a completed trade and its outcome"""
        
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        pnl_usd = position_size * (pnl_pct / 100)
        is_win = pnl_pct > 0
        
        outcome = {
            'trade_id': trade_id,
            'coin_id': coin_id,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'position_size': position_size,
            'pnl_pct': round(pnl_pct, 2),
            'pnl_usd': round(pnl_usd, 2),
            'is_win': is_win,
            'regime_at_entry': regime_at_entry,
            'regime_at_exit': regime_at_exit,
            'regime_changed': regime_at_entry != regime_at_exit,
            'hold_hours': hold_hours,
            'exit_reason': exit_reason,
            'strategy_params': strategy_params,
            'recorded_at': datetime.now(timezone.utc)
        }
        
        await self.db.trade_outcomes.insert_one(outcome)
        outcome.pop('_id', None)
        
        return outcome
    
    async def record_regime_prediction(
        self,
        predicted_regime: str,
        actual_regime: str,
        confidence: float,
        model_used: str,
        features_used: Dict[str, float]
    ) -> Dict[str, Any]:
        """Record a regime prediction for accuracy tracking"""
        
        is_correct = predicted_regime == actual_regime
        
        prediction = {
            'predicted_regime': predicted_regime,
            'actual_regime': actual_regime,
            'is_correct': is_correct,
            'confidence': confidence,
            'model_used': model_used,
            'features_used': features_used,
            'recorded_at': datetime.now(timezone.utc)
        }
        
        await self.db.regime_predictions.insert_one(prediction)
        prediction.pop('_id', None)
        
        return prediction
    
    async def get_trading_performance(self, days: int = 30) -> Dict[str, Any]:
        """Get trading performance metrics for the specified period"""
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        outcomes = await self.db.trade_outcomes.find(
            {'recorded_at': {'$gte': cutoff}},
            {'_id': 0}
        ).to_list(1000)
        
        if not outcomes:
            return {
                'period_days': days,
                'total_trades': 0,
                'message': 'No trades in this period'
            }
        
        # Calculate metrics
        wins = [o for o in outcomes if o['is_win']]
        losses = [o for o in outcomes if not o['is_win']]
        
        total_pnl = sum(o['pnl_usd'] for o in outcomes)
        avg_pnl_pct = np.mean([o['pnl_pct'] for o in outcomes])
        
        # Win rate
        win_rate = (len(wins) / len(outcomes)) * 100 if outcomes else 0
        
        # Average win/loss
        avg_win = np.mean([o['pnl_pct'] for o in wins]) if wins else 0
        avg_loss = np.mean([o['pnl_pct'] for o in losses]) if losses else 0
        
        # Profit factor
        gross_profit = sum(o['pnl_usd'] for o in wins)
        gross_loss = abs(sum(o['pnl_usd'] for o in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Sharpe ratio approximation
        returns = [o['pnl_pct'] for o in outcomes]
        sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(365/days) if len(returns) > 1 and np.std(returns) > 0 else 0
        
        # Performance by regime
        by_regime = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0})
        for o in outcomes:
            regime = o['regime_at_entry']
            by_regime[regime]['pnl'] += o['pnl_usd']
            if o['is_win']:
                by_regime[regime]['wins'] += 1
            else:
                by_regime[regime]['losses'] += 1
        
        regime_stats = {}
        for regime, stats in by_regime.items():
            total = stats['wins'] + stats['losses']
            regime_stats[regime] = {
                'trades': total,
                'win_rate': (stats['wins'] / total * 100) if total > 0 else 0,
                'pnl': round(stats['pnl'], 2)
            }
        
        # Best and worst trades
        sorted_outcomes = sorted(outcomes, key=lambda x: x['pnl_pct'], reverse=True)
        
        return {
            'period_days': days,
            'total_trades': len(outcomes),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': round(win_rate, 1),
            'total_pnl_usd': round(total_pnl, 2),
            'avg_pnl_pct': round(avg_pnl_pct, 2),
            'avg_win_pct': round(avg_win, 2),
            'avg_loss_pct': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'sharpe_ratio': round(sharpe, 2),
            'by_regime': regime_stats,
            'best_trade': {
                'coin': sorted_outcomes[0]['coin_id'],
                'pnl_pct': sorted_outcomes[0]['pnl_pct']
            } if sorted_outcomes else None,
            'worst_trade': {
                'coin': sorted_outcomes[-1]['coin_id'],
                'pnl_pct': sorted_outcomes[-1]['pnl_pct']
            } if sorted_outcomes else None
        }
    
    async def get_regime_prediction_accuracy(self, days: int = 30) -> Dict[str, Any]:
        """Get regime prediction accuracy metrics"""
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        predictions = await self.db.regime_predictions.find(
            {'recorded_at': {'$gte': cutoff}},
            {'_id': 0}
        ).to_list(1000)
        
        if not predictions:
            return {
                'period_days': days,
                'total_predictions': 0,
                'message': 'No predictions in this period'
            }
        
        # Overall accuracy
        correct = [p for p in predictions if p['is_correct']]
        accuracy = (len(correct) / len(predictions)) * 100
        
        # Accuracy by model
        by_model = defaultdict(lambda: {'correct': 0, 'total': 0, 'avg_confidence': []})
        for p in predictions:
            model = p['model_used']
            by_model[model]['total'] += 1
            by_model[model]['avg_confidence'].append(p['confidence'])
            if p['is_correct']:
                by_model[model]['correct'] += 1
        
        model_stats = {}
        for model, stats in by_model.items():
            model_stats[model] = {
                'predictions': stats['total'],
                'accuracy': round((stats['correct'] / stats['total']) * 100, 1),
                'avg_confidence': round(np.mean(stats['avg_confidence']), 1)
            }
        
        # Find best model
        best_model = max(model_stats.items(), key=lambda x: x[1]['accuracy']) if model_stats else None
        
        # Accuracy by predicted regime
        by_regime = defaultdict(lambda: {'correct': 0, 'total': 0})
        for p in predictions:
            regime = p['predicted_regime']
            by_regime[regime]['total'] += 1
            if p['is_correct']:
                by_regime[regime]['correct'] += 1
        
        regime_accuracy = {
            regime: round((stats['correct'] / stats['total']) * 100, 1)
            for regime, stats in by_regime.items()
        }
        
        return {
            'period_days': days,
            'total_predictions': len(predictions),
            'correct_predictions': len(correct),
            'overall_accuracy': round(accuracy, 1),
            'by_model': model_stats,
            'best_model': {
                'name': best_model[0],
                'accuracy': best_model[1]['accuracy']
            } if best_model else None,
            'by_regime': regime_accuracy
        }
    
    async def get_parameter_effectiveness(self, days: int = 30) -> Dict[str, Any]:
        """Analyze which parameter settings performed best"""
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        outcomes = await self.db.trade_outcomes.find(
            {'recorded_at': {'$gte': cutoff}},
            {'_id': 0}
        ).to_list(1000)
        
        if len(outcomes) < 5:
            return {
                'period_days': days,
                'message': 'Not enough trades for parameter analysis'
            }
        
        # Analyze correlation between parameters and outcomes
        param_analysis = {}
        
        # Group by stop loss ranges
        sl_buckets = {'tight': [], 'medium': [], 'wide': []}
        for o in outcomes:
            sl = o.get('strategy_params', {}).get('stop_loss_pct', 15)
            if sl <= 10:
                sl_buckets['tight'].append(o['pnl_pct'])
            elif sl <= 18:
                sl_buckets['medium'].append(o['pnl_pct'])
            else:
                sl_buckets['wide'].append(o['pnl_pct'])
        
        param_analysis['stop_loss'] = {
            bucket: {
                'trades': len(trades),
                'avg_pnl': round(np.mean(trades), 2) if trades else 0,
                'win_rate': round(len([t for t in trades if t > 0]) / len(trades) * 100, 1) if trades else 0
            }
            for bucket, trades in sl_buckets.items()
        }
        
        # Group by position size
        pos_buckets = {'small': [], 'medium': [], 'large': []}
        for o in outcomes:
            pos = o.get('position_size', 0)
            if pos <= 500:
                pos_buckets['small'].append(o['pnl_pct'])
            elif pos <= 1200:
                pos_buckets['medium'].append(o['pnl_pct'])
            else:
                pos_buckets['large'].append(o['pnl_pct'])
        
        param_analysis['position_size'] = {
            bucket: {
                'trades': len(trades),
                'avg_pnl': round(np.mean(trades), 2) if trades else 0
            }
            for bucket, trades in pos_buckets.items()
        }
        
        # Optimal parameters suggestion
        best_sl = max(param_analysis['stop_loss'].items(), 
                      key=lambda x: x[1]['avg_pnl'] if x[1]['trades'] >= 3 else -999)
        
        return {
            'period_days': days,
            'total_trades_analyzed': len(outcomes),
            'parameter_analysis': param_analysis,
            'recommendations': {
                'stop_loss': f"{best_sl[0]} stops performed best ({best_sl[1]['avg_pnl']}% avg PnL)"
            }
        }
    
    async def suggest_parameter_adjustments(self) -> Dict[str, Any]:
        """Suggest parameter adjustments based on recent performance"""
        
        # Get recent performance
        perf_7d = await self.get_trading_performance(7)
        perf_30d = await self.get_trading_performance(30)
        regime_acc = await self.get_regime_prediction_accuracy(30)
        
        suggestions = []
        adjustments = {}
        
        # Check if we have enough data
        if perf_30d.get('total_trades', 0) < self.thresholds['min_trades_for_tuning']:
            return {
                'suggestions': ['Not enough trades for auto-tuning'],
                'adjustments': {},
                'data_quality': 'insufficient'
            }
        
        # Win rate based adjustments
        win_rate = perf_30d.get('win_rate', 50)
        
        if win_rate > self.thresholds['min_accuracy_for_increase']:
            # Performing well - can increase exposure
            adjustments['max_position_pct'] = '+10%'
            adjustments['min_confidence'] = '-5%'
            suggestions.append(f"Win rate {win_rate}% > 65%: Increase position sizes")
        elif win_rate < self.thresholds['max_accuracy_for_decrease']:
            # Performing poorly - reduce exposure
            adjustments['max_position_pct'] = '-15%'
            adjustments['min_confidence'] = '+10%'
            adjustments['stop_loss_pct'] = '-3%'
            suggestions.append(f"Win rate {win_rate}% < 45%: Reduce exposure, tighten stops")
        
        # Regime-specific adjustments
        regime_stats = perf_30d.get('by_regime', {})
        for regime, stats in regime_stats.items():
            if stats['trades'] >= 5:
                if stats['win_rate'] < 40:
                    suggestions.append(f"Poor performance in {regime} regime ({stats['win_rate']}% win rate) - reduce exposure")
                elif stats['win_rate'] > 70:
                    suggestions.append(f"Strong performance in {regime} regime ({stats['win_rate']}% win rate) - can increase exposure")
        
        # Model accuracy adjustments
        if regime_acc.get('overall_accuracy', 0) < 50:
            suggestions.append("Regime prediction accuracy < 50% - rely more on base strategy")
        
        # Recent vs longer term comparison
        if perf_7d.get('win_rate', 50) < perf_30d.get('win_rate', 50) - 15:
            suggestions.append("Recent 7-day performance declining - consider defensive mode")
        
        return {
            'performance_7d': {
                'win_rate': perf_7d.get('win_rate'),
                'trades': perf_7d.get('total_trades')
            },
            'performance_30d': {
                'win_rate': perf_30d.get('win_rate'),
                'trades': perf_30d.get('total_trades'),
                'sharpe': perf_30d.get('sharpe_ratio')
            },
            'regime_accuracy': regime_acc.get('overall_accuracy'),
            'best_model': regime_acc.get('best_model'),
            'suggestions': suggestions,
            'adjustments': adjustments,
            'data_quality': 'sufficient'
        }


# Global instance
_performance_tracker = None


def get_performance_tracker(db: AsyncIOMotorDatabase = None) -> PerformanceTracker:
    """Get or create performance tracker instance"""
    global _performance_tracker
    if _performance_tracker is None and db is not None:
        _performance_tracker = PerformanceTracker(db)
    return _performance_tracker

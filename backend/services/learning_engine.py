import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
import pickle
import os

class AILearningEngine:
    """
    Advanced learning engine that improves AI predictions based on historical performance.
    Implements reinforcement learning principles to optimize trading strategies.
    """
    
    def __init__(self, db):
        self.db = db
        self.model_path = '/app/backend/models/'
        os.makedirs(self.model_path, exist_ok=True)
        self.performance_weight = 0.7
        self.accuracy_weight = 0.3
    
    async def record_strategy_outcome(
        self,
        strategy_id: str,
        predicted_action: str,
        actual_outcome: str,
        profit_loss: float,
        confidence_score: float
    ):
        """Record the outcome of a strategy prediction for learning"""
        outcome_record = {
            "strategy_id": strategy_id,
            "predicted_action": predicted_action,
            "actual_outcome": actual_outcome,
            "profit_loss": profit_loss,
            "confidence_score": confidence_score,
            "was_correct": predicted_action == actual_outcome,
            "recorded_at": datetime.now().isoformat(),
            "performance_score": self._calculate_performance_score(profit_loss, confidence_score)
        }
        
        await self.db.learning_outcomes.insert_one(outcome_record)
        
        # Update strategy learning metrics
        await self._update_strategy_learning_metrics(strategy_id)
    
    def _calculate_performance_score(self, profit_loss: float, confidence_score: float) -> float:
        """Calculate performance score for a prediction"""
        # Normalize profit/loss to -1 to 1 range
        normalized_pl = np.tanh(profit_loss / 100)
        
        # Weight by confidence (higher confidence errors are penalized more)
        confidence_factor = confidence_score / 100
        
        return normalized_pl * (1 + confidence_factor)
    
    async def _update_strategy_learning_metrics(self, strategy_id: str):
        """Update learning metrics for a strategy"""
        # Get all outcomes for this strategy
        outcomes = await self.db.learning_outcomes.find(
            {"strategy_id": strategy_id}
        ).to_list(1000)
        
        if not outcomes:
            return
        
        # Calculate metrics
        total_outcomes = len(outcomes)
        correct_predictions = sum(1 for o in outcomes if o['was_correct'])
        accuracy = (correct_predictions / total_outcomes) * 100
        
        avg_performance = sum(o['performance_score'] for o in outcomes) / total_outcomes
        total_profit_loss = sum(o['profit_loss'] for o in outcomes)
        
        # Calculate learning-adjusted confidence
        base_confidence = outcomes[-1]['confidence_score']
        learned_confidence = self._adjust_confidence(
            base_confidence,
            accuracy,
            avg_performance
        )
        
        learning_metrics = {
            "strategy_id": strategy_id,
            "total_predictions": total_outcomes,
            "accuracy": accuracy,
            "avg_performance_score": avg_performance,
            "total_profit_loss": total_profit_loss,
            "learned_confidence": learned_confidence,
            "last_updated": datetime.now().isoformat()
        }
        
        await self.db.strategy_learning_metrics.update_one(
            {"strategy_id": strategy_id},
            {"$set": learning_metrics},
            upsert=True
        )
    
    def _adjust_confidence(self, base_confidence: float, accuracy: float, performance: float) -> float:
        """Adjust confidence based on historical accuracy and performance"""
        accuracy_factor = (accuracy / 100)
        performance_factor = (performance + 1) / 2  # Normalize to 0-1
        
        adjustment = (
            self.accuracy_weight * accuracy_factor +
            self.performance_weight * performance_factor
        )
        
        # Adjust base confidence
        learned_confidence = base_confidence * adjustment
        
        # Clamp between 0 and 100
        return max(0, min(100, learned_confidence))
    
    async def get_learning_insights(self, strategy_id: str) -> Dict[str, Any]:
        """Get learning insights for a strategy"""
        metrics = await self.db.strategy_learning_metrics.find_one(
            {"strategy_id": strategy_id},
            {"_id": 0}
        )
        
        if not metrics:
            return {
                "has_learning_data": False,
                "message": "No learning data available yet"
            }
        
        # Get recent performance trend
        recent_outcomes = await self.db.learning_outcomes.find(
            {"strategy_id": strategy_id}
        ).sort("recorded_at", -1).limit(10).to_list(10)
        
        if recent_outcomes:
            recent_accuracy = sum(1 for o in recent_outcomes if o['was_correct']) / len(recent_outcomes) * 100
            recent_avg_pl = sum(o['profit_loss'] for o in recent_outcomes) / len(recent_outcomes)
            
            # Determine trend
            if len(recent_outcomes) >= 5:
                first_half_pl = sum(o['profit_loss'] for o in recent_outcomes[:5]) / 5
                second_half_pl = sum(o['profit_loss'] for o in recent_outcomes[5:]) / len(recent_outcomes[5:])
                trend = "improving" if second_half_pl > first_half_pl else "declining"
            else:
                trend = "insufficient_data"
        else:
            recent_accuracy = 0
            recent_avg_pl = 0
            trend = "no_data"
        
        return {
            "has_learning_data": True,
            "overall_metrics": metrics,
            "recent_performance": {
                "accuracy": recent_accuracy,
                "avg_profit_loss": recent_avg_pl,
                "trend": trend
            },
            "learning_status": self._get_learning_status(metrics['accuracy'], metrics['total_predictions'])
        }
    
    def _get_learning_status(self, accuracy: float, total_predictions: int) -> str:
        """Determine learning status"""
        if total_predictions < 5:
            return "gathering_data"
        elif total_predictions < 20:
            return "early_learning"
        elif accuracy >= 70:
            return "well_trained"
        elif accuracy >= 50:
            return "moderately_trained"
        else:
            return "needs_improvement"
    
    async def get_best_performing_indicators(self) -> List[Dict[str, Any]]:
        """Analyze which technical indicators perform best"""
        # Get all outcomes with indicator data
        outcomes = await self.db.learning_outcomes.find({}).to_list(1000)
        
        if len(outcomes) < 10:
            return []
        
        # Batch fetch all strategies to avoid N+1 queries
        strategy_ids = list(set(o.get('strategy_id') for o in outcomes if o.get('strategy_id')))
        strategies_list = await self.db.strategies.find(
            {'strategy_id': {'$in': strategy_ids}},
            {'_id': 0, 'strategy_id': 1, 'indicators': 1}
        ).to_list(len(strategy_ids))
        strategy_map = {s['strategy_id']: s for s in strategies_list}
        
        # Analyze indicator performance
        indicator_performance = {}
        
        for outcome in outcomes:
            strategy = strategy_map.get(outcome.get('strategy_id'))
            
            if not strategy or 'indicators' not in strategy:
                continue
            
            indicators = strategy.get('indicators', {})
            
            for indicator_name, indicator_value in indicators.items():
                if indicator_name not in indicator_performance:
                    indicator_performance[indicator_name] = {
                        "total_uses": 0,
                        "correct_predictions": 0,
                        "total_profit": 0
                    }
                
                indicator_performance[indicator_name]['total_uses'] += 1
                if outcome.get('was_correct'):
                    indicator_performance[indicator_name]['correct_predictions'] += 1
                indicator_performance[indicator_name]['total_profit'] += outcome.get('profit_loss', 0)
        
        # Calculate scores
        results = []
        for indicator_name, stats in indicator_performance.items():
            if stats['total_uses'] > 0:
                accuracy = (stats['correct_predictions'] / stats['total_uses']) * 100
                avg_profit = stats['total_profit'] / stats['total_uses']
                
                results.append({
                    "indicator": indicator_name,
                    "accuracy": accuracy,
                    "avg_profit_per_use": avg_profit,
                    "total_uses": stats['total_uses'],
                    "effectiveness_score": (accuracy * 0.6) + (avg_profit * 0.4)
                })
        
        # Sort by effectiveness
        results.sort(key=lambda x: x['effectiveness_score'], reverse=True)
        return results[:10]
    
    async def optimize_strategy_weights(self, coin_id: str) -> Dict[str, float]:
        """Use learning data to optimize indicator weights for a coin"""
        # Get historical performance data
        strategies = await self.db.strategies.find({"coin_id": coin_id}).to_list(100)
        
        if len(strategies) < 5:
            # Return default weights
            return {
                "rsi_weight": 0.25,
                "macd_weight": 0.25,
                "bb_weight": 0.20,
                "ma_weight": 0.20,
                "adx_weight": 0.10
            }
        
        # Analyze which indicators worked best
        best_indicators = await self.get_best_performing_indicators()
        
        # Create optimized weights
        weights = {
            "rsi_weight": 0.20,
            "macd_weight": 0.20,
            "bb_weight": 0.20,
            "ma_weight": 0.20,
            "adx_weight": 0.20
        }
        
        if best_indicators:
            total_effectiveness = sum(ind['effectiveness_score'] for ind in best_indicators[:5])
            
            for ind in best_indicators[:5]:
                indicator_key = f"{ind['indicator'].lower()}_weight"
                if indicator_key in weights:
                    # Redistribute weight based on effectiveness
                    weights[indicator_key] = (ind['effectiveness_score'] / total_effectiveness)
        
        return weights
    
    async def continuous_learning_update(self):
        """Periodic learning update - run this regularly to improve the AI"""
        print("🧠 Running continuous learning update...")
        
        # Get all active strategies
        strategies = await self.db.strategies.find({"status": "active"}).to_list(100)
        
        for strategy in strategies:
            strategy_id = strategy['strategy_id']
            
            # Get recent trades for this strategy
            recent_trades = await self.db.trades.find({
                "strategy_id": strategy_id,
                "created_at": {"$gte": (datetime.now() - timedelta(days=7)).isoformat()}
            }).to_list(100)
            
            # Record outcomes
            for trade in recent_trades:
                # Simulate outcome calculation (in production, use actual market data)
                profit_loss = trade.get('amount', 0) * (np.random.randn() * 0.05)  # Placeholder
                actual_outcome = "BUY" if profit_loss > 0 else "SELL"
                
                await self.record_strategy_outcome(
                    strategy_id=strategy_id,
                    predicted_action=strategy.get('technical_signal', 'HOLD'),
                    actual_outcome=actual_outcome,
                    profit_loss=profit_loss,
                    confidence_score=strategy.get('confidence_score', 50)
                )
        
        print("✅ Continuous learning update complete")
    
    async def generate_learning_report(self) -> Dict[str, Any]:
        """Generate comprehensive learning report"""
        total_strategies = await self.db.strategies.count_documents({})
        total_outcomes = await self.db.learning_outcomes.count_documents({})
        
        # Overall accuracy - fetch only required fields
        all_outcomes = await self.db.learning_outcomes.find(
            {},
            {'_id': 0, 'was_correct': 1, 'profit_loss': 1}
        ).to_list(10000)
        
        overall_accuracy = (
            sum(1 for o in all_outcomes if o.get('was_correct')) / len(all_outcomes) * 100
            if all_outcomes else 0
        )
        
        # Total profit/loss from learning
        total_learned_pl = sum(o.get('profit_loss', 0) for o in all_outcomes) if all_outcomes else 0
        
        # Best performing indicators
        best_indicators = await self.get_best_performing_indicators()
        
        return {
            "total_strategies_evaluated": total_strategies,
            "total_learning_samples": total_outcomes,
            "overall_accuracy": overall_accuracy,
            "total_learned_profit_loss": total_learned_pl,
            "best_performing_indicators": best_indicators[:5],
            "learning_system_status": "active" if total_outcomes > 0 else "initializing",
            "generated_at": datetime.now().isoformat()
        }

import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json
import os

class AILearningEngine:
    """
    Advanced learning engine that improves AI predictions based on historical performance.
    Uses statistical methods and rule-based learning for trading strategy optimization.
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
        # Normalize profit/loss to -1 to 1 range using tanh
        normalized_pl = float(np.tanh(profit_loss / 100))
        
        # Weight by confidence
        weighted_score = normalized_pl * (confidence_score / 100)
        
        return weighted_score
    
    async def _update_strategy_learning_metrics(self, strategy_id: str):
        """Update learning metrics for a strategy using aggregation pipeline"""
        # Use MongoDB aggregation for efficient computation
        pipeline = [
            {"$match": {"strategy_id": strategy_id}},
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "correct": {"$sum": {"$cond": ["$was_correct", 1, 0]}},
                "total_profit": {"$sum": "$profit_loss"},
                "avg_performance": {"$avg": "$performance_score"}
            }}
        ]
        
        result = await self.db.learning_outcomes.aggregate(pipeline).to_list(1)
        
        if not result:
            return
        
        data = result[0]
        total = data.get('total', 0)
        correct = data.get('correct', 0)
        total_profit = data.get('total_profit', 0)
        avg_performance = data.get('avg_performance', 0)
        
        metrics = {
            "strategy_id": strategy_id,
            "total_predictions": total,
            "correct_predictions": correct,
            "accuracy": (correct / total * 100) if total > 0 else 0,
            "total_profit_loss": total_profit,
            "average_performance": avg_performance,
            "updated_at": datetime.now().isoformat()
        }
        
        await self.db.strategy_learning_metrics.update_one(
            {"strategy_id": strategy_id},
            {"$set": metrics},
            upsert=True
        )
    
    async def get_learned_confidence_adjustment(self, strategy_id: str, base_confidence: float) -> float:
        """Get confidence adjustment based on historical learning"""
        metrics = await self.db.strategy_learning_metrics.find_one(
            {"strategy_id": strategy_id},
            {"_id": 0}
        )
        
        if not metrics or metrics.get('total_predictions', 0) < 5:
            return base_confidence
        
        accuracy = metrics.get('accuracy', 50)
        performance = metrics.get('average_performance', 0)
        
        # Calculate adjustment factor
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
            {"strategy_id": strategy_id},
            {"_id": 0, "was_correct": 1, "profit_loss": 1}
        ).sort("recorded_at", -1).limit(10).to_list(10)
        
        if recent_outcomes:
            recent_accuracy = sum(1 for o in recent_outcomes if o.get('was_correct', False)) / len(recent_outcomes) * 100
            recent_avg_pl = sum(o.get('profit_loss', 0) for o in recent_outcomes) / len(recent_outcomes)
            
            # Determine trend
            if len(recent_outcomes) >= 5:
                first_half_pl = sum(o.get('profit_loss', 0) for o in recent_outcomes[:5]) / 5
                second_half_pl = sum(o.get('profit_loss', 0) for o in recent_outcomes[5:]) / max(1, len(recent_outcomes[5:]))
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
            "learning_status": self._get_learning_status(metrics.get('accuracy', 0), metrics.get('total_predictions', 0))
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
        """Analyze which technical indicators perform best using aggregation"""
        # Use aggregation to limit data processing
        pipeline = [
            {"$sort": {"recorded_at": -1}},
            {"$limit": 500},  # Reduced from 1000 to 500 for better performance
            {"$project": {
                "_id": 0,
                "strategy_id": 1,
                "was_correct": 1,
                "profit_loss": 1
            }}
        ]
        
        outcomes = await self.db.learning_outcomes.aggregate(pipeline).to_list(500)
        
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
        ranked_indicators = []
        for name, perf in indicator_performance.items():
            if perf['total_uses'] < 5:
                continue
            
            accuracy = (perf['correct_predictions'] / perf['total_uses']) * 100
            avg_profit = perf['total_profit'] / perf['total_uses']
            
            # Simple weighted score without ML
            score = (accuracy * 0.6) + (max(-100, min(100, avg_profit)) * 0.4)
            
            ranked_indicators.append({
                "indicator": name,
                "accuracy": accuracy,
                "avg_profit": avg_profit,
                "total_uses": perf['total_uses'],
                "score": score
            })
        
        return sorted(ranked_indicators, key=lambda x: x['score'], reverse=True)
    
    async def generate_learning_report(self) -> Dict[str, Any]:
        """Generate comprehensive learning report"""
        total_strategies = await self.db.strategies.count_documents({})
        total_outcomes = await self.db.learning_outcomes.count_documents({})
        
        # Overall accuracy - fetch only required fields with limit
        all_outcomes = await self.db.learning_outcomes.find(
            {},
            {'_id': 0, 'was_correct': 1, 'profit_loss': 1}
        ).limit(10000).to_list(10000)
        
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
    
    async def save_learning_state(self):
        """Save current learning state to file (JSON instead of pickle)"""
        state = {
            "performance_weight": self.performance_weight,
            "accuracy_weight": self.accuracy_weight,
            "saved_at": datetime.now().isoformat()
        }
        
        state_path = os.path.join(self.model_path, 'learning_state.json')
        with open(state_path, 'w') as f:
            json.dump(state, f)
    
    async def load_learning_state(self):
        """Load learning state from file"""
        state_path = os.path.join(self.model_path, 'learning_state.json')
        if os.path.exists(state_path):
            with open(state_path, 'r') as f:
                state = json.load(f)
                self.performance_weight = state.get('performance_weight', 0.7)
                self.accuracy_weight = state.get('accuracy_weight', 0.3)

    async def continuous_learning_update(self):
        """
        Perform a continuous learning update cycle.
        Analyzes recent outcomes and updates weights based on performance.
        """
        # Load existing state
        await self.load_learning_state()
        
        # Get recent learning outcomes for analysis
        recent_outcomes = await self.db.learning_outcomes.find(
            {},
            {"_id": 0, "was_correct": 1, "profit_loss": 1, "performance_score": 1}
        ).sort("recorded_at", -1).limit(100).to_list(100)
        
        if not recent_outcomes:
            return {
                "status": "no_data",
                "message": "No learning data available yet. Execute trades to generate learning samples."
            }
        
        # Calculate performance metrics
        total = len(recent_outcomes)
        correct = sum(1 for o in recent_outcomes if o.get('was_correct', False))
        total_profit = sum(o.get('profit_loss', 0) for o in recent_outcomes)
        avg_performance = sum(o.get('performance_score', 0) for o in recent_outcomes) / total if total > 0 else 0
        
        # Adjust weights based on recent performance
        if avg_performance > 0.2:
            # Strategies are performing well, increase performance weight
            self.performance_weight = min(0.9, self.performance_weight + 0.05)
            self.accuracy_weight = 1 - self.performance_weight
        elif avg_performance < -0.2:
            # Performance is poor, shift focus to accuracy
            self.accuracy_weight = min(0.5, self.accuracy_weight + 0.05)
            self.performance_weight = 1 - self.accuracy_weight
        
        # Save updated state
        await self.save_learning_state()
        
        # Update all strategy metrics
        strategy_ids = await self.db.learning_outcomes.distinct("strategy_id")
        for strategy_id in strategy_ids[:50]:  # Limit to 50 to prevent timeout
            await self._update_strategy_learning_metrics(strategy_id)
        
        return {
            "status": "success",
            "samples_analyzed": total,
            "accuracy": (correct / total * 100) if total > 0 else 0,
            "total_profit_loss": total_profit,
            "avg_performance_score": avg_performance,
            "updated_weights": {
                "performance_weight": self.performance_weight,
                "accuracy_weight": self.accuracy_weight
            },
            "strategies_updated": len(strategy_ids[:50]),
            "updated_at": datetime.now().isoformat()
        }

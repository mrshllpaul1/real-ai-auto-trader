"""
Learning Service - Continuous learning from trading results
Implements feedback loops for model improvement
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class LearningService:
    """Service for continuous model learning and improvement"""
    
    def __init__(self, db, transformer_predictor=None, rl_agent=None, 
                 regime_predictor=None, model_persistence=None):
        self.db = db
        self.transformer = transformer_predictor
        self.rl_agent = rl_agent
        self.regime = regime_predictor
        self.model_persistence = model_persistence
        self.learning_active = False
        self.learning_stats = {
            "total_sessions": 0,
            "successful_trades_learned": 0,
            "failed_trades_analyzed": 0,
            "model_improvements": 0,
            "last_learning_time": None,
            "current_accuracy": 0.0
        }
        self.learning_history = []
    
    async def get_learning_status(self) -> Dict[str, Any]:
        """Get current learning status and statistics"""
        # Calculate recent accuracy from trades
        try:
            recent_accuracy = await self._calculate_recent_accuracy()
        except Exception as e:
            logger.error(f"Error calculating accuracy: {e}")
            recent_accuracy = 0.0
        
        # Get model statuses with safe attribute access
        model_statuses = {
            "transformer": {
                "trained": getattr(self.transformer, 'is_trained', False) if self.transformer else False,
                "last_train": None
            },
            "rl_agent": {
                "trained": getattr(self.rl_agent, 'is_trained', False) if self.rl_agent else False,
                "last_train": None
            },
            "regime": {
                "trained": getattr(self.regime, 'is_trained', False) if self.regime else False,
                "last_train": None
            }
        }
        
        return {
            "learning_active": self.learning_active,
            "stats": {
                **self.learning_stats,
                "current_accuracy": recent_accuracy
            },
            "models": model_statuses,
            "history_count": len(self.learning_history),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _calculate_recent_accuracy(self, days: int = 7) -> float:
        """Calculate prediction accuracy from recent trades"""
        if self.db is None:
            return 0.0
        
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Get recent trades with predictions
            trades = await self.db.trades.find({
                "timestamp": {"$gte": cutoff},
                "prediction": {"$exists": True}
            }).to_list(1000)
            
            if not trades:
                return 0.0
            
            correct = 0
            total = 0
            
            for trade in trades:
                prediction = trade.get("prediction", {})
                actual_result = trade.get("profit_loss", 0)
                
                # Check if prediction direction matched result
                predicted_direction = prediction.get("direction", "neutral")
                actual_direction = "bullish" if actual_result > 0 else "bearish" if actual_result < 0 else "neutral"
                
                if predicted_direction == actual_direction:
                    correct += 1
                total += 1
            
            return (correct / total * 100) if total > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating accuracy: {e}")
            return 0.0
    
    async def analyze_trade_for_learning(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a completed trade to extract learning insights"""
        insights = {
            "trade_id": str(trade.get("_id", "")),
            "symbol": trade.get("symbol"),
            "profit_loss": trade.get("profit_loss", 0),
            "prediction_accuracy": 0.0,
            "lessons": [],
            "adjustments": {}
        }
        
        prediction = trade.get("prediction", {})
        actual_result = trade.get("profit_loss", 0)
        
        # Determine prediction accuracy
        if prediction:
            predicted_direction = prediction.get("direction", "neutral")
            predicted_confidence = prediction.get("confidence", 0)
            
            if (predicted_direction == "bullish" and actual_result > 0) or \
               (predicted_direction == "bearish" and actual_result < 0):
                insights["prediction_accuracy"] = predicted_confidence
                insights["lessons"].append("Prediction was correct")
            else:
                insights["prediction_accuracy"] = 1 - predicted_confidence
                insights["lessons"].append(f"Prediction was incorrect: expected {predicted_direction}")
                
                # Suggest model adjustments
                if predicted_direction == "bullish" and actual_result < 0:
                    insights["adjustments"]["reduce_bullish_bias"] = True
                elif predicted_direction == "bearish" and actual_result > 0:
                    insights["adjustments"]["reduce_bearish_bias"] = True
        
        # Analyze market conditions during trade
        market_conditions = trade.get("market_conditions", {})
        if market_conditions:
            regime = market_conditions.get("regime", "unknown")
            insights["lessons"].append(f"Market was in {regime} regime")
            
            if actual_result < 0 and regime in ["volatile", "bearish"]:
                insights["lessons"].append("Loss occurred in unfavorable market conditions")
                insights["adjustments"]["reduce_exposure_in_volatile"] = True
        
        return insights
    
    async def learn_from_recent_trades(self, days: int = 1) -> Dict[str, Any]:
        """Analyze recent trades and extract learning insights"""
        if not self.db:
            return {"error": "Database not available"}
        
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Get recent closed trades
            trades = await self.db.trades.find({
                "timestamp": {"$gte": cutoff},
                "status": "closed"
            }).to_list(100)
            
            if not trades:
                return {
                    "trades_analyzed": 0,
                    "insights": [],
                    "summary": "No recent trades to learn from"
                }
            
            insights = []
            total_pnl = 0
            winning_trades = 0
            losing_trades = 0
            
            for trade in trades:
                trade_insights = await self.analyze_trade_for_learning(trade)
                insights.append(trade_insights)
                
                pnl = trade.get("profit_loss", 0)
                total_pnl += pnl
                if pnl > 0:
                    winning_trades += 1
                elif pnl < 0:
                    losing_trades += 1
            
            win_rate = winning_trades / len(trades) * 100 if trades else 0
            
            # Update learning stats
            self.learning_stats["successful_trades_learned"] += winning_trades
            self.learning_stats["failed_trades_analyzed"] += losing_trades
            self.learning_stats["last_learning_time"] = datetime.now(timezone.utc).isoformat()
            
            # Store in learning history
            session = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trades_analyzed": len(trades),
                "win_rate": win_rate,
                "total_pnl": total_pnl,
                "insights_count": len(insights)
            }
            self.learning_history.append(session)
            
            return {
                "trades_analyzed": len(trades),
                "win_rate": round(win_rate, 2),
                "total_pnl": round(total_pnl, 2),
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "insights": insights[:10],  # Limit to 10 for response
                "summary": self._generate_learning_summary(insights)
            }
            
        except Exception as e:
            logger.error(f"Learning error: {e}")
            return {"error": str(e)}
    
    def _generate_learning_summary(self, insights: List[Dict]) -> str:
        """Generate a summary of learning insights"""
        if not insights:
            return "No insights generated"
        
        # Aggregate adjustments
        adjustments = {}
        for insight in insights:
            for adj, val in insight.get("adjustments", {}).items():
                adjustments[adj] = adjustments.get(adj, 0) + (1 if val else 0)
        
        # Find most common needed adjustments
        summary_parts = []
        if adjustments:
            most_common = max(adjustments.items(), key=lambda x: x[1])
            summary_parts.append(f"Most needed adjustment: {most_common[0]} ({most_common[1]} occurrences)")
        
        # Calculate average prediction accuracy
        accuracies = [i["prediction_accuracy"] for i in insights if i.get("prediction_accuracy")]
        if accuracies:
            avg_accuracy = np.mean(accuracies) * 100
            summary_parts.append(f"Average prediction accuracy: {avg_accuracy:.1f}%")
        
        return " | ".join(summary_parts) if summary_parts else "Learning session completed"
    
    async def start_learning_cycle(self) -> Dict[str, Any]:
        """Start a full learning cycle: analyze trades, retrain models"""
        self.learning_active = True
        self.learning_stats["total_sessions"] += 1
        
        results = {
            "cycle_id": f"learn_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "phases": []
        }
        
        try:
            # Phase 1: Analyze recent trades
            analysis = await self.learn_from_recent_trades(days=7)
            results["phases"].append({
                "name": "trade_analysis",
                "status": "completed" if "error" not in analysis else "failed",
                "result": analysis
            })
            
            # Phase 2: Retrain models if needed
            if analysis.get("trades_analyzed", 0) >= 10:
                # Determine which models need retraining based on insights
                should_retrain = {
                    "transformer": analysis.get("win_rate", 100) < 50,
                    "rl_agent": len([i for i in analysis.get("insights", []) if i.get("adjustments")]) > 5,
                    "regime": any("volatile" in str(i.get("lessons", [])) for i in analysis.get("insights", []))
                }
                
                training_results = {}
                
                if should_retrain["transformer"] and self.transformer:
                    try:
                        await self.transformer.train()
                        training_results["transformer"] = "retrained"
                        self.learning_stats["model_improvements"] += 1
                    except Exception as e:
                        training_results["transformer"] = f"failed: {str(e)}"
                
                if should_retrain["rl_agent"] and self.rl_agent:
                    try:
                        await self.rl_agent.train_async()
                        training_results["rl_agent"] = "retrained"
                        self.learning_stats["model_improvements"] += 1
                    except Exception as e:
                        training_results["rl_agent"] = f"failed: {str(e)}"
                
                results["phases"].append({
                    "name": "model_retraining",
                    "status": "completed",
                    "should_retrain": should_retrain,
                    "result": training_results
                })
            
            # Phase 3: Save models if any were retrained
            if self.model_persistence and results.get("phases", [{}])[-1].get("result"):
                try:
                    save_results = await self.model_persistence.save_all_models()
                    results["phases"].append({
                        "name": "model_persistence",
                        "status": "completed",
                        "result": save_results
                    })
                except Exception as e:
                    results["phases"].append({
                        "name": "model_persistence",
                        "status": "failed",
                        "error": str(e)
                    })
            
            results["completed_at"] = datetime.now(timezone.utc).isoformat()
            results["status"] = "completed"
            
        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            logger.error(f"Learning cycle error: {e}")
        
        finally:
            self.learning_active = False
        
        return results
    
    async def get_learning_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations for improving trading based on learning"""
        recommendations = []
        
        # Get recent accuracy
        accuracy = await self._calculate_recent_accuracy()
        
        if accuracy < 50:
            recommendations.append({
                "priority": "high",
                "category": "model_retraining",
                "message": f"Prediction accuracy is {accuracy:.1f}%. Consider retraining all models.",
                "action": "start_learning_cycle"
            })
        elif accuracy < 70:
            recommendations.append({
                "priority": "medium",
                "category": "model_tuning",
                "message": f"Prediction accuracy at {accuracy:.1f}%. Fine-tuning recommended.",
                "action": "train_transformer"
            })
        
        # Check if models are trained
        if self.transformer and not self.transformer.is_trained:
            recommendations.append({
                "priority": "high",
                "category": "initialization",
                "message": "Transformer model not trained. Train for better predictions.",
                "action": "train_transformer"
            })
        
        if self.rl_agent and not self.rl_agent.is_trained:
            recommendations.append({
                "priority": "high",
                "category": "initialization",
                "message": "RL Agent not trained. Train for better trading decisions.",
                "action": "train_rl_agent"
            })
        
        if self.regime and not self.regime.is_trained:
            recommendations.append({
                "priority": "medium",
                "category": "initialization",
                "message": "Regime predictor not trained. Train for better market analysis.",
                "action": "train_regime"
            })
        
        # Check learning frequency
        last_learn = self.learning_stats.get("last_learning_time")
        if not last_learn:
            recommendations.append({
                "priority": "high",
                "category": "learning",
                "message": "No learning session has been run. Start a learning cycle.",
                "action": "start_learning_cycle"
            })
        else:
            last_time = datetime.fromisoformat(last_learn.replace('Z', '+00:00'))
            hours_since = (datetime.now(timezone.utc) - last_time).total_seconds() / 3600
            if hours_since > 24:
                recommendations.append({
                    "priority": "medium",
                    "category": "learning",
                    "message": f"Last learning was {hours_since:.0f} hours ago. Consider running a new cycle.",
                    "action": "start_learning_cycle"
                })
        
        return recommendations
    
    def get_learning_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent learning history"""
        return self.learning_history[-limit:]


# Global instance
_learning_service: Optional[LearningService] = None


def get_learning_service() -> Optional[LearningService]:
    return _learning_service


def init_learning_service(db, **kwargs):
    global _learning_service
    _learning_service = LearningService(db, **kwargs)
    return _learning_service

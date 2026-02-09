"""
Reinforcement Learning from Human Feedback (RLHF)
==================================================
Allows users to rate trades and uses that feedback to improve
the trading AI's decision-making through reward model training.
"""

import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from collections import deque
import json

# Hyperparameters for online reward updates
BASE_LEARNING_RATE = 0.05   # Initial step size for fresh feedback
MIN_LEARNING_RATE = 0.005   # Floor to keep learning signal alive
MOMENTUM_BETA = 0.9         # Smooth gradients across noisy feedback
NORMALIZATION_SCALE = 10.0  # Compresses typical 0-10 inputs to ~[-0.8, 0.8] via tanh to prevent gradient spikes
DECAY_RATE = 0.05           # Per-sample decay for adaptive LR

# Feature-specific normalization/validation rules
FEATURE_RULES = {
    "profit_pct": {"min": -200, "max": 200, "scale": 50.0},
    "hold_time_hours": {"min": 0, "max": 168, "scale": 48.0},
    "entry_timing_score": {"min": 0, "max": 1, "scale": 1.0},
    "exit_timing_score": {"min": 0, "max": 1, "scale": 1.0},
    "risk_reward_ratio": {"min": 0, "max": 10, "scale": 5.0},
    "position_size_score": {"min": 0, "max": 1, "scale": 1.0},
}

logger = logging.getLogger(__name__)


class TradeRating:
    """Represents a user's rating of a trade"""
    
    def __init__(
        self,
        trade_id: str,
        rating: int,  # 1-5 stars
        feedback_type: str,  # "timing", "sizing", "direction", "overall"
        comment: Optional[str] = None,
        user_id: str = "default"
    ):
        self.trade_id = trade_id
        self.rating = max(1, min(5, rating))  # Clamp to 1-5
        self.feedback_type = feedback_type
        self.comment = comment
        self.user_id = user_id
        self.created_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict:
        return {
            "trade_id": self.trade_id,
            "rating": self.rating,
            "feedback_type": self.feedback_type,
            "comment": self.comment,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat()
        }


class RewardModel:
    """
    Learns a reward function from human feedback.
    Maps trade features to predicted human ratings.
    """
    
    def __init__(self):
        # Simple linear reward model weights
        self.feature_weights = {
            "profit_pct": 0.3,
            "hold_time_hours": -0.1,
            "entry_timing_score": 0.2,
            "exit_timing_score": 0.2,
            "risk_reward_ratio": 0.15,
            "position_size_score": 0.05
        }
        
        # Learned adjustments from feedback
        self.learned_adjustments = {}
        
        # Training data
        self.training_data: List[Tuple[Dict, float]] = []
        self.sample_count = 0
        
        # Adaptive learning controls
        self.base_learning_rate = BASE_LEARNING_RATE
        self.min_learning_rate = MIN_LEARNING_RATE
        self.momentum_beta = MOMENTUM_BETA
        self.gradient_momentum: Dict[str, float] = {}
        self.last_effective_lr = self.base_learning_rate
        self.last_update_at = None
        self.normalization_scale = NORMALIZATION_SCALE
        self.decay_rate = DECAY_RATE
        self._lr_cache_count = -1
        
    def predict_reward(self, trade_features: Dict) -> float:
        """Predict human rating for a trade"""
        normalized_features = {
            feature: self._normalize_feature_value(feature, trade_features.get(feature, 0))
            for feature in self.feature_weights
        }
        return self._predict_from_normalized_features(normalized_features)
    
    def update_from_feedback(self, trade_features: Dict, human_rating: float):
        """Update model based on human feedback"""
        normalized_features = {
            feature: self._normalize_feature_value(feature, value)
            for feature, value in trade_features.items()
        }
        self.training_data.append((normalized_features, human_rating))
        self.sample_count += 1
        
        # Simple online learning update
        predicted = self._predict_from_normalized_features(normalized_features)
        error = human_rating - predicted
        
        learning_rate = self._get_effective_learning_rate()
        
        for feature in self.feature_weights:
            if feature in normalized_features:
                value = normalized_features[feature]
                gradient = error * value
                
                prev_momentum = self.gradient_momentum.get(feature, 0.0)
                momentum = self.momentum_beta * prev_momentum + (1 - self.momentum_beta) * gradient
                self.gradient_momentum[feature] = momentum
                
                if feature not in self.learned_adjustments:
                    self.learned_adjustments[feature] = 0
                
                self.learned_adjustments[feature] += learning_rate * momentum
        
        self.last_update_at = datetime.now(timezone.utc)
    
    def get_weights(self) -> Dict:
        """Get current effective weights"""
        return {
            feature: self.feature_weights[feature] + self.learned_adjustments.get(feature, 0)
            for feature in self.feature_weights
        }
    
    def _normalize_feature_value(self, feature: str, value: float) -> float:
        """Scale feature values with tanh to keep updates stable; clamps per-feature ranges first"""
        rules = FEATURE_RULES.get(feature, {})
        safe_val = 0 if value is None else value
        if isinstance(safe_val, (float, np.floating)) and np.isnan(safe_val):
            safe_val = 0
        min_val = rules.get("min")
        max_val = rules.get("max")
        if min_val is not None:
            safe_val = max(min_val, safe_val)
        if max_val is not None:
            safe_val = min(max_val, safe_val)
        
        scale = rules.get("scale", self.normalization_scale)
        if scale <= 0:
            scale = self.normalization_scale
        
        return float(np.tanh(safe_val / scale))
    
    def _get_effective_learning_rate(self) -> float:
        """Use a decaying learning rate with a safety floor to stabilize training"""
        if self.sample_count == self._lr_cache_count and self.last_effective_lr is not None:
            return self.last_effective_lr
        decay = 1 / (1 + self.decay_rate * self.sample_count)
        self.last_effective_lr = max(self.min_learning_rate, self.base_learning_rate * decay)
        self._lr_cache_count = self.sample_count
        return self.last_effective_lr
    
    def _predict_from_normalized_features(self, normalized_features: Dict) -> float:
        """Predict rating using already normalized feature values"""
        reward = 0
        for feature, weight in self.feature_weights.items():
            value = normalized_features.get(feature, 0)
            adjustment = self.learned_adjustments.get(feature, 0)
            reward += (weight + adjustment) * value
        return max(1, min(5, 2.5 + reward))
    
    def get_training_signal(self) -> Dict[str, Any]:
        """Expose training health for monitoring and curriculum building"""
        adjustments = list(self.learned_adjustments.values())
        if adjustments:
            avg_adjustment = float(np.mean(np.abs(adjustments)))
        else:
            avg_adjustment = 0.0
        return {
            "samples": self.sample_count,
            "effective_learning_rate": self.last_effective_lr,
            "avg_adjustment_magnitude": avg_adjustment,
            "last_update_at": self.last_update_at.isoformat() if self.last_update_at else None
        }


class RLHFTrainer:
    """
    Main RLHF system for training trading AI from human feedback.
    """
    
    def __init__(self, db=None):
        self.db = db
        self.reward_model = RewardModel()
        
        # Feedback storage
        self.ratings: List[TradeRating] = []
        self.pending_trades: Dict[str, Dict] = {}  # Trades awaiting feedback
        
        # Statistics
        self.stats = {
            "total_ratings": 0,
            "avg_rating": 0,
            "ratings_by_type": {},
            "improvement_trend": []
        }
        
        logger.info("🎓 RLHF Trainer initialized")
    
    async def submit_trade_for_feedback(
        self,
        trade_id: str,
        trade_data: Dict
    ) -> Dict:
        """
        Submit a trade for human feedback.
        Extracts relevant features and queues for rating.
        """
        # Extract features
        features = self._extract_trade_features(trade_data)
        
        # Store pending trade
        self.pending_trades[trade_id] = {
            "trade_data": trade_data,
            "features": features,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "predicted_rating": self.reward_model.predict_reward(features)
        }
        
        # Save to database
        if self.db is not None:
            try:
                await self.db.rlhf_pending_trades.update_one(
                    {"trade_id": trade_id},
                    {"$set": self.pending_trades[trade_id]},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Failed to save pending trade: {e}")
        
        return {
            "trade_id": trade_id,
            "features": features,
            "predicted_rating": self.pending_trades[trade_id]["predicted_rating"],
            "status": "awaiting_feedback"
        }
    
    async def submit_feedback(
        self,
        trade_id: str,
        rating: int,
        feedback_type: str = "overall",
        comment: Optional[str] = None,
        user_id: str = "default"
    ) -> Dict:
        """
        Submit human feedback for a trade.
        Updates the reward model based on the feedback.
        """
        # Create rating object
        trade_rating = TradeRating(
            trade_id=trade_id,
            rating=rating,
            feedback_type=feedback_type,
            comment=comment,
            user_id=user_id
        )
        
        self.ratings.append(trade_rating)
        
        # Get trade features
        pending = self.pending_trades.get(trade_id)
        if pending:
            features = pending["features"]
            
            # Update reward model
            self.reward_model.update_from_feedback(features, rating)
            
            # Remove from pending
            del self.pending_trades[trade_id]
        
        # Update statistics
        self._update_stats(trade_rating)
        
        # Save to database
        if self.db is not None:
            try:
                await self.db.rlhf_feedback.insert_one(trade_rating.to_dict())
                await self.db.rlhf_pending_trades.delete_one({"trade_id": trade_id})
            except Exception as e:
                logger.error(f"Failed to save feedback: {e}")
        
        return {
            "status": "feedback_recorded",
            "trade_id": trade_id,
            "rating": rating,
            "model_updated": True,
            "current_stats": self.get_stats()
        }
    
    def _extract_trade_features(self, trade_data: Dict) -> Dict:
        """Extract relevant features from trade data for reward modeling"""
        features = {}
        
        # Profit/Loss
        entry_price = trade_data.get("entry_price", 0)
        exit_price = trade_data.get("exit_price", entry_price)
        if entry_price > 0:
            if trade_data.get("direction") == "long":
                features["profit_pct"] = ((exit_price - entry_price) / entry_price) * 100
            else:
                features["profit_pct"] = ((entry_price - exit_price) / entry_price) * 100
        else:
            features["profit_pct"] = 0
        
        # Hold time
        entry_time = trade_data.get("entry_time")
        exit_time = trade_data.get("exit_time")
        if entry_time and exit_time:
            try:
                if isinstance(entry_time, str):
                    entry_time = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                if isinstance(exit_time, str):
                    exit_time = datetime.fromisoformat(exit_time.replace('Z', '+00:00'))
                features["hold_time_hours"] = (exit_time - entry_time).total_seconds() / 3600
            except:
                features["hold_time_hours"] = 1
        else:
            features["hold_time_hours"] = 1
        
        # Entry timing score (based on how close to optimal entry)
        features["entry_timing_score"] = trade_data.get("entry_timing_score", 0.5)
        
        # Exit timing score
        features["exit_timing_score"] = trade_data.get("exit_timing_score", 0.5)
        
        # Risk/Reward ratio
        stop_loss = trade_data.get("stop_loss_pct", 2)
        take_profit = trade_data.get("take_profit_pct", 4)
        features["risk_reward_ratio"] = take_profit / stop_loss if stop_loss > 0 else 1
        
        # Position size appropriateness
        position_pct = trade_data.get("position_pct", 5)
        optimal_size = 5  # Assume 5% is optimal
        features["position_size_score"] = 1 - abs(position_pct - optimal_size) / 10
        
        return features
    
    def _update_stats(self, rating: TradeRating):
        """Update statistics after new rating"""
        self.stats["total_ratings"] += 1
        
        # Update average
        all_ratings = [r.rating for r in self.ratings]
        self.stats["avg_rating"] = np.mean(all_ratings)
        
        # Update by type
        if rating.feedback_type not in self.stats["ratings_by_type"]:
            self.stats["ratings_by_type"][rating.feedback_type] = []
        self.stats["ratings_by_type"][rating.feedback_type].append(rating.rating)
        
        # Track improvement trend (rolling average)
        if len(all_ratings) >= 10:
            recent_avg = np.mean(all_ratings[-10:])
            self.stats["improvement_trend"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "avg_rating": recent_avg
            })
    
    def get_stats(self) -> Dict:
        """Get current RLHF statistics"""
        return {
            **self.stats,
            "pending_trades": len(self.pending_trades),
            "reward_model_weights": self.reward_model.get_weights(),
            "reward_model_training": self.reward_model.get_training_signal(),
            "recent_ratings": [r.to_dict() for r in self.ratings[-10:]]
        }
    
    def get_pending_trades(self, limit: int = 20) -> List[Dict]:
        """Get trades awaiting feedback"""
        pending_list = []
        for trade_id, data in list(self.pending_trades.items())[:limit]:
            pending_list.append({
                "trade_id": trade_id,
                **data
            })
        return pending_list
    
    def get_feedback_suggestions(self, trade_features: Dict) -> Dict:
        """
        Get AI suggestions for what aspects of the trade to focus feedback on.
        """
        suggestions = []
        
        profit_pct = trade_features.get("profit_pct", 0)
        hold_time = trade_features.get("hold_time_hours", 0)
        rr_ratio = trade_features.get("risk_reward_ratio", 1)
        
        if abs(profit_pct) > 10:
            suggestions.append({
                "aspect": "timing",
                "question": "Was the entry/exit timing optimal for this trade?",
                "context": f"Large move of {profit_pct:.1f}%"
            })
        
        if hold_time < 1:
            suggestions.append({
                "aspect": "timing",
                "question": "Was exiting quickly the right decision?",
                "context": f"Hold time was only {hold_time:.1f} hours"
            })
        elif hold_time > 24:
            suggestions.append({
                "aspect": "timing",
                "question": "Should the position have been held this long?",
                "context": f"Hold time was {hold_time:.1f} hours"
            })
        
        if rr_ratio < 1.5:
            suggestions.append({
                "aspect": "sizing",
                "question": "Was the risk/reward setup appropriate?",
                "context": f"R:R ratio was {rr_ratio:.2f}"
            })
        
        return {
            "suggestions": suggestions,
            "predicted_rating": self.reward_model.predict_reward(trade_features)
        }
    
    async def generate_improved_signal(
        self,
        original_signal: Dict,
        trade_context: Dict
    ) -> Dict:
        """
        Use learned preferences to potentially improve a trading signal.
        """
        # Get current reward model insights
        weights = self.reward_model.get_weights()
        
        improved_signal = original_signal.copy()
        adjustments = []
        
        # If timing is highly weighted and we have timing data
        if weights.get("entry_timing_score", 0) > 0.3:
            # Suggest waiting for better entry
            if original_signal.get("confidence", 50) < 70:
                improved_signal["wait_for_confirmation"] = True
                adjustments.append("Added confirmation requirement due to learned timing preferences")
        
        # If position sizing is important
        if weights.get("position_size_score", 0) > 0.1:
            # Adjust position size based on confidence
            confidence = original_signal.get("confidence", 50)
            base_size = 5  # 5% base position
            adjusted_size = base_size * (confidence / 100)
            improved_signal["suggested_position_pct"] = round(adjusted_size, 1)
            adjustments.append(f"Adjusted position size to {adjusted_size:.1f}% based on confidence")
        
        improved_signal["rlhf_adjustments"] = adjustments
        improved_signal["reward_model_prediction"] = self.reward_model.predict_reward(trade_context)
        
        return improved_signal


# Singleton
_rlhf_trainer: Optional[RLHFTrainer] = None


def get_rlhf_trainer(db=None) -> RLHFTrainer:
    """Get or create RLHF trainer singleton"""
    global _rlhf_trainer
    if _rlhf_trainer is None:
        _rlhf_trainer = RLHFTrainer(db)
    return _rlhf_trainer

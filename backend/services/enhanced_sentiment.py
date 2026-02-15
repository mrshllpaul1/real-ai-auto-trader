"""Enhanced Sentiment Analyzer with ML Retraining

Improves upon the basic keyword-based sentiment analyzer with:
1. Weighted keyword scoring based on calibration feedback
2. Context-aware sentiment detection
3. Learning from prediction outcomes
4. Confidence calibration adjustments
"""

import os
import json
import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class EnhancedSentimentAnalyzer:
    """ML-enhanced sentiment analyzer with retraining capability."""
    
    # Base keyword weights (will be adjusted through learning)
    DEFAULT_BULLISH_WEIGHTS = {
        'moon': 0.9, 'bullish': 0.85, 'buy': 0.6, 'hodl': 0.7, 'hold': 0.5,
        'pump': 0.75, 'breakout': 0.8, 'accumulate': 0.7, 'undervalued': 0.75,
        'gem': 0.8, 'rocket': 0.85, 'ath': 0.7, 'gains': 0.65, 'bull run': 0.9,
        'long': 0.6, 'support': 0.5, 'bounce': 0.6, 'reversal': 0.55,
        'green': 0.5, 'surge': 0.7, 'rally': 0.75, 'explosion': 0.8,
        'parabolic': 0.85, 'skyrocket': 0.9, 'breaking out': 0.8,
        'strong': 0.5, 'momentum': 0.6, 'bullish divergence': 0.85,
        'golden cross': 0.8, 'oversold': 0.65, 'accumulation': 0.7
    }
    
    DEFAULT_BEARISH_WEIGHTS = {
        'crash': 0.9, 'bearish': 0.85, 'sell': 0.6, 'dump': 0.8, 'scam': 0.95,
        'rug': 0.95, 'dead': 0.7, 'overvalued': 0.75, 'short': 0.6,
        'resistance': 0.5, 'breakdown': 0.75, 'red': 0.5, 'plunge': 0.85,
        'collapse': 0.9, 'fear': 0.7, 'panic': 0.8, 'bleeding': 0.75,
        'tank': 0.8, 'bubble': 0.7, 'correction': 0.6, 'drop': 0.55,
        'fall': 0.5, 'decline': 0.55, 'death cross': 0.8, 'overbought': 0.65,
        'distribution': 0.7, 'bearish divergence': 0.85, 'capitulation': 0.9,
        'rekt': 0.85, 'liquidation': 0.75, 'fud': 0.6
    }
    
    # Negation words that flip sentiment
    NEGATION_WORDS = ['not', "don't", "doesn't", "won't", "isn't", "aren't", 'never', 'no', 'without']
    
    # Intensifiers that strengthen sentiment
    INTENSIFIERS = {
        'very': 1.3, 'extremely': 1.5, 'super': 1.4, 'absolutely': 1.5,
        'definitely': 1.3, 'huge': 1.4, 'massive': 1.5, 'insane': 1.4
    }
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.bullish_weights = self.DEFAULT_BULLISH_WEIGHTS.copy()
        self.bearish_weights = self.DEFAULT_BEARISH_WEIGHTS.copy()
        self.confidence_adjustment = 1.0  # Calibration factor
        self.learning_rate = 0.1
        self.training_history: List[Dict] = []
        self._initialized = False
        
        # Performance tracking
        self.performance_log: List[Dict] = []
        self.version = "2.0.0"
    
    async def initialize(self):
        """Load learned weights from database."""
        if self._initialized:
            return
        
        # Try to load saved weights
        saved = await self.db.ml_model_weights.find_one({"model": "sentiment_analyzer"})
        if saved:
            self.bullish_weights = saved.get("bullish_weights", self.bullish_weights)
            self.bearish_weights = saved.get("bearish_weights", self.bearish_weights)
            self.confidence_adjustment = saved.get("confidence_adjustment", 1.0)
            self.version = saved.get("version", self.version)
            logger.info(f"Loaded sentiment analyzer weights v{self.version}")
        
        self._initialized = True
    
    async def save_weights(self):
        """Save learned weights to database."""
        await self.db.ml_model_weights.update_one(
            {"model": "sentiment_analyzer"},
            {"$set": {
                "model": "sentiment_analyzer",
                "bullish_weights": self.bullish_weights,
                "bearish_weights": self.bearish_weights,
                "confidence_adjustment": self.confidence_adjustment,
                "version": self.version,
                "updated_at": datetime.now(timezone.utc)
            }},
            upsert=True
        )
        logger.info(f"Saved sentiment analyzer weights v{self.version}")
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text with enhanced ML scoring."""
        text_lower = text.lower()
        words = text_lower.split()
        
        bullish_score = 0.0
        bearish_score = 0.0
        matched_bullish = []
        matched_bearish = []
        
        # Check for negation context
        negation_active = False
        intensifier = 1.0
        
        for i, word in enumerate(words):
            # Check for negation
            if word in self.NEGATION_WORDS:
                negation_active = True
                continue
            
            # Check for intensifiers
            if word in self.INTENSIFIERS:
                intensifier = self.INTENSIFIERS[word]
                continue
            
            # Check bullish keywords
            for keyword, weight in self.bullish_weights.items():
                if keyword in word or (len(keyword.split()) > 1 and keyword in text_lower):
                    score = weight * intensifier
                    if negation_active:
                        bearish_score += score
                        matched_bearish.append(f"NOT {keyword}")
                    else:
                        bullish_score += score
                        matched_bullish.append(keyword)
                    break
            
            # Check bearish keywords
            for keyword, weight in self.bearish_weights.items():
                if keyword in word or (len(keyword.split()) > 1 and keyword in text_lower):
                    score = weight * intensifier
                    if negation_active:
                        bullish_score += score
                        matched_bullish.append(f"NOT {keyword}")
                    else:
                        bearish_score += score
                        matched_bearish.append(keyword)
                    break
            
            # Reset modifiers after use
            if word not in self.NEGATION_WORDS and word not in self.INTENSIFIERS:
                negation_active = False
                intensifier = 1.0
        
        # Calculate final sentiment
        total = bullish_score + bearish_score
        if total == 0:
            sentiment_score = 0.0
            confidence = 0.3  # Low confidence for neutral
        else:
            sentiment_score = (bullish_score - bearish_score) / total
            # Confidence based on signal strength and keyword count
            signal_strength = abs(bullish_score - bearish_score) / max(total, 1)
            keyword_density = min(len(matched_bullish) + len(matched_bearish), 10) / 10
            confidence = 0.4 + (signal_strength * 0.4) + (keyword_density * 0.2)
        
        # Apply calibration adjustment
        confidence = min(0.95, confidence * self.confidence_adjustment)
        
        # Determine label
        if sentiment_score > 0.2:
            label = "BULLISH"
            action = "BUY"
        elif sentiment_score < -0.2:
            label = "BEARISH"
            action = "SELL"
        else:
            label = "NEUTRAL"
            action = "HOLD"
        
        return {
            "sentiment_score": round(sentiment_score, 4),
            "confidence": round(confidence, 4),
            "label": label,
            "action": action,
            "bullish_score": round(bullish_score, 4),
            "bearish_score": round(bearish_score, 4),
            "matched_bullish": matched_bullish[:5],
            "matched_bearish": matched_bearish[:5],
            "model_version": self.version
        }
    
    async def retrain(self, training_data: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Retrain the sentiment analyzer based on calibration outcomes."""
        await self.initialize()
        
        logger.info("Starting sentiment analyzer retraining...")
        
        # Load training data from calibration outcomes if not provided
        if training_data is None:
            training_data = await self._load_training_data()
        
        if len(training_data) < 10:
            return {
                "status": "insufficient_data",
                "samples": len(training_data),
                "required": 10
            }
        
        # Analyze outcomes by keyword
        keyword_outcomes = defaultdict(lambda: {"correct": 0, "incorrect": 0})
        confidence_outcomes = defaultdict(lambda: {"correct": 0, "total": 0})
        
        old_version = self.version
        adjustments_made = []
        
        for sample in training_data:
            text = sample.get("text", "")
            predicted_action = sample.get("predicted_action", "")
            was_correct = sample.get("is_correct", False)
            confidence = sample.get("confidence", 0.5)
            
            if not text:
                continue
            
            # Track confidence calibration
            conf_bucket = round(confidence, 1)
            confidence_outcomes[conf_bucket]["total"] += 1
            if was_correct:
                confidence_outcomes[conf_bucket]["correct"] += 1
            
            # Analyze which keywords were present
            text_lower = text.lower()
            
            for keyword in self.bullish_weights.keys():
                if keyword in text_lower:
                    if was_correct:
                        keyword_outcomes[keyword]["correct"] += 1
                    else:
                        keyword_outcomes[keyword]["incorrect"] += 1
            
            for keyword in self.bearish_weights.keys():
                if keyword in text_lower:
                    if was_correct:
                        keyword_outcomes[keyword]["correct"] += 1
                    else:
                        keyword_outcomes[keyword]["incorrect"] += 1
        
        # Adjust keyword weights based on outcomes
        for keyword, outcomes in keyword_outcomes.items():
            total = outcomes["correct"] + outcomes["incorrect"]
            if total >= 3:  # Need minimum samples
                accuracy = outcomes["correct"] / total
                
                # Adjust weight based on accuracy
                if keyword in self.bullish_weights:
                    old_weight = self.bullish_weights[keyword]
                    # Increase weight if accurate, decrease if not
                    adjustment = self.learning_rate * (accuracy - 0.5) * 2
                    new_weight = max(0.1, min(1.0, old_weight + adjustment))
                    if abs(new_weight - old_weight) > 0.05:
                        self.bullish_weights[keyword] = round(new_weight, 3)
                        adjustments_made.append({
                            "keyword": keyword,
                            "type": "bullish",
                            "old_weight": old_weight,
                            "new_weight": new_weight,
                            "accuracy": round(accuracy, 3)
                        })
                
                elif keyword in self.bearish_weights:
                    old_weight = self.bearish_weights[keyword]
                    adjustment = self.learning_rate * (accuracy - 0.5) * 2
                    new_weight = max(0.1, min(1.0, old_weight + adjustment))
                    if abs(new_weight - old_weight) > 0.05:
                        self.bearish_weights[keyword] = round(new_weight, 3)
                        adjustments_made.append({
                            "keyword": keyword,
                            "type": "bearish",
                            "old_weight": old_weight,
                            "new_weight": new_weight,
                            "accuracy": round(accuracy, 3)
                        })
        
        # Adjust confidence calibration
        total_predictions = sum(v["total"] for v in confidence_outcomes.values())
        if total_predictions > 0:
            # Calculate Expected Calibration Error
            ece = 0
            for conf_bucket, outcomes in confidence_outcomes.items():
                if outcomes["total"] > 0:
                    actual_accuracy = outcomes["correct"] / outcomes["total"]
                    ece += abs(conf_bucket - actual_accuracy) * (outcomes["total"] / total_predictions)
            
            # Adjust confidence if overconfident or underconfident
            if ece > 0.1:
                # Model is miscalibrated, adjust
                avg_conf = sum(k * v["total"] for k, v in confidence_outcomes.items()) / total_predictions
                avg_acc = sum(v["correct"] for v in confidence_outcomes.values()) / total_predictions
                
                if avg_conf > avg_acc + 0.05:
                    # Overconfident - reduce confidence
                    self.confidence_adjustment *= 0.9
                elif avg_conf < avg_acc - 0.05:
                    # Underconfident - increase confidence
                    self.confidence_adjustment *= 1.1
                
                self.confidence_adjustment = max(0.5, min(1.5, self.confidence_adjustment))
        
        # Update version
        version_parts = self.version.split(".")
        new_minor = int(version_parts[1]) + 1
        self.version = f"{version_parts[0]}.{new_minor}.0"
        
        # Save updated weights
        await self.save_weights()
        
        # Log training
        training_record = {
            "timestamp": datetime.now(timezone.utc),
            "samples": len(training_data),
            "adjustments": len(adjustments_made),
            "old_version": old_version,
            "new_version": self.version,
            "confidence_adjustment": self.confidence_adjustment
        }
        await self.db.ml_training_history.insert_one(training_record)
        self.training_history.append(training_record)
        
        logger.info(f"Retraining complete: {len(adjustments_made)} adjustments, v{old_version} -> v{self.version}")
        
        return {
            "status": "success",
            "old_version": old_version,
            "new_version": self.version,
            "samples_used": len(training_data),
            "adjustments_made": len(adjustments_made),
            "keyword_adjustments": adjustments_made[:10],  # Top 10
            "confidence_adjustment": round(self.confidence_adjustment, 4),
            "message": "Sentiment analyzer retrained successfully"
        }
    
    async def _load_training_data(self) -> List[Dict]:
        """Load training data from calibration outcomes."""
        # Get outcomes where model was sentiment_analyzer
        outcomes = await self.db.live_calibration_outcomes.find(
            {"model_name": "sentiment_analyzer"}
        ).limit(500).to_list(500)
        
        training_data = []
        for outcome in outcomes:
            # Try to get original text from metadata or generate synthetic
            training_data.append({
                "text": outcome.get("metadata", {}).get("text", f"{outcome.get('coin_id', '')} {outcome.get('predicted_action', '')}"),
                "predicted_action": outcome.get("predicted_action"),
                "is_correct": outcome.get("is_correct"),
                "confidence": outcome.get("confidence", 0.5)
            })
        
        return training_data
    
    async def test_accuracy(self, test_texts: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Test current model accuracy on sample texts."""
        if test_texts is None:
            # Use standard test cases
            test_texts = [
                {"text": "BTC is going to moon! Super bullish!", "expected": "BULLISH"},
                {"text": "This is a massive scam, sell everything!", "expected": "BEARISH"},
                {"text": "The price is stable, waiting for breakout", "expected": "NEUTRAL"},
                {"text": "Not bearish at all, very bullish divergence", "expected": "BULLISH"},
                {"text": "Huge crash incoming, panic selling", "expected": "BEARISH"},
                {"text": "Accumulating ETH during this dip", "expected": "BULLISH"},
                {"text": "Dead cat bounce, don't buy the dip", "expected": "BEARISH"},
                {"text": "Strong support holding, expecting rally", "expected": "BULLISH"},
                {"text": "Market is bleeding, fear everywhere", "expected": "BEARISH"},
                {"text": "Golden cross forming on daily chart", "expected": "BULLISH"},
            ]
        
        correct = 0
        results = []
        
        for test in test_texts:
            analysis = self.analyze_text(test["text"])
            is_correct = analysis["label"] == test["expected"]
            if is_correct:
                correct += 1
            results.append({
                "text": test["text"][:50] + "...",
                "expected": test["expected"],
                "predicted": analysis["label"],
                "confidence": analysis["confidence"],
                "correct": is_correct
            })
        
        return {
            "accuracy": round(correct / len(test_texts) * 100, 2),
            "correct": correct,
            "total": len(test_texts),
            "results": results,
            "model_version": self.version
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get current model configuration."""
        return {
            "version": self.version,
            "bullish_keywords": len(self.bullish_weights),
            "bearish_keywords": len(self.bearish_weights),
            "confidence_adjustment": round(self.confidence_adjustment, 4),
            "learning_rate": self.learning_rate,
            "top_bullish": sorted(self.bullish_weights.items(), key=lambda x: x[1], reverse=True)[:5],
            "top_bearish": sorted(self.bearish_weights.items(), key=lambda x: x[1], reverse=True)[:5]
        }


# Singleton instance
_enhanced_sentiment: Optional[EnhancedSentimentAnalyzer] = None


def get_enhanced_sentiment_analyzer(db=None) -> EnhancedSentimentAnalyzer:
    """Get or create enhanced sentiment analyzer."""
    global _enhanced_sentiment
    if _enhanced_sentiment is None and db is not None:
        _enhanced_sentiment = EnhancedSentimentAnalyzer(db)
    return _enhanced_sentiment


def set_sentiment_analyzer_db(db) -> EnhancedSentimentAnalyzer:
    """Set DB for sentiment analyzer."""
    global _enhanced_sentiment
    _enhanced_sentiment = EnhancedSentimentAnalyzer(db)
    return _enhanced_sentiment

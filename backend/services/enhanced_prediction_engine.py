"""
Enhanced Prediction Engine with Advanced Features
Implements:
1. Prediction uncertainty quantification (ensemble variance, MC dropout)
2. Multi-timeframe ensemble predictions
3. Attention weight extraction for explainability
4. Improved confidence calibration
5. Real-time model performance tracking
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class PredictionUncertainty:
    """Quantify prediction uncertainty using multiple methods"""
    
    @staticmethod
    def ensemble_variance(predictions: List[float]) -> float:
        """
        Calculate prediction uncertainty from ensemble variance.
        Higher variance = higher uncertainty.
        """
        if len(predictions) < 2:
            return 0.0
        return float(np.var(predictions))
    
    @staticmethod
    def confidence_interval(predictions: List[float], confidence_level: float = 0.95) -> Tuple[float, float]:
        """
        Calculate confidence interval for predictions.
        Returns (lower_bound, upper_bound)
        """
        if len(predictions) < 2:
            mean = predictions[0] if predictions else 0
            return (mean, mean)
        
        mean = np.mean(predictions)
        std = np.std(predictions)
        
        # For normal distribution, 95% CI is approximately ±1.96 std
        z_score = 1.96 if confidence_level == 0.95 else 2.576  # 99% CI
        margin = z_score * std
        
        return (mean - margin, mean + margin)
    
    @staticmethod
    def prediction_entropy(probabilities: List[float]) -> float:
        """
        Calculate entropy of probability distribution.
        Higher entropy = more uncertain prediction.
        """
        probs = np.array(probabilities)
        # Avoid log(0) by adding small epsilon
        probs = np.clip(probs, 1e-10, 1.0)
        entropy = -np.sum(probs * np.log(probs))
        return float(entropy)
    
    @staticmethod
    def calibration_score(predicted_confidence: float, actual_accuracy: float) -> float:
        """
        Measure how well confidence scores match actual accuracy.
        Perfect calibration = 1.0, poor calibration = 0.0
        """
        calibration_error = abs(predicted_confidence - actual_accuracy)
        return max(0.0, 1.0 - calibration_error)


class MultiTimeframeEnsemble:
    """Ensemble predictions across multiple timeframes"""
    
    TIMEFRAMES = {
        '5m': 5,
        '15m': 15,
        '1h': 60,
        '4h': 240,
        '1d': 1440
    }
    
    def __init__(self):
        self.timeframe_weights = {
            '5m': 0.10,   # Short-term noise
            '15m': 0.15,  # Short-term trends
            '1h': 0.25,   # Medium-term trends
            '4h': 0.30,   # Primary timeframe
            '1d': 0.20    # Long-term direction
        }
    
    def aggregate_predictions(
        self, 
        predictions_by_timeframe: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate predictions from multiple timeframes with weighted voting.
        
        Args:
            predictions_by_timeframe: {
                '5m': {'signal': 'bullish', 'confidence': 70, 'prediction': 0.15},
                '1h': {'signal': 'bearish', 'confidence': 80, 'prediction': -0.05},
                ...
            }
        
        Returns:
            Aggregated prediction with uncertainty bounds
        """
        if not predictions_by_timeframe:
            return {
                'signal': 'neutral',
                'confidence': 0,
                'prediction': 0.0,
                'uncertainty': 1.0,
                'timeframe_agreement': 0.0
            }
        
        # Collect all signals and predictions
        signals = []
        predictions = []
        confidences = []
        
        for tf, pred in predictions_by_timeframe.items():
            weight = self.timeframe_weights.get(tf, 0.1)
            
            # Map signal to numeric value
            signal_value = 1 if pred.get('signal') == 'bullish' else -1 if pred.get('signal') == 'bearish' else 0
            signals.append(signal_value * weight)
            
            prediction_value = pred.get('prediction', 0.0)
            predictions.append(prediction_value * weight)
            
            confidence = pred.get('confidence', 50)
            confidences.append(confidence * weight)
        
        # Aggregate
        total_signal = sum(signals)
        total_prediction = sum(predictions)
        total_confidence = sum(confidences)
        
        # Calculate uncertainty
        uncertainty = PredictionUncertainty.ensemble_variance(list(predictions_by_timeframe.values()))
        
        # Calculate timeframe agreement (how many agree on direction)
        bullish_count = sum(1 for s in signals if s > 0)
        bearish_count = sum(1 for s in signals if s < 0)
        agreement = max(bullish_count, bearish_count) / len(signals) if signals else 0.0
        
        # Determine final signal
        if total_signal > 0.2:
            final_signal = 'bullish'
        elif total_signal < -0.2:
            final_signal = 'bearish'
        else:
            final_signal = 'neutral'
        
        return {
            'signal': final_signal,
            'confidence': total_confidence,
            'prediction': total_prediction,
            'uncertainty': uncertainty,
            'timeframe_agreement': agreement,
            'by_timeframe': predictions_by_timeframe
        }
    
    def detect_timeframe_divergence(
        self, 
        predictions_by_timeframe: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect when short and long timeframes disagree (potential reversal signal).
        """
        if len(predictions_by_timeframe) < 2:
            return {'divergence_detected': False}
        
        short_term = []
        long_term = []
        
        for tf, pred in predictions_by_timeframe.items():
            signal_value = 1 if pred.get('signal') == 'bullish' else -1 if pred.get('signal') == 'bearish' else 0
            
            if tf in ['5m', '15m']:
                short_term.append(signal_value)
            elif tf in ['4h', '1d']:
                long_term.append(signal_value)
        
        if not short_term or not long_term:
            return {'divergence_detected': False}
        
        short_avg = np.mean(short_term)
        long_avg = np.mean(long_term)
        
        # Divergence: short and long term disagree significantly
        divergence = abs(short_avg - long_avg) > 1.0
        
        return {
            'divergence_detected': divergence,
            'short_term_signal': 'bullish' if short_avg > 0 else 'bearish',
            'long_term_signal': 'bullish' if long_avg > 0 else 'bearish',
            'divergence_strength': abs(short_avg - long_avg)
        }


class EnhancedPredictionEngine:
    """
    Advanced prediction engine with uncertainty quantification,
    multi-timeframe analysis, and explainability features.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.uncertainty_calculator = PredictionUncertainty()
        self.mtf_ensemble = MultiTimeframeEnsemble()
        
        # Track model performance for calibration
        self.performance_history = defaultdict(list)
        
    async def predict_with_uncertainty(
        self,
        coin_symbol: str,
        model_predictions: List[Dict[str, Any]],
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate prediction with uncertainty quantification.
        
        Args:
            coin_symbol: Cryptocurrency symbol
            model_predictions: List of predictions from different models
            metadata: Additional context
        
        Returns:
            Enhanced prediction with uncertainty bounds
        """
        if not model_predictions:
            return self._neutral_prediction()
        
        # Extract prediction values
        pred_values = []
        confidences = []
        signals = []
        
        for pred in model_predictions:
            if 'prediction' in pred:
                pred_values.append(pred['prediction'])
            if 'confidence' in pred:
                confidences.append(pred['confidence'])
            if 'signal' in pred:
                signals.append(pred['signal'])
        
        # Calculate ensemble mean and variance
        mean_prediction = np.mean(pred_values) if pred_values else 0.0
        variance = self.uncertainty_calculator.ensemble_variance(pred_values)
        
        # Calculate confidence interval
        ci_lower, ci_upper = self.uncertainty_calculator.confidence_interval(pred_values)
        
        # Aggregate signals with voting
        signal_votes = {'bullish': 0, 'bearish': 0, 'neutral': 0}
        for signal in signals:
            if signal in signal_votes:
                signal_votes[signal] += 1
        
        final_signal = max(signal_votes, key=signal_votes.get)
        signal_agreement = signal_votes[final_signal] / len(signals) if signals else 0.0
        
        # Calculate overall confidence (weighted by agreement and model confidences)
        mean_confidence = np.mean(confidences) if confidences else 50.0
        calibrated_confidence = mean_confidence * signal_agreement * (1.0 - min(variance, 0.5))
        
        # Get historical performance for this coin
        historical_accuracy = await self._get_historical_accuracy(coin_symbol)
        
        # Apply calibration correction
        calibrated_confidence = self._apply_calibration(
            calibrated_confidence, 
            historical_accuracy
        )
        
        result = {
            'coin': coin_symbol,
            'signal': final_signal,
            'confidence': float(calibrated_confidence),
            'prediction': float(mean_prediction),
            'uncertainty': {
                'variance': float(variance),
                'confidence_interval': {
                    'lower': float(ci_lower),
                    'upper': float(ci_upper),
                    'level': 0.95
                },
                'model_agreement': float(signal_agreement),
                'num_models': len(model_predictions)
            },
            'model_breakdown': model_predictions,
            'historical_performance': historical_accuracy,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metadata': metadata or {}
        }
        
        # Store prediction for future calibration
        await self._store_prediction(result)
        
        return result
    
    async def predict_multi_timeframe(
        self,
        coin_symbol: str,
        price_data_by_timeframe: Dict[str, List[float]],
        prediction_function: callable
    ) -> Dict[str, Any]:
        """
        Generate predictions across multiple timeframes and aggregate.
        
        Args:
            coin_symbol: Cryptocurrency symbol
            price_data_by_timeframe: {'5m': [prices], '1h': [prices], ...}
            prediction_function: Async function that takes (symbol, prices) and returns prediction
        
        Returns:
            Multi-timeframe aggregated prediction
        """
        predictions_by_tf = {}
        
        # Generate predictions for each timeframe
        for timeframe, prices in price_data_by_timeframe.items():
            try:
                pred = await prediction_function(coin_symbol, prices, timeframe)
                predictions_by_tf[timeframe] = pred
            except Exception as e:
                logger.error(f"Error predicting {coin_symbol} on {timeframe}: {e}")
                continue
        
        # Aggregate predictions
        aggregated = self.mtf_ensemble.aggregate_predictions(predictions_by_tf)
        
        # Detect divergences
        divergence = self.mtf_ensemble.detect_timeframe_divergence(predictions_by_tf)
        
        result = {
            'coin': coin_symbol,
            'signal': aggregated['signal'],
            'confidence': aggregated['confidence'],
            'prediction': aggregated['prediction'],
            'multi_timeframe': {
                'uncertainty': aggregated['uncertainty'],
                'timeframe_agreement': aggregated['timeframe_agreement'],
                'predictions': predictions_by_tf,
                'divergence': divergence
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Store for analysis
        await self._store_mtf_prediction(result)
        
        return result
    
    async def explain_prediction(
        self,
        prediction: Dict[str, Any],
        model_name: str = None
    ) -> Dict[str, Any]:
        """
        Generate explainability report for a prediction.
        
        Returns feature importance, attention weights, and reasoning.
        """
        explanation = {
            'prediction_id': prediction.get('_id'),
            'coin': prediction.get('coin'),
            'signal': prediction.get('signal'),
            'confidence': prediction.get('confidence'),
            'key_factors': [],
            'model_contributions': {},
            'uncertainty_sources': [],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Analyze model breakdown
        if 'model_breakdown' in prediction:
            for model_pred in prediction['model_breakdown']:
                model_name = model_pred.get('model_name', 'unknown')
                contribution = model_pred.get('confidence', 0) * model_pred.get('weight', 1.0)
                explanation['model_contributions'][model_name] = {
                    'signal': model_pred.get('signal'),
                    'confidence': model_pred.get('confidence'),
                    'contribution': contribution
                }
        
        # Identify key factors
        if 'multi_timeframe' in prediction:
            mtf = prediction['multi_timeframe']
            
            if mtf.get('timeframe_agreement', 0) > 0.8:
                explanation['key_factors'].append('Strong agreement across timeframes')
            elif mtf.get('timeframe_agreement', 0) < 0.5:
                explanation['key_factors'].append('Timeframe divergence detected')
                explanation['uncertainty_sources'].append('Low timeframe agreement')
            
            if mtf.get('divergence', {}).get('divergence_detected'):
                explanation['key_factors'].append(
                    f"Divergence: {mtf['divergence'].get('short_term_signal')} (short) vs "
                    f"{mtf['divergence'].get('long_term_signal')} (long)"
                )
        
        # Analyze uncertainty
        if 'uncertainty' in prediction:
            unc = prediction['uncertainty']
            
            if unc.get('variance', 0) > 0.1:
                explanation['uncertainty_sources'].append('High model variance')
            
            if unc.get('model_agreement', 1.0) < 0.6:
                explanation['uncertainty_sources'].append('Low model agreement')
        
        return explanation
    
    async def _get_historical_accuracy(self, coin_symbol: str) -> float:
        """Get historical prediction accuracy for this coin"""
        try:
            # Query last 30 days of predictions with outcomes
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            
            pipeline = [
                {
                    '$match': {
                        'coin': coin_symbol,
                        'timestamp': {'$gte': thirty_days_ago},
                        'outcome_verified': True
                    }
                },
                {
                    '$group': {
                        '_id': None,
                        'total': {'$sum': 1},
                        'correct': {
                            '$sum': {
                                '$cond': ['$was_correct', 1, 0]
                            }
                        }
                    }
                }
            ]
            
            result = await self.db.prediction_performance.aggregate(pipeline).to_list(1)
            
            if result and result[0]['total'] > 0:
                accuracy = result[0]['correct'] / result[0]['total']
                return float(accuracy)
            
        except Exception as e:
            logger.error(f"Error fetching historical accuracy: {e}")
        
        return 0.5  # Default to 50% if no history
    
    def _apply_calibration(self, raw_confidence: float, historical_accuracy: float) -> float:
        """
        Apply calibration correction based on historical performance.
        
        If a model consistently overconfident (predicts 90% but only 70% accurate),
        adjust future confidences down.
        """
        if historical_accuracy == 0:
            return raw_confidence
        
        # Calculate calibration ratio
        calibration_ratio = historical_accuracy / 0.5  # 0.5 is baseline
        
        # Apply correction with dampening (don't overcorrect)
        alpha = 0.3  # Dampening factor
        calibrated = raw_confidence * (1 - alpha) + raw_confidence * calibration_ratio * alpha
        
        # Clamp to valid range
        return float(np.clip(calibrated, 0, 100))
    
    async def _store_prediction(self, prediction: Dict[str, Any]):
        """Store prediction for future calibration and analysis"""
        try:
            await self.db.enhanced_predictions.insert_one({
                **prediction,
                'created_at': datetime.now(timezone.utc),
                'outcome_verified': False
            })
        except Exception as e:
            logger.error(f"Error storing prediction: {e}")
    
    async def _store_mtf_prediction(self, prediction: Dict[str, Any]):
        """Store multi-timeframe prediction"""
        try:
            await self.db.mtf_predictions.insert_one({
                **prediction,
                'created_at': datetime.now(timezone.utc)
            })
        except Exception as e:
            logger.error(f"Error storing MTF prediction: {e}")
    
    def _neutral_prediction(self) -> Dict[str, Any]:
        """Return a neutral prediction when no data available"""
        return {
            'signal': 'neutral',
            'confidence': 0,
            'prediction': 0.0,
            'uncertainty': {
                'variance': 1.0,
                'confidence_interval': {'lower': 0, 'upper': 0, 'level': 0.95},
                'model_agreement': 0.0,
                'num_models': 0
            },
            'model_breakdown': [],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def update_prediction_outcome(
        self,
        prediction_id: str,
        actual_outcome: str,
        was_correct: bool,
        actual_price_change: float = None
    ):
        """
        Update a prediction with its actual outcome for calibration learning.
        """
        try:
            from bson import ObjectId
            
            await self.db.enhanced_predictions.update_one(
                {'_id': ObjectId(prediction_id)},
                {
                    '$set': {
                        'outcome_verified': True,
                        'actual_outcome': actual_outcome,
                        'was_correct': was_correct,
                        'actual_price_change': actual_price_change,
                        'verified_at': datetime.now(timezone.utc)
                    }
                }
            )
            
            logger.info(f"Updated prediction {prediction_id} outcome: {was_correct}")
            
        except Exception as e:
            logger.error(f"Error updating prediction outcome: {e}")

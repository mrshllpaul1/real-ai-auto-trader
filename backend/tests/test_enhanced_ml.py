"""
Tests for Enhanced ML Prediction System

Tests the following components:
- EnhancedPredictionEngine
- OnlineLearningEngine
- PredictionUncertainty
- MultiTimeframeEnsemble
"""

import pytest
import numpy as np
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

# Import the services to test
import sys
sys.path.insert(0, '/home/runner/work/real-ai-auto-trader/real-ai-auto-trader/backend')

from services.enhanced_prediction_engine import (
    EnhancedPredictionEngine,
    PredictionUncertainty,
    MultiTimeframeEnsemble
)
from services.online_learning_engine import (
    OnlineLearningEngine,
    ConceptDriftDetector,
    AdaptiveLearningRate,
    OnlineLearningModel
)


class TestPredictionUncertainty:
    """Test uncertainty quantification methods"""
    
    def test_ensemble_variance(self):
        """Test ensemble variance calculation"""
        predictions = [0.05, 0.04, 0.06, 0.05]
        variance = PredictionUncertainty.ensemble_variance(predictions)
        
        assert variance >= 0
        assert variance < 0.001  # Low variance for similar predictions
    
    def test_ensemble_variance_high_disagreement(self):
        """Test variance with high disagreement"""
        predictions = [0.10, -0.05, 0.15, -0.10]
        variance = PredictionUncertainty.ensemble_variance(predictions)
        
        assert variance > 0.01  # High variance for disagreeing predictions
    
    def test_confidence_interval(self):
        """Test confidence interval calculation"""
        predictions = [0.05, 0.04, 0.06, 0.05, 0.04]
        lower, upper = PredictionUncertainty.confidence_interval(predictions)
        
        assert lower < upper
        assert lower <= np.mean(predictions) <= upper
    
    def test_prediction_entropy(self):
        """Test entropy calculation"""
        # Low entropy (confident prediction)
        low_entropy_probs = [0.9, 0.05, 0.05]
        low_entropy = PredictionUncertainty.prediction_entropy(low_entropy_probs)
        
        # High entropy (uncertain prediction)
        high_entropy_probs = [0.33, 0.33, 0.34]
        high_entropy = PredictionUncertainty.prediction_entropy(high_entropy_probs)
        
        assert high_entropy > low_entropy
    
    def test_calibration_score(self):
        """Test calibration score"""
        # Perfect calibration
        score_perfect = PredictionUncertainty.calibration_score(0.80, 0.80)
        assert score_perfect == 1.0
        
        # Poor calibration
        score_poor = PredictionUncertainty.calibration_score(0.90, 0.50)
        assert score_poor < 0.5


class TestMultiTimeframeEnsemble:
    """Test multi-timeframe ensemble methods"""
    
    def test_aggregate_predictions_bullish(self):
        """Test aggregation with all bullish signals"""
        mtf = MultiTimeframeEnsemble()
        
        predictions = {
            '5m': {'signal': 'bullish', 'confidence': 70, 'prediction': 0.05},
            '1h': {'signal': 'bullish', 'confidence': 75, 'prediction': 0.04},
            '4h': {'signal': 'bullish', 'confidence': 80, 'prediction': 0.06}
        }
        
        result = mtf.aggregate_predictions(predictions)
        
        assert result['signal'] == 'bullish'
        assert result['confidence'] > 60
        assert result['timeframe_agreement'] == 1.0
    
    def test_aggregate_predictions_mixed(self):
        """Test aggregation with mixed signals"""
        mtf = MultiTimeframeEnsemble()
        
        predictions = {
            '5m': {'signal': 'bullish', 'confidence': 60, 'prediction': 0.02},
            '1h': {'signal': 'bearish', 'confidence': 65, 'prediction': -0.03},
            '4h': {'signal': 'bullish', 'confidence': 70, 'prediction': 0.04}
        }
        
        result = mtf.aggregate_predictions(predictions)
        
        assert result['timeframe_agreement'] < 1.0
        assert 'by_timeframe' in result
    
    def test_detect_timeframe_divergence(self):
        """Test divergence detection"""
        mtf = MultiTimeframeEnsemble()
        
        # Diverging signals
        predictions = {
            '5m': {'signal': 'bullish', 'confidence': 70, 'prediction': 0.05},
            '15m': {'signal': 'bullish', 'confidence': 65, 'prediction': 0.03},
            '4h': {'signal': 'bearish', 'confidence': 75, 'prediction': -0.04},
            '1d': {'signal': 'bearish', 'confidence': 80, 'prediction': -0.06}
        }
        
        divergence = mtf.detect_timeframe_divergence(predictions)
        
        assert divergence['divergence_detected'] == True
        assert divergence['short_term_signal'] == 'bullish'
        assert divergence['long_term_signal'] == 'bearish'


class TestConceptDriftDetector:
    """Test concept drift detection"""
    
    def test_no_drift_stable_errors(self):
        """Test that stable errors don't trigger drift"""
        detector = ConceptDriftDetector(window_size=20, threshold=0.15)
        
        # Add stable errors
        for _ in range(30):
            detector.add_error(0.15)
        
        drift_detected, magnitude = detector.detect_drift()
        
        assert drift_detected == False
        assert magnitude < 0.15
    
    def test_drift_detected_on_change(self):
        """Test drift detection when errors change significantly"""
        detector = ConceptDriftDetector(window_size=20, threshold=0.15)
        
        # Add baseline errors
        for _ in range(25):
            detector.add_error(0.10)
        
        # Add higher errors (concept drift)
        for _ in range(15):
            detector.add_error(0.30)
        
        drift_detected, magnitude = detector.detect_drift()
        
        # Should detect drift due to significant error increase
        assert magnitude > 0.10


class TestAdaptiveLearningRate:
    """Test adaptive learning rate adjustment"""
    
    def test_lr_increases_on_improvement(self):
        """Test LR increases when performance improves"""
        alr = AdaptiveLearningRate(initial_lr=0.01)
        
        # Add improving losses
        for i in range(20):
            loss = 0.5 - i * 0.02  # Decreasing loss
            alr.update(loss, market_volatility=0.02)
        
        # LR should increase with improvement
        assert alr.get_lr() > 0.01
    
    def test_lr_decreases_on_degradation(self):
        """Test LR decreases when performance degrades"""
        alr = AdaptiveLearningRate(initial_lr=0.01)
        
        # Add degrading losses
        for i in range(20):
            loss = 0.2 + i * 0.02  # Increasing loss
            alr.update(loss, market_volatility=0.02)
        
        # LR should decrease with degradation
        assert alr.get_lr() < 0.01
    
    def test_lr_adjusts_for_volatility(self):
        """Test LR adjusts based on market volatility"""
        alr = AdaptiveLearningRate(initial_lr=0.01)
        
        # High volatility
        lr_high_vol = alr.update(0.2, market_volatility=0.08)
        assert alr.regime == 'volatile'
        assert lr_high_vol < 0.01
        
        # Low volatility
        lr_low_vol = alr.update(0.2, market_volatility=0.005)
        assert alr.regime == 'consolidating'
        assert lr_low_vol > 0.01


class TestOnlineLearningModel:
    """Test online learning model"""
    
    def test_model_initialization(self):
        """Test model initializes correctly"""
        model = OnlineLearningModel(model_type='classification', feature_dim=5)
        
        assert model.model_fitted == False
        assert model.update_count == 0
        assert len(model.performance_history) == 0
    
    def test_partial_fit_classification(self):
        """Test incremental training for classification"""
        model = OnlineLearningModel(model_type='classification', feature_dim=5)
        
        # Generate synthetic data
        X = np.random.randn(20, 5)
        y = np.random.randint(0, 3, 20)  # 3 classes
        
        loss = model.partial_fit(X, y)
        
        assert model.model_fitted == True
        assert model.update_count == 1
        assert loss >= 0
    
    def test_predict_before_training(self):
        """Test prediction returns neutral when not trained"""
        model = OnlineLearningModel(model_type='classification', feature_dim=5)
        
        X = np.random.randn(5, 5)
        predictions = model.predict(X)
        
        # Should return neutral predictions
        assert len(predictions) == 5
        assert all(p == 1 for p in predictions)  # All neutral
    
    def test_predict_after_training(self):
        """Test prediction works after training"""
        model = OnlineLearningModel(model_type='classification', feature_dim=5)
        
        # Train
        X_train = np.random.randn(50, 5)
        y_train = np.random.randint(0, 3, 50)
        model.partial_fit(X_train, y_train)
        
        # Predict
        X_test = np.random.randn(10, 5)
        predictions = model.predict(X_test)
        
        assert len(predictions) == 10
        assert all(0 <= p <= 2 for p in predictions)
    
    def test_performance_tracking(self):
        """Test performance metrics are tracked"""
        model = OnlineLearningModel(model_type='classification', feature_dim=5)
        
        # Multiple updates
        for _ in range(5):
            X = np.random.randn(20, 5)
            y = np.random.randint(0, 3, 20)
            model.partial_fit(X, y)
        
        performance = model.get_performance()
        
        assert 'avg_loss' in performance
        assert 'recent_loss' in performance
        assert 'trend' in performance
        assert model.update_count == 5


@pytest.mark.asyncio
class TestEnhancedPredictionEngine:
    """Test enhanced prediction engine"""
    
    async def test_predict_with_uncertainty_basic(self):
        """Test basic prediction with uncertainty"""
        # Mock database
        mock_db = MagicMock()
        mock_db.prediction_performance = MagicMock()
        mock_db.prediction_performance.aggregate = MagicMock()
        mock_db.prediction_performance.aggregate.return_value.to_list = AsyncMock(return_value=[])
        mock_db.enhanced_predictions = MagicMock()
        mock_db.enhanced_predictions.insert_one = AsyncMock()
        
        engine = EnhancedPredictionEngine(mock_db)
        
        model_predictions = [
            {'model_name': 'lstm', 'signal': 'bullish', 'confidence': 75, 'prediction': 0.05},
            {'model_name': 'technical', 'signal': 'bullish', 'confidence': 70, 'prediction': 0.04}
        ]
        
        result = await engine.predict_with_uncertainty('BTC', model_predictions)
        
        assert 'signal' in result
        assert 'confidence' in result
        assert 'uncertainty' in result
        assert 'model_breakdown' in result
        assert result['signal'] == 'bullish'
        assert result['uncertainty']['model_agreement'] == 1.0
    
    async def test_predict_with_uncertainty_disagreement(self):
        """Test prediction with disagreeing models"""
        mock_db = MagicMock()
        mock_db.prediction_performance = MagicMock()
        mock_db.prediction_performance.aggregate = MagicMock()
        mock_db.prediction_performance.aggregate.return_value.to_list = AsyncMock(return_value=[])
        mock_db.enhanced_predictions = MagicMock()
        mock_db.enhanced_predictions.insert_one = AsyncMock()
        
        engine = EnhancedPredictionEngine(mock_db)
        
        model_predictions = [
            {'model_name': 'lstm', 'signal': 'bullish', 'confidence': 75, 'prediction': 0.05},
            {'model_name': 'technical', 'signal': 'bearish', 'confidence': 70, 'prediction': -0.04}
        ]
        
        result = await engine.predict_with_uncertainty('BTC', model_predictions)
        
        # Model agreement should be low
        assert result['uncertainty']['model_agreement'] < 1.0
        # Variance should be high
        assert result['uncertainty']['variance'] > 0.001


@pytest.mark.asyncio
class TestOnlineLearningEngine:
    """Test online learning engine"""
    
    async def test_get_or_create_model(self):
        """Test model creation"""
        mock_db = MagicMock()
        
        engine = OnlineLearningEngine(mock_db)
        model = await engine.get_or_create_model('BTC', 'classification', 5)
        
        assert model is not None
        assert isinstance(model, OnlineLearningModel)
    
    async def test_update_model_online(self):
        """Test online model update"""
        mock_db = MagicMock()
        mock_db.online_learning_updates = MagicMock()
        mock_db.online_learning_updates.insert_one = AsyncMock()
        
        engine = OnlineLearningEngine(mock_db)
        
        features = np.random.randn(10, 5)
        labels = np.random.randint(0, 3, 10)
        
        result = await engine.update_model_online('BTC', features, labels)
        
        assert 'status' in result
        # First few calls should buffer
        assert result['status'] in ['buffered', 'updated']
    
    async def test_predict_online(self):
        """Test online prediction"""
        mock_db = MagicMock()
        
        engine = OnlineLearningEngine(mock_db)
        
        # Train model first
        features_train = np.random.randn(50, 5)
        labels_train = np.random.randint(0, 3, 50)
        
        for i in range(5):  # Multiple batches
            batch_features = features_train[i*10:(i+1)*10]
            batch_labels = labels_train[i*10:(i+1)*10]
            await engine.update_model_online('BTC', batch_features, batch_labels)
        
        # Now predict
        features_test = np.random.randn(1, 5)
        result = await engine.predict_online('BTC', features_test, return_probabilities=True)
        
        assert 'signal' in result
        assert 'confidence' in result
        if result['model_status'] == 'trained':
            assert 'probabilities' in result


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])

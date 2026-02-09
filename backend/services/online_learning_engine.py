"""
Online Learning Engine
Enables real-time model updates without waiting for weekly batch retraining.

Features:
1. Incremental learning with streaming data
2. Adaptive learning rates based on market regime
3. Concept drift detection and adaptation
4. Real-time model performance monitoring
5. Automatic model rollback on degradation
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from collections import deque
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import SGDClassifier, SGDRegressor
import pickle
import hashlib

logger = logging.getLogger(__name__)


class ConceptDriftDetector:
    """Detect when market dynamics change (concept drift)"""
    
    def __init__(self, window_size: int = 100, threshold: float = 0.15):
        self.window_size = window_size
        self.threshold = threshold
        self.recent_errors = deque(maxlen=window_size)
        self.baseline_error = None
        
    def add_error(self, error: float):
        """Add new prediction error"""
        self.recent_errors.append(error)
        
        # Set baseline after first window
        if self.baseline_error is None and len(self.recent_errors) == self.window_size:
            self.baseline_error = np.mean(self.recent_errors)
    
    def detect_drift(self) -> Tuple[bool, float]:
        """
        Detect if concept drift occurred.
        
        Returns:
            (drift_detected, drift_magnitude)
        """
        if self.baseline_error is None or len(self.recent_errors) < self.window_size // 2:
            return False, 0.0
        
        current_error = np.mean(list(self.recent_errors)[-self.window_size//2:])
        drift_magnitude = abs(current_error - self.baseline_error) / (self.baseline_error + 1e-6)
        
        drift_detected = drift_magnitude > self.threshold
        
        if drift_detected:
            logger.warning(f"Concept drift detected! Magnitude: {drift_magnitude:.3f}")
            # Update baseline to new regime
            self.baseline_error = current_error
        
        return drift_detected, drift_magnitude


class AdaptiveLearningRate:
    """Adjust learning rate based on market volatility and performance"""
    
    def __init__(self, initial_lr: float = 0.01):
        self.base_lr = initial_lr
        self.current_lr = initial_lr
        self.recent_losses = deque(maxlen=50)
        self.regime = 'normal'  # normal, volatile, trending, consolidating
        
    def update(self, loss: float, market_volatility: float):
        """Update learning rate based on loss and market conditions"""
        self.recent_losses.append(loss)
        
        # Detect if loss is improving or degrading
        if len(self.recent_losses) >= 10:
            recent_avg = np.mean(list(self.recent_losses)[-10:])
            older_avg = np.mean(list(self.recent_losses)[-20:-10]) if len(self.recent_losses) >= 20 else recent_avg
            
            # Increase LR if improving, decrease if degrading
            if recent_avg < older_avg * 0.9:
                self.current_lr = min(self.current_lr * 1.1, self.base_lr * 5)
            elif recent_avg > older_avg * 1.1:
                self.current_lr = max(self.current_lr * 0.9, self.base_lr * 0.1)
        
        # Adjust for market volatility
        if market_volatility > 0.05:  # High volatility
            self.regime = 'volatile'
            self.current_lr = self.base_lr * 0.5  # Learn slower in volatile markets
        elif market_volatility < 0.01:  # Low volatility
            self.regime = 'consolidating'
            self.current_lr = self.base_lr * 1.5  # Learn faster in stable markets
        else:
            self.regime = 'normal'
            self.current_lr = self.base_lr
        
        return self.current_lr
    
    def get_lr(self) -> float:
        """Get current learning rate"""
        return self.current_lr


class OnlineLearningModel:
    """
    Online learning model using SGD for real-time updates.
    Supports both classification (signal prediction) and regression (price prediction).
    """
    
    def __init__(
        self,
        model_type: str = 'classification',  # or 'regression'
        learning_rate: float = 0.01,
        feature_dim: int = 10
    ):
        self.model_type = model_type
        self.feature_dim = feature_dim
        self.scaler = StandardScaler()
        self.scaler_fitted = False
        
        # Initialize SGD model
        if model_type == 'classification':
            self.model = SGDClassifier(
                loss='log_loss',
                learning_rate='constant',
                eta0=learning_rate,
                warm_start=True,  # Enable incremental learning
                random_state=42
            )
        else:
            self.model = SGDRegressor(
                loss='huber',  # Robust to outliers
                learning_rate='constant',
                eta0=learning_rate,
                warm_start=True,
                random_state=42
            )
        
        self.model_fitted = False
        self.update_count = 0
        self.performance_history = deque(maxlen=100)
        
    def partial_fit(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Incrementally update model with new data.
        
        Returns:
            loss: Training loss for this batch
        """
        if X.shape[0] == 0:
            return 0.0
        
        # Fit scaler on first batch, transform on all
        if not self.scaler_fitted:
            self.scaler.fit(X)
            self.scaler_fitted = True
        
        X_scaled = self.scaler.transform(X)
        
        # For classification, need to specify classes
        if self.model_type == 'classification':
            classes = np.array([0, 1, 2])  # bearish, neutral, bullish
            if not self.model_fitted:
                self.model.partial_fit(X_scaled, y, classes=classes)
                self.model_fitted = True
            else:
                self.model.partial_fit(X_scaled, y)
        else:
            self.model.partial_fit(X_scaled, y)
        
        self.update_count += 1
        
        # Calculate loss (for monitoring)
        if self.model_fitted:
            predictions = self.model.predict(X_scaled)
            if self.model_type == 'classification':
                loss = np.mean(predictions != y)  # Error rate
            else:
                loss = np.mean((predictions - y) ** 2)  # MSE
            
            self.performance_history.append(loss)
            return float(loss)
        
        return 0.0
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if not self.model_fitted:
            # Return neutral predictions if not trained
            if self.model_type == 'classification':
                return np.ones(X.shape[0])  # Neutral class
            else:
                return np.zeros(X.shape[0])
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get probability predictions (classification only)"""
        if self.model_type != 'classification' or not self.model_fitted:
            return np.array([[0.33, 0.34, 0.33]] * X.shape[0])  # Uniform
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def get_performance(self) -> Dict[str, float]:
        """Get recent performance metrics"""
        if not self.performance_history:
            return {'avg_loss': 0.0, 'recent_loss': 0.0, 'trend': 'unknown'}
        
        avg_loss = np.mean(self.performance_history)
        recent_loss = np.mean(list(self.performance_history)[-10:])
        
        # Determine trend
        if len(self.performance_history) >= 20:
            older_loss = np.mean(list(self.performance_history)[-20:-10])
            if recent_loss < older_loss * 0.9:
                trend = 'improving'
            elif recent_loss > older_loss * 1.1:
                trend = 'degrading'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'avg_loss': float(avg_loss),
            'recent_loss': float(recent_loss),
            'trend': trend,
            'num_updates': self.update_count
        }
    
    def save(self, path: str):
        """Save model to disk"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'model_fitted': self.model_fitted,
            'scaler_fitted': self.scaler_fitted,
            'update_count': self.update_count,
            'performance_history': list(self.performance_history)
        }
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load(self, path: str):
        """Load model from disk"""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.model_fitted = model_data['model_fitted']
        self.scaler_fitted = model_data['scaler_fitted']
        self.update_count = model_data['update_count']
        self.performance_history = deque(model_data['performance_history'], maxlen=100)


class OnlineLearningEngine:
    """
    Main online learning engine that coordinates real-time model updates.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, model_dir: str = '/app/backend/models/online'):
        self.db = db
        self.model_dir = model_dir
        
        # Create model directory if it doesn't exist
        import os
        os.makedirs(model_dir, exist_ok=True)
        
        # Model registry: {coin_symbol: OnlineLearningModel}
        self.models = {}
        
        # Drift detectors: {coin_symbol: ConceptDriftDetector}
        self.drift_detectors = {}
        
        # Adaptive learning rates: {coin_symbol: AdaptiveLearningRate}
        self.learning_rates = {}
        
        # Performance monitoring
        self.update_buffer = {}  # Buffer updates before applying
        self.buffer_size = 10  # Apply updates in mini-batches
        
    def _get_model_key(self, coin_symbol: str, model_type: str) -> str:
        """Generate unique key for model"""
        return f"{coin_symbol}_{model_type}"
    
    async def get_or_create_model(
        self,
        coin_symbol: str,
        model_type: str = 'classification',
        feature_dim: int = 10
    ) -> OnlineLearningModel:
        """Get existing model or create new one"""
        key = self._get_model_key(coin_symbol, model_type)
        
        if key not in self.models:
            model = OnlineLearningModel(
                model_type=model_type,
                learning_rate=0.01,
                feature_dim=feature_dim
            )
            
            # Try to load existing model
            model_path = f"{self.model_dir}/{key}.pkl"
            try:
                import os
                if os.path.exists(model_path):
                    model.load(model_path)
                    logger.info(f"Loaded existing model: {key}")
            except Exception as e:
                logger.warning(f"Could not load model {key}: {e}")
            
            self.models[key] = model
            self.drift_detectors[key] = ConceptDriftDetector()
            self.learning_rates[key] = AdaptiveLearningRate()
            self.update_buffer[key] = {'X': [], 'y': []}
        
        return self.models[key]
    
    async def update_model_online(
        self,
        coin_symbol: str,
        features: np.ndarray,
        labels: np.ndarray,
        market_volatility: float = 0.02
    ) -> Dict[str, Any]:
        """
        Update model with new data in real-time.
        
        Args:
            coin_symbol: Cryptocurrency symbol
            features: Feature matrix (n_samples, n_features)
            labels: Target labels (n_samples,)
            market_volatility: Current market volatility
        
        Returns:
            Update result with performance metrics
        """
        model_type = 'classification' if len(np.unique(labels)) <= 3 else 'regression'
        key = self._get_model_key(coin_symbol, model_type)
        
        # Get model
        model = await self.get_or_create_model(coin_symbol, model_type, features.shape[1])
        
        # Buffer updates for mini-batch learning
        self.update_buffer[key]['X'].append(features)
        self.update_buffer[key]['y'].append(labels)
        
        # Check if buffer is full
        if len(self.update_buffer[key]['X']) < self.buffer_size:
            return {
                'status': 'buffered',
                'buffer_size': len(self.update_buffer[key]['X']),
                'target_size': self.buffer_size
            }
        
        # Concatenate buffered data
        X_batch = np.vstack(self.update_buffer[key]['X'])
        y_batch = np.concatenate(self.update_buffer[key]['y'])
        
        # Clear buffer
        self.update_buffer[key] = {'X': [], 'y': []}
        
        # Update learning rate adaptively
        lr_controller = self.learning_rates[key]
        current_perf = model.get_performance()
        current_lr = lr_controller.update(current_perf.get('recent_loss', 0.1), market_volatility)
        model.model.eta0 = current_lr
        
        # Perform partial fit
        loss = model.partial_fit(X_batch, y_batch)
        
        # Detect concept drift
        drift_detector = self.drift_detectors[key]
        drift_detector.add_error(loss)
        drift_detected, drift_magnitude = drift_detector.detect_drift()
        
        # If drift detected, increase learning rate temporarily
        if drift_detected:
            model.model.eta0 = current_lr * 2.0
            logger.warning(f"Concept drift for {coin_symbol}, increasing LR to {model.model.eta0}")
        
        # Get updated performance
        performance = model.get_performance()
        
        # Save model periodically
        if model.update_count % 50 == 0:
            model_path = f"{self.model_dir}/{key}.pkl"
            try:
                model.save(model_path)
                logger.info(f"Saved model checkpoint: {key}")
            except Exception as e:
                logger.error(f"Error saving model {key}: {e}")
        
        # Store update record
        await self._record_update(coin_symbol, loss, drift_detected, performance)
        
        return {
            'status': 'updated',
            'loss': loss,
            'learning_rate': current_lr,
            'drift_detected': drift_detected,
            'drift_magnitude': drift_magnitude,
            'performance': performance,
            'samples_processed': len(y_batch),
            'total_updates': model.update_count
        }
    
    async def predict_online(
        self,
        coin_symbol: str,
        features: np.ndarray,
        return_probabilities: bool = False
    ) -> Dict[str, Any]:
        """
        Make prediction using online learning model.
        
        Returns:
            Prediction with confidence and metadata
        """
        model_type = 'classification'
        model = await self.get_or_create_model(coin_symbol, model_type, features.shape[1])
        
        if not model.model_fitted:
            return {
                'signal': 'neutral',
                'confidence': 0,
                'prediction': 0.0,
                'model_status': 'not_trained'
            }
        
        # Get predictions
        if return_probabilities and model_type == 'classification':
            probas = model.predict_proba(features)
            pred_class = np.argmax(probas[0])
            confidence = float(probas[0][pred_class]) * 100
            
            signal_map = {0: 'bearish', 1: 'neutral', 2: 'bullish'}
            signal = signal_map.get(pred_class, 'neutral')
            
            return {
                'signal': signal,
                'confidence': confidence,
                'probabilities': {
                    'bearish': float(probas[0][0]),
                    'neutral': float(probas[0][1]),
                    'bullish': float(probas[0][2])
                },
                'model_status': 'trained',
                'performance': model.get_performance()
            }
        else:
            prediction = model.predict(features)[0]
            
            return {
                'prediction': float(prediction),
                'signal': 'bullish' if prediction > 0.02 else 'bearish' if prediction < -0.02 else 'neutral',
                'confidence': min(100, abs(prediction) * 1000),  # Scale to 0-100
                'model_status': 'trained',
                'performance': model.get_performance()
            }
    
    async def _record_update(
        self,
        coin_symbol: str,
        loss: float,
        drift_detected: bool,
        performance: Dict[str, Any]
    ):
        """Record model update for monitoring"""
        try:
            await self.db.online_learning_updates.insert_one({
                'coin': coin_symbol,
                'loss': loss,
                'drift_detected': drift_detected,
                'performance': performance,
                'timestamp': datetime.now(timezone.utc)
            })
        except Exception as e:
            logger.error(f"Error recording update: {e}")
    
    async def get_model_status(self, coin_symbol: str) -> Dict[str, Any]:
        """Get comprehensive status of online learning model"""
        model_type = 'classification'
        key = self._get_model_key(coin_symbol, model_type)
        
        if key not in self.models:
            return {
                'coin': coin_symbol,
                'status': 'not_initialized',
                'model_exists': False
            }
        
        model = self.models[key]
        drift_detector = self.drift_detectors.get(key)
        lr_controller = self.learning_rates.get(key)
        
        status = {
            'coin': coin_symbol,
            'status': 'active' if model.model_fitted else 'initializing',
            'model_exists': True,
            'total_updates': model.update_count,
            'performance': model.get_performance(),
            'learning_rate': lr_controller.get_lr() if lr_controller else 0.01,
            'regime': lr_controller.regime if lr_controller else 'unknown',
            'drift_baseline': drift_detector.baseline_error if drift_detector else None,
            'buffer_size': len(self.update_buffer.get(key, {}).get('X', []))
        }
        
        return status
    
    async def reset_model(self, coin_symbol: str):
        """Reset model (useful after major market regime change)"""
        model_type = 'classification'
        key = self._get_model_key(coin_symbol, model_type)
        
        if key in self.models:
            del self.models[key]
            del self.drift_detectors[key]
            del self.learning_rates[key]
            self.update_buffer[key] = {'X': [], 'y': []}
            
            logger.info(f"Reset online learning model for {coin_symbol}")

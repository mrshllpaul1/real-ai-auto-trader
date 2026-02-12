"""
ML/DL Regime Prediction Engine
Multiple models compete to predict market regimes.
Best model is automatically selected based on accuracy.

ENHANCED: Now includes advanced DL models for comparison:
- CNN-LSTM Hybrid
- Bidirectional LSTM
- Attention-based model
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import numpy as np
from enum import Enum
import pickle
import os
import logging

logger = logging.getLogger(__name__)

# ML Libraries
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings('ignore')

# Lazy TensorFlow loading - defer until actually needed
TF_AVAILABLE = None  # Will be set on first check
_tf_module = None
EarlyStopping = None

def _ensure_tf():
    """Lazy load TensorFlow only when needed for DL models"""
    global TF_AVAILABLE, _tf_module
    if TF_AVAILABLE is not None:
        return TF_AVAILABLE
    try:
        import tensorflow as tf
        _tf_module = tf
        TF_AVAILABLE = True
        logging.info("TensorFlow loaded for regime predictor")
    except ImportError:
        TF_AVAILABLE = False
        logging.warning("TensorFlow not available - DL models disabled")
    return TF_AVAILABLE

def _get_tf():
    """Get TensorFlow module, loading if needed"""
    _ensure_tf()
    return _tf_module


class RegimeLabel(Enum):
    """Regime labels for classification"""
    STRONG_BULL = 0
    BULL = 1
    SIDEWAYS = 2
    BEAR = 3
    STRONG_BEAR = 4
    HIGH_VOLATILITY = 5
    ACCUMULATION = 6


REGIME_NAMES = {
    0: 'strong_bull',
    1: 'bull',
    2: 'sideways',
    3: 'bear',
    4: 'strong_bear',
    5: 'high_volatility',
    6: 'accumulation'
}


class RegimePredictionEngine:
    """
    Multi-model regime prediction system with automatic model selection.
    
    ML Models:
    - Random Forest
    - Gradient Boosting (XGBoost-like)
    - Support Vector Machine
    
    DL Models:
    - LSTM Neural Network
    - GRU Neural Network
    - Bidirectional LSTM
    - CNN-LSTM Hybrid (convolutional + recurrent)
    - Transformer-style Attention
    
    The system tracks accuracy of each model and automatically selects the best.
    Supports model persistence (save/load to disk).
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.scaler = StandardScaler()
        self.models = {}
        self.model_accuracy = {}
        self.model_metadata = {}  # Store training info per model
        self.best_model = None
        self.is_trained = False
        self.sequence_length = 14  # Days of history for DL models
        self.model_path = "/app/backend/models/regime"
        
        # Ensure model directory exists
        os.makedirs(self.model_path, exist_ok=True)
        
        # Initialize ML models
        self._init_ml_models()
        
        # Initialize DL models lazily - don't load TensorFlow at startup
        # They will be initialized when first needed
        self._dl_initialized = False
        
        # Try to load saved ML models (not DL)
        self._load_saved_models()
    
    def _load_saved_models(self):
        """Attempt to load previously saved ML models (DL models loaded lazily)"""
        try:
            # Load ML models only - DL models loaded lazily when needed
            ml_path = os.path.join(self.model_path, "ml_models.pkl")
            if os.path.exists(ml_path):
                with open(ml_path, 'rb') as f:
                    saved_data = pickle.load(f)
                    self.models.update(saved_data.get('models', {}))
                    self.model_accuracy = saved_data.get('accuracy', {})
                    self.best_model = saved_data.get('best_model')
                    self.scaler = saved_data.get('scaler', self.scaler)
                    self.is_trained = saved_data.get('is_trained', False)
                logger.info(f"✅ Regime predictor loaded ML models from disk (best: {self.best_model})")
            
            # DL models will be loaded lazily when _ensure_dl_models() is called
                        
        except Exception as e:
            logger.warning(f"Could not load saved regime models: {e}")
    
    def _ensure_dl_models(self):
        """Lazy-load DL models when first needed"""
        if self._dl_initialized:
            return _ensure_tf()
        
        if not _ensure_tf():
            return False
        
        # Now load TensorFlow components
        global EarlyStopping
        tf = _get_tf()
        from tensorflow.keras.callbacks import EarlyStopping as TfEarlyStopping
        from tensorflow.keras.models import load_model
        EarlyStopping = TfEarlyStopping
        
        # Initialize DL model structures
        self._init_dl_models()
        
        # Load saved DL models if they exist
        for model_name in ['lstm', 'gru', 'bidirectional_lstm', 'cnn_lstm', 'attention']:
            model_file = os.path.join(self.model_path, f"{model_name}.keras")
            if os.path.exists(model_file):
                try:
                    self.models[model_name] = load_model(model_file)
                    logger.info(f"  Loaded DL model: {model_name}")
                except Exception as e:
                    logger.warning(f"Failed to load {model_name}: {e}")
        
        self._dl_initialized = True
        return True
    
    def save_models(self) -> bool:
        """Save trained models to disk"""
        try:
            # Save ML models and metadata
            ml_data = {
                'models': {k: v for k, v in self.models.items() 
                          if k in ['random_forest', 'gradient_boosting', 'svm']},
                'accuracy': self.model_accuracy,
                'best_model': self.best_model,
                'scaler': self.scaler,
                'is_trained': self.is_trained,
                'saved_at': datetime.now(timezone.utc).isoformat()
            }
            
            ml_path = os.path.join(self.model_path, "ml_models.pkl")
            with open(ml_path, 'wb') as f:
                pickle.dump(ml_data, f)
            
            # Save DL models if initialized
            if self._dl_initialized and _ensure_tf():
                from tensorflow.keras.models import load_model
                for model_name in ['lstm', 'gru', 'bidirectional_lstm', 'cnn_lstm', 'attention']:
                    if model_name in self.models and hasattr(self.models[model_name], 'save'):
                        model_file = os.path.join(self.model_path, f"{model_name}.keras")
                        self.models[model_name].save(model_file)
            
            logger.info(f"✅ Regime predictor saved models to {self.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save regime models: {e}")
            return False
    
    def _init_ml_models(self):
        """Initialize machine learning models"""
        self.models['random_forest'] = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        )
        self.model_metadata['random_forest'] = {
            'type': 'ML',
            'category': 'ensemble',
            'description': 'Ensemble of decision trees with bagging'
        }
        
        self.models['gradient_boosting'] = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        self.model_metadata['gradient_boosting'] = {
            'type': 'ML',
            'category': 'ensemble',
            'description': 'Sequential boosting of weak learners'
        }
        
        self.models['svm'] = SVC(
            kernel='rbf',
            C=1.0,
            probability=True,
            random_state=42
        )
        self.model_metadata['svm'] = {
            'type': 'ML',
            'category': 'kernel',
            'description': 'Support Vector Machine with RBF kernel'
        }
    
    def _init_dl_models(self):
        """Initialize deep learning models (called lazily)"""
        if not _ensure_tf():
            return
        
        # Import TF components now that we've loaded TF
        tf = _get_tf()
        from tensorflow.keras.models import Sequential, Model
        from tensorflow.keras.layers import (
            LSTM, GRU, Dense, Dropout, BatchNormalization, 
            Conv1D, MaxPooling1D, Flatten, Bidirectional,
            Input, MultiHeadAttention, LayerNormalization,
            GlobalAveragePooling1D
        )
        from tensorflow.keras.optimizers import Adam
        
        # Store these for model building
        self._tf = tf
        self._Sequential = Sequential
        self._Model = Model
        self._keras_layers = {
            'LSTM': LSTM, 'GRU': GRU, 'Dense': Dense, 'Dropout': Dropout,
            'BatchNormalization': BatchNormalization, 'Conv1D': Conv1D,
            'MaxPooling1D': MaxPooling1D, 'Flatten': Flatten,
            'Bidirectional': Bidirectional, 'Input': Input,
            'MultiHeadAttention': MultiHeadAttention, 
            'LayerNormalization': LayerNormalization,
            'GlobalAveragePooling1D': GlobalAveragePooling1D
        }
        self._Adam = Adam
        
        # LSTM model
        self.models['lstm'] = self._build_lstm_model()
        self.model_metadata['lstm'] = {
            'type': 'DL',
            'category': 'recurrent',
            'description': 'Long Short-Term Memory network for sequence learning'
        }
        
        # GRU model  
        self.models['gru'] = self._build_gru_model()
        self.model_metadata['gru'] = {
            'type': 'DL',
            'category': 'recurrent',
            'description': 'Gated Recurrent Unit - lighter than LSTM'
        }
        
        # Bidirectional LSTM
        self.models['bilstm'] = self._build_bilstm_model()
        self.model_metadata['bilstm'] = {
            'type': 'DL',
            'category': 'recurrent',
            'description': 'Bidirectional LSTM - learns forward and backward patterns'
        }
        
        # CNN-LSTM Hybrid
        self.models['cnn_lstm'] = self._build_cnn_lstm_model()
        self.model_metadata['cnn_lstm'] = {
            'type': 'DL',
            'category': 'hybrid',
            'description': 'CNN for pattern extraction + LSTM for sequence learning'
        }
        
        # Transformer-style attention
        self.models['attention'] = self._build_attention_model()
        self.model_metadata['attention'] = {
            'type': 'DL',
            'category': 'attention',
            'description': 'Multi-head attention mechanism for regime patterns'
        }
    
    def _build_lstm_model(self, input_shape: Tuple = None):
        """Build LSTM neural network"""
        if input_shape is None:
            input_shape = (self.sequence_length, 10)  # Default feature count
        
        Sequential = self._Sequential
        LSTM = self._keras_layers['LSTM']
        Dropout = self._keras_layers['Dropout']
        BatchNormalization = self._keras_layers['BatchNormalization']
        Dense = self._keras_layers['Dense']
        Adam = self._Adam
        
        model = Sequential([
            LSTM(64, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            BatchNormalization(),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dropout(0.1),
            Dense(len(RegimeLabel), activation='softmax')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def _build_gru_model(self, input_shape: Tuple = None):
        """Build GRU neural network"""
        if input_shape is None:
            input_shape = (self.sequence_length, 10)
        
        Sequential = self._Sequential
        GRU = self._keras_layers['GRU']
        Dropout = self._keras_layers['Dropout']
        BatchNormalization = self._keras_layers['BatchNormalization']
        Dense = self._keras_layers['Dense']
        Adam = self._Adam
        
        model = Sequential([
            GRU(64, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            BatchNormalization(),
            GRU(32, return_sequences=False),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dropout(0.1),
            Dense(len(RegimeLabel), activation='softmax')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def _build_bilstm_model(self, input_shape: Tuple = None):
        """Build Bidirectional LSTM neural network - learns patterns in both directions"""
        if input_shape is None:
            input_shape = (self.sequence_length, 10)
        
        Sequential = self._Sequential
        LSTM = self._keras_layers['LSTM']
        Bidirectional = self._keras_layers['Bidirectional']
        Dropout = self._keras_layers['Dropout']
        BatchNormalization = self._keras_layers['BatchNormalization']
        Dense = self._keras_layers['Dense']
        Adam = self._Adam
        
        model = Sequential([
            Bidirectional(LSTM(64, return_sequences=True), input_shape=input_shape),
            Dropout(0.2),
            BatchNormalization(),
            Bidirectional(LSTM(32, return_sequences=False)),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dropout(0.1),
            Dense(len(RegimeLabel), activation='softmax')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def _build_cnn_lstm_model(self, input_shape: Tuple = None):
        """
        Build CNN-LSTM Hybrid model.
        CNN extracts local patterns, LSTM captures temporal dependencies.
        """
        if input_shape is None:
            input_shape = (self.sequence_length, 10)
        
        Sequential = self._Sequential
        Conv1D = self._keras_layers['Conv1D']
        MaxPooling1D = self._keras_layers['MaxPooling1D']
        LSTM = self._keras_layers['LSTM']
        Dropout = self._keras_layers['Dropout']
        BatchNormalization = self._keras_layers['BatchNormalization']
        Dense = self._keras_layers['Dense']
        Adam = self._Adam
        
        model = Sequential([
            # CNN layers for pattern extraction
            Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=input_shape),
            BatchNormalization(),
            Conv1D(filters=32, kernel_size=3, activation='relu'),
            MaxPooling1D(pool_size=2),
            Dropout(0.2),
            
            # LSTM for sequence learning
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            
            # Output layers
            Dense(32, activation='relu'),
            Dropout(0.1),
            Dense(len(RegimeLabel), activation='softmax')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def _build_attention_model(self, input_shape: Tuple = None):
        """
        Build Transformer-style attention model.
        Uses multi-head attention to focus on important time steps.
        """
        if input_shape is None:
            input_shape = (self.sequence_length, 10)
        
        Model = self._Model
        Input = self._keras_layers['Input']
        Dense = self._keras_layers['Dense']
        Dropout = self._keras_layers['Dropout']
        LayerNormalization = self._keras_layers['LayerNormalization']
        MultiHeadAttention = self._keras_layers['MultiHeadAttention']
        GlobalAveragePooling1D = self._keras_layers['GlobalAveragePooling1D']
        Adam = self._Adam
        
        inputs = Input(shape=input_shape)
        
        # Initial projection
        x = Dense(64, activation='relu')(inputs)
        x = LayerNormalization()(x)
        
        # Multi-head attention
        attention_output = MultiHeadAttention(
            num_heads=4,
            key_dim=16,
            dropout=0.1
        )(x, x)
        
        # Add & Normalize
        x = LayerNormalization()(x + attention_output)
        
        # Feed-forward network
        ff = Dense(128, activation='relu')(x)
        ff = Dropout(0.2)(ff)
        ff = Dense(64)(ff)
        x = LayerNormalization()(x + ff)
        
        # Global pooling and output
        x = GlobalAveragePooling1D()(x)
        x = Dense(32, activation='relu')(x)
        x = Dropout(0.1)(x)
        outputs = Dense(len(RegimeLabel), activation='softmax')(x)
        
        model = Model(inputs=inputs, outputs=outputs)
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    async def _prepare_features(self, ohlcv_data: List[Dict]) -> np.ndarray:
        """
        Prepare feature matrix from OHLCV data.
        
        Features:
        - Price change % (1d, 7d, 14d, 30d)
        - Volatility (7d, 14d rolling std)
        - Volume change %
        - RSI approximation
        - Moving average ratios
        - High-low range
        """
        if len(ohlcv_data) < 30:
            return None
        
        # Sort by date ascending - handle both int timestamps and string dates
        def get_sort_key(x):
            ts = x.get('timestamp', x.get('date', 0))
            if isinstance(ts, str):
                try:
                    return datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp()
                except:
                    return 0
            return ts if ts else 0
        
        data = sorted(ohlcv_data, key=get_sort_key)
        
        features = []
        
        for i in range(30, len(data)):
            window = data[i-30:i]
            current = data[i]
            
            closes = [float(d.get('close', 0)) for d in window]
            volumes = [float(d.get('volume_to', d.get('volume', 0)) or 0) for d in window]
            highs = [float(d.get('high', 0)) for d in window]
            lows = [float(d.get('low', 0)) for d in window]
            
            # Price changes
            price_1d = (closes[-1] - closes[-2]) / closes[-2] * 100 if closes[-2] else 0
            price_7d = (closes[-1] - closes[-8]) / closes[-8] * 100 if closes[-8] else 0
            price_14d = (closes[-1] - closes[-15]) / closes[-15] * 100 if closes[-15] else 0
            price_30d = (closes[-1] - closes[0]) / closes[0] * 100 if closes[0] else 0
            
            # Volatility
            returns = [(closes[j] - closes[j-1]) / closes[j-1] * 100 for j in range(1, len(closes)) if closes[j-1]]
            vol_7d = np.std(returns[-7:]) if len(returns) >= 7 else 0
            vol_14d = np.std(returns[-14:]) if len(returns) >= 14 else 0
            
            # Volume change
            vol_change = (volumes[-1] - np.mean(volumes[-7:])) / np.mean(volumes[-7:]) * 100 if np.mean(volumes[-7:]) else 0
            
            # RSI approximation (simplified)
            gains = [r for r in returns[-14:] if r > 0]
            losses = [-r for r in returns[-14:] if r < 0]
            avg_gain = np.mean(gains) if gains else 0
            avg_loss = np.mean(losses) if losses else 0.001
            rsi = 100 - (100 / (1 + avg_gain / avg_loss))
            
            # MA ratios
            ma_7 = np.mean(closes[-7:])
            ma_30 = np.mean(closes)
            ma_ratio = (ma_7 / ma_30 - 1) * 100 if ma_30 else 0
            
            # High-low range
            hl_range = (max(highs[-7:]) - min(lows[-7:])) / closes[-1] * 100 if closes[-1] else 0
            
            feature_row = [
                price_1d, price_7d, price_14d, price_30d,
                vol_7d, vol_14d,
                vol_change,
                rsi,
                ma_ratio,
                hl_range
            ]
            
            features.append(feature_row)
        
        return np.array(features)
    
    def _determine_regime_label(self, features: np.ndarray) -> int:
        """Determine regime label from features"""
        price_30d = features[3]
        vol_14d = features[5]
        
        # High volatility check first
        if vol_14d > 8:
            return RegimeLabel.HIGH_VOLATILITY.value
        
        # Price-based regimes
        if price_30d > 20:
            return RegimeLabel.STRONG_BULL.value
        elif price_30d > 5:
            return RegimeLabel.BULL.value
        elif price_30d < -20:
            return RegimeLabel.STRONG_BEAR.value
        elif price_30d < -5:
            return RegimeLabel.BEAR.value
        elif abs(price_30d) < 5 and vol_14d < 3:
            return RegimeLabel.ACCUMULATION.value
        else:
            return RegimeLabel.SIDEWAYS.value
    
    async def train_models(self, symbol: str = 'BTC') -> Dict[str, Any]:
        """
        Train all models on historical data.
        Returns training results with accuracy for each model.
        """
        print(f"🎓 Training regime prediction models on {symbol} data...")
        
        # Get historical OHLCV data
        ohlcv_data = await self.db.historical_ohlcv.find(
            {'symbol': symbol},
            {'_id': 0}
        ).sort('timestamp', -1).limit(500).to_list(500)
        
        if len(ohlcv_data) < 100:
            return {'error': f'Insufficient data: {len(ohlcv_data)} records (need 100+)'}
        
        # Prepare features
        X = await self._prepare_features(ohlcv_data)
        if X is None or len(X) < 50:
            return {'error': 'Could not prepare enough features'}
        
        # Create labels
        y = np.array([self._determine_regime_label(row) for row in X])
        
        # Scale features for ML models
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data (80/20)
        split_idx = int(len(X_scaled) * 0.8)
        X_train, X_test = X_scaled[:split_idx], X_scaled[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        results = {
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'models': {}
        }
        
        # Train ML models
        for name in ['random_forest', 'gradient_boosting', 'svm']:
            try:
                model = self.models[name]
                
                # Cross-validation on training set
                cv_scores = cross_val_score(model, X_train, y_train, cv=5)
                
                # Train on full training set
                model.fit(X_train, y_train)
                
                # Test accuracy
                test_accuracy = model.score(X_test, y_test) * 100
                
                self.model_accuracy[name] = test_accuracy
                
                results['models'][name] = {
                    'type': 'ML',
                    'cv_accuracy': round(np.mean(cv_scores) * 100, 1),
                    'test_accuracy': round(test_accuracy, 1),
                    'status': 'trained'
                }
                
                print(f"  ✅ {name}: {test_accuracy:.1f}% accuracy")
                
            except Exception as e:
                results['models'][name] = {
                    'status': 'failed',
                    'error': str(e)
                }
                print(f"  ❌ {name}: {e}")
        
        # Train DL models if available (lazy load TF)
        if self._ensure_dl_models():
            # Prepare sequences for LSTM/GRU
            X_seq, y_seq = self._prepare_sequences(X_scaled, y)
            
            if len(X_seq) > 30:
                split_seq = int(len(X_seq) * 0.8)
                X_train_seq, X_test_seq = X_seq[:split_seq], X_seq[split_seq:]
                y_train_seq, y_test_seq = y_seq[:split_seq], y_seq[split_seq:]
                
                # Train all DL models
                dl_models = ['lstm', 'gru', 'bilstm', 'cnn_lstm', 'attention']
                
                for name in dl_models:
                    try:
                        # Rebuild model with correct input shape
                        input_shape = X_train_seq.shape[1:]
                        
                        if name == 'lstm':
                            self.models[name] = self._build_lstm_model(input_shape)
                        elif name == 'gru':
                            self.models[name] = self._build_gru_model(input_shape)
                        elif name == 'bilstm':
                            self.models[name] = self._build_bilstm_model(input_shape)
                        elif name == 'cnn_lstm':
                            # CNN-LSTM needs longer sequences
                            if input_shape[0] >= 6:  # Min length for convolutions
                                self.models[name] = self._build_cnn_lstm_model(input_shape)
                            else:
                                results['models'][name] = {
                                    'status': 'skipped',
                                    'reason': 'Sequence too short for CNN'
                                }
                                continue
                        elif name == 'attention':
                            self.models[name] = self._build_attention_model(input_shape)
                        
                        model = self.models[name]
                        
                        early_stop = EarlyStopping(
                            monitor='val_loss',
                            patience=5,
                            restore_best_weights=True
                        )
                        
                        history = model.fit(
                            X_train_seq, y_train_seq,
                            epochs=50,
                            batch_size=16,
                            validation_split=0.2,
                            callbacks=[early_stop],
                            verbose=0
                        )
                        
                        # Test accuracy
                        _, test_accuracy = model.evaluate(X_test_seq, y_test_seq, verbose=0)
                        test_accuracy *= 100
                        
                        self.model_accuracy[name] = test_accuracy
                        
                        results['models'][name] = {
                            'type': 'DL',
                            'category': self.model_metadata.get(name, {}).get('category', 'unknown'),
                            'epochs_trained': len(history.history['loss']),
                            'test_accuracy': round(test_accuracy, 1),
                            'status': 'trained'
                        }
                        
                        print(f"  ✅ {name}: {test_accuracy:.1f}% accuracy")
                        
                    except Exception as e:
                        results['models'][name] = {
                            'status': 'failed',
                            'error': str(e)
                        }
                        print(f"  ❌ {name}: {e}")
        
        # Select best model
        if self.model_accuracy:
            best_name = max(self.model_accuracy.items(), key=lambda x: x[1])
            self.best_model = best_name[0]
            results['best_model'] = {
                'name': best_name[0],
                'accuracy': round(best_name[1], 1)
            }
            print(f"\n🏆 Best Model: {best_name[0]} ({best_name[1]:.1f}%)")
        
        self.is_trained = True
        
        # Auto-save models after training
        self.save_models()
        
        # Save model accuracy to DB
        await self.db.model_training_history.insert_one({
            'timestamp': datetime.now(timezone.utc),
            'symbol': symbol,
            'results': results
        })
        
        return results
    
    def _prepare_sequences(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequences for LSTM/GRU"""
        sequences = []
        labels = []
        
        for i in range(self.sequence_length, len(X)):
            sequences.append(X[i-self.sequence_length:i])
            labels.append(y[i])
        
        return np.array(sequences), np.array(labels)
    
    async def predict_regime(
        self,
        symbol: str = 'BTC',
        use_model: str = None
    ) -> Dict[str, Any]:
        """
        Predict current market regime using trained models.
        
        Args:
            symbol: Coin symbol
            use_model: Specific model to use (or 'best' for auto-select)
        """
        if not self.is_trained:
            # Try to train first
            await self.train_models(symbol)
        
        if not self.is_trained:
            return {'error': 'Models not trained'}
        
        # Get recent data
        ohlcv_data = await self.db.historical_ohlcv.find(
            {'symbol': symbol},
            {'_id': 0}
        ).sort('timestamp', -1).limit(50).to_list(50)
        
        if len(ohlcv_data) < 35:
            return {'error': 'Insufficient recent data'}
        
        # Prepare features
        X = await self._prepare_features(ohlcv_data)
        if X is None or len(X) == 0:
            return {'error': 'Could not prepare features'}
        
        # Use latest features
        X_latest = X[-1:] if len(X) > 0 else X
        X_scaled = self.scaler.transform(X_latest)
        
        # Select model
        model_name = use_model if use_model and use_model in self.models else self.best_model
        
        predictions = {}
        
        # DL models that need sequence data
        dl_models = ['lstm', 'gru', 'bilstm', 'cnn_lstm', 'attention']
        
        # Get predictions from all models for comparison
        for name, model in self.models.items():
            try:
                if name in dl_models and TF_AVAILABLE:
                    # Need sequence for DL models
                    if len(X) >= self.sequence_length:
                        X_seq = self.scaler.transform(X[-self.sequence_length:])
                        X_seq = X_seq.reshape(1, self.sequence_length, -1)
                        probs = model.predict(X_seq, verbose=0)[0]
                        pred_class = np.argmax(probs)
                        confidence = float(probs[pred_class]) * 100
                    else:
                        # Not enough data for DL model
                        predictions[name] = {
                            'error': f'Need at least {self.sequence_length} data points for DL model'
                        }
                        continue
                else:
                    # ML models
                    pred_class = model.predict(X_scaled)[0]
                    probs = model.predict_proba(X_scaled)[0]
                    confidence = float(max(probs)) * 100
                
                predictions[name] = {
                    'regime': REGIME_NAMES[pred_class],
                    'confidence': round(confidence, 1),
                    'accuracy': round(self.model_accuracy.get(name, 0), 1)
                }
                
            except Exception as e:
                predictions[name] = {'error': str(e)}
        
        # Get best model's prediction
        best_pred = predictions.get(self.best_model, {})
        
        return {
            'symbol': symbol,
            'predicted_regime': best_pred.get('regime', 'unknown'),
            'confidence': best_pred.get('confidence', 0),
            'model_used': self.best_model,
            'model_accuracy': self.model_accuracy.get(self.best_model, 0),
            'all_predictions': predictions,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def compare_models(self) -> Dict[str, Any]:
        """Compare all models' performance"""
        if not self.model_accuracy:
            return {'error': 'No trained models'}
        
        # Sort by accuracy
        sorted_models = sorted(
            self.model_accuracy.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            'ranking': [
                {
                    'rank': i + 1,
                    'model': name,
                    'accuracy': round(acc, 1),
                    'type': 'DL' if name in ['lstm', 'gru'] else 'ML'
                }
                for i, (name, acc) in enumerate(sorted_models)
            ],
            'best_model': {
                'name': sorted_models[0][0],
                'accuracy': round(sorted_models[0][1], 1)
            },
            'best_ml': next(
                ({'name': n, 'accuracy': round(a, 1)} 
                 for n, a in sorted_models if n not in ['lstm', 'gru']),
                None
            ),
            'best_dl': next(
                ({'name': n, 'accuracy': round(a, 1)} 
                 for n, a in sorted_models if n in ['lstm', 'gru']),
                None
            ) if self._dl_initialized else None
        }
    
    async def get_training_history(self, limit: int = 10) -> List[Dict]:
        """Get model training history"""
        history = await self.db.model_training_history.find(
            {}, {'_id': 0}
        ).sort('timestamp', -1).limit(limit).to_list(limit)
        
        return history


# Global instance
_regime_predictor = None


def get_regime_predictor(db: AsyncIOMotorDatabase = None) -> RegimePredictionEngine:
    """Get or create regime prediction engine"""
    global _regime_predictor
    if _regime_predictor is None and db is not None:
        _regime_predictor = RegimePredictionEngine(db)
    return _regime_predictor

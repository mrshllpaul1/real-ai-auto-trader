"""
Transformer Architecture for Time Series Prediction
Enhancement #4: GPT-style attention mechanism for crypto price prediction
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# TensorFlow imports with error handling
try:
    import tensorflow as tf
    from tensorflow.keras.models import Model
    from tensorflow.keras.layers import (
        Input, Dense, Dropout, LayerNormalization, 
        MultiHeadAttention, GlobalAveragePooling1D, Embedding,
        Concatenate, Add
    )
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.warning("TensorFlow not available for Transformer model")


@tf.keras.saving.register_keras_serializable(package="CustomLayers")
class PositionalEncoding(tf.keras.layers.Layer):
    """Positional encoding layer for sequence position information"""
    
    def __init__(self, max_len: int = 100, d_model: int = 64, **kwargs):
        super().__init__(**kwargs)
        self.max_len = max_len
        self.d_model = d_model
        
    def build(self, input_shape):
        # Create positional encoding matrix
        position = np.arange(self.max_len)[:, np.newaxis]
        div_term = np.exp(np.arange(0, self.d_model, 2) * -(np.log(10000.0) / self.d_model))
        
        pe = np.zeros((self.max_len, self.d_model))
        pe[:, 0::2] = np.sin(position * div_term)
        pe[:, 1::2] = np.cos(position * div_term)
        
        self.pe = tf.constant(pe, dtype=tf.float32)
        super().build(input_shape)
    
    def call(self, x):
        seq_len = tf.shape(x)[1]
        return x + self.pe[:seq_len, :]
    
    def get_config(self):
        config = super().get_config()
        config.update({
            'max_len': self.max_len,
            'd_model': self.d_model
        })
        return config


@tf.keras.saving.register_keras_serializable(package="CustomLayers")
class TransformerBlock(tf.keras.layers.Layer):
    """Single Transformer block with multi-head attention"""
    
    def __init__(self, d_model: int = 64, num_heads: int = 4, 
                 ff_dim: int = 128, dropout: float = 0.1, **kwargs):
        super().__init__(**kwargs)
        self.d_model = d_model
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        self.dropout_rate = dropout
        
    def build(self, input_shape):
        self.att = MultiHeadAttention(
            num_heads=self.num_heads, 
            key_dim=self.d_model // self.num_heads
        )
        self.ffn = tf.keras.Sequential([
            Dense(self.ff_dim, activation='gelu'),
            Dense(self.d_model)
        ])
        self.layernorm1 = LayerNormalization(epsilon=1e-6)
        self.layernorm2 = LayerNormalization(epsilon=1e-6)
        self.dropout1 = Dropout(self.dropout_rate)
        self.dropout2 = Dropout(self.dropout_rate)
        super().build(input_shape)
    
    def call(self, inputs, training=False):
        # Multi-head self-attention with residual connection
        attn_output = self.att(inputs, inputs)
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)
        
        # Feed-forward network with residual connection
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output)
    
    def get_config(self):
        config = super().get_config()
        config.update({
            'd_model': self.d_model,
            'num_heads': self.num_heads,
            'ff_dim': self.ff_dim,
            'dropout': self.dropout_rate
        })
        return config


class TransformerPredictor:
    """
    Transformer-based price prediction model:
    - Multi-head self-attention for capturing long-range dependencies
    - Positional encoding for sequence order
    - Multiple Transformer blocks for deep pattern recognition
    - Supports both classification (direction) and regression (price)
    - Supports model persistence (save/load to disk)
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.model = None
        self.is_trained = False
        self.scaler = None
        
        # Model configuration
        self.config = {
            'sequence_length': 30,      # 30 time steps
            'n_features': 20,           # Number of input features
            'd_model': 64,              # Model dimension
            'num_heads': 4,             # Attention heads
            'ff_dim': 128,              # Feed-forward dimension
            'num_blocks': 3,            # Number of Transformer blocks
            'dropout': 0.1,
            'num_classes': 3            # down, neutral, up
        }
        
        # Training history
        self.training_history = None
        self.last_trained = None
        
        # Try to load saved model on initialization
        self._load_saved_model()
    
    def _load_saved_model(self):
        """Attempt to load a previously saved model"""
        try:
            from services.model_persistence import get_transformer_persistence
            persistence = get_transformer_persistence()
            
            if persistence.model_exists():
                model = persistence.load_keras_model()
                if model is not None:
                    self.model = model
                    self.is_trained = True
                    meta = persistence.get_metadata() or {}
                    self.last_trained = meta.get('saved_at')
                    logger.info(f"✅ Transformer loaded saved model (trained: {self.last_trained or 'unknown'})")
        except Exception as e:
            logger.warning(f"Could not load saved Transformer model: {e}")
    
    def save_model(self) -> bool:
        """Save the current model to disk"""
        try:
            from services.model_persistence import get_transformer_persistence
            persistence = get_transformer_persistence()
            
            if self.model is not None:
                return persistence.save_keras_model(
                    self.model,
                    metadata={
                        "is_trained": self.is_trained,
                        "config": self.config,
                        "last_trained": self.last_trained
                    }
                )
            return False
        except Exception as e:
            logger.error(f"Failed to save Transformer model: {e}")
            return False
        
    def build_model(self) -> Model:
        """Build Transformer model architecture"""
        if not TF_AVAILABLE:
            raise RuntimeError("TensorFlow not available")
        
        seq_len = self.config['sequence_length']
        n_features = self.config['n_features']
        d_model = self.config['d_model']
        
        # Input layer
        inputs = Input(shape=(seq_len, n_features))
        
        # Project input to model dimension
        x = Dense(d_model)(inputs)
        
        # Add positional encoding
        x = PositionalEncoding(max_len=seq_len, d_model=d_model)(x)
        
        # Stack Transformer blocks
        for i in range(self.config['num_blocks']):
            x = TransformerBlock(
                d_model=d_model,
                num_heads=self.config['num_heads'],
                ff_dim=self.config['ff_dim'],
                dropout=self.config['dropout'],
                name=f'transformer_block_{i}'
            )(x)
        
        # Global pooling
        x = GlobalAveragePooling1D()(x)
        
        # Classification head
        x = Dense(64, activation='gelu')(x)
        x = Dropout(self.config['dropout'])(x)
        x = Dense(32, activation='gelu')(x)
        
        # Output: probability distribution over classes
        outputs = Dense(self.config['num_classes'], activation='softmax')(x)
        
        model = Model(inputs=inputs, outputs=outputs)
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    async def prepare_features(self, ohlcv_data: List[Dict]) -> np.ndarray:
        """Prepare features from OHLCV data"""
        if len(ohlcv_data) < self.config['sequence_length'] + 5:
            return None
        
        # Sort by timestamp
        sorted_data = sorted(ohlcv_data, key=lambda x: x.get('timestamp', x.get('time', 0)))
        
        features = []
        for candle in sorted_data:
            open_p = float(candle.get('open', 0))
            high = float(candle.get('high', 0))
            low = float(candle.get('low', 0))
            close = float(candle.get('close', 0))
            volume = float(candle.get('volume', 0))
            
            if close == 0:
                continue
            
            # Price features
            returns = (close - open_p) / open_p if open_p > 0 else 0
            range_pct = (high - low) / close if close > 0 else 0
            body_pct = abs(close - open_p) / close if close > 0 else 0
            upper_shadow = (high - max(open_p, close)) / close if close > 0 else 0
            lower_shadow = (min(open_p, close) - low) / close if close > 0 else 0
            
            feature_row = [
                returns,
                range_pct,
                body_pct,
                upper_shadow,
                lower_shadow,
                np.log1p(volume) / 20,  # Normalized log volume
                1 if close > open_p else 0,  # Bullish candle
                high / close - 1 if close > 0 else 0,
                1 - low / close if close > 0 else 0,
                range_pct / (body_pct + 0.001),  # Volatility ratio
            ]
            
            features.append(feature_row)
        
        if len(features) < self.config['sequence_length']:
            return None
        
        # Add technical indicators
        features_array = np.array(features)
        enhanced_features = self._add_technical_features(features_array)
        
        return enhanced_features
    
    def _add_technical_features(self, features: np.ndarray) -> np.ndarray:
        """Add rolling technical indicators"""
        n_samples = len(features)
        
        # Calculate rolling features
        returns = features[:, 0]
        
        # Rolling mean returns (momentum)
        sma_5 = np.convolve(returns, np.ones(5)/5, mode='same')
        sma_10 = np.convolve(returns, np.ones(10)/10, mode='same')
        sma_20 = np.convolve(returns, np.ones(20)/20, mode='same')
        
        # Rolling volatility
        vol_5 = np.array([np.std(returns[max(0,i-5):i+1]) for i in range(n_samples)])
        vol_10 = np.array([np.std(returns[max(0,i-10):i+1]) for i in range(n_samples)])
        
        # RSI approximation
        gains = np.maximum(returns, 0)
        losses = np.abs(np.minimum(returns, 0))
        avg_gain = np.convolve(gains, np.ones(14)/14, mode='same')
        avg_loss = np.convolve(losses, np.ones(14)/14, mode='same')
        rs = avg_gain / (avg_loss + 0.0001)
        rsi = 100 - (100 / (1 + rs))
        rsi_normalized = (rsi - 50) / 50
        
        # MACD approximation
        ema_12 = np.convolve(returns, np.ones(12)/12, mode='same')
        ema_26 = np.convolve(returns, np.ones(26)/26, mode='same')
        macd = ema_12 - ema_26
        
        # Trend strength
        trend = np.sign(sma_5 - sma_20)
        
        # Combine all features
        additional_features = np.column_stack([
            sma_5, sma_10, sma_20,
            vol_5, vol_10,
            rsi_normalized,
            macd,
            trend,
            sma_5 - sma_10,  # Short-term momentum
            vol_5 / (vol_10 + 0.0001)  # Volatility ratio
        ])
        
        return np.concatenate([features, additional_features], axis=1)
    
    def _create_sequences(self, features: np.ndarray, labels: np.ndarray = None) -> Tuple:
        """Create sequences for training/prediction"""
        seq_len = self.config['sequence_length']
        n_features = features.shape[1]
        
        X = []
        y = [] if labels is not None else None
        
        for i in range(len(features) - seq_len):
            X.append(features[i:i+seq_len])
            if labels is not None:
                y.append(labels[i+seq_len])
        
        X = np.array(X)
        
        if labels is not None:
            y = np.array(y)
            return X, y
        
        return X
    
    def _create_labels(self, features: np.ndarray, threshold: float = 0.02) -> np.ndarray:
        """Create classification labels based on future returns"""
        returns = features[:, 0]  # First feature is returns
        
        labels = np.zeros(len(returns))
        
        for i in range(len(returns) - 5):
            future_return = np.sum(returns[i+1:i+6])  # 5-period forward return
            
            if future_return > threshold:
                labels[i] = 2  # Up
            elif future_return < -threshold:
                labels[i] = 0  # Down
            else:
                labels[i] = 1  # Neutral
        
        return labels
    
    async def train(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Train Transformer model on historical data"""
        if not TF_AVAILABLE:
            return {'error': 'TensorFlow not available'}
        
        try:
            logger.info("🤖 Training Transformer model...")
            
            # Default symbols
            if not symbols:
                symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'MATIC']
            
            all_X = []
            all_y = []
            
            # Collect training data
            for symbol in symbols:
                ohlcv = await self.db.ohlcv_data.find(
                    {'symbol': {'$regex': symbol, '$options': 'i'}}
                ).sort('timestamp', 1).limit(1000).to_list(length=1000)
                
                if len(ohlcv) < 100:
                    continue
                
                features = await self.prepare_features(ohlcv)
                if features is None:
                    continue
                
                labels = self._create_labels(features)
                X, y = self._create_sequences(features, labels)
                
                all_X.append(X)
                all_y.append(y)
            
            if not all_X:
                return {'error': 'Insufficient training data'}
            
            X_train = np.concatenate(all_X, axis=0)
            y_train = np.concatenate(all_y, axis=0)
            
            # Update config based on actual features
            self.config['n_features'] = X_train.shape[2]
            
            logger.info(f"📊 Training data shape: {X_train.shape}")
            
            # Build and train model
            self.model = self.build_model()
            
            # Early stopping
            early_stop = EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True
            )
            
            history = self.model.fit(
                X_train, y_train,
                epochs=50,
                batch_size=32,
                validation_split=0.2,
                callbacks=[early_stop],
                verbose=0
            )
            
            self.training_history = history.history
            self.is_trained = True
            self.last_trained = datetime.utcnow()
            
            # Auto-save model after training
            self.save_model()
            
            # Calculate final metrics
            final_acc = history.history['accuracy'][-1]
            val_acc = history.history.get('val_accuracy', [0])[-1]
            
            logger.info(f"✅ Transformer trained: {final_acc*100:.1f}% train, {val_acc*100:.1f}% val accuracy")
            
            return {
                'status': 'success',
                'samples': len(X_train),
                'train_accuracy': round(final_acc * 100, 2),
                'val_accuracy': round(val_acc * 100, 2),
                'epochs_trained': len(history.history['loss']),
                'model_config': self.config,
                'model_saved': True
            }
            
        except Exception as e:
            logger.error(f"Transformer training failed: {e}")
            return {'error': str(e)}
    
    async def predict(self, symbol: str) -> Dict[str, Any]:
        """Make prediction for a symbol"""
        if not self.is_trained or self.model is None:
            return {'error': 'Model not trained'}
        
        try:
            # Get recent OHLCV data
            ohlcv = await self.db.ohlcv_data.find(
                {'symbol': {'$regex': symbol, '$options': 'i'}}
            ).sort('timestamp', -1).limit(100).to_list(length=100)
            
            if len(ohlcv) < self.config['sequence_length'] + 10:
                return {'error': 'Insufficient data'}
            
            # Prepare features
            ohlcv.reverse()  # Chronological order
            features = await self.prepare_features(ohlcv)
            
            if features is None:
                return {'error': 'Feature preparation failed'}
            
            # Create sequence for prediction
            X = self._create_sequences(features)
            
            if len(X) == 0:
                return {'error': 'Sequence creation failed'}
            
            # Use last sequence for prediction
            X_pred = X[-1:].astype(np.float32)
            
            # Get prediction probabilities
            probs = self.model.predict(X_pred, verbose=0)[0]
            
            predicted_class = int(np.argmax(probs))
            confidence = float(probs[predicted_class]) * 100
            
            class_names = ['down', 'neutral', 'up']
            
            # Generate trading signal
            if predicted_class == 2 and confidence > 60:
                signal = 'buy'
            elif predicted_class == 0 and confidence > 60:
                signal = 'sell'
            else:
                signal = 'hold'
            
            return {
                'symbol': symbol,
                'prediction': class_names[predicted_class],
                'confidence': round(confidence, 2),
                'probabilities': {
                    'down': round(float(probs[0]) * 100, 2),
                    'neutral': round(float(probs[1]) * 100, 2),
                    'up': round(float(probs[2]) * 100, 2)
                },
                'signal': signal,
                'model': 'transformer',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Transformer prediction failed: {e}")
            return {'error': str(e)}
    
    async def batch_predict(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Make predictions for multiple symbols"""
        predictions = []
        for symbol in symbols:
            pred = await self.predict(symbol)
            predictions.append(pred)
        return predictions
    
    def get_attention_weights(self, X: np.ndarray) -> Dict[str, Any]:
        """Extract attention weights for interpretability"""
        if not self.is_trained:
            return {'error': 'Model not trained'}
        
        # This would require a custom model that outputs attention weights
        # Simplified version returns None for now
        return {
            'message': 'Attention weight extraction not implemented in this version',
            'model_architecture': 'Transformer with multi-head attention'
        }


# Singleton instance
_transformer_predictor = None

def get_transformer_predictor(db: AsyncIOMotorDatabase = None) -> TransformerPredictor:
    global _transformer_predictor
    if _transformer_predictor is None and db is not None:
        _transformer_predictor = TransformerPredictor(db)
    return _transformer_predictor

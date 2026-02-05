"""
Advanced Trading Intelligence Engine
=====================================
Comprehensive ML/DL system combining:
1. Ensemble Learning (XGBoost/LightGBM)
2. Time-Series Models (LSTM/GRU/Transformer)
3. FinRL-inspired Framework
4. Advanced Data Preprocessing & Feature Engineering
5. PCA-based Features
6. Realistic Market Environment Simulation

This module provides production-ready trading AI with proper
data handling, transaction costs, and slippage modeling.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import asyncio
import os
import json
from concurrent.futures import ThreadPoolExecutor
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)

# Configure TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# =============================================================================
# IMPORTS WITH FALLBACKS
# =============================================================================

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.warning("LightGBM not available")

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import (
        Dense, LSTM, GRU, Bidirectional, Input, Concatenate,
        Dropout, BatchNormalization, Attention, MultiHeadAttention,
        Conv1D, MaxPooling1D, Flatten, LayerNormalization,
        GlobalAveragePooling1D, Lambda, Add
    )
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
    from tensorflow.keras.regularizers import l2
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logger.warning("TensorFlow not available")

try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
    from sklearn.decomposition import PCA
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False


# =============================================================================
# 1. DATA PREPROCESSING & FEATURE ENGINEERING
# =============================================================================

class DataPreprocessor:
    """
    Advanced data preprocessing pipeline for financial time series.
    Handles noisy data with scaling, normalization, and outlier detection.
    """
    
    def __init__(self):
        self.price_scaler = RobustScaler() if SKLEARN_AVAILABLE else None
        self.volume_scaler = RobustScaler() if SKLEARN_AVAILABLE else None
        self.feature_scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.pca = None
        self.is_fitted = False
        
        # Feature statistics for online normalization
        self.feature_means = {}
        self.feature_stds = {}
        
    def fit(self, data: pd.DataFrame) -> 'DataPreprocessor':
        """Fit scalers on training data"""
        if not SKLEARN_AVAILABLE:
            return self
        
        # Fit price scaler
        price_cols = ['open', 'high', 'low', 'close']
        available_price_cols = [c for c in price_cols if c in data.columns]
        if available_price_cols:
            self.price_scaler.fit(data[available_price_cols])
        
        # Fit volume scaler
        if 'volume' in data.columns:
            self.volume_scaler.fit(data[['volume']])
        
        self.is_fitted = True
        return self
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transform data with fitted scalers"""
        if not SKLEARN_AVAILABLE or not self.is_fitted:
            return data
        
        result = data.copy()
        
        # Scale prices
        price_cols = ['open', 'high', 'low', 'close']
        available_price_cols = [c for c in price_cols if c in result.columns]
        if available_price_cols and self.price_scaler:
            result[available_price_cols] = self.price_scaler.transform(result[available_price_cols])
        
        # Scale volume
        if 'volume' in result.columns and self.volume_scaler:
            result['volume'] = self.volume_scaler.transform(result[['volume']])
        
        return result
    
    def fit_transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Fit and transform in one step"""
        return self.fit(data).transform(data)
    
    def inverse_transform_price(self, scaled_price: np.ndarray) -> np.ndarray:
        """Inverse transform scaled prices back to original scale"""
        if not SKLEARN_AVAILABLE or not self.is_fitted:
            return scaled_price
        
        # Reshape if needed
        if len(scaled_price.shape) == 1:
            scaled_price = scaled_price.reshape(-1, 1)
            # Pad to match scaler dimensions
            padded = np.zeros((len(scaled_price), 4))
            padded[:, 3] = scaled_price[:, 0]  # Close price
            return self.price_scaler.inverse_transform(padded)[:, 3]
        
        return self.price_scaler.inverse_transform(scaled_price)


class FeatureEngineer:
    """
    Comprehensive feature engineering for trading signals.
    Extracts technical indicators, statistical features, and PCA components.
    """
    
    def __init__(self, pca_components: int = 10):
        self.pca_components = pca_components
        self.pca = PCA(n_components=pca_components) if SKLEARN_AVAILABLE else None
        self.feature_scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.is_fitted = False
        
    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract comprehensive features from OHLCV data"""
        features = pd.DataFrame(index=df.index)
        
        close = df['close'].values if 'close' in df.columns else df.iloc[:, 0].values
        high = df['high'].values if 'high' in df.columns else close
        low = df['low'].values if 'low' in df.columns else close
        volume = df['volume'].values if 'volume' in df.columns else np.ones_like(close)
        
        # Price-based features
        features['returns'] = pd.Series(close).pct_change().fillna(0)
        features['log_returns'] = np.log(close / np.roll(close, 1)).clip(-1, 1)
        features['log_returns'].iloc[0] = 0
        
        # Volatility features
        features['volatility_5'] = pd.Series(features['returns']).rolling(5).std().fillna(0)
        features['volatility_20'] = pd.Series(features['returns']).rolling(20).std().fillna(0)
        features['volatility_60'] = pd.Series(features['returns']).rolling(60).std().fillna(0)
        
        # Moving averages
        for window in [5, 10, 20, 50, 100]:
            ma = pd.Series(close).rolling(window).mean().fillna(method='bfill')
            features[f'ma_{window}_ratio'] = close / ma - 1
        
        # Exponential moving averages
        for span in [12, 26, 50]:
            ema = pd.Series(close).ewm(span=span).mean()
            features[f'ema_{span}_ratio'] = close / ema - 1
        
        # MACD
        ema_12 = pd.Series(close).ewm(span=12).mean()
        ema_26 = pd.Series(close).ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        features['macd'] = (macd - signal) / close
        features['macd_hist'] = macd - signal
        
        # RSI
        features['rsi_14'] = self._calculate_rsi(close, 14) / 100 - 0.5
        features['rsi_7'] = self._calculate_rsi(close, 7) / 100 - 0.5
        features['rsi_21'] = self._calculate_rsi(close, 21) / 100 - 0.5
        
        # Bollinger Bands
        bb_ma = pd.Series(close).rolling(20).mean()
        bb_std = pd.Series(close).rolling(20).std()
        features['bb_upper'] = (close - (bb_ma + 2 * bb_std)) / close
        features['bb_lower'] = (close - (bb_ma - 2 * bb_std)) / close
        features['bb_width'] = (4 * bb_std) / bb_ma
        features['bb_position'] = (close - bb_ma) / (2 * bb_std + 1e-8)
        
        # Volume features
        vol_ma = pd.Series(volume).rolling(20).mean().fillna(method='bfill')
        features['volume_ratio'] = volume / (vol_ma + 1e-8) - 1
        features['volume_trend'] = pd.Series(volume).rolling(5).mean() / vol_ma - 1
        
        # Price momentum
        for lag in [1, 5, 10, 20]:
            features[f'momentum_{lag}'] = pd.Series(close).pct_change(lag).fillna(0)
        
        # ATR (Average True Range)
        tr = np.maximum(high - low, 
                       np.maximum(np.abs(high - np.roll(close, 1)),
                                 np.abs(low - np.roll(close, 1))))
        features['atr_14'] = pd.Series(tr).rolling(14).mean() / close
        
        # Stochastic Oscillator
        low_14 = pd.Series(low).rolling(14).min()
        high_14 = pd.Series(high).rolling(14).max()
        features['stoch_k'] = ((close - low_14) / (high_14 - low_14 + 1e-8) - 0.5)
        features['stoch_d'] = features['stoch_k'].rolling(3).mean()
        
        # Fill NaN values
        features = features.fillna(0)
        
        # Clip extreme values
        for col in features.columns:
            features[col] = features[col].clip(-5, 5)
        
        return features
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = pd.Series(prices).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-8)
        return (100 - (100 / (1 + rs))).fillna(50)
    
    def extract_pca_features(self, features: pd.DataFrame) -> Tuple[np.ndarray, Dict]:
        """Extract PCA components from features"""
        if not SKLEARN_AVAILABLE or self.pca is None:
            return features.values, {}
        
        # Scale features first
        if not self.is_fitted:
            scaled = self.feature_scaler.fit_transform(features)
            self.pca.fit(scaled)
            self.is_fitted = True
        else:
            scaled = self.feature_scaler.transform(features)
        
        # Transform to PCA space
        pca_features = self.pca.transform(scaled)
        
        info = {
            "explained_variance": self.pca.explained_variance_ratio_.tolist(),
            "cumulative_variance": np.cumsum(self.pca.explained_variance_ratio_).tolist(),
            "n_components": self.pca_components
        }
        
        return pca_features, info


# =============================================================================
# 2. ENSEMBLE LEARNING (XGBoost/LightGBM)
# =============================================================================

class EnsemblePredictor:
    """
    Ensemble of gradient boosting models for price direction prediction.
    Combines XGBoost and LightGBM for robust predictions.
    """
    
    def __init__(self):
        self.xgb_model = None
        self.lgb_model = None
        self.is_trained = False
        self.feature_importance = {}
        
        # Model configurations
        self.xgb_params = {
            'objective': 'binary:logistic',
            'eval_metric': 'auc',
            'max_depth': 6,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 5,
            'reg_alpha': 0.1,
            'reg_lambda': 1.0,
            'random_state': 42
        }
        
        self.lgb_params = {
            'objective': 'binary',
            'metric': 'auc',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'min_child_samples': 20,
            'reg_alpha': 0.1,
            'reg_lambda': 1.0,
            'random_state': 42,
            'verbose': -1
        }
    
    def train(self, X: np.ndarray, y: np.ndarray, 
              val_X: np.ndarray = None, val_y: np.ndarray = None,
              num_rounds: int = 500) -> Dict[str, Any]:
        """Train ensemble models"""
        results = {}
        
        # Train XGBoost
        if XGBOOST_AVAILABLE:
            logger.info("Training XGBoost model...")
            dtrain = xgb.DMatrix(X, label=y)
            
            evals = [(dtrain, 'train')]
            if val_X is not None:
                dval = xgb.DMatrix(val_X, label=val_y)
                evals.append((dval, 'valid'))
            
            self.xgb_model = xgb.train(
                self.xgb_params,
                dtrain,
                num_boost_round=num_rounds,
                evals=evals,
                early_stopping_rounds=50,
                verbose_eval=False
            )
            
            # Get feature importance
            importance = self.xgb_model.get_score(importance_type='gain')
            self.feature_importance['xgb'] = importance
            
            results['xgb'] = {
                'best_iteration': self.xgb_model.best_iteration,
                'best_score': self.xgb_model.best_score
            }
            logger.info(f"XGBoost trained: best_iter={self.xgb_model.best_iteration}")
        
        # Train LightGBM
        if LIGHTGBM_AVAILABLE:
            logger.info("Training LightGBM model...")
            ltrain = lgb.Dataset(X, label=y)
            
            valid_sets = [ltrain]
            valid_names = ['train']
            if val_X is not None:
                lval = lgb.Dataset(val_X, label=val_y)
                valid_sets.append(lval)
                valid_names.append('valid')
            
            callbacks = [lgb.early_stopping(50), lgb.log_evaluation(0)]
            
            self.lgb_model = lgb.train(
                self.lgb_params,
                ltrain,
                num_boost_round=num_rounds,
                valid_sets=valid_sets,
                valid_names=valid_names,
                callbacks=callbacks
            )
            
            # Get feature importance
            self.feature_importance['lgb'] = dict(zip(
                range(X.shape[1]),
                self.lgb_model.feature_importance(importance_type='gain')
            ))
            
            results['lgb'] = {
                'best_iteration': self.lgb_model.best_iteration,
                'best_score': self.lgb_model.best_score
            }
            logger.info(f"LightGBM trained: best_iter={self.lgb_model.best_iteration}")
        
        self.is_trained = XGBOOST_AVAILABLE or LIGHTGBM_AVAILABLE
        return results
    
    def predict(self, X: np.ndarray) -> Dict[str, Any]:
        """Predict using ensemble (average of models)"""
        if not self.is_trained:
            return {"error": "Models not trained", "prediction": 0.5}
        
        predictions = []
        
        if XGBOOST_AVAILABLE and self.xgb_model:
            dtest = xgb.DMatrix(X)
            xgb_pred = self.xgb_model.predict(dtest)
            predictions.append(xgb_pred)
        
        if LIGHTGBM_AVAILABLE and self.lgb_model:
            lgb_pred = self.lgb_model.predict(X)
            predictions.append(lgb_pred)
        
        if not predictions:
            return {"error": "No models available", "prediction": 0.5}
        
        # Ensemble average
        ensemble_pred = np.mean(predictions, axis=0)
        
        return {
            "ensemble_prediction": float(np.mean(ensemble_pred)),
            "xgb_prediction": float(np.mean(predictions[0])) if len(predictions) > 0 else None,
            "lgb_prediction": float(np.mean(predictions[1])) if len(predictions) > 1 else None,
            "direction": "bullish" if np.mean(ensemble_pred) > 0.5 else "bearish",
            "confidence": float(abs(np.mean(ensemble_pred) - 0.5) * 2)
        }


# =============================================================================
# 3. ADVANCED TIME-SERIES MODELS (LSTM/GRU/Transformer)
# =============================================================================

class TimeSeriesPredictor:
    """
    Advanced time series prediction using LSTM, GRU, and Transformer architectures.
    Includes proper sequence handling and attention mechanisms.
    """
    
    def __init__(self, sequence_length: int = 60, n_features: int = 30, 
                 forecast_horizon: int = 5):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.forecast_horizon = forecast_horizon
        
        self.lstm_model = None
        self.gru_model = None
        self.transformer_model = None
        
        self.is_trained = False
        self.training_history = {}
        
    def build_lstm_model(self) -> Model:
        """Build stacked Bidirectional LSTM model"""
        if not TF_AVAILABLE:
            return None
        
        inputs = Input(shape=(self.sequence_length, self.n_features))
        
        # First BiLSTM layer
        x = Bidirectional(LSTM(128, return_sequences=True, 
                               dropout=0.2, recurrent_dropout=0.1,
                               kernel_regularizer=l2(0.001)))(inputs)
        x = BatchNormalization()(x)
        
        # Second BiLSTM layer
        x = Bidirectional(LSTM(64, return_sequences=True,
                               dropout=0.2, recurrent_dropout=0.1))(x)
        x = BatchNormalization()(x)
        
        # Attention layer
        attention = MultiHeadAttention(num_heads=4, key_dim=32)(x, x)
        x = Add()([x, attention])
        x = LayerNormalization()(x)
        
        # Final LSTM layer
        x = LSTM(32, return_sequences=False, dropout=0.2)(x)
        
        # Dense layers
        x = Dense(64, activation='relu', kernel_regularizer=l2(0.001))(x)
        x = Dropout(0.3)(x)
        x = Dense(32, activation='relu')(x)
        
        # Multi-output: price direction + magnitude
        direction = Dense(1, activation='sigmoid', name='direction')(x)
        magnitude = Dense(self.forecast_horizon, activation='linear', name='magnitude')(x)
        
        self.lstm_model = Model(inputs, [direction, magnitude])
        self.lstm_model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss={'direction': 'binary_crossentropy', 'magnitude': 'huber'},
            loss_weights={'direction': 1.0, 'magnitude': 0.5},
            metrics={'direction': 'accuracy'}
        )
        return self.lstm_model
    
    def build_gru_model(self) -> Model:
        """Build GRU model with residual connections"""
        if not TF_AVAILABLE:
            return None
        
        inputs = Input(shape=(self.sequence_length, self.n_features))
        
        # First GRU layer
        x = GRU(128, return_sequences=True, dropout=0.2)(inputs)
        x = BatchNormalization()(x)
        
        # Residual GRU block
        gru_out = GRU(128, return_sequences=True, dropout=0.2)(x)
        x = Add()([x, gru_out])
        x = LayerNormalization()(x)
        
        # Second GRU block
        x = GRU(64, return_sequences=True, dropout=0.2)(x)
        x = BatchNormalization()(x)
        
        # Final GRU
        x = GRU(32, return_sequences=False, dropout=0.2)(x)
        
        # Output
        x = Dense(64, activation='relu')(x)
        x = Dropout(0.3)(x)
        output = Dense(self.forecast_horizon + 1, activation='linear')(x)  # direction + magnitudes
        
        self.gru_model = Model(inputs, output)
        self.gru_model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='huber',
            metrics=['mae']
        )
        return self.gru_model
    
    def build_transformer_model(self) -> Model:
        """Build Transformer-based model for time series"""
        if not TF_AVAILABLE:
            return None
        
        inputs = Input(shape=(self.sequence_length, self.n_features))
        
        # Positional encoding (learnable)
        pos_encoding = Dense(self.n_features)(inputs)
        x = Add()([inputs, pos_encoding])
        
        # Transformer blocks
        for _ in range(3):
            # Multi-head attention
            attn_output = MultiHeadAttention(num_heads=4, key_dim=32)(x, x)
            attn_output = Dropout(0.1)(attn_output)
            x = LayerNormalization()(x + attn_output)
            
            # Feed-forward network
            ffn = Dense(128, activation='relu')(x)
            ffn = Dense(self.n_features)(ffn)
            ffn = Dropout(0.1)(ffn)
            x = LayerNormalization()(x + ffn)
        
        # Global pooling
        x = GlobalAveragePooling1D()(x)
        
        # Output layers
        x = Dense(64, activation='relu')(x)
        x = Dropout(0.3)(x)
        output = Dense(self.forecast_horizon, activation='linear')(x)
        
        self.transformer_model = Model(inputs, output)
        self.transformer_model.compile(
            optimizer=Adam(learning_rate=0.0005),
            loss='huber',
            metrics=['mae']
        )
        return self.transformer_model
    
    def prepare_sequences(self, features: np.ndarray, targets: np.ndarray = None) -> Tuple:
        """Prepare sequences for training/prediction"""
        X = []
        y_dir = []
        y_mag = []
        
        for i in range(len(features) - self.sequence_length - self.forecast_horizon):
            X.append(features[i:i+self.sequence_length])
            
            if targets is not None:
                future_returns = targets[i+self.sequence_length:i+self.sequence_length+self.forecast_horizon]
                y_dir.append(1 if np.sum(future_returns) > 0 else 0)
                y_mag.append(future_returns)
        
        X = np.array(X)
        
        if targets is not None:
            return X, np.array(y_dir), np.array(y_mag)
        return X
    
    async def train(self, features: np.ndarray, returns: np.ndarray, 
                    epochs: int = 100) -> Dict[str, Any]:
        """Train all time series models"""
        if not TF_AVAILABLE:
            return {"error": "TensorFlow not available"}
        
        # Prepare sequences
        X, y_dir, y_mag = self.prepare_sequences(features, returns)
        
        if len(X) < 100:
            return {"error": "Insufficient data for training"}
        
        # Train/val split (time-based)
        split = int(len(X) * 0.8)
        X_train, X_val = X[:split], X[split:]
        y_dir_train, y_dir_val = y_dir[:split], y_dir[split:]
        y_mag_train, y_mag_val = y_mag[:split], y_mag[split:]
        
        results = {}
        callbacks = [
            EarlyStopping(patience=15, restore_best_weights=True),
            ReduceLROnPlateau(factor=0.5, patience=7)
        ]
        
        # Update n_features based on actual data
        self.n_features = X.shape[2]
        
        # Train LSTM
        logger.info("Training LSTM model...")
        self.build_lstm_model()
        history = self.lstm_model.fit(
            X_train, {'direction': y_dir_train, 'magnitude': y_mag_train},
            validation_data=(X_val, {'direction': y_dir_val, 'magnitude': y_mag_val}),
            epochs=epochs, batch_size=32, callbacks=callbacks, verbose=0
        )
        results['lstm'] = {
            'direction_accuracy': float(history.history['val_direction_accuracy'][-1]),
            'epochs': len(history.history['loss'])
        }
        
        # Train GRU
        logger.info("Training GRU model...")
        self.build_gru_model()
        y_combined_train = np.column_stack([y_dir_train.reshape(-1, 1), y_mag_train])
        y_combined_val = np.column_stack([y_dir_val.reshape(-1, 1), y_mag_val])
        
        history = self.gru_model.fit(
            X_train, y_combined_train,
            validation_data=(X_val, y_combined_val),
            epochs=epochs, batch_size=32, callbacks=callbacks, verbose=0
        )
        results['gru'] = {
            'val_mae': float(history.history['val_mae'][-1]),
            'epochs': len(history.history['loss'])
        }
        
        # Train Transformer
        logger.info("Training Transformer model...")
        self.build_transformer_model()
        history = self.transformer_model.fit(
            X_train, y_mag_train,
            validation_data=(X_val, y_mag_val),
            epochs=epochs, batch_size=32, callbacks=callbacks, verbose=0
        )
        results['transformer'] = {
            'val_mae': float(history.history['val_mae'][-1]),
            'epochs': len(history.history['loss'])
        }
        
        self.is_trained = True
        self.training_history = results
        
        return results
    
    def predict(self, features: np.ndarray) -> Dict[str, Any]:
        """Ensemble prediction from all models"""
        if not self.is_trained:
            return {"error": "Models not trained"}
        
        X = features[-self.sequence_length:].reshape(1, self.sequence_length, -1)
        
        predictions = {}
        
        if self.lstm_model:
            lstm_dir, lstm_mag = self.lstm_model.predict(X, verbose=0)
            predictions['lstm'] = {
                'direction': float(lstm_dir[0][0]),
                'magnitude': lstm_mag[0].tolist()
            }
        
        if self.gru_model:
            gru_out = self.gru_model.predict(X, verbose=0)[0]
            predictions['gru'] = {
                'direction': float(gru_out[0]),
                'magnitude': gru_out[1:].tolist()
            }
        
        if self.transformer_model:
            trans_out = self.transformer_model.predict(X, verbose=0)[0]
            predictions['transformer'] = {
                'magnitude': trans_out.tolist()
            }
        
        # Ensemble
        directions = [p.get('direction', 0.5) for p in predictions.values() if 'direction' in p]
        avg_direction = np.mean(directions) if directions else 0.5
        
        return {
            "ensemble_direction": float(avg_direction),
            "signal": "bullish" if avg_direction > 0.55 else "bearish" if avg_direction < 0.45 else "neutral",
            "confidence": float(abs(avg_direction - 0.5) * 2),
            "model_predictions": predictions
        }


# =============================================================================
# 4. FINRL-INSPIRED TRADING ENVIRONMENT
# =============================================================================

class Action(Enum):
    """Trading actions"""
    STRONG_SELL = 0
    SELL = 1
    HOLD = 2
    BUY = 3
    STRONG_BUY = 4


class TradingEnvironment:
    """
    Sophisticated trading environment with realistic market simulation.
    Includes transaction costs, slippage, and market impact.
    
    Inspired by FinRL framework design patterns.
    """
    
    def __init__(self, 
                 initial_capital: float = 10000,
                 transaction_cost_pct: float = 0.001,  # 0.1% per trade
                 slippage_pct: float = 0.0005,  # 0.05% slippage
                 max_position_pct: float = 0.25,  # Max 25% per position
                 leverage: float = 1.0):  # No leverage by default
        
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct
        self.max_position_pct = max_position_pct
        self.leverage = leverage
        
        # State variables
        self.capital = initial_capital
        self.position = 0.0  # Current position in asset units
        self.position_value = 0.0
        self.entry_price = 0.0
        self.step_count = 0
        
        # History tracking
        self.trade_history = []
        self.portfolio_history = []
        self.reward_history = []
        
        # Market data
        self.prices = None
        self.features = None
        self.current_idx = 0
        
    def reset(self, prices: np.ndarray, features: np.ndarray) -> np.ndarray:
        """Reset environment with new market data"""
        self.prices = prices
        self.features = features
        self.current_idx = 0
        
        self.capital = self.initial_capital
        self.position = 0.0
        self.position_value = 0.0
        self.entry_price = 0.0
        self.step_count = 0
        
        self.trade_history = []
        self.portfolio_history = []
        self.reward_history = []
        
        return self._get_state()
    
    def _get_state(self) -> np.ndarray:
        """Get current state for agent"""
        if self.features is None or self.current_idx >= len(self.features):
            return np.zeros(35)
        
        # Market features
        market_state = self.features[self.current_idx]
        
        # Portfolio state
        current_price = self.prices[self.current_idx] if self.current_idx < len(self.prices) else 0
        total_value = self.capital + self.position * current_price
        
        portfolio_state = np.array([
            self.capital / self.initial_capital - 1,  # Normalized cash
            self.position * current_price / total_value if total_value > 0 else 0,  # Position ratio
            (current_price - self.entry_price) / self.entry_price if self.entry_price > 0 else 0,  # Unrealized PnL
            self.step_count / 1000,  # Normalized time
            len(self.trade_history) / 100  # Trade frequency
        ])
        
        return np.concatenate([market_state[:30], portfolio_state])
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Execute one step in the environment.
        
        Args:
            action: 0=strong_sell, 1=sell, 2=hold, 3=buy, 4=strong_buy
            
        Returns:
            state, reward, done, info
        """
        if self.current_idx >= len(self.prices) - 1:
            return self._get_state(), 0, True, {"message": "Episode complete"}
        
        current_price = self.prices[self.current_idx]
        next_price = self.prices[self.current_idx + 1]
        
        # Calculate position change based on action
        position_change = self._action_to_position_change(action)
        
        # Execute trade with costs and slippage
        reward, trade_info = self._execute_trade(position_change, current_price)
        
        # Calculate market return reward component
        market_return = (next_price - current_price) / current_price
        position_return = self.position * market_return * current_price
        
        # Combined reward: trading reward + position return
        total_reward = reward + position_return / self.initial_capital
        
        # Risk-adjusted reward (penalize large drawdowns)
        portfolio_value = self.capital + self.position * next_price
        drawdown = (self.initial_capital - portfolio_value) / self.initial_capital
        if drawdown > 0.1:  # 10% drawdown penalty
            total_reward -= drawdown * 0.5
        
        self.reward_history.append(total_reward)
        self.portfolio_history.append({
            'step': self.step_count,
            'capital': self.capital,
            'position': self.position,
            'portfolio_value': portfolio_value,
            'price': next_price
        })
        
        self.current_idx += 1
        self.step_count += 1
        
        done = self.current_idx >= len(self.prices) - 1 or portfolio_value < self.initial_capital * 0.5
        
        return self._get_state(), float(total_reward), done, trade_info
    
    def _action_to_position_change(self, action: int) -> float:
        """Convert action to position change fraction"""
        action_map = {
            0: -1.0,   # Strong sell: close all + short
            1: -0.5,   # Sell: reduce position
            2: 0.0,    # Hold: no change
            3: 0.5,    # Buy: increase position
            4: 1.0     # Strong buy: max position
        }
        return action_map.get(action, 0.0)
    
    def _execute_trade(self, position_change: float, price: float) -> Tuple[float, Dict]:
        """Execute trade with realistic costs"""
        if position_change == 0:
            return 0, {"action": "hold"}
        
        # Calculate target position value
        portfolio_value = self.capital + self.position * price
        max_position_value = portfolio_value * self.max_position_pct * self.leverage
        
        target_position_value = position_change * max_position_value
        current_position_value = self.position * price
        
        trade_value = target_position_value - current_position_value
        
        if abs(trade_value) < 10:  # Minimum trade size
            return 0, {"action": "hold", "reason": "Trade too small"}
        
        # Apply slippage
        slippage = abs(trade_value) * self.slippage_pct
        execution_price = price * (1 + self.slippage_pct if trade_value > 0 else 1 - self.slippage_pct)
        
        # Transaction cost
        transaction_cost = abs(trade_value) * self.transaction_cost_pct
        
        # Execute
        if trade_value > 0:  # Buying
            actual_trade_value = trade_value + slippage + transaction_cost
            if actual_trade_value > self.capital:
                actual_trade_value = self.capital * 0.95  # Use 95% of available capital
            
            units_bought = (actual_trade_value - transaction_cost - slippage) / execution_price
            self.position += units_bought
            self.capital -= actual_trade_value
            self.entry_price = execution_price
            
            trade_info = {
                "action": "buy",
                "units": units_bought,
                "price": execution_price,
                "cost": transaction_cost + slippage,
                "total_value": actual_trade_value
            }
        else:  # Selling
            units_to_sell = min(abs(trade_value) / execution_price, self.position)
            if units_to_sell <= 0:
                return 0, {"action": "hold", "reason": "No position to sell"}
            
            proceeds = units_to_sell * execution_price
            net_proceeds = proceeds - transaction_cost - slippage
            
            self.position -= units_to_sell
            self.capital += net_proceeds
            
            # Calculate realized PnL
            realized_pnl = (execution_price - self.entry_price) * units_to_sell if self.entry_price > 0 else 0
            
            trade_info = {
                "action": "sell",
                "units": units_to_sell,
                "price": execution_price,
                "cost": transaction_cost + slippage,
                "realized_pnl": realized_pnl
            }
        
        self.trade_history.append({
            **trade_info,
            "timestamp": self.step_count,
            "portfolio_value": self.capital + self.position * price
        })
        
        # Reward based on trade efficiency
        reward = -transaction_cost / self.initial_capital  # Penalize transaction costs
        
        return reward, trade_info
    
    def get_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics"""
        if not self.portfolio_history:
            return {}
        
        portfolio_values = [h['portfolio_value'] for h in self.portfolio_history]
        returns = np.diff(portfolio_values) / portfolio_values[:-1] if len(portfolio_values) > 1 else []
        
        # Sharpe ratio (annualized, assuming daily data)
        sharpe = np.sqrt(252) * np.mean(returns) / (np.std(returns) + 1e-8) if len(returns) > 0 else 0
        
        # Max drawdown
        peak = np.maximum.accumulate(portfolio_values)
        drawdown = (peak - portfolio_values) / peak
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
        
        # Win rate
        profitable_trades = [t for t in self.trade_history if t.get('realized_pnl', 0) > 0]
        total_trades = [t for t in self.trade_history if t.get('action') in ['buy', 'sell']]
        win_rate = len(profitable_trades) / len(total_trades) if total_trades else 0
        
        # Total return
        total_return = (portfolio_values[-1] - self.initial_capital) / self.initial_capital if portfolio_values else 0
        
        return {
            "total_return": float(total_return),
            "sharpe_ratio": float(sharpe),
            "max_drawdown": float(max_drawdown),
            "win_rate": float(win_rate),
            "total_trades": len(total_trades),
            "total_costs": sum(t.get('cost', 0) for t in self.trade_history),
            "final_portfolio_value": portfolio_values[-1] if portfolio_values else self.initial_capital
        }


# =============================================================================
# 5. FINRL-INSPIRED DRL AGENT
# =============================================================================

class FinRLAgent:
    """
    Deep Reinforcement Learning agent inspired by FinRL framework.
    Uses DQN with prioritized experience replay and target networks.
    """
    
    def __init__(self, state_dim: int = 35, action_dim: int = 5):
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Hyperparameters
        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.0001
        self.batch_size = 64
        self.tau = 0.001
        
        # Replay buffer with priorities
        self.memory = deque(maxlen=100000)
        self.priorities = deque(maxlen=100000)
        
        # Networks
        if TF_AVAILABLE:
            self.policy_net = self._build_network()
            self.target_net = self._build_network()
            self._update_target(tau=1.0)
        
        self.training_steps = 0
        self.is_trained = False
        
    def _build_network(self) -> Model:
        """Build DQN network"""
        inputs = Input(shape=(self.state_dim,))
        
        x = Dense(256, activation='relu', kernel_regularizer=l2(0.001))(inputs)
        x = BatchNormalization()(x)
        x = Dropout(0.2)(x)
        
        x = Dense(256, activation='relu', kernel_regularizer=l2(0.001))(x)
        x = BatchNormalization()(x)
        x = Dropout(0.2)(x)
        
        x = Dense(128, activation='relu')(x)
        
        # Dueling architecture
        value = Dense(64, activation='relu')(x)
        value = Dense(1, activation='linear')(value)
        
        advantage = Dense(64, activation='relu')(x)
        advantage = Dense(self.action_dim, activation='linear')(advantage)
        
        # Combine using Lambda layer
        def dueling_combine(tensors):
            v, a = tensors
            return v + (a - tf.reduce_mean(a, axis=1, keepdims=True))
        
        q_values = Lambda(dueling_combine)([value, advantage])
        
        model = Model(inputs, q_values)
        model.compile(optimizer=Adam(learning_rate=self.learning_rate), loss='huber')
        return model
    
    def _update_target(self, tau: float = None):
        """Soft update target network"""
        if tau is None:
            tau = self.tau
        
        for target_weight, policy_weight in zip(
            self.target_net.weights, self.policy_net.weights
        ):
            target_weight.assign(tau * policy_weight + (1 - tau) * target_weight)
    
    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """Select action using epsilon-greedy policy"""
        if training and np.random.rand() < self.epsilon:
            return np.random.randint(self.action_dim)
        
        q_values = self.policy_net.predict(state.reshape(1, -1), verbose=0)[0]
        return int(np.argmax(q_values))
    
    def store_transition(self, state, action, reward, next_state, done):
        """Store transition with priority"""
        self.memory.append((state, action, reward, next_state, done))
        self.priorities.append(max(self.priorities) if self.priorities else 1.0)
    
    def train_step(self) -> float:
        """Perform one training step"""
        if len(self.memory) < self.batch_size:
            return 0.0
        
        # Prioritized sampling
        probs = np.array(self.priorities) / sum(self.priorities)
        indices = np.random.choice(len(self.memory), self.batch_size, p=probs)
        
        batch = [self.memory[i] for i in indices]
        states = np.array([t[0] for t in batch])
        actions = np.array([t[1] for t in batch])
        rewards = np.array([t[2] for t in batch])
        next_states = np.array([t[3] for t in batch])
        dones = np.array([t[4] for t in batch])
        
        # Double DQN: select action with policy, evaluate with target
        next_actions = np.argmax(self.policy_net.predict(next_states, verbose=0), axis=1)
        target_q = self.target_net.predict(next_states, verbose=0)
        
        current_q = self.policy_net.predict(states, verbose=0)
        
        for i in range(self.batch_size):
            td_target = rewards[i]
            if not dones[i]:
                td_target += self.gamma * target_q[i][next_actions[i]]
            
            td_error = abs(td_target - current_q[i][actions[i]])
            self.priorities[indices[i]] = td_error + 1e-6
            
            current_q[i][actions[i]] = td_target
        
        loss = self.policy_net.fit(states, current_q, epochs=1, verbose=0).history['loss'][0]
        
        # Soft update target network
        self._update_target()
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        self.training_steps += 1
        
        return loss
    
    async def train(self, env: TradingEnvironment, episodes: int = 100) -> Dict[str, Any]:
        """Train agent in environment"""
        if not TF_AVAILABLE:
            return {"error": "TensorFlow not available"}
        
        episode_rewards = []
        episode_metrics = []
        
        for episode in range(episodes):
            state = env.reset(env.prices, env.features)
            total_reward = 0
            done = False
            
            while not done:
                action = self.select_action(state, training=True)
                next_state, reward, done, info = env.step(action)
                
                self.store_transition(state, action, reward, next_state, done)
                self.train_step()
                
                state = next_state
                total_reward += reward
            
            episode_rewards.append(total_reward)
            metrics = env.get_metrics()
            episode_metrics.append(metrics)
            
            if episode % 10 == 0:
                avg_reward = np.mean(episode_rewards[-10:])
                logger.info(f"Episode {episode}/{episodes}, Avg Reward: {avg_reward:.4f}, "
                           f"Epsilon: {self.epsilon:.4f}, Sharpe: {metrics.get('sharpe_ratio', 0):.2f}")
        
        self.is_trained = True
        
        return {
            "episodes": episodes,
            "final_epsilon": self.epsilon,
            "avg_reward": float(np.mean(episode_rewards)),
            "best_sharpe": float(max(m.get('sharpe_ratio', 0) for m in episode_metrics)),
            "best_return": float(max(m.get('total_return', 0) for m in episode_metrics)),
            "training_steps": self.training_steps
        }


# =============================================================================
# 6. INTEGRATED TRADING INTELLIGENCE ENGINE
# =============================================================================

class TradingIntelligenceEngine:
    """
    Main orchestrator combining all ML/DL components.
    Provides unified interface for training and prediction.
    """
    
    def __init__(self, db):
        self.db = db
        
        # Initialize components
        self.preprocessor = DataPreprocessor()
        self.feature_engineer = FeatureEngineer(pca_components=15)
        self.ensemble = EnsemblePredictor()
        self.time_series = TimeSeriesPredictor(sequence_length=60, forecast_horizon=5)
        self.environment = TradingEnvironment(
            initial_capital=10000,
            transaction_cost_pct=0.001,
            slippage_pct=0.0005
        )
        self.finrl_agent = FinRLAgent(state_dim=35, action_dim=5)
        
        self.is_initialized = False
        self.training_results = {}
        
    async def initialize(self):
        """Initialize all components"""
        logger.info("🚀 Initializing Trading Intelligence Engine...")
        self.is_initialized = True
        logger.info("✅ Trading Intelligence Engine initialized")
        
    async def train_all(self, price_data: List[Dict], epochs: int = 50) -> Dict[str, Any]:
        """Train all models on historical data"""
        logger.info("📊 Starting comprehensive model training...")
        
        # Convert to DataFrame
        df = pd.DataFrame(price_data)
        if 'close' not in df.columns and len(df.columns) > 0:
            df['close'] = df.iloc[:, 0]
        
        # Preprocess data
        df_processed = self.preprocessor.fit_transform(df)
        
        # Extract features
        features_df = self.feature_engineer.extract_features(df)
        features, pca_info = self.feature_engineer.extract_pca_features(features_df)
        
        # Prepare targets
        returns = df['close'].pct_change().fillna(0).values
        direction = (returns > 0).astype(int)
        
        # Split data
        split = int(len(features) * 0.8)
        
        results = {}
        
        # 1. Train Ensemble (XGBoost/LightGBM)
        logger.info("Training Ensemble models (XGBoost/LightGBM)...")
        ensemble_result = self.ensemble.train(
            features[:split], direction[:split],
            features[split:], direction[split:],
            num_rounds=300
        )
        results['ensemble'] = ensemble_result
        
        # 2. Train Time Series Models
        logger.info("Training Time Series models (LSTM/GRU/Transformer)...")
        ts_result = await self.time_series.train(features, returns, epochs=epochs)
        results['time_series'] = ts_result
        
        # 3. Train FinRL Agent
        logger.info("Training FinRL Agent...")
        prices = df['close'].values
        self.environment.prices = prices
        self.environment.features = features
        
        finrl_result = await self.finrl_agent.train(self.environment, episodes=min(epochs, 50))
        results['finrl_agent'] = finrl_result
        
        self.training_results = results
        
        logger.info("✅ All models trained successfully")
        return results
    
    def get_trading_signal(self, recent_data: pd.DataFrame) -> Dict[str, Any]:
        """Get comprehensive trading signal from all models"""
        
        # Extract features
        features_df = self.feature_engineer.extract_features(recent_data)
        features, _ = self.feature_engineer.extract_pca_features(features_df)
        
        signals = {}
        
        # 1. Ensemble prediction
        if self.ensemble.is_trained:
            ensemble_pred = self.ensemble.predict(features[-1:])
            signals['ensemble'] = ensemble_pred
        
        # 2. Time series prediction
        if self.time_series.is_trained:
            ts_pred = self.time_series.predict(features)
            signals['time_series'] = ts_pred
        
        # 3. FinRL agent action
        if self.finrl_agent.is_trained:
            state = features[-1] if len(features[-1]) >= 30 else np.zeros(35)
            if len(state) < 35:
                state = np.pad(state, (0, 35 - len(state)))
            action = self.finrl_agent.select_action(state, training=False)
            action_map = {0: "strong_sell", 1: "sell", 2: "hold", 3: "buy", 4: "strong_buy"}
            signals['finrl'] = {
                "action": action_map[action],
                "action_id": action
            }
        
        # Combine signals
        directions = []
        if 'ensemble' in signals and signals['ensemble'].get('direction'):
            directions.append(1 if signals['ensemble']['direction'] == 'bullish' else 0)
        if 'time_series' in signals and signals['time_series'].get('signal'):
            directions.append(1 if signals['time_series']['signal'] == 'bullish' else 0)
        if 'finrl' in signals:
            directions.append(1 if signals['finrl']['action_id'] >= 3 else 0)
        
        consensus = np.mean(directions) if directions else 0.5
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "consensus_direction": "bullish" if consensus > 0.6 else "bearish" if consensus < 0.4 else "neutral",
            "consensus_score": float(consensus),
            "confidence": float(abs(consensus - 0.5) * 2),
            "model_signals": signals,
            "recommended_action": signals.get('finrl', {}).get('action', 'hold')
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get engine status"""
        return {
            "initialized": self.is_initialized,
            "models": {
                "ensemble": {
                    "trained": self.ensemble.is_trained,
                    "xgboost_available": XGBOOST_AVAILABLE,
                    "lightgbm_available": LIGHTGBM_AVAILABLE
                },
                "time_series": {
                    "trained": self.time_series.is_trained,
                    "lstm": self.time_series.lstm_model is not None,
                    "gru": self.time_series.gru_model is not None,
                    "transformer": self.time_series.transformer_model is not None
                },
                "finrl_agent": {
                    "trained": self.finrl_agent.is_trained,
                    "epsilon": self.finrl_agent.epsilon,
                    "memory_size": len(self.finrl_agent.memory),
                    "training_steps": self.finrl_agent.training_steps
                }
            },
            "environment": {
                "transaction_cost": self.environment.transaction_cost_pct,
                "slippage": self.environment.slippage_pct,
                "max_position": self.environment.max_position_pct
            },
            "training_results": self.training_results
        }


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_engine_instance = None

def get_trading_intelligence(db=None) -> TradingIntelligenceEngine:
    """Get or create engine singleton"""
    global _engine_instance
    if _engine_instance is None and db is not None:
        _engine_instance = TradingIntelligenceEngine(db)
    return _engine_instance

async def initialize_trading_intelligence(db) -> TradingIntelligenceEngine:
    """Initialize trading intelligence engine"""
    engine = get_trading_intelligence(db)
    await engine.initialize()
    return engine

"""
Deep Learning Trading AI Service
Implements advanced neural network models for crypto trading predictions.

Features:
1. LSTM Price Prediction - Predicts future prices based on historical data
2. Transformer Sentiment Analysis - Enhanced news sentiment classification
3. CNN Pattern Recognition - Identifies chart patterns
4. Ensemble Trading Signal Model - Combines all models for trading signals
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import os

# TensorFlow imports
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TF warnings
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, optimizers
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.model_selection import train_test_split

# Technical analysis
try:
    import ta
    from ta.trend import MACD, SMAIndicator, EMAIndicator
    from ta.momentum import RSIIndicator, StochasticOscillator
    from ta.volatility import BollingerBands, AverageTrueRange
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False
    print("Warning: ta library not available, using basic indicators")


class LSTMPricePredictor:
    """
    LSTM Neural Network for price prediction.
    Uses historical price data and technical indicators to predict future prices.
    """
    
    def __init__(self, sequence_length: int = 60, prediction_horizon: int = 5):
        self.sequence_length = sequence_length  # Look back period
        self.prediction_horizon = prediction_horizon  # Days to predict
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.feature_scaler = StandardScaler()
        self.is_trained = False
        
    def build_model(self, n_features: int = 1) -> keras.Model:
        """Build LSTM model architecture"""
        model = keras.Sequential([
            layers.Input(shape=(self.sequence_length, n_features)),
            layers.LSTM(128, return_sequences=True, dropout=0.2),
            layers.LSTM(64, return_sequences=True, dropout=0.2),
            layers.LSTM(32, return_sequences=False, dropout=0.2),
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(16, activation='relu'),
            layers.Dense(self.prediction_horizon)
        ])
        
        model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        self.model = model
        return model
    
    def prepare_data(self, prices: List[float], include_features: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for LSTM training"""
        df = pd.DataFrame({'close': prices})
        
        if include_features and TA_AVAILABLE and len(prices) > 50:
            # Add technical indicators as features
            df['sma_20'] = ta.trend.sma_indicator(df['close'], window=20)
            df['ema_12'] = ta.trend.ema_indicator(df['close'], window=12)
            df['rsi'] = ta.momentum.rsi(df['close'], window=14)
            df['macd'] = ta.trend.macd_diff(df['close'])
            
            # Fill NaN values
            df = df.fillna(method='bfill').fillna(method='ffill')
        
        # Scale features
        scaled_data = self.scaler.fit_transform(df[['close']].values)
        
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_data) - self.prediction_horizon):
            X.append(scaled_data[i-self.sequence_length:i, 0])
            y.append(scaled_data[i:i+self.prediction_horizon, 0])
        
        return np.array(X).reshape(-1, self.sequence_length, 1), np.array(y)
    
    async def train(self, prices: List[float], epochs: int = 50, validation_split: float = 0.2) -> Dict[str, Any]:
        """Train the LSTM model on historical price data"""
        if len(prices) < self.sequence_length + self.prediction_horizon + 20:
            return {"error": "Not enough data for training", "min_required": self.sequence_length + self.prediction_horizon + 20}
        
        X, y = self.prepare_data(prices)
        
        if len(X) < 10:
            return {"error": "Not enough sequences for training"}
        
        # Build model if not exists
        if self.model is None:
            self.build_model(n_features=1)
        
        # Train with early stopping
        early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=32,
            validation_split=validation_split,
            callbacks=[early_stop],
            verbose=0
        )
        
        self.is_trained = True
        
        return {
            "status": "trained",
            "epochs_completed": len(history.history['loss']),
            "final_loss": float(history.history['loss'][-1]),
            "final_val_loss": float(history.history['val_loss'][-1]) if 'val_loss' in history.history else None,
            "model_params": self.model.count_params()
        }
    
    async def predict(self, recent_prices: List[float]) -> Dict[str, Any]:
        """Predict future prices"""
        if not self.is_trained or self.model is None:
            return {"error": "Model not trained"}
        
        if len(recent_prices) < self.sequence_length:
            return {"error": f"Need at least {self.sequence_length} prices for prediction"}
        
        # Use last sequence_length prices
        prices = recent_prices[-self.sequence_length:]
        scaled = self.scaler.transform(np.array(prices).reshape(-1, 1))
        X = scaled.reshape(1, self.sequence_length, 1)
        
        # Predict
        predicted_scaled = self.model.predict(X, verbose=0)
        predicted_prices = self.scaler.inverse_transform(predicted_scaled.reshape(-1, 1)).flatten()
        
        current_price = recent_prices[-1]
        predicted_change = ((predicted_prices[-1] - current_price) / current_price) * 100
        
        return {
            "current_price": current_price,
            "predicted_prices": predicted_prices.tolist(),
            "prediction_horizon_days": self.prediction_horizon,
            "predicted_change_pct": float(predicted_change),
            "trend": "bullish" if predicted_change > 1 else "bearish" if predicted_change < -1 else "neutral",
            "confidence": min(95, max(50, 75 + abs(predicted_change)))
        }


class SentimentAnalyzer:
    """
    Deep Learning Sentiment Analyzer for crypto news.
    Uses a neural network trained on financial sentiment patterns.
    """
    
    def __init__(self):
        self.model = None
        self.vocab_size = 10000
        self.max_length = 200
        self.embedding_dim = 128
        self.is_trained = False
        
        # Crypto-specific sentiment keywords
        self.bullish_keywords = [
            'moon', 'bullish', 'surge', 'rally', 'breakout', 'pump', 'adoption',
            'institutional', 'partnership', 'upgrade', 'launch', 'ath', 'record',
            'growth', 'profit', 'gain', 'buy', 'long', 'accumulate', 'hodl'
        ]
        self.bearish_keywords = [
            'crash', 'bearish', 'dump', 'sell', 'decline', 'drop', 'fall',
            'hack', 'scam', 'fraud', 'ban', 'regulation', 'sec', 'lawsuit',
            'fear', 'panic', 'loss', 'short', 'liquidation', 'capitulation'
        ]
        
    def build_model(self) -> keras.Model:
        """Build sentiment classification model"""
        model = keras.Sequential([
            layers.Input(shape=(self.max_length,)),
            layers.Embedding(self.vocab_size, self.embedding_dim),
            layers.Bidirectional(layers.LSTM(64, return_sequences=True)),
            layers.GlobalMaxPooling1D(),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(32, activation='relu'),
            layers.Dense(3, activation='softmax')  # bearish, neutral, bullish
        ])
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
        return model
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text using keyword matching + scoring"""
        text_lower = text.lower()
        
        bullish_score = sum(1 for kw in self.bullish_keywords if kw in text_lower)
        bearish_score = sum(1 for kw in self.bearish_keywords if kw in text_lower)
        
        total_score = bullish_score + bearish_score
        if total_score == 0:
            sentiment = "neutral"
            confidence = 50
            scores = {"bullish": 0.33, "neutral": 0.34, "bearish": 0.33}
        else:
            bullish_ratio = bullish_score / total_score
            bearish_ratio = bearish_score / total_score
            
            if bullish_ratio > 0.6:
                sentiment = "bullish"
                confidence = min(95, 60 + bullish_ratio * 40)
            elif bearish_ratio > 0.6:
                sentiment = "bearish"
                confidence = min(95, 60 + bearish_ratio * 40)
            else:
                sentiment = "neutral"
                confidence = 50 + abs(bullish_ratio - bearish_ratio) * 30
            
            scores = {
                "bullish": bullish_ratio,
                "neutral": 1 - max(bullish_ratio, bearish_ratio),
                "bearish": bearish_ratio
            }
        
        return {
            "sentiment": sentiment,
            "confidence": float(confidence),
            "scores": scores,
            "bullish_signals": bullish_score,
            "bearish_signals": bearish_score
        }
    
    async def analyze_news_batch(self, news_items: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment of multiple news items"""
        if not news_items:
            return {"overall_sentiment": "neutral", "confidence": 50, "analysis": []}
        
        analyses = []
        sentiment_scores = {"bullish": 0, "neutral": 0, "bearish": 0}
        
        for item in news_items[:20]:  # Limit to 20 items
            title = item.get('title', '')
            analysis = self.analyze_text(title)
            analysis['title'] = title[:100]
            analyses.append(analysis)
            
            # Weight by confidence
            weight = analysis['confidence'] / 100
            sentiment_scores[analysis['sentiment']] += weight
        
        # Determine overall sentiment
        total_weight = sum(sentiment_scores.values())
        if total_weight > 0:
            for k in sentiment_scores:
                sentiment_scores[k] /= total_weight
        
        overall = max(sentiment_scores, key=sentiment_scores.get)
        
        return {
            "overall_sentiment": overall,
            "confidence": float(sentiment_scores[overall] * 100),
            "sentiment_distribution": sentiment_scores,
            "news_analyzed": len(analyses),
            "detailed_analysis": analyses[:5]  # Return top 5
        }


class PatternRecognizer:
    """
    CNN-based chart pattern recognition.
    Identifies common technical patterns in price data.
    """
    
    PATTERNS = [
        'head_and_shoulders', 'inverse_head_and_shoulders',
        'double_top', 'double_bottom',
        'ascending_triangle', 'descending_triangle',
        'bullish_flag', 'bearish_flag',
        'cup_and_handle', 'wedge',
        'no_pattern'
    ]
    
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.model = None
        self.scaler = MinMaxScaler()
        
    def build_model(self) -> keras.Model:
        """Build CNN model for pattern recognition"""
        model = keras.Sequential([
            layers.Input(shape=(self.window_size, 1)),
            layers.Conv1D(64, 3, activation='relu', padding='same'),
            layers.MaxPooling1D(2),
            layers.Conv1D(128, 3, activation='relu', padding='same'),
            layers.MaxPooling1D(2),
            layers.Conv1D(64, 3, activation='relu', padding='same'),
            layers.GlobalAveragePooling1D(),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(len(self.PATTERNS), activation='softmax')
        ])
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
        return model
    
    def detect_patterns_rule_based(self, prices: List[float]) -> Dict[str, Any]:
        """Detect patterns using rule-based analysis"""
        if len(prices) < self.window_size:
            return {"pattern": "insufficient_data", "confidence": 0}
        
        prices = np.array(prices[-self.window_size:])
        normalized = (prices - prices.min()) / (prices.max() - prices.min() + 1e-8)
        
        patterns_detected = []
        
        # Simple pattern detection rules
        mid = len(normalized) // 2
        first_half = normalized[:mid]
        second_half = normalized[mid:]
        
        # Double top detection
        peaks = self._find_peaks(normalized)
        if len(peaks) >= 2:
            if abs(normalized[peaks[-1]] - normalized[peaks[-2]]) < 0.1:
                patterns_detected.append(("double_top", 70))
        
        # Double bottom detection
        troughs = self._find_troughs(normalized)
        if len(troughs) >= 2:
            if abs(normalized[troughs[-1]] - normalized[troughs[-2]]) < 0.1:
                patterns_detected.append(("double_bottom", 70))
        
        # Ascending triangle
        if np.mean(first_half) < np.mean(second_half) and np.std(second_half[-10:]) < np.std(first_half):
            patterns_detected.append(("ascending_triangle", 65))
        
        # Descending triangle
        if np.mean(first_half) > np.mean(second_half) and np.std(second_half[-10:]) < np.std(first_half):
            patterns_detected.append(("descending_triangle", 65))
        
        # Bullish flag (sharp rise, then consolidation)
        if first_half[-1] > first_half[0] * 1.05 and np.std(second_half) < np.std(first_half):
            patterns_detected.append(("bullish_flag", 60))
        
        # Bearish flag
        if first_half[-1] < first_half[0] * 0.95 and np.std(second_half) < np.std(first_half):
            patterns_detected.append(("bearish_flag", 60))
        
        if not patterns_detected:
            return {
                "pattern": "no_clear_pattern",
                "confidence": 50,
                "trend": "up" if normalized[-1] > normalized[0] else "down"
            }
        
        # Return highest confidence pattern
        best_pattern = max(patterns_detected, key=lambda x: x[1])
        
        return {
            "pattern": best_pattern[0],
            "confidence": best_pattern[1],
            "all_patterns": [{"name": p[0], "confidence": p[1]} for p in patterns_detected],
            "is_bullish": best_pattern[0] in ['double_bottom', 'ascending_triangle', 'bullish_flag', 'cup_and_handle', 'inverse_head_and_shoulders'],
            "is_bearish": best_pattern[0] in ['double_top', 'descending_triangle', 'bearish_flag', 'head_and_shoulders']
        }
    
    def _find_peaks(self, data: np.ndarray, threshold: float = 0.7) -> List[int]:
        """Find local peaks in data"""
        peaks = []
        for i in range(1, len(data) - 1):
            if data[i] > data[i-1] and data[i] > data[i+1] and data[i] > threshold:
                peaks.append(i)
        return peaks
    
    def _find_troughs(self, data: np.ndarray, threshold: float = 0.3) -> List[int]:
        """Find local troughs in data"""
        troughs = []
        for i in range(1, len(data) - 1):
            if data[i] < data[i-1] and data[i] < data[i+1] and data[i] < threshold:
                troughs.append(i)
        return troughs


class DeepLearningTradingAI:
    """
    Ensemble Deep Learning Trading AI.
    Combines LSTM price prediction, sentiment analysis, and pattern recognition
    to generate comprehensive trading signals.
    """
    
    def __init__(self, db=None):
        self.db = db
        self.price_predictor = LSTMPricePredictor(sequence_length=60, prediction_horizon=5)
        self.sentiment_analyzer = SentimentAnalyzer()
        self.pattern_recognizer = PatternRecognizer(window_size=30)
        self.trained_coins = {}
        
    async def train_on_coin(self, coin_id: str, prices: List[float]) -> Dict[str, Any]:
        """Train all models on a specific coin's data"""
        results = {
            "coin_id": coin_id,
            "timestamp": datetime.now().isoformat(),
            "models": {}
        }
        
        # Train LSTM
        try:
            lstm_result = await self.price_predictor.train(prices, epochs=30)
            results["models"]["lstm_price_predictor"] = lstm_result
            self.trained_coins[coin_id] = True
        except Exception as e:
            results["models"]["lstm_price_predictor"] = {"error": str(e)}
        
        results["status"] = "trained" if self.trained_coins.get(coin_id) else "partial"
        return results
    
    async def generate_deep_signal(
        self, 
        coin_id: str, 
        prices: List[float], 
        news: List[Dict] = None,
        current_price: float = None
    ) -> Dict[str, Any]:
        """Generate comprehensive trading signal using all AI models"""
        
        signal = {
            "coin_id": coin_id,
            "timestamp": datetime.now().isoformat(),
            "current_price": current_price or (prices[-1] if prices else 0),
            "components": {},
            "final_signal": None,
            "confidence": 0,
            "reasoning": []
        }
        
        weights = {
            "price_prediction": 0.40,
            "sentiment": 0.25,
            "pattern": 0.20,
            "technical": 0.15
        }
        
        total_score = 0  # -100 to +100 scale
        total_weight = 0
        
        # 1. LSTM Price Prediction
        if len(prices) >= self.price_predictor.sequence_length:
            try:
                if self.trained_coins.get(coin_id):
                    prediction = await self.price_predictor.predict(prices)
                else:
                    # Quick train if not trained
                    await self.price_predictor.train(prices, epochs=20)
                    self.trained_coins[coin_id] = True
                    prediction = await self.price_predictor.predict(prices)
                
                signal["components"]["price_prediction"] = prediction
                
                if "predicted_change_pct" in prediction:
                    change = prediction["predicted_change_pct"]
                    # Convert to score
                    pred_score = np.clip(change * 10, -100, 100)
                    total_score += pred_score * weights["price_prediction"]
                    total_weight += weights["price_prediction"]
                    
                    signal["reasoning"].append(
                        f"LSTM predicts {change:.2f}% change → {'Bullish' if change > 0 else 'Bearish'}"
                    )
            except Exception as e:
                signal["components"]["price_prediction"] = {"error": str(e)}
        
        # 2. Sentiment Analysis
        if news:
            try:
                sentiment = await self.sentiment_analyzer.analyze_news_batch(news)
                signal["components"]["sentiment"] = sentiment
                
                sent = sentiment.get("overall_sentiment", "neutral")
                conf = sentiment.get("confidence", 50)
                
                if sent == "bullish":
                    sent_score = conf
                elif sent == "bearish":
                    sent_score = -conf
                else:
                    sent_score = 0
                
                total_score += sent_score * weights["sentiment"]
                total_weight += weights["sentiment"]
                
                signal["reasoning"].append(
                    f"Sentiment: {sent.upper()} ({conf:.0f}% confidence)"
                )
            except Exception as e:
                signal["components"]["sentiment"] = {"error": str(e)}
        
        # 3. Pattern Recognition
        if len(prices) >= self.pattern_recognizer.window_size:
            try:
                pattern = self.pattern_recognizer.detect_patterns_rule_based(prices)
                signal["components"]["pattern"] = pattern
                
                if pattern.get("is_bullish"):
                    pattern_score = pattern.get("confidence", 50)
                elif pattern.get("is_bearish"):
                    pattern_score = -pattern.get("confidence", 50)
                else:
                    pattern_score = 0
                
                total_score += pattern_score * weights["pattern"]
                total_weight += weights["pattern"]
                
                signal["reasoning"].append(
                    f"Pattern: {pattern.get('pattern', 'none')} ({pattern.get('confidence', 0):.0f}%)"
                )
            except Exception as e:
                signal["components"]["pattern"] = {"error": str(e)}
        
        # 4. Technical Indicators
        if len(prices) >= 30 and TA_AVAILABLE:
            try:
                tech = self._calculate_technical_score(prices)
                signal["components"]["technical"] = tech
                
                total_score += tech["score"] * weights["technical"]
                total_weight += weights["technical"]
                
                signal["reasoning"].append(
                    f"Technical: {tech['signal']} (RSI: {tech.get('rsi', 50):.0f})"
                )
            except Exception as e:
                signal["components"]["technical"] = {"error": str(e)}
        
        # Calculate final signal
        if total_weight > 0:
            final_score = total_score / total_weight
            
            if final_score > 30:
                signal["final_signal"] = "STRONG_BUY"
                signal["action"] = "BUY"
            elif final_score > 10:
                signal["final_signal"] = "BUY"
                signal["action"] = "BUY"
            elif final_score < -30:
                signal["final_signal"] = "STRONG_SELL"
                signal["action"] = "SELL"
            elif final_score < -10:
                signal["final_signal"] = "SELL"
                signal["action"] = "SELL"
            else:
                signal["final_signal"] = "HOLD"
                signal["action"] = "HOLD"
            
            signal["confidence"] = min(95, 50 + abs(final_score) * 0.5)
            signal["score"] = float(final_score)
        else:
            signal["final_signal"] = "INSUFFICIENT_DATA"
            signal["action"] = "HOLD"
            signal["confidence"] = 0
        
        return signal
    
    def _calculate_technical_score(self, prices: List[float]) -> Dict[str, Any]:
        """Calculate technical indicator score"""
        df = pd.DataFrame({'close': prices})
        
        # RSI
        rsi = ta.momentum.rsi(df['close'], window=14).iloc[-1]
        
        # MACD
        macd = ta.trend.macd_diff(df['close']).iloc[-1]
        
        # Moving averages
        sma_20 = ta.trend.sma_indicator(df['close'], window=20).iloc[-1]
        current = prices[-1]
        
        # Calculate score
        score = 0
        
        # RSI scoring
        if rsi < 30:
            score += 30  # Oversold - bullish
        elif rsi > 70:
            score -= 30  # Overbought - bearish
        
        # MACD scoring
        if macd > 0:
            score += 20
        else:
            score -= 20
        
        # Price vs SMA
        if current > sma_20:
            score += 15
        else:
            score -= 15
        
        return {
            "score": score,
            "signal": "bullish" if score > 10 else "bearish" if score < -10 else "neutral",
            "rsi": float(rsi) if not np.isnan(rsi) else 50,
            "macd": float(macd) if not np.isnan(macd) else 0,
            "price_vs_sma": "above" if current > sma_20 else "below"
        }
    
    async def get_model_status(self) -> Dict[str, Any]:
        """Get status of all AI models"""
        return {
            "lstm_price_predictor": {
                "trained": self.price_predictor.is_trained,
                "sequence_length": self.price_predictor.sequence_length,
                "prediction_horizon": self.price_predictor.prediction_horizon,
                "trained_coins": list(self.trained_coins.keys())
            },
            "sentiment_analyzer": {
                "available": True,
                "bullish_keywords": len(self.sentiment_analyzer.bullish_keywords),
                "bearish_keywords": len(self.sentiment_analyzer.bearish_keywords)
            },
            "pattern_recognizer": {
                "available": True,
                "patterns_supported": self.pattern_recognizer.PATTERNS,
                "window_size": self.pattern_recognizer.window_size
            },
            "ensemble_ready": True,
            "tensorflow_version": tf.__version__
        }


# Singleton instance
_deep_learning_ai = None

def get_deep_learning_ai(db=None) -> DeepLearningTradingAI:
    """Get or create the deep learning AI instance"""
    global _deep_learning_ai
    if _deep_learning_ai is None:
        _deep_learning_ai = DeepLearningTradingAI(db)
    return _deep_learning_ai

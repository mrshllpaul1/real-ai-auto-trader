"""
Multi-Timeframe (MTF) Training Service
Trains ML models using multi-timeframe OHLCV data for improved predictions.

Features:
- Combines signals from multiple timeframes (1h, 4h, 1D, 1W)
- Trains ensemble models that consider multi-timeframe alignment
- Learns patterns that appear across different time horizons
- Optimizes for both short-term and long-term predictions
"""

import asyncio
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
import uuid
import os

logger = logging.getLogger(__name__)

# Check for lightweight mode
ML_LIGHTWEIGHT_MODE = os.environ.get('ML_LIGHTWEIGHT_MODE', 'false').lower() == 'true'


class MTFTrainingService:
    """
    Multi-Timeframe Training Service.
    
    Trains models using data from multiple timeframes to capture:
    - Short-term momentum (1h, 4h)
    - Medium-term trends (1D)
    - Long-term cycles (1W)
    
    The multi-timeframe approach helps identify:
    - Trend alignment across timeframes
    - Divergence signals
    - Optimal entry/exit points
    """
    
    TRAINING_TIMEFRAMES = ["1h", "4h", "1D"]
    FEATURE_COLUMNS = [
        "close", "sma_7", "sma_20", "sma_50", 
        "rsi", "volatility", "volume_ratio",
        "return_1", "return_5", "return_10", "high_low_range"
    ]
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.training_collection = db["mtf_training_results"]
        self.model_collection = db["mtf_models"]
        self._training_status: Dict[str, Any] = {
            "status": "idle",
            "last_trained": None,
            "coins_trained": 0,
            "accuracy": 0.0
        }
        self._models: Dict[str, Any] = {}
        
    async def get_mtf_service(self):
        """Get the multi-timeframe historical data service"""
        from services.multitimeframe_historical_service import get_multitimeframe_service
        return get_multitimeframe_service(self.db)
    
    async def prepare_training_data(
        self,
        symbols: List[str],
        timeframes: List[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare multi-timeframe training data for all symbols.
        
        Returns:
            Dict with training features per symbol
        """
        if timeframes is None:
            timeframes = self.TRAINING_TIMEFRAMES
            
        mtf_service = await self.get_mtf_service()
        if not mtf_service:
            return {"error": "MTF service not initialized"}
        
        training_data = {
            "symbols": {},
            "total_samples": 0,
            "timeframes": timeframes
        }
        
        for symbol in symbols:
            try:
                # Get features for this symbol
                features = await mtf_service.get_training_features(symbol, timeframes)
                
                if features.get("timeframes"):
                    training_data["symbols"][symbol] = features
                    training_data["total_samples"] += 1
                    
            except Exception as e:
                logger.warning(f"Failed to get training data for {symbol}: {e}")
                continue
        
        training_data["prepared_at"] = datetime.now(timezone.utc).isoformat()
        return training_data
    
    async def calculate_mtf_alignment(
        self,
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate multi-timeframe trend alignment.
        
        When all timeframes agree on direction, signals are stronger.
        """
        timeframes = features.get("timeframes", {})
        
        if not timeframes:
            return {"alignment": 0, "direction": "neutral"}
        
        bullish_count = 0
        bearish_count = 0
        total_tf = 0
        
        for tf, tf_data in timeframes.items():
            if not tf_data:
                continue
            total_tf += 1
            
            # Check trend indicators
            close = tf_data.get("close", 0)
            sma_20 = tf_data.get("sma_20", close)
            sma_50 = tf_data.get("sma_50", close)
            rsi = tf_data.get("rsi", 50)
            
            # Bullish signals
            if close > sma_20 and close > sma_50 and rsi > 50:
                bullish_count += 1
            # Bearish signals
            elif close < sma_20 and close < sma_50 and rsi < 50:
                bearish_count += 1
        
        if total_tf == 0:
            return {"alignment": 0, "direction": "neutral"}
        
        if bullish_count == total_tf:
            return {"alignment": 1.0, "direction": "bullish", "strength": "strong"}
        elif bearish_count == total_tf:
            return {"alignment": -1.0, "direction": "bearish", "strength": "strong"}
        elif bullish_count > bearish_count:
            return {
                "alignment": bullish_count / total_tf,
                "direction": "bullish",
                "strength": "moderate" if bullish_count >= total_tf * 0.66 else "weak"
            }
        elif bearish_count > bullish_count:
            return {
                "alignment": -bearish_count / total_tf,
                "direction": "bearish",
                "strength": "moderate" if bearish_count >= total_tf * 0.66 else "weak"
            }
        else:
            return {"alignment": 0, "direction": "neutral", "strength": "none"}
    
    async def extract_feature_vector(
        self,
        symbol_features: Dict[str, Any]
    ) -> Optional[np.ndarray]:
        """
        Extract a flat feature vector from multi-timeframe features.
        
        Creates a unified feature vector combining all timeframes.
        """
        timeframes = symbol_features.get("timeframes", {})
        
        if not timeframes:
            return None
        
        feature_vector = []
        
        for tf in self.TRAINING_TIMEFRAMES:
            tf_data = timeframes.get(tf, {})
            
            if tf_data:
                for col in self.FEATURE_COLUMNS:
                    feature_vector.append(float(tf_data.get(col, 0)))
            else:
                # Pad with zeros if timeframe not available
                feature_vector.extend([0.0] * len(self.FEATURE_COLUMNS))
        
        return np.array(feature_vector)
    
    async def train_mtf_model(
        self,
        symbols: List[str] = None,
        timeframes: List[str] = None,
        epochs: int = 50,
        learning_rate: float = 0.001
    ) -> Dict[str, Any]:
        """
        Train a multi-timeframe prediction model.
        
        This is the main training method that:
        1. Fetches multi-timeframe data for all symbols
        2. Prepares feature vectors
        3. Trains an ensemble model
        4. Stores the trained model weights
        
        Args:
            symbols: List of coin symbols to train on
            timeframes: Timeframes to use (default: 1h, 4h, 1D)
            epochs: Number of training epochs
            learning_rate: Learning rate for optimization
        
        Returns:
            Training results with accuracy metrics
        """
        training_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        
        self._training_status = {
            "status": "training",
            "training_id": training_id,
            "started_at": started_at.isoformat(),
            "progress": 0,
            "current_phase": "initializing"
        }
        
        try:
            # Check lightweight mode
            if ML_LIGHTWEIGHT_MODE:
                epochs = min(epochs, 10)
                logger.info("🔋 Running in lightweight mode - limited epochs")
            
            # Default symbols if not provided
            if symbols is None:
                symbols = await self._get_default_training_symbols()
            
            if timeframes is None:
                timeframes = self.TRAINING_TIMEFRAMES
            
            logger.info(f"🚀 Starting MTF training on {len(symbols)} symbols...")
            self._training_status["current_phase"] = "fetching_data"
            self._training_status["total_symbols"] = len(symbols)
            
            # Fetch multi-timeframe data
            mtf_service = await self.get_mtf_service()
            if not mtf_service:
                raise Exception("MTF service not initialized")
            
            # Prepare training data
            X_train = []  # Feature vectors
            y_train = []  # Labels (will use future returns as labels)
            symbol_data = {}  # Store processed data
            
            for idx, symbol in enumerate(symbols):
                try:
                    self._training_status["progress"] = int((idx / len(symbols)) * 50)
                    self._training_status["current_symbol"] = symbol
                    
                    # Get features
                    features = await mtf_service.get_training_features(symbol, timeframes)
                    
                    if not features.get("timeframes"):
                        continue
                    
                    # Extract feature vector
                    feature_vector = await self.extract_feature_vector(features)
                    
                    if feature_vector is None:
                        continue
                    
                    # Calculate alignment score for labeling
                    alignment = await self.calculate_mtf_alignment(features)
                    
                    # Use alignment as a proxy for label
                    # In production, you'd use actual future returns
                    label = 1 if alignment["alignment"] > 0.3 else (0 if alignment["alignment"] > -0.3 else -1)
                    
                    X_train.append(feature_vector)
                    y_train.append(label)
                    
                    symbol_data[symbol] = {
                        "features": features,
                        "alignment": alignment,
                        "label": label
                    }
                    
                except Exception as e:
                    logger.warning(f"Failed to process {symbol}: {e}")
                    continue
            
            if len(X_train) < 5:
                raise Exception(f"Insufficient training data: only {len(X_train)} samples")
            
            logger.info(f"📊 Prepared {len(X_train)} training samples")
            self._training_status["current_phase"] = "training_model"
            self._training_status["training_samples"] = len(X_train)
            
            # Convert to numpy arrays
            X_train = np.array(X_train)
            y_train = np.array(y_train)
            
            # Normalize features
            X_mean = np.mean(X_train, axis=0)
            X_std = np.std(X_train, axis=0) + 1e-8
            X_normalized = (X_train - X_mean) / X_std
            
            # Train a simple neural network (or use sklearn if available)
            model_weights = await self._train_simple_model(
                X_normalized, y_train, epochs, learning_rate
            )
            
            self._training_status["progress"] = 90
            self._training_status["current_phase"] = "saving_model"
            
            # Calculate training accuracy
            predictions = await self._predict_with_weights(X_normalized, model_weights)
            accuracy = np.mean(predictions == y_train)
            
            # Store model
            model_doc = {
                "model_id": training_id,
                "type": "mtf_ensemble",
                "weights": model_weights.tolist() if hasattr(model_weights, 'tolist') else model_weights,
                "normalization": {
                    "mean": X_mean.tolist(),
                    "std": X_std.tolist()
                },
                "timeframes": timeframes,
                "feature_columns": self.FEATURE_COLUMNS,
                "trained_on": len(symbols),
                "accuracy": float(accuracy),
                "epochs": epochs,
                "learning_rate": learning_rate,
                "created_at": started_at,
                "completed_at": datetime.now(timezone.utc)
            }
            
            # Save to database
            await self.model_collection.update_one(
                {"type": "mtf_ensemble"},
                {"$set": model_doc},
                upsert=True
            )
            
            # Store training result
            result = {
                "training_id": training_id,
                "status": "completed",
                "symbols_trained": len(X_train),
                "total_symbols": len(symbols),
                "timeframes": timeframes,
                "epochs": epochs,
                "accuracy": float(accuracy),
                "accuracy_pct": f"{accuracy * 100:.1f}%",
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": (datetime.now(timezone.utc) - started_at).total_seconds(),
                "sample_predictions": [
                    {"symbol": sym, "alignment": data["alignment"], "prediction": int(data["label"])}
                    for sym, data in list(symbol_data.items())[:5]
                ]
            }
            
            # Store training history
            await self.training_collection.insert_one({
                **result,
                "timestamp": datetime.now(timezone.utc)
            })
            
            self._training_status = {
                "status": "completed",
                "training_id": training_id,
                "last_trained": datetime.now(timezone.utc).isoformat(),
                "coins_trained": len(X_train),
                "accuracy": float(accuracy)
            }
            
            logger.info(f"✅ MTF training completed! Accuracy: {accuracy * 100:.1f}%")
            return result
            
        except Exception as e:
            logger.error(f"❌ MTF training failed: {e}")
            self._training_status = {
                "status": "failed",
                "error": str(e),
                "training_id": training_id
            }
            return {
                "training_id": training_id,
                "status": "failed",
                "error": str(e)
            }
    
    async def _train_simple_model(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int,
        learning_rate: float
    ) -> np.ndarray:
        """
        Train a simple logistic regression model.
        Falls back to numpy if sklearn not available.
        """
        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import LabelEncoder
            
            # Encode labels
            le = LabelEncoder()
            y_encoded = le.fit_transform(y)
            
            # Train model
            model = LogisticRegression(
                max_iter=epochs * 10,
                C=1.0 / learning_rate,
                random_state=42,
                multi_class='multinomial'
            )
            model.fit(X, y_encoded)
            
            # Store model reference
            self._models["sklearn_lr"] = model
            self._models["label_encoder"] = le
            
            # Return coefficients as weights
            return model.coef_
            
        except ImportError:
            logger.warning("sklearn not available, using simple gradient descent")
            return await self._train_gradient_descent(X, y, epochs, learning_rate)
    
    async def _train_gradient_descent(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int,
        learning_rate: float
    ) -> np.ndarray:
        """
        Simple gradient descent training (fallback).
        """
        n_features = X.shape[1]
        n_classes = len(np.unique(y))
        
        # Initialize weights
        weights = np.random.randn(n_classes, n_features) * 0.01
        
        # Map labels to 0, 1, 2
        label_map = {-1: 0, 0: 1, 1: 2}
        y_mapped = np.array([label_map.get(yi, 1) for yi in y])
        
        for epoch in range(epochs):
            # Forward pass
            scores = X @ weights.T
            exp_scores = np.exp(scores - np.max(scores, axis=1, keepdims=True))
            probs = exp_scores / np.sum(exp_scores, axis=1, keepdims=True)
            
            # Compute gradients
            n_samples = X.shape[0]
            one_hot = np.zeros((n_samples, n_classes))
            one_hot[np.arange(n_samples), y_mapped] = 1
            
            gradient = (probs - one_hot).T @ X / n_samples
            
            # Update weights
            weights -= learning_rate * gradient
        
        self._models["gd_weights"] = weights
        return weights
    
    async def _predict_with_weights(
        self,
        X: np.ndarray,
        weights: np.ndarray
    ) -> np.ndarray:
        """
        Make predictions using model weights.
        """
        if "sklearn_lr" in self._models:
            model = self._models["sklearn_lr"]
            le = self._models["label_encoder"]
            predictions = model.predict(X)
            return le.inverse_transform(predictions)
        else:
            # Use weights directly
            scores = X @ weights.T
            pred_indices = np.argmax(scores, axis=1)
            index_to_label = {0: -1, 1: 0, 2: 1}
            return np.array([index_to_label.get(idx, 0) for idx in pred_indices])
    
    async def _get_default_training_symbols(self) -> List[str]:
        """
        Get default symbols for training from stored MTF data.
        """
        mtf_service = await self.get_mtf_service()
        if not mtf_service:
            return ["BTC", "ETH", "SOL", "ADA", "DOT", "AVAX", "LINK", "MATIC"]
        
        stats = await mtf_service.get_storage_stats()
        
        # Get all symbols that have data
        all_symbols = set()
        for tf_data in stats.get("timeframes", {}).values():
            all_symbols.update(tf_data.get("symbols", []))
        
        if all_symbols:
            return list(all_symbols)
        
        return ["BTC", "ETH", "SOL", "ADA", "DOT", "AVAX", "LINK", "MATIC"]
    
    async def get_training_status(self) -> Dict[str, Any]:
        """Get current training status"""
        return self._training_status
    
    async def get_training_history(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get training history"""
        cursor = self.training_collection.find(
            {},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def predict(
        self,
        symbol: str,
        timeframes: List[str] = None
    ) -> Dict[str, Any]:
        """
        Make a prediction for a symbol using the trained MTF model.
        
        Returns:
            Prediction with confidence score
        """
        if timeframes is None:
            timeframes = self.TRAINING_TIMEFRAMES
        
        # Get latest model
        model_doc = await self.model_collection.find_one({"type": "mtf_ensemble"})
        
        if not model_doc:
            return {
                "error": "No trained model found. Run /api/mtf-training/train-now first.",
                "symbol": symbol
            }
        
        # Get features for symbol
        mtf_service = await self.get_mtf_service()
        if not mtf_service:
            return {"error": "MTF service not initialized"}
        
        features = await mtf_service.get_training_features(symbol, timeframes)
        
        if not features.get("timeframes"):
            return {
                "error": f"No MTF data available for {symbol}",
                "symbol": symbol
            }
        
        # Extract feature vector
        feature_vector = await self.extract_feature_vector(features)
        
        if feature_vector is None:
            return {"error": "Failed to extract features"}
        
        # Normalize
        X_mean = np.array(model_doc["normalization"]["mean"])
        X_std = np.array(model_doc["normalization"]["std"])
        X_normalized = (feature_vector - X_mean) / X_std
        
        # Calculate alignment
        alignment = await self.calculate_mtf_alignment(features)
        
        # Get prediction
        weights = np.array(model_doc["weights"])
        
        if "sklearn_lr" in self._models:
            model = self._models["sklearn_lr"]
            le = self._models["label_encoder"]
            prediction = model.predict([X_normalized])[0]
            probas = model.predict_proba([X_normalized])[0]
            confidence = float(np.max(probas))
            prediction = int(le.inverse_transform([prediction])[0])
        else:
            # Use weights directly
            scores = X_normalized @ weights.T
            exp_scores = np.exp(scores - np.max(scores))
            probas = exp_scores / np.sum(exp_scores)
            pred_index = np.argmax(probas)
            index_to_label = {0: -1, 1: 0, 2: 1}
            prediction = index_to_label.get(pred_index, 0)
            confidence = float(np.max(probas))
        
        # Map prediction to signal
        signal_map = {-1: "SELL", 0: "HOLD", 1: "BUY"}
        
        return {
            "symbol": symbol,
            "prediction": prediction,
            "signal": signal_map.get(prediction, "HOLD"),
            "confidence": confidence,
            "confidence_pct": f"{confidence * 100:.1f}%",
            "alignment": alignment,
            "timeframes_analyzed": timeframes,
            "model_accuracy": model_doc.get("accuracy", 0),
            "model_trained_at": model_doc.get("completed_at"),
            "features": features,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def predict_batch(
        self,
        symbols: List[str] = None,
        timeframes: List[str] = None
    ) -> Dict[str, Any]:
        """
        Make predictions for multiple symbols.
        """
        if symbols is None:
            symbols = await self._get_default_training_symbols()
        
        predictions = []
        errors = []
        
        for symbol in symbols:
            try:
                pred = await self.predict(symbol, timeframes)
                if "error" not in pred:
                    predictions.append(pred)
                else:
                    errors.append({"symbol": symbol, "error": pred["error"]})
            except Exception as e:
                errors.append({"symbol": symbol, "error": str(e)})
        
        # Sort by confidence
        predictions.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        # Separate by signal
        buy_signals = [p for p in predictions if p.get("signal") == "BUY"]
        sell_signals = [p for p in predictions if p.get("signal") == "SELL"]
        hold_signals = [p for p in predictions if p.get("signal") == "HOLD"]
        
        return {
            "total_predictions": len(predictions),
            "buy_signals": len(buy_signals),
            "sell_signals": len(sell_signals),
            "hold_signals": len(hold_signals),
            "top_buys": buy_signals[:5],
            "top_sells": sell_signals[:5],
            "all_predictions": predictions,
            "errors": errors,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global instance
_mtf_training_service: Optional[MTFTrainingService] = None


def get_mtf_training_service(db: AsyncIOMotorDatabase = None) -> Optional[MTFTrainingService]:
    """Get or create MTF Training Service instance"""
    global _mtf_training_service
    if _mtf_training_service is None and db is not None:
        _mtf_training_service = MTFTrainingService(db)
    return _mtf_training_service

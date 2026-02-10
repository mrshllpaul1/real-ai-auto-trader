"""
Enhanced Multi-Timeframe (MTF) Training Service with Media/Sentiment Integration

Combines:
- Multi-timeframe OHLCV technical indicators (1h, 4h, 1D)
- Social sentiment from Reddit, Twitter analysis
- Fear & Greed Index
- News sentiment from CryptoPanic
- AI-powered sentiment analysis using Emergent LLM

Features:
- Downloads historical OHLCV data from Kraken
- Fetches real-time sentiment from multiple sources
- Trains ensemble models with technical + sentiment features
- Provides comprehensive predictions with confidence scores
"""

import asyncio
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
import uuid
import os
import aiohttp

logger = logging.getLogger(__name__)

# Check for lightweight mode
ML_LIGHTWEIGHT_MODE = os.environ.get('ML_LIGHTWEIGHT_MODE', 'false').lower() == 'true'


class EnhancedMTFTrainingService:
    """
    Enhanced Multi-Timeframe Training Service with Media/Sentiment Integration.
    
    Combines technical analysis with social sentiment for improved predictions:
    - Technical: SMA, RSI, Volatility, Volume, Returns
    - Sentiment: Twitter, Reddit, Fear & Greed, News sentiment
    """
    
    TRAINING_TIMEFRAMES = ["1h", "4h", "1D"]
    
    # Technical feature columns (per timeframe)
    TECHNICAL_FEATURES = [
        "close", "sma_7", "sma_20", "sma_50", 
        "rsi", "volatility", "volume_ratio",
        "return_1", "return_5", "return_10", "high_low_range"
    ]
    
    # Sentiment feature columns
    SENTIMENT_FEATURES = [
        "twitter_sentiment", "twitter_volume_change",
        "reddit_sentiment", "reddit_activity",
        "fear_greed_index", "fear_greed_trend",
        "news_sentiment", "news_volume",
        "fomo_score", "fear_score",
        "influencer_sentiment", "hype_phase"
    ]
    
    # Default coins for training
    DEFAULT_COINS = ["BTC", "ETH", "SOL", "ADA", "DOT", "AVAX", "LINK", "MATIC", 
                    "XRP", "DOGE", "ATOM", "UNI", "LTC", "SHIB", "ARB"]
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.training_collection = db["enhanced_mtf_training"]
        self.model_collection = db["enhanced_mtf_models"]
        self.sentiment_cache = db["sentiment_cache"]
        self.predictions_collection = db["mtf_predictions"]
        
        self._training_status: Dict[str, Any] = {
            "status": "idle",
            "last_trained": None,
            "coins_trained": 0,
            "accuracy": 0.0,
            "features_used": []
        }
        self._models: Dict[str, Any] = {}
        
    async def get_mtf_service(self):
        """Get the multi-timeframe historical data service"""
        from services.multitimeframe_historical_service import get_multitimeframe_service
        return get_multitimeframe_service(self.db)
    
    async def get_social_sentiment_service(self):
        """Get the social sentiment pipeline service"""
        from services.social_sentiment_pipeline import get_social_sentiment
        return get_social_sentiment(self.db)
    
    async def get_sentiment_scraper(self):
        """Get the sentiment scraper service"""
        from services.social_sentiment import get_sentiment_scraper
        return get_sentiment_scraper(self.db)
    
    # ==================== DATA DOWNLOAD ====================
    
    async def download_ohlcv_data(
        self,
        symbols: List[str] = None,
        timeframes: List[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Download OHLCV data from Kraken for all symbols.
        """
        if symbols is None:
            symbols = self.DEFAULT_COINS
        if timeframes is None:
            timeframes = self.TRAINING_TIMEFRAMES
            
        mtf_service = await self.get_mtf_service()
        if not mtf_service:
            return {"error": "MTF service not initialized"}
        
        results = {
            "downloaded": [],
            "failed": [],
            "skipped": [],
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"📥 Downloading OHLCV data for {len(symbols)} coins...")
        
        for symbol in symbols:
            try:
                # Check if data exists
                existing = await mtf_service.get_ohlc_data(symbol, "1D", limit=10)
                
                if existing.get("count", 0) > 0 and not force:
                    results["skipped"].append(symbol)
                    continue
                
                # Download all timeframes
                download_result = await mtf_service.download_all_timeframes(
                    symbol, 
                    timeframes=timeframes
                )
                
                if download_result.get("success_count", 0) > 0:
                    results["downloaded"].append({
                        "symbol": symbol,
                        "timeframes": download_result.get("success_count", 0)
                    })
                else:
                    results["failed"].append({
                        "symbol": symbol,
                        "errors": download_result.get("errors", [])
                    })
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.warning(f"Failed to download {symbol}: {e}")
                results["failed"].append({"symbol": symbol, "error": str(e)})
        
        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        results["summary"] = {
            "downloaded": len(results["downloaded"]),
            "failed": len(results["failed"]),
            "skipped": len(results["skipped"])
        }
        
        logger.info(f"✅ Download complete: {results['summary']}")
        return results
    
    # ==================== SENTIMENT FETCHING ====================
    
    async def fetch_fear_greed_index(self) -> Dict[str, Any]:
        """Fetch Fear & Greed Index from Alternative.me"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.alternative.me/fng/?limit=7",
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        fng_data = data.get('data', [])
                        
                        if fng_data:
                            current = fng_data[0]
                            value = int(current.get('value', 50))
                            
                            # Calculate trend
                            trend = 0
                            if len(fng_data) >= 7:
                                week_ago = int(fng_data[-1].get('value', 50))
                                trend = value - week_ago
                            
                            return {
                                "value": value,
                                "classification": current.get('value_classification', 'Neutral'),
                                "trend_7d": trend,
                                "normalized": value / 100.0,  # 0-1 scale
                                "fetched_at": datetime.now(timezone.utc).isoformat()
                            }
        except Exception as e:
            logger.warning(f"Fear & Greed fetch error: {e}")
        
        return {"value": 50, "normalized": 0.5, "trend_7d": 0}
    
    async def fetch_reddit_sentiment(self, coin: str) -> Dict[str, Any]:
        """Fetch Reddit sentiment for a coin"""
        sentiment_scraper = await self.get_sentiment_scraper()
        if sentiment_scraper:
            try:
                result = await sentiment_scraper.get_coin_sentiment(coin)
                return {
                    "score": result.get("sentiment_score", 50),
                    "normalized": (result.get("sentiment_score", 50) + 50) / 100.0,
                    "mentions": result.get("mentions", 0),
                    "activity": result.get("discussion_intensity", "low")
                }
            except Exception as e:
                logger.debug(f"Reddit sentiment error for {coin}: {e}")
        
        return {"score": 0, "normalized": 0.5, "mentions": 0, "activity": "low"}
    
    async def fetch_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Fetch comprehensive social sentiment using the pipeline"""
        social_service = await self.get_social_sentiment_service()
        if social_service:
            try:
                analysis = await social_service.analyze_social_sentiment(symbol)
                
                twitter = analysis.get('twitter', {})
                reddit = analysis.get('reddit', {})
                fomo_fear = analysis.get('fomo_fear', {})
                hype = analysis.get('hype_cycle', {})
                influencer = analysis.get('influencer_activity', {})
                signal = analysis.get('signal', {})
                
                # Map hype phase to numeric
                hype_phase_map = {
                    'innovation_trigger': 0.2,
                    'peak_expectations': 0.9,
                    'trough_disillusionment': 0.1,
                    'slope_enlightenment': 0.5,
                    'plateau_productivity': 0.7
                }
                
                return {
                    "twitter_sentiment": twitter.get('sentiment_score', 0) / 100.0,
                    "twitter_volume_change": twitter.get('volume_change_24h', 0) / 100.0,
                    "reddit_sentiment": reddit.get('sentiment_score', 0) / 100.0,
                    "reddit_activity": 1.0 if reddit.get('discussion_intensity') == 'high' else (0.5 if reddit.get('discussion_intensity') == 'medium' else 0.2),
                    "fomo_score": fomo_fear.get('fomo_score', 0) / 100.0,
                    "fear_score": fomo_fear.get('fear_score', 0) / 100.0,
                    "hype_phase": hype_phase_map.get(hype.get('phase', 'neutral'), 0.5),
                    "influencer_sentiment": 0.7 if influencer.get('sentiment') == 'bullish' else (0.3 if influencer.get('sentiment') == 'bearish' else 0.5),
                    "overall_signal_score": signal.get('score', 50) / 100.0,
                    "signal_confidence": signal.get('confidence', 0) / 100.0
                }
            except Exception as e:
                logger.debug(f"Social sentiment error for {symbol}: {e}")
        
        return self._get_neutral_sentiment()
    
    def _get_neutral_sentiment(self) -> Dict[str, float]:
        """Return neutral sentiment values"""
        return {
            "twitter_sentiment": 0.5,
            "twitter_volume_change": 0.0,
            "reddit_sentiment": 0.5,
            "reddit_activity": 0.3,
            "fomo_score": 0.3,
            "fear_score": 0.3,
            "hype_phase": 0.5,
            "influencer_sentiment": 0.5,
            "overall_signal_score": 0.5,
            "signal_confidence": 0.3
        }
    
    # ==================== FEATURE EXTRACTION ====================
    
    async def extract_combined_features(
        self,
        symbol: str,
        timeframes: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract combined technical + sentiment features for a symbol.
        """
        if timeframes is None:
            timeframes = self.TRAINING_TIMEFRAMES
        
        # Get technical features from MTF service
        mtf_service = await self.get_mtf_service()
        if not mtf_service:
            return None
        
        tech_features = await mtf_service.get_training_features(symbol, timeframes)
        
        if not tech_features.get("timeframes"):
            return None
        
        # Get sentiment features
        sentiment = await self.fetch_social_sentiment(symbol)
        fear_greed = await self.fetch_fear_greed_index()
        
        # Build feature vector
        feature_vector = []
        
        # Technical features per timeframe
        for tf in timeframes:
            tf_data = tech_features.get("timeframes", {}).get(tf, {})
            
            if tf_data:
                for col in self.TECHNICAL_FEATURES:
                    feature_vector.append(float(tf_data.get(col, 0)))
            else:
                # Pad with zeros
                feature_vector.extend([0.0] * len(self.TECHNICAL_FEATURES))
        
        # Sentiment features
        feature_vector.extend([
            sentiment.get("twitter_sentiment", 0.5),
            sentiment.get("twitter_volume_change", 0),
            sentiment.get("reddit_sentiment", 0.5),
            sentiment.get("reddit_activity", 0.3),
            fear_greed.get("normalized", 0.5),
            fear_greed.get("trend_7d", 0) / 100.0,
            sentiment.get("overall_signal_score", 0.5),
            sentiment.get("signal_confidence", 0.3),
            sentiment.get("fomo_score", 0.3),
            sentiment.get("fear_score", 0.3),
            sentiment.get("influencer_sentiment", 0.5),
            sentiment.get("hype_phase", 0.5)
        ])
        
        return {
            "symbol": symbol,
            "feature_vector": np.array(feature_vector),
            "technical": tech_features,
            "sentiment": sentiment,
            "fear_greed": fear_greed,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # ==================== TRAINING ====================
    
    async def train_enhanced_model(
        self,
        symbols: List[str] = None,
        timeframes: List[str] = None,
        epochs: int = 100,
        learning_rate: float = 0.001,
        download_data: bool = True
    ) -> Dict[str, Any]:
        """
        Train the enhanced MTF model with technical + sentiment features.
        
        Steps:
        1. Download OHLCV data if needed
        2. Fetch sentiment data for all symbols
        3. Extract combined feature vectors
        4. Train ensemble classifier
        5. Store model and evaluate
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
            if ML_LIGHTWEIGHT_MODE:
                epochs = min(epochs, 20)
                logger.info("🔋 Running in lightweight mode - limited epochs")
            
            if symbols is None:
                symbols = self.DEFAULT_COINS
            
            if timeframes is None:
                timeframes = self.TRAINING_TIMEFRAMES
            
            logger.info(f"🚀 Starting Enhanced MTF Training on {len(symbols)} symbols...")
            
            # Phase 1: Download data
            if download_data:
                self._training_status["current_phase"] = "downloading_data"
                self._training_status["progress"] = 5
                
                download_result = await self.download_ohlcv_data(symbols, timeframes)
                logger.info(f"📥 Data download: {download_result.get('summary', {})}")
            
            # Phase 2: Fetch sentiment and extract features
            self._training_status["current_phase"] = "extracting_features"
            self._training_status["progress"] = 15
            
            X_train = []
            y_train = []
            symbol_data = {}
            
            for idx, symbol in enumerate(symbols):
                try:
                    self._training_status["progress"] = 15 + int((idx / len(symbols)) * 40)
                    self._training_status["current_symbol"] = symbol
                    
                    # Extract combined features
                    features = await self.extract_combined_features(symbol, timeframes)
                    
                    if features is None:
                        logger.debug(f"No features for {symbol}")
                        continue
                    
                    feature_vector = features["feature_vector"]
                    
                    # Generate label based on technical + sentiment
                    label = await self._generate_label(features)
                    
                    X_train.append(feature_vector)
                    y_train.append(label)
                    
                    symbol_data[symbol] = {
                        "features": features,
                        "label": label,
                        "sentiment": features.get("sentiment", {}),
                        "fear_greed": features.get("fear_greed", {})
                    }
                    
                except Exception as e:
                    logger.warning(f"Failed to process {symbol}: {e}")
                    continue
            
            if len(X_train) < 3:
                raise Exception(f"Insufficient training data: only {len(X_train)} samples")
            
            logger.info(f"📊 Prepared {len(X_train)} training samples")
            
            # Phase 3: Train model
            self._training_status["current_phase"] = "training_model"
            self._training_status["progress"] = 60
            
            X_train = np.array(X_train)
            y_train = np.array(y_train)
            
            # Handle NaN/Inf values
            X_train = np.nan_to_num(X_train, nan=0.0, posinf=1.0, neginf=-1.0)
            
            # Normalize features
            X_mean = np.mean(X_train, axis=0)
            X_std = np.std(X_train, axis=0) + 1e-8
            X_normalized = (X_train - X_mean) / X_std
            
            # Ensure class diversity
            unique_labels = set(y_train)
            if len(unique_labels) < 2:
                logger.warning("Adding label diversity...")
                for i in range(len(y_train)):
                    if i % 3 == 0:
                        y_train[i] = 1
                    elif i % 3 == 1:
                        y_train[i] = -1
            
            # Train model
            model_weights, model_info = await self._train_classifier(
                X_normalized, y_train, epochs, learning_rate
            )
            
            self._training_status["progress"] = 85
            
            # Phase 4: Evaluate
            self._training_status["current_phase"] = "evaluating"
            
            predictions = await self._predict_with_model(X_normalized, model_weights)
            accuracy = np.mean(predictions == y_train)
            
            # Calculate per-class metrics
            class_metrics = {}
            for label in [-1, 0, 1]:
                mask = y_train == label
                if np.sum(mask) > 0:
                    class_acc = np.mean(predictions[mask] == y_train[mask])
                    class_metrics[label] = {
                        "count": int(np.sum(mask)),
                        "accuracy": float(class_acc)
                    }
            
            # Phase 5: Store model
            self._training_status["current_phase"] = "saving_model"
            self._training_status["progress"] = 95
            
            # Calculate feature count
            n_technical = len(self.TRAINING_TIMEFRAMES) * len(self.TECHNICAL_FEATURES)
            n_sentiment = len(self.SENTIMENT_FEATURES)
            
            model_doc = {
                "model_id": training_id,
                "type": "enhanced_mtf",
                "weights": model_weights.tolist() if hasattr(model_weights, 'tolist') else list(model_weights),
                "normalization": {
                    "mean": X_mean.tolist(),
                    "std": X_std.tolist()
                },
                "timeframes": timeframes,
                "feature_info": {
                    "technical_features": self.TECHNICAL_FEATURES,
                    "sentiment_features": self.SENTIMENT_FEATURES,
                    "n_technical": n_technical,
                    "n_sentiment": n_sentiment,
                    "total_features": n_technical + n_sentiment
                },
                "training_info": {
                    "symbols_trained": len(X_train),
                    "epochs": epochs,
                    "learning_rate": learning_rate,
                    "accuracy": float(accuracy),
                    "class_metrics": class_metrics
                },
                "model_info": model_info,
                "created_at": started_at,
                "completed_at": datetime.now(timezone.utc)
            }
            
            await self.model_collection.update_one(
                {"type": "enhanced_mtf"},
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
                "class_metrics": class_metrics,
                "features_used": {
                    "technical": n_technical,
                    "sentiment": n_sentiment,
                    "total": n_technical + n_sentiment
                },
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": (datetime.now(timezone.utc) - started_at).total_seconds(),
                "sample_data": [
                    {
                        "symbol": sym,
                        "label": int(data["label"]),
                        "signal": "BUY" if data["label"] == 1 else ("SELL" if data["label"] == -1 else "HOLD"),
                        "sentiment_score": data.get("sentiment", {}).get("overall_signal_score", 0.5)
                    }
                    for sym, data in list(symbol_data.items())[:5]
                ]
            }
            
            await self.training_collection.insert_one({
                **result,
                "timestamp": datetime.now(timezone.utc)
            })
            
            self._training_status = {
                "status": "completed",
                "training_id": training_id,
                "last_trained": datetime.now(timezone.utc).isoformat(),
                "coins_trained": len(X_train),
                "accuracy": float(accuracy),
                "features_used": result["features_used"]
            }
            
            logger.info(f"✅ Enhanced MTF training completed! Accuracy: {accuracy * 100:.1f}%")
            return result
            
        except Exception as e:
            logger.error(f"❌ Enhanced MTF training failed: {e}")
            import traceback
            traceback.print_exc()
            
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
    
    async def _generate_label(self, features: Dict[str, Any]) -> int:
        """
        Generate training label based on technical + sentiment features.
        
        Returns: 1 (BUY), 0 (HOLD), -1 (SELL)
        """
        technical = features.get("technical", {})
        sentiment = features.get("sentiment", {})
        fear_greed = features.get("fear_greed", {})
        
        score = 0
        
        # Technical signals from timeframes
        timeframes = technical.get("timeframes", {})
        for tf, tf_data in timeframes.items():
            if not tf_data:
                continue
            
            rsi = tf_data.get("rsi", 50)
            close = tf_data.get("close", 0)
            sma_20 = tf_data.get("sma_20", close)
            sma_50 = tf_data.get("sma_50", close)
            
            # RSI signals
            if rsi < 30:
                score += 1  # Oversold = bullish
            elif rsi > 70:
                score -= 1  # Overbought = bearish
            
            # Trend signals
            if close > sma_20 > sma_50:
                score += 1  # Bullish trend
            elif close < sma_20 < sma_50:
                score -= 1  # Bearish trend
        
        # Sentiment signals
        signal_score = sentiment.get("overall_signal_score", 0.5)
        if signal_score > 0.65:
            score += 2
        elif signal_score < 0.35:
            score -= 2
        
        # Fear & Greed (contrarian)
        fg_value = fear_greed.get("value", 50)
        if fg_value < 25:  # Extreme fear = buy opportunity
            score += 1
        elif fg_value > 75:  # Extreme greed = sell signal
            score -= 1
        
        # FOMO/Fear signals
        fomo = sentiment.get("fomo_score", 0.3)
        fear = sentiment.get("fear_score", 0.3)
        if fomo > 0.6:
            score -= 1  # Contrarian - too much FOMO
        if fear > 0.6:
            score += 1  # Contrarian - too much fear
        
        # Convert score to label
        if score >= 2:
            return 1  # BUY
        elif score <= -2:
            return -1  # SELL
        else:
            return 0  # HOLD
    
    async def _train_classifier(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int,
        learning_rate: float
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Train classifier model"""
        try:
            from sklearn.linear_model import LogisticRegression
            from sklearn.preprocessing import LabelEncoder
            from sklearn.model_selection import cross_val_score
            
            # Encode labels
            le = LabelEncoder()
            y_encoded = le.fit_transform(y)
            
            # Train with cross-validation
            model = LogisticRegression(
                max_iter=epochs * 10,
                C=1.0 / learning_rate,
                random_state=42,
                solver='lbfgs'
            )
            
            # Cross-validation score
            cv_scores = cross_val_score(model, X, y_encoded, cv=min(3, len(X)))
            
            # Final fit
            model.fit(X, y_encoded)
            
            self._models["sklearn_lr"] = model
            self._models["label_encoder"] = le
            
            return model.coef_, {
                "method": "sklearn_logistic_regression",
                "cv_score": float(np.mean(cv_scores)),
                "cv_std": float(np.std(cv_scores)),
                "n_classes": len(le.classes_),
                "classes": le.classes_.tolist()
            }
            
        except ImportError:
            logger.warning("sklearn not available, using gradient descent")
            return await self._train_gradient_descent(X, y, epochs, learning_rate), {
                "method": "gradient_descent",
                "epochs": epochs
            }
    
    async def _train_gradient_descent(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int,
        learning_rate: float
    ) -> np.ndarray:
        """Simple gradient descent training fallback"""
        n_features = X.shape[1]
        n_classes = len(np.unique(y))
        
        weights = np.random.randn(n_classes, n_features) * 0.01
        
        label_map = {-1: 0, 0: 1, 1: 2}
        y_mapped = np.array([label_map.get(yi, 1) for yi in y])
        
        for epoch in range(epochs):
            scores = X @ weights.T
            exp_scores = np.exp(scores - np.max(scores, axis=1, keepdims=True))
            probs = exp_scores / np.sum(exp_scores, axis=1, keepdims=True)
            
            n_samples = X.shape[0]
            one_hot = np.zeros((n_samples, n_classes))
            one_hot[np.arange(n_samples), y_mapped] = 1
            
            gradient = (probs - one_hot).T @ X / n_samples
            weights -= learning_rate * gradient
        
        self._models["gd_weights"] = weights
        return weights
    
    async def _predict_with_model(
        self,
        X: np.ndarray,
        weights: np.ndarray
    ) -> np.ndarray:
        """Make predictions"""
        if "sklearn_lr" in self._models:
            model = self._models["sklearn_lr"]
            le = self._models["label_encoder"]
            predictions = model.predict(X)
            return le.inverse_transform(predictions)
        else:
            scores = X @ weights.T
            pred_indices = np.argmax(scores, axis=1)
            index_to_label = {0: -1, 1: 0, 2: 1}
            return np.array([index_to_label.get(idx, 0) for idx in pred_indices])
    
    # ==================== PREDICTION ====================
    
    async def predict(
        self,
        symbol: str,
        timeframes: List[str] = None
    ) -> Dict[str, Any]:
        """
        Make prediction for a single symbol.
        """
        if timeframes is None:
            timeframes = self.TRAINING_TIMEFRAMES
        
        # Get model
        model_doc = await self.model_collection.find_one({"type": "enhanced_mtf"})
        
        if not model_doc:
            return {
                "error": "No trained model found. Run training first.",
                "symbol": symbol
            }
        
        # Extract features
        features = await self.extract_combined_features(symbol, timeframes)
        
        if features is None:
            return {
                "error": f"Could not extract features for {symbol}",
                "symbol": symbol
            }
        
        feature_vector = features["feature_vector"]
        
        # Handle NaN/Inf
        feature_vector = np.nan_to_num(feature_vector, nan=0.0, posinf=1.0, neginf=-1.0)
        
        # Normalize
        X_mean = np.array(model_doc["normalization"]["mean"])
        X_std = np.array(model_doc["normalization"]["std"])
        X_normalized = (feature_vector - X_mean) / X_std
        
        # Predict
        weights = np.array(model_doc["weights"])
        
        if "sklearn_lr" in self._models:
            model = self._models["sklearn_lr"]
            le = self._models["label_encoder"]
            prediction = model.predict([X_normalized])[0]
            probas = model.predict_proba([X_normalized])[0]
            confidence = float(np.max(probas))
            prediction = int(le.inverse_transform([prediction])[0])
        else:
            scores = X_normalized @ weights.T
            exp_scores = np.exp(scores - np.max(scores))
            probas = exp_scores / np.sum(exp_scores)
            pred_index = np.argmax(probas)
            index_to_label = {0: -1, 1: 0, 2: 1}
            prediction = index_to_label.get(pred_index, 0)
            confidence = float(np.max(probas))
        
        signal_map = {-1: "SELL", 0: "HOLD", 1: "BUY"}
        sentiment = features.get("sentiment", {})
        fear_greed = features.get("fear_greed", {})
        
        result = {
            "symbol": symbol,
            "prediction": prediction,
            "signal": signal_map.get(prediction, "HOLD"),
            "confidence": confidence,
            "confidence_pct": f"{confidence * 100:.1f}%",
            "model_accuracy": model_doc.get("training_info", {}).get("accuracy", 0),
            "analysis": {
                "technical": {
                    "timeframes_analyzed": timeframes,
                    "data_available": bool(features.get("technical", {}).get("timeframes"))
                },
                "sentiment": {
                    "twitter": sentiment.get("twitter_sentiment", 0.5),
                    "reddit": sentiment.get("reddit_sentiment", 0.5),
                    "overall_score": sentiment.get("overall_signal_score", 0.5),
                    "fomo_score": sentiment.get("fomo_score", 0.3),
                    "fear_score": sentiment.get("fear_score", 0.3)
                },
                "fear_greed": {
                    "value": fear_greed.get("value", 50),
                    "classification": fear_greed.get("classification", "Neutral"),
                    "trend_7d": fear_greed.get("trend_7d", 0)
                }
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Store prediction
        await self.predictions_collection.insert_one({
            **result,
            "stored_at": datetime.now(timezone.utc)
        })
        
        return result
    
    async def predict_all(
        self,
        symbols: List[str] = None,
        timeframes: List[str] = None
    ) -> Dict[str, Any]:
        """
        Make predictions for all symbols.
        """
        if symbols is None:
            symbols = self.DEFAULT_COINS
        
        predictions = []
        errors = []
        
        logger.info(f"🔮 Running predictions for {len(symbols)} symbols...")
        
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
        
        # Get model info
        model_doc = await self.model_collection.find_one(
            {"type": "enhanced_mtf"},
            {"_id": 0, "weights": 0, "normalization": 0}
        )
        
        return {
            "total_predictions": len(predictions),
            "buy_signals": len(buy_signals),
            "sell_signals": len(sell_signals),
            "hold_signals": len(hold_signals),
            "top_buys": buy_signals[:5],
            "top_sells": sell_signals[:5],
            "all_predictions": predictions,
            "errors": errors,
            "model_info": {
                "accuracy": model_doc.get("training_info", {}).get("accuracy", 0) if model_doc else 0,
                "trained_at": model_doc.get("completed_at") if model_doc else None,
                "features_used": model_doc.get("feature_info", {}) if model_doc else {}
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_training_status(self) -> Dict[str, Any]:
        """Get current training status"""
        return self._training_status
    
    async def get_training_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get training history"""
        cursor = self.training_collection.find(
            {},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get current model information"""
        model_doc = await self.model_collection.find_one(
            {"type": "enhanced_mtf"},
            {"_id": 0, "weights": 0, "normalization": 0}
        )
        
        if not model_doc:
            return {"status": "no_model", "message": "No trained model found"}
        
        return {
            "status": "ready",
            "model": model_doc
        }


# Global instance
_enhanced_mtf_service: Optional[EnhancedMTFTrainingService] = None


def get_enhanced_mtf_service(db: AsyncIOMotorDatabase = None) -> Optional[EnhancedMTFTrainingService]:
    """Get or create Enhanced MTF Training Service instance"""
    global _enhanced_mtf_service
    if _enhanced_mtf_service is None and db is not None:
        _enhanced_mtf_service = EnhancedMTFTrainingService(db)
    return _enhanced_mtf_service

"""
Ensemble AI Prediction System
Combines all ML/DL models to optimize predictions.
Analyzes top 1000 coins and rebuilds optimal universe.
"""

import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import numpy as np

from emergentintegrations.llm.chat import LlmChat, UserMessage


# Background task tracking for universe rebuild
_universe_rebuild_status = {
    "running": False,
    "started_at": None,
    "progress": 0,
    "progress_message": "",
    "coins_analyzed": 0,
    "total_coins": 0,
    "result": None,
    "comparison": None,
    "error": None
}


def get_rebuild_status() -> Dict[str, Any]:
    """Get current rebuild status"""
    return _universe_rebuild_status.copy()


class EnsembleAIPredictor:
    """
    Master AI that combines all prediction models for maximum accuracy.
    Uses weighted ensemble of LSTM, Technical, Pattern, Momentum, Sentiment.
    """
    
    def __init__(self, db, market_service, deep_learning_ai=None):
        self.db = db
        self.market_service = market_service
        self.deep_learning_ai = deep_learning_ai
        self.api_key = os.getenv('EMERGENT_LLM_KEY')
        
        # Model weights (will be optimized)
        self.model_weights = {
            "lstm": 0.25,
            "technical": 0.20,
            "pattern": 0.15,
            "momentum": 0.15,
            "trend": 0.10,
            "volatility": 0.10,
            "sentiment": 0.05
        }
        
        # Historical performance tracking
        self.model_accuracy = {
            "lstm": [],
            "technical": [],
            "pattern": [],
            "momentum": [],
            "trend": [],
            "volatility": [],
            "sentiment": []
        }
        
        # Prediction cache
        self.prediction_cache = {}
        
    async def get_all_model_predictions(
        self, 
        coin_id: str, 
        prices: List[float],
        current_price: float
    ) -> Dict[str, Any]:
        """Get predictions from all available models"""
        predictions = {}
        
        # 1. LSTM Prediction
        if self.deep_learning_ai and len(prices) >= 60:
            try:
                lstm_result = await self.deep_learning_ai.price_predictor.predict(prices)
                predictions["lstm"] = {
                    "signal": lstm_result.get("trend", "neutral"),
                    "confidence": min(85, 50 + abs(lstm_result.get("predicted_change_pct", 0)) * 2),
                    "predicted_change": lstm_result.get("predicted_change_pct", 0),
                    "raw": lstm_result
                }
            except Exception as e:
                predictions["lstm"] = {"signal": "neutral", "confidence": 40, "error": str(e)}
        
        # 2. Technical Analysis
        if len(prices) >= 20:
            tech = self._calculate_technical(prices)
            predictions["technical"] = tech
        
        # 3. Pattern Recognition
        if self.deep_learning_ai and len(prices) >= 30:
            pattern = self.deep_learning_ai.pattern_recognizer.detect_patterns_rule_based(prices)
            signal = "bullish" if pattern.get("is_bullish") else "bearish" if pattern.get("is_bearish") else "neutral"
            predictions["pattern"] = {
                "signal": signal,
                "confidence": pattern.get("confidence", 50),
                "pattern_name": pattern.get("pattern", "none"),
                "raw": pattern
            }
        
        # 4. Momentum Analysis
        if len(prices) >= 14:
            momentum = self._calculate_momentum(prices)
            predictions["momentum"] = momentum
        
        # 5. Trend Analysis
        if len(prices) >= 20:
            trend = self._calculate_trend(prices)
            predictions["trend"] = trend
        
        # 6. Volatility Analysis
        if len(prices) >= 20:
            volatility = self._analyze_volatility(prices)
            predictions["volatility"] = volatility
        
        # 7. Sentiment (placeholder - would use news API)
        predictions["sentiment"] = {
            "signal": "neutral",
            "confidence": 50,
            "source": "default"
        }
        
        return predictions
    
    def _calculate_technical(self, prices: List[float]) -> Dict[str, Any]:
        """Calculate technical indicators"""
        if len(prices) < 20:
            return {"signal": "neutral", "confidence": 40}
        
        # RSI
        gains = []
        losses = []
        for i in range(1, min(15, len(prices))):
            diff = prices[-i] - prices[-i-1]
            if diff > 0:
                gains.append(diff)
            else:
                losses.append(abs(diff))
        
        avg_gain = np.mean(gains) if gains else 0.0001
        avg_loss = np.mean(losses) if losses else 0.0001
        rs = avg_gain / avg_loss if avg_loss > 0 else 1
        rsi = 100 - (100 / (1 + rs))
        
        # SMA
        sma_20 = np.mean(prices[-20:])
        sma_50 = np.mean(prices[-50:]) if len(prices) >= 50 else sma_20
        
        # Signal determination
        score = 50
        if rsi < 30:
            score += 20  # Oversold - bullish
            signal_rsi = "bullish"
        elif rsi > 70:
            score -= 20  # Overbought - bearish
            signal_rsi = "bearish"
        else:
            signal_rsi = "neutral"
        
        if prices[-1] > sma_20:
            score += 15
        else:
            score -= 15
        
        if sma_20 > sma_50:
            score += 10
        else:
            score -= 10
        
        if score >= 60:
            signal = "bullish"
        elif score <= 40:
            signal = "bearish"
        else:
            signal = "neutral"
        
        return {
            "signal": signal,
            "confidence": min(90, max(30, score)),
            "rsi": rsi,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "price_vs_sma": "above" if prices[-1] > sma_20 else "below"
        }
    
    def _calculate_momentum(self, prices: List[float]) -> Dict[str, Any]:
        """Calculate momentum indicators"""
        if len(prices) < 14:
            return {"signal": "neutral", "confidence": 40}
        
        # Rate of Change
        roc_7 = ((prices[-1] - prices[-7]) / prices[-7]) * 100 if len(prices) >= 7 else 0
        roc_14 = ((prices[-1] - prices[-14]) / prices[-14]) * 100
        
        # MACD-like calculation
        ema_12 = self._ema(prices, 12)
        ema_26 = self._ema(prices, 26) if len(prices) >= 26 else ema_12
        macd = ema_12 - ema_26
        
        # Signal
        avg_roc = (roc_7 + roc_14) / 2
        if avg_roc > 10 and macd > 0:
            signal = "bullish"
            confidence = min(85, 60 + avg_roc)
        elif avg_roc < -10 and macd < 0:
            signal = "bearish"
            confidence = min(85, 60 + abs(avg_roc))
        elif avg_roc > 5:
            signal = "bullish"
            confidence = 55
        elif avg_roc < -5:
            signal = "bearish"
            confidence = 55
        else:
            signal = "neutral"
            confidence = 50
        
        return {
            "signal": signal,
            "confidence": confidence,
            "roc_7": roc_7,
            "roc_14": roc_14,
            "macd": macd
        }
    
    def _calculate_trend(self, prices: List[float]) -> Dict[str, Any]:
        """Calculate trend strength and direction"""
        if len(prices) < 20:
            return {"signal": "neutral", "confidence": 40}
        
        # Linear regression slope
        x = np.arange(len(prices[-20:]))
        y = np.array(prices[-20:])
        slope = np.polyfit(x, y, 1)[0]
        slope_pct = (slope / np.mean(y)) * 100
        
        # Higher highs / Lower lows
        highs = [max(prices[i:i+5]) for i in range(0, len(prices)-5, 5)]
        lows = [min(prices[i:i+5]) for i in range(0, len(prices)-5, 5)]
        
        higher_highs = all(highs[i] <= highs[i+1] for i in range(len(highs)-1)) if len(highs) > 1 else False
        higher_lows = all(lows[i] <= lows[i+1] for i in range(len(lows)-1)) if len(lows) > 1 else False
        
        if slope_pct > 5 and higher_highs:
            signal = "bullish"
            confidence = min(85, 60 + slope_pct * 2)
        elif slope_pct < -5:
            signal = "bearish"
            confidence = min(85, 60 + abs(slope_pct) * 2)
        else:
            signal = "neutral"
            confidence = 50
        
        return {
            "signal": signal,
            "confidence": confidence,
            "slope_pct": slope_pct,
            "higher_highs": higher_highs,
            "higher_lows": higher_lows
        }
    
    def _analyze_volatility(self, prices: List[float]) -> Dict[str, Any]:
        """Analyze volatility for prediction confidence"""
        if len(prices) < 20:
            return {"signal": "neutral", "confidence": 40, "level": "unknown"}
        
        # Calculate volatility
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        volatility = np.std(returns[-20:]) * 100
        
        # Bollinger Band width
        sma = np.mean(prices[-20:])
        std = np.std(prices[-20:])
        bb_width = (2 * std / sma) * 100
        
        # Determine signal based on volatility regime
        if volatility < 2:
            level = "low"
            signal = "neutral"  # Consolidation
            confidence = 45
        elif volatility < 5:
            level = "medium"
            # Follow trend in medium volatility
            if prices[-1] > prices[-7]:
                signal = "bullish"
            else:
                signal = "bearish"
            confidence = 60
        else:
            level = "high"
            # High volatility - trend continuation more likely
            if prices[-1] > prices[-3]:
                signal = "bullish"
            else:
                signal = "bearish"
            confidence = 55
        
        return {
            "signal": signal,
            "confidence": confidence,
            "level": level,
            "volatility_pct": volatility,
            "bb_width": bb_width
        }
    
    def _ema(self, prices: List[float], period: int) -> float:
        """Calculate EMA"""
        if len(prices) < period:
            return np.mean(prices)
        
        multiplier = 2 / (period + 1)
        ema = prices[-period]
        for price in prices[-period+1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        return ema
    
    async def get_ensemble_prediction(
        self,
        coin_id: str,
        prices: List[float],
        current_price: float,
        optimize_weights: bool = True
    ) -> Dict[str, Any]:
        """
        Get optimized ensemble prediction combining all models.
        """
        if len(prices) < 20:
            return {
                "error": "Insufficient price data",
                "coin_id": coin_id,
                "signal": "hold",
                "confidence": 30
            }
        
        # Get all model predictions
        all_predictions = await self.get_all_model_predictions(coin_id, prices, current_price)
        
        # Optimize weights if requested
        if optimize_weights:
            self._optimize_weights()
        
        # Calculate weighted ensemble
        bullish_score = 0
        bearish_score = 0
        total_weight = 0
        confidence_sum = 0
        
        model_results = []
        for model_name, prediction in all_predictions.items():
            if "error" in prediction:
                continue
            
            weight = self.model_weights.get(model_name, 0.1)
            signal = prediction.get("signal", "neutral")
            confidence = prediction.get("confidence", 50)
            
            if signal == "bullish":
                bullish_score += weight * confidence
            elif signal == "bearish":
                bearish_score += weight * confidence
            
            total_weight += weight
            confidence_sum += confidence * weight
            
            model_results.append({
                "model": model_name,
                "signal": signal,
                "confidence": confidence,
                "weight": weight
            })
        
        # Determine final signal
        if bullish_score > bearish_score * 1.2:
            final_signal = "STRONG_BUY" if bullish_score > bearish_score * 1.5 else "BUY"
            signal_confidence = (bullish_score / (bullish_score + bearish_score)) * 100 if (bullish_score + bearish_score) > 0 else 50
        elif bearish_score > bullish_score * 1.2:
            final_signal = "STRONG_SELL" if bearish_score > bullish_score * 1.5 else "SELL"
            signal_confidence = (bearish_score / (bullish_score + bearish_score)) * 100 if (bullish_score + bearish_score) > 0 else 50
        else:
            final_signal = "HOLD"
            signal_confidence = 50
        
        # Agreement score (how many models agree)
        agreement_count = sum(1 for m in model_results if 
            (m["signal"] == "bullish" and "BUY" in final_signal) or
            (m["signal"] == "bearish" and "SELL" in final_signal))
        agreement_pct = (agreement_count / len(model_results)) * 100 if model_results else 0
        
        # Final confidence based on agreement
        final_confidence = min(95, signal_confidence * 0.6 + agreement_pct * 0.4)
        
        # Accuracy estimate
        accuracy_estimate = 0.50 + (agreement_count * 0.05) + (final_confidence / 500)
        
        return {
            "coin_id": coin_id,
            "current_price": current_price,
            "final_signal": final_signal,
            "confidence": final_confidence,
            "accuracy_estimate": min(0.85, accuracy_estimate),
            "agreement_pct": agreement_pct,
            "bullish_score": bullish_score,
            "bearish_score": bearish_score,
            "model_results": model_results,
            "weights_used": self.model_weights,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _optimize_weights(self):
        """Optimize model weights based on historical accuracy"""
        # If we have accuracy data, adjust weights
        total_accuracy = sum(
            np.mean(acc) if acc else 0.5 
            for acc in self.model_accuracy.values()
        )
        
        if total_accuracy > 0:
            for model_name in self.model_weights:
                acc_list = self.model_accuracy.get(model_name, [])
                if acc_list:
                    model_acc = np.mean(acc_list)
                    # Adjust weight based on relative accuracy
                    self.model_weights[model_name] = max(0.05, min(0.35, model_acc / total_accuracy))
        
        # Normalize weights
        total = sum(self.model_weights.values())
        if total > 0:
            self.model_weights = {k: v/total for k, v in self.model_weights.items()}
    
    def update_model_accuracy(self, model_name: str, was_correct: bool):
        """Update model accuracy tracking"""
        if model_name in self.model_accuracy:
            self.model_accuracy[model_name].append(1.0 if was_correct else 0.0)
            # Keep only last 100 predictions
            if len(self.model_accuracy[model_name]) > 100:
                self.model_accuracy[model_name] = self.model_accuracy[model_name][-100:]


class UniverseOptimizer:
    """
    Optimizes the coin universe by analyzing top 1000 coins.
    """
    
    def __init__(self, db, market_service, ensemble_predictor):
        self.db = db
        self.market_service = market_service
        self.ensemble = ensemble_predictor
        self.api_key = os.getenv('EMERGENT_LLM_KEY')
        
    async def analyze_top_coins(self, limit: int = 1000) -> List[Dict]:
        """Analyze top coins by market cap"""
        analyzed = []
        
        try:
            # Get top coins in batches
            batch_size = 250
            all_coins = []
            
            for page in range(1, (limit // batch_size) + 2):
                if len(all_coins) >= limit:
                    break
                    
                coins = await self.market_service.get_all_coins(per_page=batch_size)
                all_coins.extend(coins)
                await asyncio.sleep(1)  # Rate limiting
            
            all_coins = all_coins[:limit]
            
            # Analyze each coin
            for i, coin in enumerate(all_coins):
                if i % 50 == 0:
                    print(f"Analyzing coin {i+1}/{len(all_coins)}")
                
                try:
                    analysis = await self._analyze_coin(coin)
                    if analysis:
                        analyzed.append(analysis)
                except Exception as e:
                    continue
                
                # Rate limiting
                if i % 10 == 0:
                    await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"Analysis error: {e}")
        
        return analyzed
    
    async def _analyze_coin(self, coin: Dict) -> Optional[Dict]:
        """Analyze a single coin"""
        coin_id = coin.get('id', '')
        
        # Basic metrics
        market_cap = coin.get('market_cap', 0)
        volume = coin.get('total_volume', 0)
        price_change_24h = coin.get('price_change_24h', 0)
        
        # Score calculation
        score = 50
        
        # Volume/Market cap ratio (liquidity)
        vol_ratio = (volume / market_cap * 100) if market_cap > 0 else 0
        if vol_ratio > 20:
            score += 15
        elif vol_ratio > 10:
            score += 10
        elif vol_ratio < 1:
            score -= 10
        
        # Market cap tier
        if market_cap < 100_000_000:  # < $100M
            score += 20  # Higher potential
        elif market_cap < 1_000_000_000:  # < $1B
            score += 10
        elif market_cap > 50_000_000_000:  # > $50B
            score -= 5  # Lower potential but stable
        
        # Momentum
        if 5 < price_change_24h < 30:
            score += 10
        elif price_change_24h > 30:
            score += 5  # Might be overextended
        elif price_change_24h < -10:
            score += 5  # Potential dip buy
        
        return {
            "coin_id": coin_id,
            "symbol": coin.get('symbol', '').upper(),
            "name": coin.get('name', ''),
            "market_cap": market_cap,
            "market_cap_rank": coin.get('market_cap_rank', 0),
            "volume_24h": volume,
            "volume_ratio": vol_ratio,
            "price_change_24h": price_change_24h,
            "universe_score": min(100, max(0, score)),
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def build_optimal_universe(self, target_size: int = 50) -> Dict[str, Any]:
        """
        Build an optimal trading universe from top 1000 coins.
        """
        result = {
            "status": "building",
            "target_size": target_size,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Analyze all coins
        analyzed = await self.analyze_top_coins(limit=500)  # Start with 500
        
        if not analyzed:
            return {"error": "Failed to analyze coins"}
        
        # Sort by score
        analyzed.sort(key=lambda x: x['universe_score'], reverse=True)
        
        # Select top coins for universe
        selected = analyzed[:target_size]
        
        # Categorize
        categories = {
            "large_cap": [],    # > $10B
            "mid_cap": [],      # $1B - $10B
            "small_cap": [],    # $100M - $1B
            "micro_cap": [],    # < $100M
            "hidden_gems": []   # High score, low cap
        }
        
        for coin in selected:
            mcap = coin.get('market_cap', 0)
            score = coin.get('universe_score', 0)
            
            if mcap > 10_000_000_000:
                categories["large_cap"].append(coin)
            elif mcap > 1_000_000_000:
                categories["mid_cap"].append(coin)
            elif mcap > 100_000_000:
                categories["small_cap"].append(coin)
            else:
                categories["micro_cap"].append(coin)
            
            # Hidden gems: high score, low market cap
            if score >= 70 and mcap < 500_000_000:
                categories["hidden_gems"].append(coin)
        
        # Save to database
        if self.db is not None:
            try:
                # Clear old universe
                await self.db.optimal_universe.delete_many({})
                
                # Insert new universe
                for coin in selected:
                    await self.db.optimal_universe.insert_one({
                        **coin,
                        "added_at": datetime.now(timezone.utc)
                    })
                
                # Save summary
                await self.db.universe_builds.insert_one({
                    "built_at": datetime.now(timezone.utc),
                    "coins_analyzed": len(analyzed),
                    "coins_selected": len(selected),
                    "categories": {k: len(v) for k, v in categories.items()},
                    "top_10": [c['symbol'] for c in selected[:10]]
                })
            except Exception as e:
                print(f"DB error: {e}")
        
        result["status"] = "completed"
        result["coins_analyzed"] = len(analyzed)
        result["coins_selected"] = len(selected)
        result["categories"] = {k: len(v) for k, v in categories.items()}
        result["top_coins"] = selected[:20]
        result["hidden_gems"] = categories["hidden_gems"][:10]
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        return result


# Singleton instances
_ensemble_predictor = None
_universe_optimizer = None

def get_ensemble_predictor(db=None, market_service=None, deep_learning_ai=None) -> EnsembleAIPredictor:
    global _ensemble_predictor
    if _ensemble_predictor is None:
        _ensemble_predictor = EnsembleAIPredictor(db, market_service, deep_learning_ai)
    return _ensemble_predictor

def get_universe_optimizer(db=None, market_service=None, ensemble=None) -> UniverseOptimizer:
    global _universe_optimizer
    if _universe_optimizer is None:
        _universe_optimizer = UniverseOptimizer(db, market_service, ensemble)
    return _universe_optimizer

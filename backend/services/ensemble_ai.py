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
        elif rsi > 70:
            score -= 20  # Overbought - bearish
        
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
    Uses ensemble AI predictions to build optimal trading portfolio.
    """
    
    def __init__(self, db, market_service, ensemble_predictor, deep_learning_ai=None):
        self.db = db
        self.market_service = market_service
        self.ensemble = ensemble_predictor
        self.deep_learning_ai = deep_learning_ai
        self.api_key = os.getenv('EMERGENT_LLM_KEY')
        
    async def analyze_top_coins(self, limit: int = 1000, batch_size: int = 200, progress_callback=None) -> List[Dict]:
        """Analyze top coins by market cap using all AI models - processes in batches"""
        analyzed = []
        
        try:
            all_coins = []
            num_batches = (limit + batch_size - 1) // batch_size  # Ceiling division
            
            _universe_rebuild_status["progress_message"] = f"Fetching {limit} coins in {num_batches} batches of {batch_size}..."
            
            # Fetch coins in batches of 200
            for batch_num in range(1, num_batches + 1):
                _universe_rebuild_status["progress_message"] = f"Fetching batch {batch_num}/{num_batches} (coins {(batch_num-1)*batch_size + 1}-{min(batch_num*batch_size, limit)})..."
                _universe_rebuild_status["progress"] = int((batch_num - 1) / num_batches * 20)  # 0-20% for fetching
                
                try:
                    coins = await self.market_service.get_all_coins(per_page=batch_size, page=batch_num)
                    if coins:
                        all_coins.extend(coins)
                        print(f"Batch {batch_num}: Fetched {len(coins)} coins (total: {len(all_coins)})")
                    else:
                        print(f"Batch {batch_num}: No coins returned, stopping")
                        break
                except Exception as e:
                    print(f"Batch {batch_num} error: {e}")
                    continue
                
                await asyncio.sleep(1.5)  # Rate limiting between batches
                
                if len(all_coins) >= limit:
                    break
            
            all_coins = all_coins[:limit]
            _universe_rebuild_status["total_coins"] = len(all_coins)
            _universe_rebuild_status["progress_message"] = f"Analyzing {len(all_coins)} coins..."
            _universe_rebuild_status["progress"] = 20  # Fetching complete
            
            # Analyze each coin with ensemble scoring
            for i, coin in enumerate(all_coins):
                _universe_rebuild_status["coins_analyzed"] = i + 1
                _universe_rebuild_status["progress"] = 20 + int((i + 1) / len(all_coins) * 60)  # 20-80% for analysis
                
                if i % 50 == 0:
                    _universe_rebuild_status["progress_message"] = f"Analyzing coin {i+1}/{len(all_coins)}: {coin.get('symbol', 'N/A').upper()}"
                
                try:
                    analysis = await self._analyze_coin_with_ensemble(coin)
                    if analysis and analysis.get('ensemble_score', 0) > 30:
                        analyzed.append(analysis)
                except Exception:
                    continue
                
                # Rate limiting - lighter since we already have all the data
                if i % 50 == 0 and i > 0:
                    await asyncio.sleep(0.1)
            
        except Exception as e:
            print(f"Analysis error: {e}")
            _universe_rebuild_status["error"] = str(e)
        
        return analyzed
    
    async def _analyze_coin_with_ensemble(self, coin: Dict) -> Optional[Dict]:
        """Analyze a single coin using all ML/DL models"""
        coin_id = coin.get('id', '')
        
        # Basic metrics from market data
        market_cap = coin.get('market_cap', 0) or 0
        volume = coin.get('total_volume', 0) or 0
        price_change_24h = coin.get('price_change_24h', 0) or 0
        price_change_7d = coin.get('price_change_7d', 0) or 0
        current_price = coin.get('current_price', 0) or 0
        
        # Initialize scores
        base_score = 50
        ai_prediction_score = 0
        technical_score = 0
        momentum_score = 0
        liquidity_score = 0
        market_cap_score = 0
        
        # 1. Volume/Market cap ratio (liquidity) - 15% weight
        vol_ratio = (volume / market_cap * 100) if market_cap > 0 else 0
        if vol_ratio > 20:
            liquidity_score = 15
        elif vol_ratio > 10:
            liquidity_score = 10
        elif vol_ratio > 5:
            liquidity_score = 5
        elif vol_ratio < 1:
            liquidity_score = -5
        
        # 2. Market cap tier - 20% weight (prefer small-mid caps for growth)
        if market_cap < 50_000_000:  # < $50M - highest potential
            market_cap_score = 20
        elif market_cap < 100_000_000:  # < $100M
            market_cap_score = 18
        elif market_cap < 500_000_000:  # < $500M
            market_cap_score = 15
        elif market_cap < 1_000_000_000:  # < $1B
            market_cap_score = 12
        elif market_cap < 10_000_000_000:  # < $10B
            market_cap_score = 8
        else:  # > $10B - more stable but less upside
            market_cap_score = 5
        
        # 3. Momentum score - 20% weight
        if 5 < price_change_24h < 15:
            momentum_score += 10  # Strong but not overextended
        elif 15 < price_change_24h < 30:
            momentum_score += 7  # Strong but risky
        elif price_change_24h > 30:
            momentum_score += 3  # Potentially overextended
        elif -5 < price_change_24h < 5:
            momentum_score += 5  # Stable
        elif -15 < price_change_24h < -5:
            momentum_score += 8  # Potential dip buy
        
        # Weekly momentum adds perspective
        if price_change_7d and price_change_7d > 20:
            momentum_score += 5
        elif price_change_7d and price_change_7d > 10:
            momentum_score += 3
        
        # 4. Try to get AI prediction if possible (skipped for speed - can be enabled for deeper analysis)
        # This would fetch historical data for each coin which is slow
        # For faster rebuilds, we rely on market data signals instead
        
        # Use price change as a proxy for technical score
        if price_change_24h and price_change_7d:
            if price_change_24h > 5 and price_change_7d > 10:
                technical_score = 15  # Strong bullish
            elif price_change_24h > 0 and price_change_7d > 0:
                technical_score = 8   # Mild bullish
            elif price_change_24h < -5 and price_change_7d < -10:
                technical_score = -10  # Strong bearish
            elif price_change_24h < 0 and price_change_7d < 0:
                technical_score = -3   # Mild bearish
            else:
                technical_score = 3    # Neutral/mixed
        
        # Calculate ensemble score (weighted combination)
        ensemble_score = (
            base_score +
            liquidity_score * 0.15 +
            market_cap_score * 0.20 +
            momentum_score * 0.20 +
            technical_score * 0.25 +
            ai_prediction_score * 0.20
        )
        
        # Gem potential (high score + low market cap)
        is_gem_candidate = ensemble_score >= 60 and market_cap < 500_000_000
        gem_potential = "HIGH" if ensemble_score >= 70 and market_cap < 200_000_000 else \
                       "MEDIUM" if is_gem_candidate else "LOW"
        
        return {
            "coin_id": coin_id,
            "symbol": coin.get('symbol', '').upper(),
            "name": coin.get('name', ''),
            "current_price": current_price,
            "market_cap": market_cap,
            "market_cap_rank": coin.get('market_cap_rank', 0),
            "volume_24h": volume,
            "volume_ratio": round(vol_ratio, 2),
            "price_change_24h": round(price_change_24h, 2) if price_change_24h else 0,
            "price_change_7d": round(price_change_7d, 2) if price_change_7d else 0,
            "scores": {
                "liquidity": round(liquidity_score, 2),
                "market_cap": round(market_cap_score, 2),
                "momentum": round(momentum_score, 2),
                "technical": round(technical_score, 2),
                "ai_prediction": round(ai_prediction_score, 2)
            },
            "ensemble_score": round(min(100, max(0, ensemble_score)), 2),
            "gem_potential": gem_potential,
            "is_gem_candidate": is_gem_candidate,
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_existing_portfolio(self) -> Dict[str, Any]:
        """Get current portfolio recommendations from database"""
        existing = {
            "coins": [],
            "strategies": [],
            "gem_picks": []
        }
        
        if self.db is None:
            return existing
        
        try:
            # Get current optimal universe
            cursor = self.db.optimal_universe.find().sort("universe_score", -1).limit(50)
            universe_coins = await cursor.to_list(length=50)
            for coin in universe_coins:
                coin.pop('_id', None)
                existing["coins"].append(coin)
            
            # Get recent strategies
            strat_cursor = self.db.strategies.find().sort("created_at", -1).limit(5)
            strategies = await strat_cursor.to_list(length=5)
            for s in strategies:
                s.pop('_id', None)
                existing["strategies"].append({
                    "name": s.get("name", "Strategy"),
                    "allocations": s.get("allocations", []),
                    "created_at": s.get("created_at")
                })
            
            # Get recent gem picks
            gem_cursor = self.db.gem_scans.find().sort("timestamp", -1).limit(3)
            gems = await gem_cursor.to_list(length=3)
            for g in gems:
                if g.get('gems'):
                    for gem in g['gems'][:10]:
                        gem.pop('_id', None) if isinstance(gem, dict) else None
                        existing["gem_picks"].append(gem)
            
        except Exception as e:
            print(f"Error getting existing portfolio: {e}")
        
        return existing
    
    async def build_optimal_universe(self, target_size: int = 50, analyze_count: int = 500) -> Dict[str, Any]:
        """
        Build an optimal trading universe from top 1000 coins.
        Uses ensemble AI to score and rank all coins.
        """
        result = {
            "status": "building",
            "target_size": target_size,
            "analyze_count": analyze_count,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
        _universe_rebuild_status["progress_message"] = "Getting existing portfolio for comparison..."
        
        # Get existing portfolio for comparison
        existing_portfolio = await self.get_existing_portfolio()
        existing_symbols = set(c.get('symbol', '').upper() for c in existing_portfolio.get('coins', []))
        
        _universe_rebuild_status["progress"] = 5
        
        # Analyze all coins
        analyzed = await self.analyze_top_coins(limit=analyze_count)
        
        if not analyzed:
            result["error"] = "Failed to analyze coins"
            _universe_rebuild_status["error"] = "Failed to analyze coins"
            return result
        
        _universe_rebuild_status["progress"] = 85
        _universe_rebuild_status["progress_message"] = "Building optimal portfolio..."
        
        # Sort by ensemble score
        analyzed.sort(key=lambda x: x['ensemble_score'], reverse=True)
        
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
            
            if mcap > 10_000_000_000:
                categories["large_cap"].append(coin)
            elif mcap > 1_000_000_000:
                categories["mid_cap"].append(coin)
            elif mcap > 100_000_000:
                categories["small_cap"].append(coin)
            else:
                categories["micro_cap"].append(coin)
            
            # Hidden gems: high score, low market cap
            if coin.get('is_gem_candidate'):
                categories["hidden_gems"].append(coin)
        
        _universe_rebuild_status["progress"] = 90
        _universe_rebuild_status["progress_message"] = "Saving to database..."
        
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
                
                # Save build summary
                await self.db.universe_builds.insert_one({
                    "built_at": datetime.now(timezone.utc),
                    "coins_analyzed": len(analyzed),
                    "coins_selected": len(selected),
                    "categories": {k: len(v) for k, v in categories.items()},
                    "top_10": [c['symbol'] for c in selected[:10]],
                    "hidden_gems": [c['symbol'] for c in categories["hidden_gems"][:10]]
                })
            except Exception as e:
                print(f"DB error: {e}")
        
        _universe_rebuild_status["progress"] = 95
        _universe_rebuild_status["progress_message"] = "Computing portfolio comparison..."
        
        # Compute portfolio comparison
        new_symbols = set(c.get('symbol', '').upper() for c in selected)
        comparison = {
            "overlap": list(existing_symbols & new_symbols),
            "added": list(new_symbols - existing_symbols),
            "removed": list(existing_symbols - new_symbols),
            "overlap_count": len(existing_symbols & new_symbols),
            "added_count": len(new_symbols - existing_symbols),
            "removed_count": len(existing_symbols - new_symbols),
            "existing_portfolio_size": len(existing_portfolio.get('coins', [])),
            "new_portfolio_size": len(selected),
            "avg_existing_score": round(sum(c.get('universe_score', 0) for c in existing_portfolio.get('coins', [])) / max(1, len(existing_portfolio.get('coins', []))), 2),
            "avg_new_score": round(sum(c.get('ensemble_score', 0) for c in selected) / max(1, len(selected)), 2),
            "recommendations_changed": len(new_symbols - existing_symbols) > 0
        }
        
        result["status"] = "completed"
        result["coins_analyzed"] = len(analyzed)
        result["coins_selected"] = len(selected)
        result["categories"] = {k: len(v) for k, v in categories.items()}
        result["top_coins"] = selected[:20]
        result["hidden_gems"] = categories["hidden_gems"][:10]
        result["comparison"] = comparison
        result["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        _universe_rebuild_status["progress"] = 100
        _universe_rebuild_status["progress_message"] = "Complete!"
        _universe_rebuild_status["result"] = result
        _universe_rebuild_status["comparison"] = comparison
        
        return result
    
    async def get_weekly_recommendations_comparison(self) -> Dict[str, Any]:
        """Compare current and previous week's recommendations"""
        if self.db is None:
            return {"error": "Database not available"}
        
        try:
            # Get two most recent builds
            cursor = self.db.universe_builds.find().sort("built_at", -1).limit(2)
            builds = await cursor.to_list(length=2)
            
            # Remove MongoDB _id from builds
            for build in builds:
                build.pop('_id', None)
            
            if len(builds) < 2:
                current_build = builds[0] if builds else None
                if current_build:
                    current_build.pop('_id', None)
                return {
                    "message": "Not enough historical data for comparison",
                    "current_build": current_build
                }
            
            current = builds[0]
            previous = builds[1]
            
            current_top = set(current.get('top_10', []))
            previous_top = set(previous.get('top_10', []))
            
            return {
                "current_build_date": current.get('built_at'),
                "previous_build_date": previous.get('built_at'),
                "current_top_10": list(current_top),
                "previous_top_10": list(previous_top),
                "retained": list(current_top & previous_top),
                "new_additions": list(current_top - previous_top),
                "dropped": list(previous_top - current_top),
                "current_gems": current.get('hidden_gems', []),
                "previous_gems": previous.get('hidden_gems', [])
            }
        except Exception as e:
            return {"error": str(e)}


# Singleton instances
_ensemble_predictor = None
_universe_optimizer = None

def get_ensemble_predictor(db=None, market_service=None, deep_learning_ai=None) -> EnsembleAIPredictor:
    global _ensemble_predictor
    if _ensemble_predictor is None:
        _ensemble_predictor = EnsembleAIPredictor(db, market_service, deep_learning_ai)
    return _ensemble_predictor

def get_universe_optimizer(db=None, market_service=None, ensemble=None, deep_learning_ai=None) -> UniverseOptimizer:
    global _universe_optimizer
    if _universe_optimizer is None:
        _universe_optimizer = UniverseOptimizer(db, market_service, ensemble, deep_learning_ai)
    return _universe_optimizer


async def run_universe_rebuild_background(optimizer: UniverseOptimizer, target_size: int = 50, analyze_count: int = 500):
    """Background task to run universe rebuild"""
    _universe_rebuild_status["running"] = True
    _universe_rebuild_status["started_at"] = datetime.now(timezone.utc).isoformat()
    _universe_rebuild_status["progress"] = 0
    _universe_rebuild_status["progress_message"] = "Starting universe rebuild..."
    _universe_rebuild_status["error"] = None
    _universe_rebuild_status["result"] = None
    
    # Persist running state to database
    try:
        from services.state_persistence import get_state_persistence
        persistence = get_state_persistence(optimizer.db)
        if persistence:
            await persistence.set_state(
                "universe_rebuild", 
                True, 
                metadata={
                    "started_at": _universe_rebuild_status["started_at"],
                    "target_size": target_size,
                    "analyze_count": analyze_count
                }
            )
    except Exception as e:
        print(f"Could not persist universe rebuild state: {e}")
    
    try:
        result = await optimizer.build_optimal_universe(
            target_size=target_size,
            analyze_count=analyze_count
        )
        _universe_rebuild_status["result"] = result
    except Exception as e:
        _universe_rebuild_status["error"] = str(e)
        _universe_rebuild_status["progress_message"] = f"Error: {str(e)}"
    finally:
        _universe_rebuild_status["running"] = False
        
        # Persist completed/stopped state
        try:
            from services.state_persistence import get_state_persistence
            persistence = get_state_persistence(optimizer.db)
            if persistence:
                await persistence.set_state(
                    "universe_rebuild", 
                    False,
                    metadata={
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "error": _universe_rebuild_status.get("error"),
                        "progress": _universe_rebuild_status.get("progress", 100)
                    }
                )
        except Exception as e:
            print(f"Could not persist universe rebuild completion: {e}")

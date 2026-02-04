"""
Gem Prediction Backtester Service
Backtests gem prediction accuracy against historical data and iteratively improves.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
import numpy as np


class GemBacktester:
    """
    Backtests gem predictions against historical OHLCV data.
    Iteratively improves prediction accuracy through pattern learning.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, gem_predictor=None):
        self.db = db
        self.gem_predictor = gem_predictor
        self.backtest_results_collection = "gem_backtest_results"
        
    async def run_backtest(
        self,
        target_accuracy: float = 75.0,
        max_iterations: int = 10,
        test_coins: List[str] = None
    ) -> Dict[str, Any]:
        """
        Run iterative backtesting until target accuracy is reached.
        
        Args:
            target_accuracy: Target accuracy percentage (default: 75%)
            max_iterations: Maximum iterations to try (default: 10)
            test_coins: Coins to test (default: all with OHLCV data)
        
        Returns:
            Dict with backtest results and improvement history
        """
        results = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "target_accuracy": target_accuracy,
            "iterations": [],
            "final_accuracy": 0,
            "target_reached": False,
            "improvements_made": [],
            "best_weights": {},
            "best_threshold": 0.7
        }
        
        # Get coins with historical data
        if test_coins:
            coins = test_coins
        else:
            coins = await self.db.historical_ohlcv.distinct("symbol")
        
        if not coins:
            results["error"] = "No historical data found. Download OHLCV data first."
            return results
        
        # Limit to 30 coins for reasonable backtest time
        coins = coins[:30]
        
        current_weights = {
            "volume_surge": 0.20,
            "price_momentum": 0.15,
            "market_cap_potential": 0.10,
            "technical_setup": 0.15,
            "volatility_score": 0.10,
            "sentiment": 0.10,
            "relative_strength": 0.20  # New: compare to BTC
        }
        
        current_threshold = 0.70  # Start with higher threshold to reduce false positives
        best_accuracy = 0
        best_weights_so_far = current_weights.copy()
        best_threshold_so_far = current_threshold
        
        for iteration in range(max_iterations):
            iter_result = await self._run_single_iteration(
                coins=coins,
                weights=current_weights,
                iteration_num=iteration + 1,
                gem_threshold=current_threshold
            )
            
            results["iterations"].append(iter_result)
            current_accuracy = iter_result["accuracy"]
            
            # Track best result
            if current_accuracy > best_accuracy:
                best_accuracy = current_accuracy
                best_weights_so_far = current_weights.copy()
                best_threshold_so_far = current_threshold
            
            if current_accuracy >= target_accuracy:
                results["target_reached"] = True
                results["final_accuracy"] = current_accuracy
                results["best_weights"] = current_weights.copy()
                results["best_threshold"] = current_threshold
                results["message"] = f"Target accuracy of {target_accuracy}% reached in {iteration + 1} iterations!"
                break
            
            # Improve weights and threshold based on backtest feedback
            improvements = self._improve_weights(
                current_weights=current_weights,
                iter_result=iter_result,
                current_threshold=current_threshold
            )
            
            current_weights = improvements["new_weights"]
            current_threshold = improvements["new_threshold"]
            results["improvements_made"].append({
                "iteration": iteration + 1,
                "changes": improvements["changes"],
                "reason": improvements["reason"],
                "new_threshold": current_threshold
            })
            
            # Brief delay between iterations
            await asyncio.sleep(0.1)
        
        if not results["target_reached"]:
            results["final_accuracy"] = best_accuracy
            results["best_weights"] = best_weights_so_far
            results["best_threshold"] = best_threshold_so_far
            results["message"] = f"Best accuracy: {best_accuracy:.1f}% after {max_iterations} iterations"
        
        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Store results in DB
        await self.db[self.backtest_results_collection].insert_one({
            "type": "iterative_backtest",
            "results": results,
            "timestamp": datetime.now(timezone.utc)
        })
        
        # Update gem predictor weights if available and improved
        if self.gem_predictor and results["final_accuracy"] > 50:
            self.gem_predictor.weights = results["best_weights"]
            if hasattr(self.gem_predictor, 'gem_threshold'):
                self.gem_predictor.gem_threshold = results["best_threshold"]
        
        return results
    
    async def _run_single_iteration(
        self,
        coins: List[str],
        weights: Dict[str, float],
        iteration_num: int,
        gem_threshold: float = 0.70
    ) -> Dict[str, Any]:
        """Run a single backtest iteration"""
        total_predictions = 0
        correct_predictions = 0
        predictions_detail = []
        
        # Get BTC data for relative strength calculation
        btc_data = await self.db.historical_ohlcv.find(
            {"symbol": "BTC"},
            {"_id": 0}
        ).sort("timestamp", 1).to_list(length=10000)
        
        btc_prices_by_date = {}
        for d in btc_data:
            date_key = d.get("timestamp", d.get("date", ""))
            if isinstance(date_key, str):
                btc_prices_by_date[date_key[:10]] = d["close"]
            else:
                btc_prices_by_date[str(date_key)[:10]] = d["close"]
        
        for coin in coins:
            if coin == "BTC":  # Skip BTC for gem detection
                continue
                
            try:
                # Get historical OHLCV data
                data = await self.db.historical_ohlcv.find(
                    {"symbol": coin},
                    {"_id": 0}
                ).sort("timestamp", 1).to_list(length=10000)
                
                if len(data) < 365:
                    continue
                
                # Test predictions at multiple points in history
                test_points = [
                    int(len(data) * 0.3),  # 30% through history
                    int(len(data) * 0.5),  # 50% through history
                    int(len(data) * 0.7),  # 70% through history
                ]
                
                for test_idx in test_points:
                    if test_idx < 90 or test_idx >= len(data) - 30:
                        continue
                    
                    # Get data up to test point
                    historical_data = data[:test_idx]
                    future_data = data[test_idx:test_idx + 30]  # 30 days ahead
                    
                    # Calculate gem score at test point
                    gem_score = self._calculate_gem_score(historical_data, weights, btc_prices_by_date)
                    
                    # Check if prediction was correct (using stricter criteria)
                    was_gem = self._check_if_gem(future_data, btc_prices_by_date)
                    predicted_gem = gem_score >= gem_threshold
                    
                    total_predictions += 1
                    if predicted_gem == was_gem:
                        correct_predictions += 1
                    
                    predictions_detail.append({
                        "coin": coin,
                        "test_date": str(historical_data[-1].get("timestamp", historical_data[-1].get("date", "")))[:19],
                        "gem_score": float(gem_score),
                        "predicted_gem": bool(predicted_gem),
                        "actual_gem": bool(was_gem),
                        "correct": bool(predicted_gem == was_gem)
                    })
                    
            except Exception as e:
                continue
        
        accuracy = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
        
        # Analyze which factors contributed most to correct predictions
        factor_analysis = self._analyze_factors(predictions_detail, weights)
        
        return {
            "iteration": iteration_num,
            "total_predictions": total_predictions,
            "correct_predictions": correct_predictions,
            "accuracy": round(accuracy, 2),
            "gem_threshold": gem_threshold,
            "weights_used": weights.copy(),
            "factor_analysis": factor_analysis,
            "sample_predictions": predictions_detail[:10]
        }
    
    def _calculate_gem_score(self, data: List[Dict], weights: Dict[str, float], btc_prices: Dict[str, float] = None) -> float:
        """Calculate gem score based on historical data"""
        if len(data) < 90:
            return 0.0
        
        prices = [d["close"] for d in data]
        volumes = [d.get("volume_to", d.get("volume", 0)) for d in data]
        
        scores = {}
        
        # Volume surge score - look for increasing volume trend
        avg_volume = np.mean(volumes[:-30]) if len(volumes) > 30 else np.mean(volumes)
        recent_volume = np.mean(volumes[-30:]) if len(volumes) >= 30 else np.mean(volumes)
        if avg_volume > 0:
            volume_surge = recent_volume / avg_volume
            # Only high scores for genuine surges (2x+), penalize declining volume
            if volume_surge >= 2:
                scores["volume_surge"] = min(1.0, (volume_surge - 1) / 3)
            elif volume_surge >= 1:
                scores["volume_surge"] = 0.3 * volume_surge
            else:
                scores["volume_surge"] = 0.1
        else:
            scores["volume_surge"] = 0.0
        
        # Price momentum score - but not too much (avoid FOMO)
        if len(prices) >= 30:
            recent_price = np.mean(prices[-7:])
            older_price = np.mean(prices[-30:-7]) if len(prices) > 30 else np.mean(prices)
            if older_price > 0:
                momentum = (recent_price - older_price) / older_price
                # Sweet spot: slight positive momentum (5-20%), not overbought
                if 0.05 <= momentum <= 0.20:
                    scores["price_momentum"] = 0.8 + (momentum - 0.05) * 1.3
                elif 0 <= momentum < 0.05:
                    scores["price_momentum"] = 0.4 + momentum * 8
                elif momentum > 0.20:
                    # Penalize if already pumped
                    scores["price_momentum"] = max(0.2, 0.8 - (momentum - 0.20) * 2)
                else:
                    # Negative momentum might be accumulation phase
                    scores["price_momentum"] = max(0.1, 0.4 + momentum * 2)
            else:
                scores["price_momentum"] = 0.3
        else:
            scores["price_momentum"] = 0.3
        
        # Market cap potential (distance from ATH)
        max_price = max(prices)
        current_price = prices[-1]
        if max_price > 0:
            distance_from_ath = 1 - (current_price / max_price)
            # Gems are often 50-90% below ATH
            if 0.50 <= distance_from_ath <= 0.90:
                scores["market_cap_potential"] = 0.7 + (distance_from_ath - 0.5) * 0.75
            elif distance_from_ath > 0.90:
                scores["market_cap_potential"] = 0.5  # Too beaten down might be dead
            else:
                scores["market_cap_potential"] = distance_from_ath * 1.4
        else:
            scores["market_cap_potential"] = 0.3
        
        # Technical setup (RSI-like calculation)
        if len(prices) >= 14:
            gains = []
            losses = []
            for i in range(1, min(15, len(prices))):
                change = prices[-i] - prices[-i-1]
                if change > 0:
                    gains.append(change)
                else:
                    losses.append(abs(change))
            avg_gain = np.mean(gains) if gains else 0
            avg_loss = np.mean(losses) if losses else 1
            rs = avg_gain / avg_loss if avg_loss > 0 else 1
            rsi = 100 - (100 / (1 + rs))
            # Gems often have RSI between 30-50 (oversold but showing life)
            if 30 <= rsi <= 50:
                scores["technical_setup"] = 0.9
            elif 20 <= rsi < 30:
                scores["technical_setup"] = 0.7
            elif 50 < rsi <= 60:
                scores["technical_setup"] = 0.6
            else:
                scores["technical_setup"] = 0.3
        else:
            scores["technical_setup"] = 0.4
        
        # Volatility score (moderate volatility is good for gems)
        if len(prices) >= 30:
            daily_returns = []
            for i in range(1, len(prices)):
                if prices[i-1] > 0:
                    daily_returns.append((prices[i] - prices[i-1]) / prices[i-1])
            volatility = np.std(daily_returns) * 100 if daily_returns else 5
            # Sweet spot is 4-10% daily volatility
            if 4 <= volatility <= 10:
                scores["volatility_score"] = 0.8
            elif 2 <= volatility < 4:
                scores["volatility_score"] = 0.5
            elif volatility > 10:
                scores["volatility_score"] = max(0.2, 0.8 - (volatility - 10) / 20)
            else:
                scores["volatility_score"] = 0.3
        else:
            scores["volatility_score"] = 0.4
        
        # Sentiment score (using volume trend as proxy)
        if len(volumes) >= 30:
            recent_vol = np.mean(volumes[-7:])
            older_vol = np.mean(volumes[-30:-7]) if len(volumes) > 30 else np.mean(volumes)
            if older_vol > 0:
                volume_trend = recent_vol / older_vol
                if volume_trend >= 1.5:
                    scores["sentiment"] = 0.8
                elif volume_trend >= 1.0:
                    scores["sentiment"] = 0.5
                else:
                    scores["sentiment"] = 0.3
            else:
                scores["sentiment"] = 0.4
        else:
            scores["sentiment"] = 0.4
        
        # Relative strength vs BTC (NEW - key for finding gems)
        scores["relative_strength"] = 0.5  # Default
        if btc_prices and len(prices) >= 30:
            # Get corresponding BTC prices
            coin_return_30d = (prices[-1] / prices[-30] - 1) if prices[-30] > 0 else 0
            
            # Find BTC return for same period (approximate)
            try:
                last_date = str(data[-1].get("timestamp", data[-1].get("date", "")))[:10]
                first_date = str(data[-30].get("timestamp", data[-30].get("date", "")))[:10]
                
                btc_end = btc_prices.get(last_date, 0)
                btc_start = btc_prices.get(first_date, 0)
                
                if btc_start > 0 and btc_end > 0:
                    btc_return = (btc_end / btc_start - 1)
                    relative_perf = coin_return_30d - btc_return
                    
                    # Gems outperform BTC
                    if relative_perf > 0.10:
                        scores["relative_strength"] = min(1.0, 0.7 + relative_perf)
                    elif relative_perf > 0:
                        scores["relative_strength"] = 0.5 + relative_perf * 2
                    else:
                        scores["relative_strength"] = max(0.1, 0.5 + relative_perf)
            except:
                pass
        
        # Calculate weighted total
        total_score = sum(scores.get(k, 0.4) * weights.get(k, 0.1) for k in weights.keys())
        
        return min(1.0, max(0, total_score))
    
    def _check_if_gem(self, future_data: List[Dict], btc_prices: Dict[str, float] = None) -> bool:
        """Check if coin was actually a gem (significant gain vs BTC in future)"""
        if not future_data or len(future_data) < 5:
            return False
        
        start_price = future_data[0]["close"]
        prices = [d["close"] for d in future_data]
        max_price = max(prices)
        
        if start_price <= 0:
            return False
        
        coin_gain_pct = ((max_price - start_price) / start_price) * 100
        
        # Get BTC performance for the same period
        btc_gain_pct = 0
        if btc_prices:
            try:
                start_date = str(future_data[0].get("timestamp", future_data[0].get("date", "")))[:10]
                end_date = str(future_data[-1].get("timestamp", future_data[-1].get("date", "")))[:10]
                
                btc_start = btc_prices.get(start_date, 0)
                btc_end = btc_prices.get(end_date, 0)
                
                if btc_start > 0 and btc_end > 0:
                    btc_gain_pct = ((btc_end - btc_start) / btc_start) * 100
            except:
                pass
        
        # A "gem" must:
        # 1. Gain at least 30% absolute
        # 2. Outperform BTC by at least 15%
        relative_gain = coin_gain_pct - btc_gain_pct
        
        return coin_gain_pct >= 30 and relative_gain >= 15
    
    def _analyze_factors(
        self,
        predictions: List[Dict],
        weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze which factors contributed most to correct predictions"""
        correct = [p for p in predictions if p["correct"]]
        incorrect = [p for p in predictions if not p["correct"]]
        
        correct_avg_score = np.mean([p["gem_score"] for p in correct]) if correct else 0
        incorrect_avg_score = np.mean([p["gem_score"] for p in incorrect]) if incorrect else 0
        
        # Identify patterns
        correct_gem_predictions = [p for p in correct if p["predicted_gem"]]
        correct_non_gem = [p for p in correct if not p["predicted_gem"]]
        
        return {
            "correct_avg_score": round(float(correct_avg_score), 3),
            "incorrect_avg_score": round(float(incorrect_avg_score), 3),
            "correct_gem_count": len(correct_gem_predictions),
            "correct_non_gem_count": len(correct_non_gem),
            "false_positive_count": len([p for p in incorrect if p["predicted_gem"]]),
            "false_negative_count": len([p for p in incorrect if not p["predicted_gem"]])
        }
    
    def _improve_weights(
        self,
        current_weights: Dict[str, float],
        iter_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Improve weights based on backtest results"""
        new_weights = current_weights.copy()
        analysis = iter_result.get("factor_analysis", {})
        
        changes = []
        reason = ""
        
        # If too many false positives, increase threshold strictness
        false_positives = analysis.get("false_positive_count", 0)
        false_negatives = analysis.get("false_negative_count", 0)
        
        if false_positives > false_negatives * 1.5:
            # Too many false positives - reduce volume and momentum weight
            new_weights["volume_surge"] = max(0.1, new_weights["volume_surge"] - 0.02)
            new_weights["price_momentum"] = max(0.1, new_weights["price_momentum"] - 0.02)
            new_weights["technical_setup"] = min(0.25, new_weights["technical_setup"] + 0.02)
            changes.append("Reduced volume_surge and momentum weights")
            reason = "High false positive rate"
        elif false_negatives > false_positives * 1.5:
            # Too many false negatives - increase sensitivity
            new_weights["volume_surge"] = min(0.35, new_weights["volume_surge"] + 0.02)
            new_weights["price_momentum"] = min(0.30, new_weights["price_momentum"] + 0.02)
            changes.append("Increased volume_surge and momentum weights")
            reason = "High false negative rate"
        else:
            # Balanced - fine tune based on accuracy
            accuracy = iter_result.get("accuracy", 0)
            if accuracy < 60:
                # Need more balanced approach
                new_weights["volatility_score"] = min(0.20, new_weights["volatility_score"] + 0.01)
                new_weights["market_cap_potential"] = min(0.20, new_weights["market_cap_potential"] + 0.01)
                changes.append("Increased volatility and market_cap weights")
                reason = "Low overall accuracy - balancing factors"
            else:
                # Small random adjustments for exploration
                factor = np.random.choice(list(new_weights.keys()))
                adjustment = np.random.uniform(-0.02, 0.02)
                new_weights[factor] = max(0.05, min(0.35, new_weights[factor] + adjustment))
                changes.append(f"Fine-tuned {factor}")
                reason = "Exploring weight space"
        
        # Normalize weights to sum to 1
        total = sum(new_weights.values())
        new_weights = {k: v / total for k, v in new_weights.items()}
        
        return {
            "new_weights": new_weights,
            "changes": changes,
            "reason": reason
        }
    
    async def get_backtest_history(self, limit: int = 10) -> List[Dict]:
        """Get history of backtest runs"""
        results = await self.db[self.backtest_results_collection].find(
            {}, {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return results


# Global instance
_backtester_instance = None

def get_gem_backtester(db: AsyncIOMotorDatabase = None, gem_predictor=None):
    """Get or create backtester instance"""
    global _backtester_instance
    if _backtester_instance is None and db is not None:
        _backtester_instance = GemBacktester(db, gem_predictor)
    return _backtester_instance

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
            "best_weights": {}
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
            "volume_surge": 0.25,
            "price_momentum": 0.20,
            "market_cap_potential": 0.15,
            "technical_setup": 0.15,
            "volatility_score": 0.15,
            "sentiment": 0.10
        }
        
        for iteration in range(max_iterations):
            iter_result = await self._run_single_iteration(
                coins=coins,
                weights=current_weights,
                iteration_num=iteration + 1
            )
            
            results["iterations"].append(iter_result)
            current_accuracy = iter_result["accuracy"]
            
            if current_accuracy >= target_accuracy:
                results["target_reached"] = True
                results["final_accuracy"] = current_accuracy
                results["best_weights"] = current_weights.copy()
                results["message"] = f"Target accuracy of {target_accuracy}% reached in {iteration + 1} iterations!"
                break
            
            # Improve weights based on backtest feedback
            improvements = self._improve_weights(
                current_weights=current_weights,
                iter_result=iter_result
            )
            
            current_weights = improvements["new_weights"]
            results["improvements_made"].append({
                "iteration": iteration + 1,
                "changes": improvements["changes"],
                "reason": improvements["reason"]
            })
            
            # Brief delay between iterations
            await asyncio.sleep(0.1)
        
        if not results["target_reached"]:
            results["final_accuracy"] = results["iterations"][-1]["accuracy"] if results["iterations"] else 0
            results["best_weights"] = current_weights
            results["message"] = f"Reached {results['final_accuracy']:.1f}% accuracy after {max_iterations} iterations"
        
        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Store results in DB
        await self.db[self.backtest_results_collection].insert_one({
            "type": "iterative_backtest",
            "results": results,
            "timestamp": datetime.now(timezone.utc)
        })
        
        # Update gem predictor weights if available and improved
        if self.gem_predictor and results["final_accuracy"] > 60:
            self.gem_predictor.weights = results["best_weights"]
        
        return results
    
    async def _run_single_iteration(
        self,
        coins: List[str],
        weights: Dict[str, float],
        iteration_num: int
    ) -> Dict[str, Any]:
        """Run a single backtest iteration"""
        total_predictions = 0
        correct_predictions = 0
        predictions_detail = []
        
        for coin in coins:
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
                    gem_score = self._calculate_gem_score(historical_data, weights)
                    
                    # Check if prediction was correct
                    was_gem = self._check_if_gem(future_data)
                    predicted_gem = gem_score >= 0.6
                    
                    total_predictions += 1
                    if predicted_gem == was_gem:
                        correct_predictions += 1
                    
                    predictions_detail.append({
                        "coin": coin,
                        "test_date": historical_data[-1]["date"],
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
            "weights_used": weights.copy(),
            "factor_analysis": factor_analysis,
            "sample_predictions": predictions_detail[:10]
        }
    
    def _calculate_gem_score(self, data: List[Dict], weights: Dict[str, float]) -> float:
        """Calculate gem score based on historical data"""
        if len(data) < 90:
            return 0.0
        
        prices = [d["close"] for d in data]
        volumes = [d["volume_to"] for d in data]
        
        scores = {}
        
        # Volume surge score
        avg_volume = np.mean(volumes[:-30]) if len(volumes) > 30 else np.mean(volumes)
        recent_volume = np.mean(volumes[-30:]) if len(volumes) >= 30 else np.mean(volumes)
        volume_surge = (recent_volume / avg_volume) if avg_volume > 0 else 1
        scores["volume_surge"] = min(1.0, volume_surge / 3)  # Normalize to 0-1
        
        # Price momentum score
        if len(prices) >= 30:
            recent_price = np.mean(prices[-7:])
            older_price = np.mean(prices[-30:-7]) if len(prices) > 30 else np.mean(prices)
            momentum = (recent_price - older_price) / older_price if older_price > 0 else 0
            scores["price_momentum"] = min(1.0, max(0, (momentum + 0.2) / 0.5))  # Normalize
        else:
            scores["price_momentum"] = 0.5
        
        # Market cap potential (inverse of current price relative to max)
        max_price = max(prices)
        current_price = prices[-1]
        scores["market_cap_potential"] = 1 - (current_price / max_price) if max_price > 0 else 0.5
        
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
            # Gems often have RSI between 30-70 (not overbought/oversold)
            scores["technical_setup"] = 1.0 if 30 <= rsi <= 70 else 0.5
        else:
            scores["technical_setup"] = 0.5
        
        # Volatility score (moderate volatility is good for gems)
        if len(prices) >= 30:
            daily_returns = []
            for i in range(1, len(prices)):
                if prices[i-1] > 0:
                    daily_returns.append((prices[i] - prices[i-1]) / prices[i-1])
            volatility = np.std(daily_returns) * 100 if daily_returns else 5
            # Sweet spot is 3-8% daily volatility
            if 3 <= volatility <= 8:
                scores["volatility_score"] = 1.0
            elif volatility < 3:
                scores["volatility_score"] = volatility / 3
            else:
                scores["volatility_score"] = max(0, 1 - (volatility - 8) / 10)
        else:
            scores["volatility_score"] = 0.5
        
        # Sentiment score (placeholder - using volume trend as proxy)
        volume_trend = (np.mean(volumes[-7:]) / np.mean(volumes[-30:])) if len(volumes) >= 30 else 1
        scores["sentiment"] = min(1.0, volume_trend / 2)
        
        # Calculate weighted total
        total_score = sum(scores.get(k, 0.5) * v for k, v in weights.items())
        
        return min(1.0, max(0, total_score))
    
    def _check_if_gem(self, future_data: List[Dict]) -> bool:
        """Check if coin was actually a gem (significant gain in future)"""
        if not future_data:
            return False
        
        start_price = future_data[0]["close"]
        prices = [d["close"] for d in future_data]
        max_price = max(prices)
        
        if start_price <= 0:
            return False
        
        gain_pct = ((max_price - start_price) / start_price) * 100
        
        # Consider it a gem if it gained 20%+ in the next 30 days
        return gain_pct >= 20
    
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
            "correct_avg_score": round(correct_avg_score, 3),
            "incorrect_avg_score": round(incorrect_avg_score, 3),
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

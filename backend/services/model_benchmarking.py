"""
Model Performance Benchmarking Service

Compares FinRL vs Ensemble vs Time-Series models across different market conditions.
Provides insights on which strategy performs best in various scenarios.
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


class MarketCondition(Enum):
    """Market condition classifications"""
    STRONG_BULL = "strong_bull"      # >20% monthly return
    BULL = "bull"                    # 5-20% monthly return
    SIDEWAYS = "sideways"            # -5% to 5% monthly return
    BEAR = "bear"                    # -20% to -5% monthly return
    STRONG_BEAR = "strong_bear"      # <-20% monthly return
    HIGH_VOLATILITY = "high_volatility"  # >50% annualized volatility
    LOW_VOLATILITY = "low_volatility"    # <20% annualized volatility


@dataclass
class BenchmarkResult:
    """Single benchmark run result"""
    model_name: str
    period_start: datetime
    period_end: datetime
    market_condition: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    volatility: float
    calmar_ratio: float  # Return / Max Drawdown
    sortino_ratio: float  # Risk-adjusted return using downside deviation


class ModelBenchmarkingService:
    """
    Service for benchmarking and comparing AI trading models.
    """
    
    def __init__(self, db=None):
        self.db = db
        self._benchmark_cache = {}
        self._last_benchmark_time = None
        
        # Model configurations for benchmarking
        self.model_configs = {
            "ensemble": {
                "name": "XGBoost/LightGBM Ensemble",
                "type": "ensemble",
                "description": "Gradient boosting ensemble for pattern recognition"
            },
            "time_series": {
                "name": "LSTM/GRU/Transformer",
                "type": "time_series", 
                "description": "Deep learning models for sequential prediction"
            },
            "finrl": {
                "name": "FinRL DRL Agent",
                "type": "reinforcement_learning",
                "description": "Deep Q-Network with experience replay"
            },
            "combined": {
                "name": "Combined Strategy",
                "type": "hybrid",
                "description": "Weighted combination of all models"
            }
        }
    
    def classify_market_condition(self, returns: np.ndarray, prices: np.ndarray) -> str:
        """Classify market condition based on returns and volatility"""
        if len(returns) < 5:
            return MarketCondition.SIDEWAYS.value
        
        # Calculate metrics
        monthly_return = np.mean(returns) * 30  # Approximate monthly
        volatility = np.std(returns) * np.sqrt(252)  # Annualized
        
        # Classify by volatility first
        if volatility > 0.5:
            return MarketCondition.HIGH_VOLATILITY.value
        elif volatility < 0.2:
            return MarketCondition.LOW_VOLATILITY.value
        
        # Classify by return
        if monthly_return > 0.20:
            return MarketCondition.STRONG_BULL.value
        elif monthly_return > 0.05:
            return MarketCondition.BULL.value
        elif monthly_return < -0.20:
            return MarketCondition.STRONG_BEAR.value
        elif monthly_return < -0.05:
            return MarketCondition.BEAR.value
        else:
            return MarketCondition.SIDEWAYS.value
    
    def calculate_performance_metrics(
        self, 
        returns: np.ndarray,
        trades: List[Dict] = None
    ) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        if len(returns) == 0:
            return {
                "total_return": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
                "volatility": 0,
                "win_rate": 0,
                "calmar_ratio": 0,
                "sortino_ratio": 0
            }
        
        # Total return (cumulative)
        total_return = np.prod(1 + returns) - 1
        
        # Volatility (annualized)
        volatility = np.std(returns) * np.sqrt(252)
        
        # Sharpe ratio (assuming 0% risk-free rate)
        sharpe = np.sqrt(252) * np.mean(returns) / (np.std(returns) + 1e-8)
        
        # Max drawdown
        cumulative = np.cumprod(1 + returns)
        peak = np.maximum.accumulate(cumulative)
        drawdown = (peak - cumulative) / peak
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
        
        # Calmar ratio
        calmar = total_return / (max_drawdown + 1e-8) if max_drawdown > 0 else total_return
        
        # Sortino ratio (downside deviation)
        negative_returns = returns[returns < 0]
        downside_std = np.std(negative_returns) if len(negative_returns) > 0 else 1e-8
        sortino = np.sqrt(252) * np.mean(returns) / (downside_std + 1e-8)
        
        # Win rate from trades
        win_rate = 0
        if trades:
            winning = len([t for t in trades if t.get('pnl', 0) > 0])
            win_rate = winning / len(trades) if trades else 0
        else:
            win_rate = len(returns[returns > 0]) / len(returns) if len(returns) > 0 else 0
        
        return {
            "total_return": float(total_return),
            "sharpe_ratio": float(sharpe),
            "max_drawdown": float(max_drawdown),
            "volatility": float(volatility),
            "win_rate": float(win_rate),
            "calmar_ratio": float(calmar),
            "sortino_ratio": float(sortino)
        }
    
    def simulate_model_performance(
        self,
        model_type: str,
        prices: np.ndarray,
        features: np.ndarray = None
    ) -> Dict[str, Any]:
        """
        Simulate model performance on historical data.
        Uses model-specific logic to generate signals and calculate returns.
        """
        if len(prices) < 10:
            return {"error": "Insufficient data"}
        
        returns = np.diff(prices) / prices[:-1]
        
        # Model-specific signal generation (simplified simulation)
        if model_type == "ensemble":
            # Ensemble: Momentum + mean reversion blend
            signals = self._generate_ensemble_signals(prices, returns)
        elif model_type == "time_series":
            # Time series: Trend following with lag
            signals = self._generate_timeseries_signals(prices, returns)
        elif model_type == "finrl":
            # FinRL: More aggressive, learns patterns
            signals = self._generate_finrl_signals(prices, returns)
        elif model_type == "combined":
            # Combined: Average of all models
            s1 = self._generate_ensemble_signals(prices, returns)
            s2 = self._generate_timeseries_signals(prices, returns)
            s3 = self._generate_finrl_signals(prices, returns)
            signals = (s1 + s2 + s3) / 3
        else:
            signals = np.zeros(len(returns))
        
        # Calculate strategy returns (signal * next period return)
        strategy_returns = signals[:-1] * returns[1:]
        
        # Apply transaction costs (0.1% per trade)
        signal_changes = np.abs(np.diff(signals))
        transaction_costs = signal_changes[:-1] * 0.001
        strategy_returns = strategy_returns[:-1] - transaction_costs
        
        # Generate mock trades
        trades = []
        position = 0
        for i, (sig, ret) in enumerate(zip(signals[:-2], strategy_returns)):
            if sig > 0.3 and position <= 0:
                trades.append({"type": "buy", "pnl": ret, "step": i})
                position = 1
            elif sig < -0.3 and position >= 0:
                trades.append({"type": "sell", "pnl": ret, "step": i})
                position = -1
        
        metrics = self.calculate_performance_metrics(strategy_returns, trades)
        metrics["total_trades"] = len(trades)
        
        return metrics
    
    def _generate_ensemble_signals(self, prices: np.ndarray, returns: np.ndarray) -> np.ndarray:
        """Generate signals mimicking ensemble model behavior"""
        signals = np.zeros(len(returns))
        
        # Short-term momentum
        for i in range(5, len(returns)):
            momentum = np.mean(returns[i-5:i])
            # Mean reversion component
            mean_price = np.mean(prices[max(0,i-20):i])
            deviation = (prices[i] - mean_price) / mean_price
            
            # Combine momentum and mean reversion
            signals[i] = 0.6 * np.tanh(momentum * 50) - 0.4 * np.tanh(deviation * 5)
        
        return signals
    
    def _generate_timeseries_signals(self, prices: np.ndarray, returns: np.ndarray) -> np.ndarray:
        """Generate signals mimicking LSTM/GRU behavior"""
        signals = np.zeros(len(returns))
        
        # Trend following with smoothing (mimics LSTM memory)
        for i in range(10, len(returns)):
            # Exponential weighted trend
            weights = np.exp(np.linspace(-2, 0, 10))
            weights /= weights.sum()
            trend = np.sum(returns[i-10:i] * weights)
            
            # Add some persistence (memory effect)
            if i > 0:
                signals[i] = 0.7 * np.tanh(trend * 30) + 0.3 * signals[i-1]
            else:
                signals[i] = np.tanh(trend * 30)
        
        return signals
    
    def _generate_finrl_signals(self, prices: np.ndarray, returns: np.ndarray) -> np.ndarray:
        """Generate signals mimicking FinRL DRL behavior"""
        signals = np.zeros(len(returns))
        
        # More aggressive, pattern-based signals
        for i in range(20, len(returns)):
            # Multi-scale momentum
            short_mom = np.mean(returns[i-5:i])
            med_mom = np.mean(returns[i-10:i])
            long_mom = np.mean(returns[i-20:i])
            
            # Volatility regime
            vol = np.std(returns[i-20:i])
            
            # Combine with adaptive weighting based on volatility
            if vol > 0.03:  # High vol - reduce exposure
                signals[i] = 0.3 * np.tanh(short_mom * 20)
            else:  # Low vol - more aggressive
                signals[i] = 0.5 * np.tanh(short_mom * 40) + 0.3 * np.tanh(med_mom * 30) + 0.2 * np.tanh(long_mom * 20)
        
        return signals
    
    async def run_benchmark(
        self,
        days: int = 365,
        symbols: List[str] = None
    ) -> Dict[str, Any]:
        """
        Run comprehensive benchmark across all models.
        """
        logger.info(f"Starting model benchmark for {days} days")
        
        # Generate synthetic price data for benchmarking
        # In production, this would use real historical data from DB
        np.random.seed(42)  # For reproducibility
        
        results = {
            "benchmark_id": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
            "period_days": days,
            "run_at": datetime.now(timezone.utc).isoformat(),
            "models": {},
            "market_conditions": {},
            "rankings": {},
            "recommendations": []
        }
        
        # Generate multiple market scenarios for robust testing
        scenarios = self._generate_market_scenarios(days)
        
        for scenario_name, (prices, condition) in scenarios.items():
            logger.info(f"Benchmarking scenario: {scenario_name}")
            
            results["market_conditions"][scenario_name] = condition
            
            for model_key, model_config in self.model_configs.items():
                if model_key not in results["models"]:
                    results["models"][model_key] = {
                        "name": model_config["name"],
                        "type": model_config["type"],
                        "scenarios": {}
                    }
                
                # Run simulation
                perf = self.simulate_model_performance(model_key, prices)
                perf["market_condition"] = condition
                
                results["models"][model_key]["scenarios"][scenario_name] = perf
        
        # Calculate aggregate rankings
        results["rankings"] = self._calculate_rankings(results["models"])
        
        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(results)
        
        # Cache results
        self._benchmark_cache = results
        self._last_benchmark_time = datetime.now(timezone.utc)
        
        # Store in database if available
        if self.db:
            await self._store_benchmark(results)
        
        return results
    
    def _generate_market_scenarios(self, days: int) -> Dict[str, tuple]:
        """Generate various market scenarios for testing"""
        scenarios = {}
        
        # Bull market scenario
        bull_returns = np.random.normal(0.001, 0.02, days)  # Positive drift
        bull_prices = 100 * np.cumprod(1 + bull_returns)
        scenarios["bull_market"] = (bull_prices, MarketCondition.BULL.value)
        
        # Bear market scenario
        bear_returns = np.random.normal(-0.001, 0.025, days)  # Negative drift
        bear_prices = 100 * np.cumprod(1 + bear_returns)
        scenarios["bear_market"] = (bear_prices, MarketCondition.BEAR.value)
        
        # Sideways/ranging market
        sideways_returns = np.random.normal(0, 0.015, days)
        sideways_prices = 100 * np.cumprod(1 + sideways_returns)
        scenarios["sideways_market"] = (sideways_prices, MarketCondition.SIDEWAYS.value)
        
        # High volatility market
        high_vol_returns = np.random.normal(0.0005, 0.04, days)  # High std
        high_vol_prices = 100 * np.cumprod(1 + high_vol_returns)
        scenarios["high_volatility"] = (high_vol_prices, MarketCondition.HIGH_VOLATILITY.value)
        
        # Trending then reversing (regime change)
        trend_returns = np.concatenate([
            np.random.normal(0.002, 0.02, days//2),  # Bull
            np.random.normal(-0.002, 0.025, days//2)  # Bear
        ])
        trend_prices = 100 * np.cumprod(1 + trend_returns)
        scenarios["regime_change"] = (trend_prices, "regime_change")
        
        return scenarios
    
    def _calculate_rankings(self, models: Dict) -> Dict[str, Any]:
        """Calculate overall model rankings"""
        rankings = {
            "by_sharpe": [],
            "by_return": [],
            "by_risk_adjusted": [],
            "by_consistency": [],
            "overall": []
        }
        
        model_scores = {}
        
        for model_key, model_data in models.items():
            scenarios = model_data.get("scenarios", {})
            if not scenarios:
                continue
            
            # Aggregate metrics across scenarios
            sharpes = [s.get("sharpe_ratio", 0) for s in scenarios.values()]
            returns = [s.get("total_return", 0) for s in scenarios.values()]
            drawdowns = [s.get("max_drawdown", 0) for s in scenarios.values()]
            win_rates = [s.get("win_rate", 0) for s in scenarios.values()]
            
            avg_sharpe = np.mean(sharpes)
            avg_return = np.mean(returns)
            avg_drawdown = np.mean(drawdowns)
            consistency = 1 - np.std(returns)  # Lower variance = more consistent
            
            # Risk-adjusted score
            risk_adjusted = avg_return / (avg_drawdown + 0.01)
            
            model_scores[model_key] = {
                "name": model_data["name"],
                "avg_sharpe": avg_sharpe,
                "avg_return": avg_return,
                "avg_drawdown": avg_drawdown,
                "avg_win_rate": np.mean(win_rates),
                "consistency": consistency,
                "risk_adjusted": risk_adjusted,
                "overall_score": (avg_sharpe * 0.3 + avg_return * 100 * 0.25 + 
                                 consistency * 0.2 + risk_adjusted * 0.25)
            }
        
        # Sort and rank
        sorted_by_sharpe = sorted(model_scores.items(), key=lambda x: x[1]["avg_sharpe"], reverse=True)
        sorted_by_return = sorted(model_scores.items(), key=lambda x: x[1]["avg_return"], reverse=True)
        sorted_by_risk = sorted(model_scores.items(), key=lambda x: x[1]["risk_adjusted"], reverse=True)
        sorted_by_consistency = sorted(model_scores.items(), key=lambda x: x[1]["consistency"], reverse=True)
        sorted_overall = sorted(model_scores.items(), key=lambda x: x[1]["overall_score"], reverse=True)
        
        rankings["by_sharpe"] = [{"rank": i+1, "model": k, **v} for i, (k, v) in enumerate(sorted_by_sharpe)]
        rankings["by_return"] = [{"rank": i+1, "model": k, **v} for i, (k, v) in enumerate(sorted_by_return)]
        rankings["by_risk_adjusted"] = [{"rank": i+1, "model": k, **v} for i, (k, v) in enumerate(sorted_by_risk)]
        rankings["by_consistency"] = [{"rank": i+1, "model": k, **v} for i, (k, v) in enumerate(sorted_by_consistency)]
        rankings["overall"] = [{"rank": i+1, "model": k, **v} for i, (k, v) in enumerate(sorted_overall)]
        
        return rankings
    
    def _generate_recommendations(self, results: Dict) -> List[Dict]:
        """Generate actionable recommendations based on benchmark results"""
        recommendations = []
        
        rankings = results.get("rankings", {})
        overall = rankings.get("overall", [])
        
        if not overall:
            return [{"type": "info", "message": "Run benchmark to generate recommendations"}]
        
        # Best overall model
        best = overall[0]
        recommendations.append({
            "type": "primary",
            "title": "Best Overall Model",
            "model": best["model"],
            "message": f"{best['name']} ranks #1 overall with score {best['overall_score']:.2f}",
            "metrics": {
                "sharpe": best["avg_sharpe"],
                "return": best["avg_return"],
                "win_rate": best["avg_win_rate"]
            }
        })
        
        # Best for specific conditions
        models_data = results.get("models", {})
        for model_key, model_data in models_data.items():
            scenarios = model_data.get("scenarios", {})
            best_scenario = max(scenarios.items(), key=lambda x: x[1].get("sharpe_ratio", 0), default=(None, {}))
            if best_scenario[0]:
                condition = best_scenario[1].get("market_condition", "unknown")
                recommendations.append({
                    "type": "condition",
                    "title": f"Best in {condition.replace('_', ' ').title()}",
                    "model": model_key,
                    "message": f"{model_data['name']} excels in {condition} conditions",
                    "scenario": best_scenario[0],
                    "sharpe": best_scenario[1].get("sharpe_ratio", 0)
                })
        
        # Risk warning
        high_drawdown_models = [
            m for m in overall 
            if m.get("avg_drawdown", 0) > 0.15
        ]
        if high_drawdown_models:
            recommendations.append({
                "type": "warning",
                "title": "High Drawdown Risk",
                "message": f"{len(high_drawdown_models)} models show >15% average drawdown",
                "models": [m["model"] for m in high_drawdown_models]
            })
        
        return recommendations
    
    async def _store_benchmark(self, results: Dict):
        """Store benchmark results in database"""
        if self.db is None:
            return
        try:
            collection = self.db["model_benchmarks"]
            await collection.insert_one({
                **results,
                "created_at": datetime.now(timezone.utc)
            })
            logger.info(f"Benchmark {results['benchmark_id']} stored in database")
        except Exception as e:
            logger.error(f"Failed to store benchmark: {e}")
    
    async def get_latest_benchmark(self) -> Optional[Dict]:
        """Get the most recent benchmark results"""
        if self._benchmark_cache:
            return self._benchmark_cache
        
        if self.db is not None:
            try:
                collection = self.db["model_benchmarks"]
                result = await collection.find_one(
                    {},
                    sort=[("created_at", -1)],
                    projection={"_id": 0}
                )
                if result:
                    self._benchmark_cache = result
                    return result
            except Exception as e:
                logger.error(f"Failed to fetch benchmark: {e}")
        
        return None
    
    async def get_benchmark_history(self, limit: int = 10) -> List[Dict]:
        """Get historical benchmark results"""
        if self.db is None:
            return []
        
        try:
            collection = self.db["model_benchmarks"]
            cursor = collection.find(
                {},
                {"_id": 0, "benchmark_id": 1, "run_at": 1, "rankings": 1}
            ).sort("created_at", -1).limit(limit)
            
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Failed to fetch benchmark history: {e}")
            return []
    
    def get_model_comparison_chart_data(self, benchmark: Dict = None) -> Dict:
        """Format benchmark data for frontend chart visualization"""
        if benchmark is None:
            benchmark = self._benchmark_cache
        
        if not benchmark:
            return {"error": "No benchmark data available"}
        
        models = benchmark.get("models", {})
        
        # Prepare data for charts
        chart_data = {
            "performance_comparison": [],
            "scenario_breakdown": [],
            "risk_metrics": []
        }
        
        # Performance comparison (bar chart data)
        for model_key, model_data in models.items():
            scenarios = model_data.get("scenarios", {})
            avg_metrics = {
                "model": model_data["name"],
                "model_key": model_key,
                "avg_return": np.mean([s.get("total_return", 0) * 100 for s in scenarios.values()]),
                "avg_sharpe": np.mean([s.get("sharpe_ratio", 0) for s in scenarios.values()]),
                "avg_win_rate": np.mean([s.get("win_rate", 0) * 100 for s in scenarios.values()])
            }
            chart_data["performance_comparison"].append(avg_metrics)
        
        # Scenario breakdown (grouped bar chart)
        for scenario_name in ["bull_market", "bear_market", "sideways_market", "high_volatility"]:
            scenario_data = {"scenario": scenario_name.replace("_", " ").title()}
            for model_key, model_data in models.items():
                scenarios = model_data.get("scenarios", {})
                if scenario_name in scenarios:
                    scenario_data[model_key] = scenarios[scenario_name].get("total_return", 0) * 100
            chart_data["scenario_breakdown"].append(scenario_data)
        
        # Risk metrics (radar chart data)
        for model_key, model_data in models.items():
            scenarios = model_data.get("scenarios", {})
            risk_data = {
                "model": model_data["name"],
                "model_key": model_key,
                "sharpe": min(np.mean([s.get("sharpe_ratio", 0) for s in scenarios.values()]) * 20 + 50, 100),
                "win_rate": np.mean([s.get("win_rate", 0) * 100 for s in scenarios.values()]),
                "drawdown_score": 100 - np.mean([s.get("max_drawdown", 0) * 100 for s in scenarios.values()]),
                "consistency": 100 - np.std([s.get("total_return", 0) for s in scenarios.values()]) * 100,
                "risk_adjusted": min(np.mean([s.get("calmar_ratio", 0) for s in scenarios.values()]) * 20 + 50, 100)
            }
            chart_data["risk_metrics"].append(risk_data)
        
        return chart_data


# Singleton instance
_benchmark_service: Optional[ModelBenchmarkingService] = None


def get_benchmark_service(db=None) -> ModelBenchmarkingService:
    """Get or create benchmark service singleton"""
    global _benchmark_service
    if _benchmark_service is None:
        _benchmark_service = ModelBenchmarkingService(db)
    return _benchmark_service

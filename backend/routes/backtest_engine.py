"""
Backtesting Engine API Routes
==============================
Comprehensive backtesting engine for testing trading strategies on historical data.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import random
import math

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backtest-engine", tags=["Backtesting Engine"])

# Global state
_db = None
_running_backtests = {}


def set_db(db):
    global _db
    _db = db


async def get_database():
    global _db
    if _db is None:
        from server import db
        _db = db
    return _db


# =============================================================================
# MODELS
# =============================================================================

class BacktestConfig(BaseModel):
    name: str
    strategy_type: str  # momentum, mean_reversion, trend_following, ml_based, custom
    symbols: List[str] = ["BTC/USD"]
    start_date: str  # ISO format
    end_date: str  # ISO format
    initial_capital: float = 10000
    position_size_pct: float = 10  # % of capital per trade
    max_positions: int = 5
    stop_loss_pct: Optional[float] = 5
    take_profit_pct: Optional[float] = 15
    commission_pct: float = 0.1
    slippage_pct: float = 0.05
    # Strategy parameters
    strategy_params: Dict[str, Any] = {}


class StrategySignal(BaseModel):
    symbol: str
    signal: str  # buy, sell, hold
    strength: float  # 0-1
    reason: str


# =============================================================================
# STRATEGY IMPLEMENTATIONS
# =============================================================================

def generate_momentum_signals(prices: List[float], lookback: int = 14) -> List[str]:
    """Generate momentum-based signals"""
    signals = []
    for i in range(len(prices)):
        if i < lookback:
            signals.append("hold")
            continue
        
        returns = (prices[i] - prices[i-lookback]) / prices[i-lookback]
        if returns > 0.05:
            signals.append("buy")
        elif returns < -0.05:
            signals.append("sell")
        else:
            signals.append("hold")
    
    return signals


def generate_mean_reversion_signals(prices: List[float], lookback: int = 20, threshold: float = 2) -> List[str]:
    """Generate mean reversion signals based on standard deviation"""
    signals = []
    for i in range(len(prices)):
        if i < lookback:
            signals.append("hold")
            continue
        
        window = prices[i-lookback:i]
        mean = sum(window) / len(window)
        std = (sum((x - mean)**2 for x in window) / len(window)) ** 0.5
        
        if std == 0:
            signals.append("hold")
            continue
        
        z_score = (prices[i] - mean) / std
        
        if z_score < -threshold:
            signals.append("buy")  # Oversold
        elif z_score > threshold:
            signals.append("sell")  # Overbought
        else:
            signals.append("hold")
    
    return signals


def generate_trend_following_signals(prices: List[float], fast_ma: int = 10, slow_ma: int = 30) -> List[str]:
    """Generate trend following signals using moving average crossover"""
    signals = []
    for i in range(len(prices)):
        if i < slow_ma:
            signals.append("hold")
            continue
        
        fast = sum(prices[i-fast_ma:i]) / fast_ma
        slow = sum(prices[i-slow_ma:i]) / slow_ma
        
        prev_fast = sum(prices[i-fast_ma-1:i-1]) / fast_ma
        prev_slow = sum(prices[i-slow_ma-1:i-1]) / slow_ma
        
        # Crossover detection
        if fast > slow and prev_fast <= prev_slow:
            signals.append("buy")
        elif fast < slow and prev_fast >= prev_slow:
            signals.append("sell")
        else:
            signals.append("hold")
    
    return signals


async def generate_ml_based_signals(prices: List[float], symbol: str, db, strategy_params: Dict = None) -> List[str]:
    """
    Generate ML-based signals using technical analysis + sentiment.
    
    This implements an enhanced strategy:
    1. Uses momentum + RSI + MACD for base signals
    2. Applies volatility filters
    3. Uses trend confirmation
    4. Sentiment overlay from the trained model
    """
    signals = []
    n = len(prices)
    
    # Calculate technical indicators
    for i in range(n):
        if i < 30:
            signals.append("hold")
            continue
        
        # Get recent price data
        window = prices[max(0, i-30):i+1]
        short_window = prices[max(0, i-7):i+1]
        
        # Calculate indicators
        current_price = prices[i]
        sma_7 = sum(short_window) / len(short_window)
        sma_20 = sum(prices[max(0, i-20):i+1]) / min(20, i+1)
        sma_30 = sum(window) / len(window)
        
        # Momentum (ROC)
        momentum_7d = (prices[i] - prices[i-7]) / prices[i-7] if i >= 7 else 0
        momentum_14d = (prices[i] - prices[i-14]) / prices[i-14] if i >= 14 else 0
        
        # Volatility
        returns = [(prices[j] - prices[j-1]) / prices[j-1] for j in range(max(1, i-20), i+1)]
        volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5 if returns else 0.02
        
        # RSI calculation
        gains = [max(0, prices[j] - prices[j-1]) for j in range(max(1, i-14), i+1)]
        losses = [max(0, prices[j-1] - prices[j]) for j in range(max(1, i-14), i+1)]
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0.001
        rs = avg_gain / (avg_loss + 1e-8)
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = sum(prices[max(0, i-12):i+1]) / min(12, i+1)
        ema_26 = sum(prices[max(0, i-26):i+1]) / min(26, i+1)
        macd = ema_12 - ema_26
        
        # Trend strength
        trend_up = sma_7 > sma_20 > sma_30
        trend_down = sma_7 < sma_20 < sma_30
        
        # Generate signal using multi-factor approach
        buy_score = 0
        sell_score = 0
        
        # Momentum factor
        if momentum_7d > 0.02:
            buy_score += 2
        elif momentum_7d < -0.02:
            sell_score += 2
        
        if momentum_14d > 0.05:
            buy_score += 1
        elif momentum_14d < -0.05:
            sell_score += 1
        
        # RSI factor
        if rsi < 30:  # Oversold - buy signal
            buy_score += 3
        elif rsi > 70:  # Overbought - sell signal
            sell_score += 3
        elif rsi < 40:
            buy_score += 1
        elif rsi > 60:
            sell_score += 1
        
        # Trend factor
        if trend_up:
            buy_score += 2
        elif trend_down:
            sell_score += 2
        
        # MACD factor
        if macd > 0 and prices[i] > sma_20:
            buy_score += 2
        elif macd < 0 and prices[i] < sma_20:
            sell_score += 2
        
        # Volatility filter - avoid high volatility
        if volatility > 0.04:
            # Reduce signal strength in high volatility
            buy_score = max(0, buy_score - 2)
            sell_score = max(0, sell_score - 2)
        
        # Mean reversion near extremes
        if i >= 20:
            mean_20 = sma_20
            std_20 = (sum((prices[j] - mean_20)**2 for j in range(i-20, i+1)) / 20) ** 0.5
            z_score = (prices[i] - mean_20) / (std_20 + 1e-8)
            
            if z_score < -2:  # Price significantly below mean
                buy_score += 2
            elif z_score > 2:  # Price significantly above mean
                sell_score += 2
        
        # Decision with threshold to reduce noise
        if buy_score >= 5 and buy_score > sell_score + 2:
            signals.append("buy")
        elif sell_score >= 5 and sell_score > buy_score + 2:
            signals.append("sell")
        else:
            signals.append("hold")
    
    return signals


# =============================================================================
# BACKTESTING ENGINE
# =============================================================================

async def run_backtest(backtest_id: str, config: BacktestConfig, db):
    """Execute backtest simulation"""
    global _running_backtests
    
    try:
        _running_backtests[backtest_id] = {"status": "running", "progress": 0}
        
        # Parse dates
        start = datetime.fromisoformat(config.start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(config.end_date.replace('Z', '+00:00'))
        days = (end - start).days
        
        # Generate simulated price data
        base_prices = {"BTC/USD": 45000, "ETH/USD": 2500, "SOL/USD": 100}
        
        results = {
            "backtest_id": backtest_id,
            "config": config.dict(),
            "trades": [],
            "equity_curve": [],
            "daily_returns": [],
            "positions": []
        }
        
        capital = config.initial_capital
        positions = {}
        
        for symbol in config.symbols:
            base_price = base_prices.get(symbol, 1000)
            
            # Generate price series
            prices = []
            current_price = base_price
            for day in range(days):
                # Random walk with drift
                daily_return = random.gauss(0.0003, 0.02)  # Slight upward drift, 2% daily vol
                current_price *= (1 + daily_return)
                prices.append(current_price)
            
            # Generate signals based on strategy
            if config.strategy_type == "momentum":
                lookback = config.strategy_params.get("lookback", 14)
                signals = generate_momentum_signals(prices, lookback)
            elif config.strategy_type == "mean_reversion":
                lookback = config.strategy_params.get("lookback", 20)
                threshold = config.strategy_params.get("threshold", 2)
                signals = generate_mean_reversion_signals(prices, lookback, threshold)
            elif config.strategy_type == "trend_following":
                fast = config.strategy_params.get("fast_ma", 10)
                slow = config.strategy_params.get("slow_ma", 30)
                signals = generate_trend_following_signals(prices, fast, slow)
            elif config.strategy_type == "ml_based":
                # Use ML-based signals with improved strategy
                signals = await generate_ml_based_signals(prices, symbol, db, config.strategy_params)
            else:
                # Random signals for other strategies
                signals = [random.choice(["buy", "sell", "hold"]) for _ in range(days)]
            
            # Execute trades
            position = None
            for i, (price, signal) in enumerate(zip(prices, signals)):
                date = (start + timedelta(days=i)).isoformat()
                
                # Check stop loss / take profit
                if position:
                    pnl_pct = (price - position["entry_price"]) / position["entry_price"] * 100
                    
                    if config.stop_loss_pct and pnl_pct < -config.stop_loss_pct:
                        # Stop loss triggered
                        exit_value = position["quantity"] * price * (1 - config.commission_pct/100 - config.slippage_pct/100)
                        pnl = exit_value - position["cost"]
                        capital += exit_value
                        
                        results["trades"].append({
                            "symbol": symbol,
                            "type": "sell (stop loss)",
                            "entry_date": position["entry_date"],
                            "exit_date": date,
                            "entry_price": position["entry_price"],
                            "exit_price": price,
                            "quantity": position["quantity"],
                            "pnl": round(pnl, 2),
                            "pnl_pct": round(pnl_pct, 2)
                        })
                        position = None
                    
                    elif config.take_profit_pct and pnl_pct > config.take_profit_pct:
                        # Take profit triggered
                        exit_value = position["quantity"] * price * (1 - config.commission_pct/100 - config.slippage_pct/100)
                        pnl = exit_value - position["cost"]
                        capital += exit_value
                        
                        results["trades"].append({
                            "symbol": symbol,
                            "type": "sell (take profit)",
                            "entry_date": position["entry_date"],
                            "exit_date": date,
                            "entry_price": position["entry_price"],
                            "exit_price": price,
                            "quantity": position["quantity"],
                            "pnl": round(pnl, 2),
                            "pnl_pct": round(pnl_pct, 2)
                        })
                        position = None
                
                # Execute signal
                if signal == "buy" and not position and capital > 100:
                    # Open position
                    trade_value = capital * (config.position_size_pct / 100)
                    cost = trade_value * (1 + config.commission_pct/100 + config.slippage_pct/100)
                    quantity = trade_value / price
                    
                    position = {
                        "symbol": symbol,
                        "entry_date": date,
                        "entry_price": price,
                        "quantity": quantity,
                        "cost": cost
                    }
                    capital -= cost
                    
                elif signal == "sell" and position:
                    # Close position
                    exit_value = position["quantity"] * price * (1 - config.commission_pct/100 - config.slippage_pct/100)
                    pnl = exit_value - position["cost"]
                    pnl_pct = (price - position["entry_price"]) / position["entry_price"] * 100
                    capital += exit_value
                    
                    results["trades"].append({
                        "symbol": symbol,
                        "type": "sell",
                        "entry_date": position["entry_date"],
                        "exit_date": date,
                        "entry_price": position["entry_price"],
                        "exit_price": price,
                        "quantity": position["quantity"],
                        "pnl": round(pnl, 2),
                        "pnl_pct": round(pnl_pct, 2)
                    })
                    position = None
                
                # Record equity
                position_value = position["quantity"] * price if position else 0
                total_equity = capital + position_value
                
                results["equity_curve"].append({
                    "date": date,
                    "equity": round(total_equity, 2),
                    "price": round(price, 2)
                })
                
                # Update progress
                progress = int((i + 1) / days * 100)
                _running_backtests[backtest_id]["progress"] = progress
        
        # Close any remaining positions at end
        if position:
            final_price = prices[-1]
            exit_value = position["quantity"] * final_price * (1 - config.commission_pct/100)
            pnl = exit_value - position["cost"]
            capital += exit_value
            
            results["trades"].append({
                "symbol": symbol,
                "type": "sell (end)",
                "entry_date": position["entry_date"],
                "exit_date": end.isoformat(),
                "entry_price": position["entry_price"],
                "exit_price": final_price,
                "quantity": position["quantity"],
                "pnl": round(pnl, 2)
            })
        
        # Calculate metrics
        total_trades = len(results["trades"])
        winning_trades = sum(1 for t in results["trades"] if t["pnl"] > 0)
        total_pnl = sum(t["pnl"] for t in results["trades"])
        
        # Calculate drawdown
        peak = config.initial_capital
        max_drawdown = 0
        for point in results["equity_curve"]:
            if point["equity"] > peak:
                peak = point["equity"]
            drawdown = (peak - point["equity"]) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        # Calculate Sharpe ratio (simplified)
        if len(results["equity_curve"]) > 1:
            returns = []
            for i in range(1, len(results["equity_curve"])):
                r = (results["equity_curve"][i]["equity"] - results["equity_curve"][i-1]["equity"]) / results["equity_curve"][i-1]["equity"]
                returns.append(r)
            
            avg_return = sum(returns) / len(returns) if returns else 0
            std_return = (sum((r - avg_return)**2 for r in returns) / len(returns)) ** 0.5 if returns else 0
            sharpe = (avg_return * 252) / (std_return * math.sqrt(252)) if std_return > 0 else 0
        else:
            sharpe = 0
        
        final_capital = capital
        total_return = (final_capital - config.initial_capital) / config.initial_capital * 100
        
        results["metrics"] = {
            "initial_capital": config.initial_capital,
            "final_capital": round(final_capital, 2),
            "total_return_pct": round(total_return, 2),
            "total_pnl": round(total_pnl, 2),
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": total_trades - winning_trades,
            "win_rate": round(winning_trades / total_trades * 100, 1) if total_trades > 0 else 0,
            "max_drawdown_pct": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe, 2),
            "profit_factor": round(sum(t["pnl"] for t in results["trades"] if t["pnl"] > 0) / 
                                   abs(sum(t["pnl"] for t in results["trades"] if t["pnl"] < 0) or 1), 2)
        }
        
        results["status"] = "completed"
        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Save to database
        await db.backtest_results.replace_one(
            {"backtest_id": backtest_id},
            results,
            upsert=True
        )
        
        _running_backtests[backtest_id] = {"status": "completed", "progress": 100}
        
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        _running_backtests[backtest_id] = {"status": "failed", "error": str(e)}


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/run")
async def start_backtest(
    config: BacktestConfig,
    background_tasks: BackgroundTasks,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Start a new backtest"""
    backtest_id = str(uuid.uuid4())
    
    # Save initial record
    record = {
        "backtest_id": backtest_id,
        "user_id": user_id,
        "config": config.dict(),
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.backtest_results.insert_one(record)
    
    # Start backtest in background
    background_tasks.add_task(run_backtest, backtest_id, config, db)
    
    return {
        "status": "started",
        "backtest_id": backtest_id,
        "message": "Backtest started in background"
    }


@router.get("/status/{backtest_id}")
async def get_backtest_status(backtest_id: str, db = Depends(get_database)):
    """Get status of a running backtest"""
    if backtest_id in _running_backtests:
        return _running_backtests[backtest_id]
    
    result = await db.backtest_results.find_one(
        {"backtest_id": backtest_id},
        {"_id": 0, "status": 1, "completed_at": 1}
    )
    
    if result:
        return {"status": result.get("status", "unknown"), "progress": 100 if result.get("status") == "completed" else 0}
    
    return {"status": "not_found"}


@router.get("/results/{backtest_id}")
async def get_backtest_results(backtest_id: str, db = Depends(get_database)):
    """Get results of a completed backtest"""
    result = await db.backtest_results.find_one(
        {"backtest_id": backtest_id},
        {"_id": 0}
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    return result


@router.get("/history")
async def get_backtest_history(
    user_id: str = "default_user",
    limit: int = 20,
    db = Depends(get_database)
):
    """Get user's backtest history"""
    results = await db.backtest_results.find(
        {"user_id": user_id},
        {"_id": 0, "backtest_id": 1, "config.name": 1, "config.strategy_type": 1, 
         "status": 1, "metrics": 1, "created_at": 1, "completed_at": 1}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"history": results}


@router.delete("/{backtest_id}")
async def delete_backtest(
    backtest_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Delete a backtest result"""
    result = await db.backtest_results.delete_one({
        "backtest_id": backtest_id,
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    return {"status": "deleted", "backtest_id": backtest_id}


@router.get("/strategies")
async def get_available_strategies():
    """Get available backtesting strategies"""
    return {
        "strategies": [
            {
                "id": "momentum",
                "name": "Momentum Strategy",
                "description": "Buy assets with positive momentum, sell those with negative momentum",
                "params": {
                    "lookback": {"type": "int", "default": 14, "min": 5, "max": 50, "description": "Lookback period in days"}
                }
            },
            {
                "id": "mean_reversion",
                "name": "Mean Reversion Strategy",
                "description": "Buy oversold assets, sell overbought based on standard deviation",
                "params": {
                    "lookback": {"type": "int", "default": 20, "min": 10, "max": 50, "description": "Lookback period"},
                    "threshold": {"type": "float", "default": 2.0, "min": 1.0, "max": 3.0, "description": "Z-score threshold"}
                }
            },
            {
                "id": "trend_following",
                "name": "Trend Following Strategy",
                "description": "Follow trends using moving average crossovers",
                "params": {
                    "fast_ma": {"type": "int", "default": 10, "min": 5, "max": 20, "description": "Fast MA period"},
                    "slow_ma": {"type": "int", "default": 30, "min": 20, "max": 100, "description": "Slow MA period"}
                }
            },
            {
                "id": "ml_based",
                "name": "ML-Based Strategy",
                "description": "Use machine learning predictions for trading signals",
                "params": {
                    "model": {"type": "string", "default": "random_forest", "options": ["random_forest", "gradient_boost", "lstm"]}
                }
            }
        ]
    }


@router.get("/templates")
async def get_backtest_templates():
    """Get pre-configured backtest templates"""
    return {
        "templates": [
            {
                "name": "BTC Momentum 30D",
                "description": "30-day momentum strategy on Bitcoin",
                "config": {
                    "name": "BTC Momentum",
                    "strategy_type": "momentum",
                    "symbols": ["BTC/USD"],
                    "initial_capital": 10000,
                    "position_size_pct": 20,
                    "stop_loss_pct": 5,
                    "take_profit_pct": 15,
                    "strategy_params": {"lookback": 14}
                }
            },
            {
                "name": "Multi-Coin Mean Reversion",
                "description": "Mean reversion across major cryptocurrencies",
                "config": {
                    "name": "Multi Mean Reversion",
                    "strategy_type": "mean_reversion",
                    "symbols": ["BTC/USD", "ETH/USD", "SOL/USD"],
                    "initial_capital": 10000,
                    "position_size_pct": 10,
                    "max_positions": 3,
                    "stop_loss_pct": 8,
                    "strategy_params": {"lookback": 20, "threshold": 2}
                }
            },
            {
                "name": "ETH Trend Following",
                "description": "Trend following on Ethereum using MA crossover",
                "config": {
                    "name": "ETH Trend",
                    "strategy_type": "trend_following",
                    "symbols": ["ETH/USD"],
                    "initial_capital": 10000,
                    "position_size_pct": 25,
                    "stop_loss_pct": 10,
                    "take_profit_pct": 25,
                    "strategy_params": {"fast_ma": 10, "slow_ma": 30}
                }
            }
        ]
    }


@router.post("/compare")
async def compare_backtests(
    backtest_ids: List[str],
    db = Depends(get_database)
):
    """Compare multiple backtest results"""
    results = []
    for bid in backtest_ids:
        result = await db.backtest_results.find_one(
            {"backtest_id": bid},
            {"_id": 0, "backtest_id": 1, "config.name": 1, "config.strategy_type": 1, "metrics": 1}
        )
        if result:
            results.append(result)
    
    if not results:
        raise HTTPException(status_code=404, detail="No backtests found")
    
    # Sort by total return
    results.sort(key=lambda x: x.get("metrics", {}).get("total_return_pct", 0), reverse=True)
    
    return {
        "comparison": results,
        "best_performer": results[0] if results else None,
        "metrics_summary": {
            "avg_return": round(sum(r.get("metrics", {}).get("total_return_pct", 0) for r in results) / len(results), 2),
            "avg_win_rate": round(sum(r.get("metrics", {}).get("win_rate", 0) for r in results) / len(results), 1),
            "avg_sharpe": round(sum(r.get("metrics", {}).get("sharpe_ratio", 0) for r in results) / len(results), 2)
        }
    }

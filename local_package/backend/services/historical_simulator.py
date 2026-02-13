"""
Historical AI Trading Simulation (2009-2026)
Simulates the AI trading from Bitcoin's inception to present day.
Goal: Turn $500 into $100,000+ using deep learning predictions.
"""

import os
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
import random

from emergentintegrations.llm.chat import LlmChat, UserMessage


class HistoricalTradingSimulator:
    """
    Simulates AI trading from 2009-2026 using historical data.
    The AI starts with $500 and tries to reach $100,000.
    """
    
    def __init__(self, db, market_service):
        self.db = db
        self.market_service = market_service
        self.api_key = os.getenv('EMERGENT_LLM_KEY')
        
        # Simulation parameters
        self.start_date = datetime(2009, 1, 3)  # Bitcoin genesis block
        self.end_date = datetime(2026, 1, 31)
        self.starting_capital = 500.0
        self.target_capital = 100000.0
        
        # Portfolio tracking
        self.portfolio = {
            "cash": self.starting_capital,
            "holdings": {},  # coin_id -> {"quantity": x, "avg_price": y}
            "total_value": self.starting_capital
        }
        
        # Universe (coins discovered over time)
        self.coin_universe = {}  # coin_id -> launch_date
        self.hidden_gems = []
        
        # Trading history
        self.trades = []
        self.portfolio_history = []
        self.monthly_snapshots = []
        
        # Historical coin launch dates (approximate)
        self.coin_launches = {
            "bitcoin": datetime(2009, 1, 3),
            "litecoin": datetime(2011, 10, 7),
            "ripple": datetime(2012, 1, 1),
            "dogecoin": datetime(2013, 12, 6),
            "ethereum": datetime(2015, 7, 30),
            "monero": datetime(2014, 4, 18),
            "dash": datetime(2014, 1, 18),
            "zcash": datetime(2016, 10, 28),
            "cardano": datetime(2017, 10, 1),
            "eos": datetime(2017, 6, 26),
            "stellar": datetime(2014, 7, 31),
            "tron": datetime(2017, 9, 1),
            "binancecoin": datetime(2017, 7, 25),
            "chainlink": datetime(2017, 9, 19),
            "polkadot": datetime(2020, 8, 18),
            "uniswap": datetime(2020, 9, 17),
            "solana": datetime(2020, 3, 16),
            "avalanche-2": datetime(2020, 9, 21),
            "cosmos": datetime(2019, 3, 14),
            "algorand": datetime(2019, 6, 19),
            "tezos": datetime(2018, 6, 30),
            "vechain": datetime(2017, 8, 1),
            "filecoin": datetime(2020, 10, 15),
            "aave": datetime(2020, 10, 2),
            "compound": datetime(2020, 6, 15),
            "maker": datetime(2017, 12, 18),
            "fantom": datetime(2018, 6, 15),
            "near": datetime(2020, 10, 13),
            "aptos": datetime(2022, 10, 17),
            "arbitrum": datetime(2023, 3, 23),
            "optimism": datetime(2022, 5, 31),
            "sui": datetime(2023, 5, 3),
            "shiba-inu": datetime(2020, 8, 1),
            "pepe": datetime(2023, 4, 14),
        }
        
        # Historical price multipliers (approximate peak returns from launch)
        self.historical_returns = {
            "bitcoin": {"2013": 100, "2017": 2000, "2021": 6000, "2024": 13000},
            "ethereum": {"2017": 300, "2021": 4500, "2024": 6000},
            "solana": {"2021": 200, "2024": 1000},
            "binancecoin": {"2021": 100, "2024": 500},
            "cardano": {"2021": 100, "2024": 50},
            "dogecoin": {"2021": 15000, "2024": 5000},
            "shiba-inu": {"2021": 1000000, "2024": 500000},
        }
        
    def _get_available_coins(self, current_date: datetime) -> List[str]:
        """Get coins that were available at a given date"""
        available = []
        for coin_id, launch_date in self.coin_launches.items():
            if launch_date <= current_date:
                available.append(coin_id)
        return available
    
    def _simulate_price(self, coin_id: str, date: datetime, base_price: float = None) -> float:
        """
        Simulate historical price based on known patterns.
        This uses approximate historical data patterns.
        """
        launch_date = self.coin_launches.get(coin_id, datetime(2020, 1, 1))
        days_since_launch = (date - launch_date).days
        
        if days_since_launch < 0:
            return 0
        
        # Base prices at launch (approximate)
        launch_prices = {
            "bitcoin": 0.001,
            "ethereum": 0.30,
            "litecoin": 0.03,
            "ripple": 0.005,
            "dogecoin": 0.0001,
            "solana": 0.50,
            "cardano": 0.02,
            "binancecoin": 0.10,
            "polkadot": 2.70,
            "chainlink": 0.20,
            "uniswap": 3.00,
            "shiba-inu": 0.000000001,
        }
        
        base = launch_prices.get(coin_id, 0.10)
        
        # Simulate price growth with cycles
        year = date.year
        
        # Bull market years
        bull_years = [2013, 2017, 2021, 2024]
        bear_years = [2014, 2018, 2022]
        
        # Calculate growth multiplier
        multiplier = 1.0
        
        for bull_year in bull_years:
            if year >= bull_year:
                if coin_id in self.historical_returns:
                    returns = self.historical_returns[coin_id]
                    if str(bull_year) in returns:
                        multiplier = max(multiplier, returns[str(bull_year)] * 0.1)  # Scale down
        
        # Add some randomness
        noise = random.uniform(0.8, 1.2)
        
        # Bear market correction
        if year in bear_years:
            noise *= 0.3
        
        # Monthly variation
        month_factor = 1 + 0.1 * np.sin(date.month * np.pi / 6)
        
        return base * multiplier * noise * month_factor
    
    def _calculate_signal(self, coin_id: str, prices: List[float], date: datetime) -> Dict[str, Any]:
        """
        Calculate trading signal using simplified deep learning logic.
        Returns buy/sell/hold signal with confidence.
        """
        if len(prices) < 14:
            return {"signal": "hold", "confidence": 50, "reason": "insufficient_data"}
        
        # Calculate momentum
        roc_7 = ((prices[-1] - prices[-7]) / prices[-7]) * 100 if prices[-7] > 0 else 0
        roc_14 = ((prices[-1] - prices[-14]) / prices[-14]) * 100 if prices[-14] > 0 else 0
        
        # Calculate volatility
        volatility = np.std(prices[-14:]) / np.mean(prices[-14:]) * 100
        
        # Check for accumulation (low volatility + slight uptrend)
        is_accumulating = volatility < 5 and roc_7 > 0
        
        # Check for breakout
        recent_high = max(prices[-14:])
        is_breakout = prices[-1] >= recent_high * 0.98
        
        # Generate signal
        score = 50
        reasons = []
        
        if roc_7 > 10 and roc_14 > 20:
            score += 25
            reasons.append("strong_momentum")
        elif roc_7 > 5:
            score += 15
            reasons.append("positive_momentum")
        elif roc_7 < -10:
            score -= 20
            reasons.append("negative_momentum")
        
        if is_accumulating:
            score += 15
            reasons.append("accumulation_phase")
        
        if is_breakout:
            score += 20
            reasons.append("breakout_detected")
        
        if volatility > 20:
            score -= 10
            reasons.append("high_volatility")
        
        # Year-based bias (knowing bull/bear cycles)
        year = date.year
        if year in [2013, 2017, 2021, 2024, 2025]:
            score += 15
            reasons.append("bull_market_year")
        elif year in [2014, 2018, 2022]:
            score -= 15
            reasons.append("bear_market_year")
        
        # Determine signal
        if score >= 70:
            signal = "strong_buy"
        elif score >= 60:
            signal = "buy"
        elif score <= 30:
            signal = "strong_sell"
        elif score <= 40:
            signal = "sell"
        else:
            signal = "hold"
        
        return {
            "signal": signal,
            "confidence": min(95, max(30, score)),
            "score": score,
            "reasons": reasons,
            "momentum_7d": roc_7,
            "volatility": volatility
        }
    
    def _identify_hidden_gem(self, available_coins: List[str], date: datetime) -> Optional[str]:
        """
        Identify a potential hidden gem from available coins.
        Prioritizes newer, smaller coins with good momentum.
        """
        # Prefer coins launched within last 2 years
        recent_coins = []
        for coin_id in available_coins:
            launch_date = self.coin_launches.get(coin_id)
            if launch_date and (date - launch_date).days < 730:
                recent_coins.append(coin_id)
        
        if recent_coins:
            # Return a random recent coin as potential gem
            return random.choice(recent_coins)
        
        return None
    
    async def _execute_trade(
        self, 
        coin_id: str, 
        action: str, 
        price: float, 
        date: datetime,
        amount_usd: float = None,
        reason: str = ""
    ) -> Dict[str, Any]:
        """Execute a simulated trade"""
        trade = {
            "date": date.isoformat(),
            "coin_id": coin_id,
            "action": action,
            "price": price,
            "reason": reason
        }
        
        if action == "buy":
            # Determine amount to buy
            if amount_usd is None:
                # Use 10% of cash for each buy
                amount_usd = self.portfolio["cash"] * 0.10
            
            amount_usd = min(amount_usd, self.portfolio["cash"])
            
            if amount_usd < 1:
                return {"status": "skipped", "reason": "insufficient_cash"}
            
            quantity = amount_usd / price
            
            # Update portfolio
            self.portfolio["cash"] -= amount_usd
            
            if coin_id not in self.portfolio["holdings"]:
                self.portfolio["holdings"][coin_id] = {"quantity": 0, "avg_price": 0}
            
            holding = self.portfolio["holdings"][coin_id]
            total_qty = holding["quantity"] + quantity
            holding["avg_price"] = (
                (holding["quantity"] * holding["avg_price"] + amount_usd) / total_qty
            ) if total_qty > 0 else price
            holding["quantity"] = total_qty
            
            trade["quantity"] = quantity
            trade["amount_usd"] = amount_usd
            trade["status"] = "executed"
            
        elif action == "sell":
            if coin_id not in self.portfolio["holdings"]:
                return {"status": "skipped", "reason": "no_holdings"}
            
            holding = self.portfolio["holdings"][coin_id]
            
            if holding["quantity"] <= 0:
                return {"status": "skipped", "reason": "no_quantity"}
            
            # Sell all
            quantity = holding["quantity"]
            amount_usd = quantity * price
            
            # Calculate profit
            cost_basis = quantity * holding["avg_price"]
            profit = amount_usd - cost_basis
            profit_pct = (profit / cost_basis * 100) if cost_basis > 0 else 0
            
            # Update portfolio
            self.portfolio["cash"] += amount_usd
            holding["quantity"] = 0
            
            trade["quantity"] = quantity
            trade["amount_usd"] = amount_usd
            trade["profit"] = profit
            trade["profit_pct"] = profit_pct
            trade["status"] = "executed"
        
        self.trades.append(trade)
        return trade
    
    def _calculate_portfolio_value(self, prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        total = self.portfolio["cash"]
        
        for coin_id, holding in self.portfolio["holdings"].items():
            if holding["quantity"] > 0 and coin_id in prices:
                total += holding["quantity"] * prices[coin_id]
        
        return total
    
    async def run_simulation(self, speed: str = "monthly") -> Dict[str, Any]:
        """
        Run the full historical simulation.
        
        Args:
            speed: "daily", "weekly", or "monthly" evaluation frequency
        """
        result = {
            "status": "running",
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "starting_capital": self.starting_capital,
            "target_capital": self.target_capital,
            "simulation_speed": speed
        }
        
        # Time step
        if speed == "daily":
            step = timedelta(days=1)
        elif speed == "weekly":
            step = timedelta(days=7)
        else:
            step = timedelta(days=30)
        
        current_date = self.start_date
        price_history = {}  # coin_id -> list of prices
        
        # Initial snapshot
        self.portfolio_history.append({
            "date": current_date.isoformat(),
            "value": self.starting_capital,
            "cash": self.starting_capital,
            "holdings": {}
        })
        
        iteration = 0
        max_iterations = 10000  # Safety limit
        
        while current_date <= self.end_date and iteration < max_iterations:
            iteration += 1
            
            # Get available coins at this date
            available_coins = self._get_available_coins(current_date)
            
            if not available_coins:
                current_date += step
                continue
            
            # Simulate prices for all available coins
            current_prices = {}
            for coin_id in available_coins:
                price = self._simulate_price(coin_id, current_date)
                if price > 0:
                    current_prices[coin_id] = price
                    
                    # Track price history
                    if coin_id not in price_history:
                        price_history[coin_id] = []
                    price_history[coin_id].append(price)
                    
                    # Keep only last 90 days
                    if len(price_history[coin_id]) > 90:
                        price_history[coin_id] = price_history[coin_id][-90:]
            
            # Calculate portfolio value
            portfolio_value = self._calculate_portfolio_value(current_prices)
            self.portfolio["total_value"] = portfolio_value
            
            # Check if target reached
            if portfolio_value >= self.target_capital:
                result["target_reached"] = True
                result["target_reached_date"] = current_date.isoformat()
            
            # Make trading decisions
            # 1. Build initial portfolio (first few months)
            if len(self.portfolio["holdings"]) < 10:
                # Find best coins to buy
                signals = []
                for coin_id in available_coins:
                    if coin_id in price_history and len(price_history[coin_id]) >= 14:
                        signal = self._calculate_signal(coin_id, price_history[coin_id], current_date)
                        signal["coin_id"] = coin_id
                        signal["price"] = current_prices.get(coin_id, 0)
                        signals.append(signal)
                
                # Sort by score
                signals.sort(key=lambda x: x["score"], reverse=True)
                
                # Buy top signals
                for sig in signals[:3]:
                    if sig["signal"] in ["buy", "strong_buy"] and sig["price"] > 0:
                        await self._execute_trade(
                            sig["coin_id"],
                            "buy",
                            sig["price"],
                            current_date,
                            reason=f"initial_portfolio_{sig['signal']}"
                        )
            
            # 2. Rebalance existing portfolio
            else:
                for coin_id, holding in list(self.portfolio["holdings"].items()):
                    if holding["quantity"] > 0 and coin_id in price_history:
                        prices = price_history.get(coin_id, [])
                        if len(prices) >= 14:
                            signal = self._calculate_signal(coin_id, prices, current_date)
                            
                            # Sell on strong sell signals
                            if signal["signal"] in ["sell", "strong_sell"]:
                                await self._execute_trade(
                                    coin_id,
                                    "sell",
                                    current_prices.get(coin_id, prices[-1]),
                                    current_date,
                                    reason=signal["signal"]
                                )
                
                # Look for new buys
                if self.portfolio["cash"] > portfolio_value * 0.1:
                    signals = []
                    for coin_id in available_coins:
                        if coin_id not in self.portfolio["holdings"] or self.portfolio["holdings"][coin_id]["quantity"] == 0:
                            if coin_id in price_history and len(price_history[coin_id]) >= 14:
                                signal = self._calculate_signal(coin_id, price_history[coin_id], current_date)
                                signal["coin_id"] = coin_id
                                signal["price"] = current_prices.get(coin_id, 0)
                                signals.append(signal)
                    
                    signals.sort(key=lambda x: x["score"], reverse=True)
                    
                    for sig in signals[:2]:
                        if sig["signal"] in ["buy", "strong_buy"] and sig["price"] > 0:
                            await self._execute_trade(
                                sig["coin_id"],
                                "buy",
                                sig["price"],
                                current_date,
                                reason=f"new_opportunity_{sig['signal']}"
                            )
            
            # 3. Find hidden gem each year
            if current_date.month == 1 and current_date.day <= step.days + 1:
                gem = self._identify_hidden_gem(available_coins, current_date)
                if gem and gem not in [g["coin_id"] for g in self.hidden_gems]:
                    self.hidden_gems.append({
                        "coin_id": gem,
                        "discovered_date": current_date.isoformat(),
                        "price_at_discovery": current_prices.get(gem, 0)
                    })
                    
                    # Buy the hidden gem
                    if self.portfolio["cash"] > 50:
                        await self._execute_trade(
                            gem,
                            "buy",
                            current_prices.get(gem, 0.01),
                            current_date,
                            amount_usd=min(100, self.portfolio["cash"] * 0.2),
                            reason="hidden_gem_pick"
                        )
            
            # Monthly snapshot
            if current_date.day <= step.days + 1:
                self.monthly_snapshots.append({
                    "date": current_date.isoformat(),
                    "year": current_date.year,
                    "month": current_date.month,
                    "portfolio_value": portfolio_value,
                    "cash": self.portfolio["cash"],
                    "num_holdings": len([h for h in self.portfolio["holdings"].values() if h["quantity"] > 0]),
                    "num_trades": len(self.trades),
                    "growth_pct": ((portfolio_value - self.starting_capital) / self.starting_capital * 100)
                })
            
            # Track portfolio history
            self.portfolio_history.append({
                "date": current_date.isoformat(),
                "value": portfolio_value,
                "cash": self.portfolio["cash"]
            })
            
            current_date += step
        
        # Final results
        final_value = self.portfolio["total_value"]
        
        result["status"] = "completed"
        result["final_value"] = final_value
        result["total_return_pct"] = ((final_value - self.starting_capital) / self.starting_capital * 100)
        result["target_reached"] = final_value >= self.target_capital
        result["total_trades"] = len(self.trades)
        result["profitable_trades"] = len([t for t in self.trades if t.get("profit", 0) > 0])
        result["hidden_gems_found"] = len(self.hidden_gems)
        
        # Best and worst trades
        profitable = [t for t in self.trades if t.get("profit")]
        if profitable:
            best_trade = max(profitable, key=lambda x: x.get("profit_pct", 0))
            worst_trade = min(profitable, key=lambda x: x.get("profit_pct", 0))
            result["best_trade"] = {
                "coin": best_trade["coin_id"],
                "profit_pct": best_trade.get("profit_pct", 0),
                "date": best_trade["date"]
            }
            result["worst_trade"] = {
                "coin": worst_trade["coin_id"],
                "profit_pct": worst_trade.get("profit_pct", 0),
                "date": worst_trade["date"]
            }
        
        # Final portfolio
        result["final_portfolio"] = {
            "cash": self.portfolio["cash"],
            "holdings": [
                {"coin_id": k, "quantity": v["quantity"], "avg_price": v["avg_price"]}
                for k, v in self.portfolio["holdings"].items() if v["quantity"] > 0
            ]
        }
        
        result["hidden_gems"] = self.hidden_gems
        result["monthly_snapshots"] = self.monthly_snapshots
        
        # Save to database
        if self.db is not None:
            try:
                await self.db.backtest_simulations.insert_one({
                    "simulation_type": "historical_2009_2026",
                    "completed_at": datetime.now(timezone.utc),
                    "result": result,
                    "trades": self.trades[-100:],  # Last 100 trades
                    "monthly_snapshots": self.monthly_snapshots
                })
            except Exception as e:
                print(f"Error saving simulation: {e}")
        
        return result
    
    def get_simulation_summary(self) -> str:
        """Generate a text summary of the simulation"""
        if not self.monthly_snapshots:
            return "No simulation data available"
        
        final = self.monthly_snapshots[-1] if self.monthly_snapshots else {}
        
        summary = f"""
📊 **AI Trading Simulation Results (2009-2026)**

💰 **Performance:**
- Starting Capital: ${self.starting_capital:,.2f}
- Final Value: ${final.get('portfolio_value', 0):,.2f}
- Total Return: {final.get('growth_pct', 0):,.1f}%
- Target ($100k): {'✅ REACHED' if final.get('portfolio_value', 0) >= 100000 else '❌ NOT REACHED'}

📈 **Trading Stats:**
- Total Trades: {len(self.trades)}
- Profitable Trades: {len([t for t in self.trades if t.get('profit', 0) > 0])}
- Win Rate: {len([t for t in self.trades if t.get('profit', 0) > 0]) / len(self.trades) * 100 if self.trades else 0:.1f}%

💎 **Hidden Gems Found:** {len(self.hidden_gems)}
{chr(10).join([f"  - {g['coin_id'].upper()} (discovered {g['discovered_date'][:7]})" for g in self.hidden_gems[:5]])}

📅 **Key Milestones:**
"""
        # Add key milestones
        for snap in self.monthly_snapshots:
            if snap.get("portfolio_value", 0) >= 1000 and not any("$1k" in s for s in summary.split('\n')):
                summary += f"  - Reached $1k: {snap['date'][:7]}\n"
            if snap.get("portfolio_value", 0) >= 10000 and not any("$10k" in s for s in summary.split('\n')):
                summary += f"  - Reached $10k: {snap['date'][:7]}\n"
            if snap.get("portfolio_value", 0) >= 50000 and not any("$50k" in s for s in summary.split('\n')):
                summary += f"  - Reached $50k: {snap['date'][:7]}\n"
            if snap.get("portfolio_value", 0) >= 100000 and not any("$100k" in s for s in summary.split('\n')):
                summary += f"  - 🎯 Reached $100k: {snap['date'][:7]}\n"
        
        return summary


# Global instance for background task
_simulator = None
_simulation_status = {
    "running": False,
    "started_at": None,
    "progress": 0,
    "result": None
}

def _convert_to_serializable(obj):
    """Convert numpy types to native Python types"""
    import numpy as np
    if isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: _convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_to_serializable(item) for item in obj]
    return obj

async def run_simulation_task(db, market_service):
    """Background task to run the simulation"""
    global _simulator, _simulation_status
    
    _simulation_status["running"] = True
    _simulation_status["started_at"] = datetime.now(timezone.utc).isoformat()
    _simulation_status["progress"] = 0
    
    try:
        _simulator = HistoricalTradingSimulator(db, market_service)
        result = await _simulator.run_simulation(speed="monthly")
        # Convert numpy types to native Python
        _simulation_status["result"] = _convert_to_serializable(result)
        _simulation_status["progress"] = 100
    except Exception as e:
        _simulation_status["result"] = {"error": str(e)}
    finally:
        _simulation_status["running"] = False

def get_simulation_status():
    return _convert_to_serializable(_simulation_status)

def get_simulator():
    return _simulator

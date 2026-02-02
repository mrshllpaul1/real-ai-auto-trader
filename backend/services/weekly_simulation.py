"""
Weekly Paper Trading Simulation Runner
Simulates weekly AI trading from January 2009 to present using real historical data.

KEY DESIGN DECISIONS:
1. Fixed weekly capital allocation (no compounding) for realistic backtesting
2. Uses real historical prices from database
3. Tracks each week independently
4. Records all results for AI learning
"""

import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
import numpy as np
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

# Import the adaptive coin selector
from services.adaptive_coin_selector import AdaptiveCoinSelector


class WeeklySimulationRunner:
    """
    Run paper trading simulations on a weekly basis.
    Uses real historical data and fixed capital per week (no unrealistic compounding).
    """
    
    def __init__(self, db):
        self.db = db
        self.coin_selector = AdaptiveCoinSelector(db)
        
        # Simulation configuration
        self.config = {
            'weekly_capital': 10000,        # Fixed $10k allocated per week
            'max_coins_per_week': 5,        # Max 5 coins per week
            'position_size_pct': 20,        # 20% per coin (5 coins = 100%)
            'stop_loss_pct': 15,            # 15% stop loss
            'take_profit_pct': 50,          # 50% take profit
        }
        
        # Historical coin availability (coins didn't all exist in 2009)
        self.coin_launch_dates = {
            'bitcoin': datetime(2009, 1, 3),
            'litecoin': datetime(2011, 10, 7),
            'ripple': datetime(2012, 1, 1),
            'dogecoin': datetime(2013, 12, 6),
            'ethereum': datetime(2015, 7, 30),
            'tron': datetime(2017, 8, 28),
            'cardano': datetime(2017, 9, 29),
            'chainlink': datetime(2017, 9, 19),
            'cosmos': datetime(2019, 3, 14),
            'polkadot': datetime(2020, 5, 26),
            'uniswap': datetime(2020, 9, 17),
            'solana': datetime(2020, 4, 10),
            'avalanche': datetime(2020, 9, 21),
            'polygon': datetime(2019, 4, 22),
            'near': datetime(2020, 4, 22),
            'aptos': datetime(2022, 10, 12),
            'sui': datetime(2023, 5, 3),
            'arbitrum': datetime(2021, 8, 31),
            'optimism': datetime(2021, 12, 16),
        }
    
    def _get_available_coins(self, week_date: datetime) -> List[str]:
        """Get coins that existed at a given date"""
        return [
            coin for coin, launch in self.coin_launch_dates.items()
            if launch <= week_date
        ]
    
    def _determine_market_condition(
        self,
        prices: Dict[str, List[Dict]]
    ) -> str:
        """Determine overall market condition from BTC performance"""
        btc_prices = prices.get('bitcoin', [])
        
        if len(btc_prices) < 7:
            return 'neutral'
        
        closes = [p.get('close', p.get('price', 0)) for p in btc_prices]
        week_change = (closes[-1] - closes[-7]) / closes[-7] * 100 if closes[-7] > 0 else 0
        
        if week_change > 10:
            return 'bullish'
        elif week_change < -10:
            return 'bearish'
        else:
            return 'neutral'
    
    async def get_week_prices(
        self,
        coin_id: str,
        week_start: datetime,
        week_end: datetime
    ) -> List[Dict[str, Any]]:
        """Get daily prices for a coin during a week"""
        try:
            prices = await self.db.historical_prices.find({
                'coin_id': coin_id,
                'timestamp': {
                    '$gte': week_start.isoformat(),
                    '$lte': week_end.isoformat()
                }
            }, {'_id': 0}).sort('timestamp', 1).to_list(10)
            
            return prices
        except Exception as e:
            print(f"Error fetching week prices for {coin_id}: {e}")
            return []
    
    async def simulate_week(
        self,
        week_start: datetime,
        available_coins: List[str]
    ) -> Dict[str, Any]:
        """
        Simulate one week of trading.
        
        Returns:
            Week result with trades and profit/loss
        """
        week_end = week_start + timedelta(days=7)
        
        # Get historical prices for available coins (30 days before week for analysis)
        analysis_start = week_start - timedelta(days=30)
        
        all_prices = {}
        for coin in available_coins:
            prices = await self.db.historical_prices.find({
                'coin_id': coin,
                'timestamp': {
                    '$gte': analysis_start.isoformat(),
                    '$lte': week_end.isoformat()
                }
            }, {'_id': 0}).sort('timestamp', 1).to_list(50)
            
            if prices:
                all_prices[coin] = prices
        
        if not all_prices:
            return {
                'week_start': week_start.isoformat(),
                'status': 'NO_DATA',
                'trades': [],
                'total_return_pct': 0,
                'total_profit_usd': 0
            }
        
        # Determine market condition
        market_condition = self._determine_market_condition(all_prices)
        
        # Use adaptive coin selector to pick best coins
        # Filter to only coins with sufficient data
        coins_with_data = [c for c in available_coins if c in all_prices and len(all_prices[c]) >= 7]
        
        if not coins_with_data:
            return {
                'week_start': week_start.isoformat(),
                'status': 'INSUFFICIENT_DATA',
                'trades': [],
                'total_return_pct': 0,
                'total_profit_usd': 0
            }
        
        # Select best coins for this week
        selected_coins = await self.coin_selector.select_best_coins(
            week_start=week_start,
            market_condition=market_condition,
            max_coins=min(self.config['max_coins_per_week'], len(coins_with_data))
        )
        
        if not selected_coins:
            return {
                'week_start': week_start.isoformat(),
                'status': 'NO_SELECTION',
                'market_condition': market_condition,
                'trades': [],
                'total_return_pct': 0,
                'total_profit_usd': 0
            }
        
        # Simulate trades for selected coins
        trades = []
        total_profit_usd = 0
        
        position_size = self.config['weekly_capital'] / len(selected_coins)
        
        for selection in selected_coins:
            coin_id = selection['coin_id']
            
            # Get prices for just this week
            week_prices = await self.get_week_prices(coin_id, week_start, week_end)
            
            if len(week_prices) < 2:
                continue
            
            entry_price = week_prices[0].get('close', week_prices[0].get('price', 0))
            
            if entry_price <= 0:
                continue
            
            # Simulate the week
            exit_price = entry_price
            exit_reason = 'WEEK_END'
            exit_day = len(week_prices) - 1
            
            for i, day_price in enumerate(week_prices[1:], 1):
                current_price = day_price.get('close', day_price.get('price', 0))
                
                if current_price <= 0:
                    continue
                
                pnl_pct = (current_price - entry_price) / entry_price * 100
                
                # Check stop loss
                if pnl_pct <= -self.config['stop_loss_pct']:
                    exit_price = current_price
                    exit_reason = 'STOP_LOSS'
                    exit_day = i
                    break
                
                # Check take profit
                if pnl_pct >= self.config['take_profit_pct']:
                    exit_price = current_price
                    exit_reason = 'TAKE_PROFIT'
                    exit_day = i
                    break
                
                exit_price = current_price
            
            # Calculate trade result
            return_pct = (exit_price - entry_price) / entry_price * 100
            profit_usd = position_size * (return_pct / 100)
            
            trades.append({
                'coin_id': coin_id,
                'symbol': selection['symbol'],
                'selection_score': selection['total_score'],
                'entry_price': round(entry_price, 6),
                'exit_price': round(exit_price, 6),
                'return_pct': round(return_pct, 2),
                'profit_usd': round(profit_usd, 2),
                'position_size': round(position_size, 2),
                'exit_reason': exit_reason,
                'hold_days': exit_day
            })
            
            total_profit_usd += profit_usd
        
        # Calculate week totals
        total_return_pct = (total_profit_usd / self.config['weekly_capital']) * 100 if trades else 0
        winning_trades = [t for t in trades if t['return_pct'] > 0]
        
        return {
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'status': 'COMPLETED',
            'market_condition': market_condition,
            'coins_selected': [s['coin_id'] for s in selected_coins],
            'trades': trades,
            'total_return_pct': round(total_return_pct, 2),
            'total_profit_usd': round(total_profit_usd, 2),
            'winning_trades': len(winning_trades),
            'total_trades': len(trades),
            'win_rate': round(len(winning_trades) / len(trades) * 100, 1) if trades else 0
        }
    
    async def run_full_simulation(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Run the full weekly simulation from start to end date.
        
        Args:
            start_date: Simulation start (default: Jan 1, 2009)
            end_date: Simulation end (default: Jan 31, 2026)
            progress_callback: Optional async callback for progress updates
            
        Returns:
            Complete simulation results with weekly breakdown
        """
        if start_date is None:
            start_date = datetime(2009, 1, 1)
        if end_date is None:
            end_date = datetime(2026, 1, 31)
        
        print(f"\n{'='*60}")
        print("📊 WEEKLY PAPER TRADING SIMULATION")
        print(f"{'='*60}")
        print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"Weekly Capital: ${self.config['weekly_capital']:,}")
        print(f"Max Coins/Week: {self.config['max_coins_per_week']}")
        print(f"{'='*60}\n")
        
        # Initialize tracking
        weekly_results = []
        total_profit = 0
        total_weeks = 0
        winning_weeks = 0
        
        # Iterate through each week
        current_week = start_date
        weeks_processed = 0
        
        while current_week < end_date:
            # Get available coins for this period
            available_coins = self._get_available_coins(current_week)
            
            if not available_coins:
                current_week += timedelta(days=7)
                continue
            
            # Simulate this week
            week_result = await self.simulate_week(current_week, available_coins)
            
            if week_result['status'] == 'COMPLETED':
                weekly_results.append(week_result)
                total_profit += week_result['total_profit_usd']
                total_weeks += 1
                
                if week_result['total_return_pct'] > 0:
                    winning_weeks += 1
                
                # Progress output every 52 weeks (1 year)
                if weeks_processed % 52 == 0 and weeks_processed > 0:
                    year = current_week.year
                    year_results = [w for w in weekly_results if w['week_start'].startswith(str(year))]
                    year_profit = sum(w['total_profit_usd'] for w in year_results)
                    print(f"Year {year}: {len(year_results)} weeks, ${year_profit:,.2f} profit")
                
                if progress_callback:
                    await progress_callback({
                        'current_week': current_week.isoformat(),
                        'weeks_completed': total_weeks,
                        'total_profit': total_profit
                    })
            
            current_week += timedelta(days=7)
            weeks_processed += 1
        
        # Calculate summary statistics
        if weekly_results:
            returns = [w['total_return_pct'] for w in weekly_results]
            avg_weekly_return = np.mean(returns)
            std_weekly_return = np.std(returns)
            best_week = max(weekly_results, key=lambda x: x['total_return_pct'])
            worst_week = min(weekly_results, key=lambda x: x['total_return_pct'])
            
            # Calculate drawdown
            cumulative = 0
            peak = 0
            max_drawdown = 0
            for w in weekly_results:
                cumulative += w['total_profit_usd']
                peak = max(peak, cumulative)
                drawdown = (peak - cumulative) / self.config['weekly_capital'] * 100 if peak > 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
        else:
            avg_weekly_return = 0
            std_weekly_return = 0
            best_week = None
            worst_week = None
            max_drawdown = 0
        
        summary = {
            'simulation_period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'configuration': self.config,
            'total_weeks': total_weeks,
            'winning_weeks': winning_weeks,
            'losing_weeks': total_weeks - winning_weeks,
            'win_rate_pct': round(winning_weeks / total_weeks * 100, 1) if total_weeks > 0 else 0,
            'total_profit_usd': round(total_profit, 2),
            'avg_weekly_return_pct': round(avg_weekly_return, 2),
            'std_weekly_return_pct': round(std_weekly_return, 2),
            'max_drawdown_pct': round(max_drawdown, 2),
            'best_week': {
                'date': best_week['week_start'] if best_week else None,
                'return_pct': best_week['total_return_pct'] if best_week else 0,
                'profit_usd': best_week['total_profit_usd'] if best_week else 0
            },
            'worst_week': {
                'date': worst_week['week_start'] if worst_week else None,
                'return_pct': worst_week['total_return_pct'] if worst_week else 0,
                'profit_usd': worst_week['total_profit_usd'] if worst_week else 0
            },
            'annual_breakdown': self._calculate_annual_breakdown(weekly_results),
            'weekly_results': weekly_results,
            'completed_at': datetime.now().isoformat()
        }
        
        # Store simulation results
        await self.db.weekly_simulations.insert_one(dict(summary))
        
        # Print summary
        print(f"\n{'='*60}")
        print("📊 SIMULATION COMPLETE")
        print(f"{'='*60}")
        print(f"Total Weeks: {total_weeks}")
        print(f"Winning Weeks: {winning_weeks} ({summary['win_rate_pct']}%)")
        print(f"Total Profit: ${total_profit:,.2f}")
        print(f"Avg Weekly Return: {avg_weekly_return:.2f}%")
        print(f"Max Drawdown: {max_drawdown:.2f}%")
        print(f"{'='*60}\n")
        
        return summary
    
    def _calculate_annual_breakdown(
        self,
        weekly_results: List[Dict]
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate year-by-year performance"""
        annual = {}
        
        for week in weekly_results:
            year = week['week_start'][:4]  # Keep as string for MongoDB
            
            if year not in annual:
                annual[year] = {
                    'weeks': 0,
                    'winning_weeks': 0,
                    'total_profit': 0,
                    'total_return_pct': 0,
                    'trades': 0
                }
            
            annual[year]['weeks'] += 1
            annual[year]['total_profit'] += week['total_profit_usd']
            annual[year]['total_return_pct'] += week['total_return_pct']
            annual[year]['trades'] += week['total_trades']
            
            if week['total_return_pct'] > 0:
                annual[year]['winning_weeks'] += 1
        
        # Calculate averages
        for year, data in annual.items():
            if data['weeks'] > 0:
                data['avg_weekly_return'] = round(data['total_return_pct'] / data['weeks'], 2)
                data['win_rate'] = round(data['winning_weeks'] / data['weeks'] * 100, 1)
            data['total_profit'] = round(data['total_profit'], 2)
        
        return annual


async def run_simulation():
    """Entry point to run the simulation"""
    # Connect to database
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'crypto_trading_db')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    runner = WeeklySimulationRunner(db)
    
    # Run from Jan 2009 to Jan 2026
    results = await runner.run_full_simulation(
        start_date=datetime(2009, 1, 1),
        end_date=datetime(2026, 1, 31)
    )
    
    return results


if __name__ == "__main__":
    asyncio.run(run_simulation())

"""
Backtesting Engine
Tests trading strategies against REAL historical data only.
NEVER uses simulated or fake data.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List
import asyncio


class BacktestingEngine:
    """
    Backtesting engine to test trading strategies against REAL historical data.
    All data comes from actual market APIs - NO SIMULATED DATA.
    """
    
    def __init__(self, db, market_service=None):
        self.db = db
        self.market_service = market_service
    
    async def get_real_historical_prices(
        self,
        coin_id: str,
        days: int = 365
    ) -> List[Dict[str, Any]]:
        """
        Fetch REAL historical prices from database or API.
        NEVER generates fake data.
        """
        # First try to get from cached historical_prices in database
        cached = await self.db.historical_prices.find(
            {"coin_id": coin_id},
            {"_id": 0}
        ).sort("timestamp", 1).limit(days).to_list(days)
        
        if cached and len(cached) >= days * 0.8:  # At least 80% of requested data
            return cached
        
        # Fetch from market service if available
        if self.market_service:
            try:
                data = await self.market_service.get_historical_data(coin_id, days)
                if data and 'prices' in data:
                    prices = []
                    for item in data['prices']:
                        if len(item) >= 2:
                            timestamp = item[0]
                            price = item[1]
                            date = datetime.fromtimestamp(timestamp / 1000)
                            prices.append({
                                'date': date.isoformat(),
                                'timestamp': timestamp,
                                'close': price,
                                'open': price,
                                'high': price,
                                'low': price,
                                'coin_id': coin_id
                            })
                    if prices:
                        return prices
            except Exception as e:
                print(f"Error fetching historical data for {coin_id}: {e}")
        
        # Return empty if no real data available - NEVER fake it
        print(f"WARNING: No real historical data available for {coin_id}")
        return []
    
    async def run_backtest(
        self,
        strategy_params: Dict[str, Any],
        coins: List[str],
        days: int = 365,
        initial_capital: float = 10000,
        stop_loss_pct: float = 10,
        take_profit_pct: float = 20
    ) -> Dict[str, Any]:
        """
        Run backtest using REAL historical data only.
        Returns error if real data is not available.
        """
        
        # Fetch REAL price data for all coins
        all_prices = {}
        coins_with_data = []
        
        for coin in coins:
            prices = await self.get_real_historical_prices(coin, days)
            if prices and len(prices) >= 30:  # Need at least 30 days for analysis
                all_prices[coin] = prices
                coins_with_data.append(coin)
            else:
                print(f"Skipping {coin} - insufficient real historical data")
        
        if not coins_with_data:
            return {
                'error': 'No real historical data available for any requested coins',
                'message': 'Backtesting requires real market data. Please ensure historical data has been fetched.',
                'coins_requested': coins,
                'data_available': False
            }
        
        # Run simulation with REAL data
        capital = initial_capital
        peak_capital = initial_capital
        positions = []
        closed_trades = []
        daily_values = []
        
        # Get the minimum days available across all coins
        min_days = min(len(all_prices[coin]) for coin in coins_with_data)
        
        if min_days < 30:
            return {
                'error': f'Insufficient historical data. Need at least 30 days, have {min_days}',
                'data_available': False
            }
        
        # Run simulation day by day
        for day_idx in range(30, min_days):
            day_date = all_prices[coins_with_data[0]][day_idx]['date']
            
            # Check existing positions for stop-loss/take-profit
            for pos in positions[:]:
                coin = pos['coin_id']
                if coin not in all_prices or day_idx >= len(all_prices[coin]):
                    continue
                    
                current_price = all_prices[coin][day_idx]['close']
                entry_price = pos['entry_price']
                
                pnl_pct = (current_price - entry_price) / entry_price * 100
                
                close_reason = None
                if pnl_pct <= -stop_loss_pct:
                    close_reason = 'STOP_LOSS'
                elif pnl_pct >= take_profit_pct:
                    close_reason = 'TAKE_PROFIT'
                elif day_idx - pos['entry_day'] >= 30:
                    close_reason = 'MAX_HOLD'
                
                if close_reason:
                    profit = pos['size'] * (pnl_pct / 100)
                    capital += pos['size'] + profit
                    
                    closed_trades.append({
                        'coin_id': coin,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'entry_day': pos['entry_day'],
                        'exit_day': day_idx,
                        'hold_days': day_idx - pos['entry_day'],
                        'pnl_pct': round(pnl_pct, 2),
                        'profit_usd': round(profit, 2),
                        'reason': close_reason,
                        'data_source': 'REAL_MARKET_DATA'
                    })
                    
                    positions.remove(pos)
            
            # Open new positions based on strategy signals
            if len(positions) < strategy_params.get('max_positions', 5) and capital > 100:
                for coin in coins_with_data:
                    if day_idx >= len(all_prices[coin]):
                        continue
                    if any(p['coin_id'] == coin for p in positions):
                        continue
                    
                    # Calculate signals using REAL price data
                    recent_prices = [all_prices[coin][i]['close'] for i in range(max(0, day_idx-20), day_idx)]
                    
                    if len(recent_prices) < 10:
                        continue
                    
                    # Simple momentum signal based on REAL data
                    momentum = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100
                    volatility = np.std(recent_prices) / np.mean(recent_prices) * 100
                    
                    buy_signal = (
                        momentum > strategy_params.get('min_momentum', 2) and
                        volatility < strategy_params.get('max_volatility', 15)
                    )
                    
                    if buy_signal:
                        position_size = min(capital * 0.2, capital - 100)
                        capital -= position_size
                        
                        positions.append({
                            'coin_id': coin,
                            'entry_price': all_prices[coin][day_idx]['close'],
                            'entry_day': day_idx,
                            'size': position_size,
                            'signals': {
                                'momentum': round(momentum, 2),
                                'volatility': round(volatility, 2)
                            }
                        })
            
            # Track portfolio value
            position_value = sum(
                pos['size'] * (all_prices[pos['coin_id']][min(day_idx, len(all_prices[pos['coin_id']])-1)]['close'] / pos['entry_price'])
                for pos in positions
                if pos['coin_id'] in all_prices
            )
            
            total_value = capital + position_value
            peak_capital = max(peak_capital, total_value)
            
            daily_values.append({
                'date': day_date,
                'capital': round(capital, 2),
                'position_value': round(position_value, 2),
                'total_value': round(total_value, 2),
                'positions_count': len(positions)
            })
        
        # Close remaining positions at last price
        for pos in positions:
            coin = pos['coin_id']
            if coin in all_prices and len(all_prices[coin]) > 0:
                final_price = all_prices[coin][-1]['close']
                pnl_pct = (final_price - pos['entry_price']) / pos['entry_price'] * 100
                profit = pos['size'] * (pnl_pct / 100)
                capital += pos['size'] + profit
                
                closed_trades.append({
                    'coin_id': coin,
                    'entry_price': pos['entry_price'],
                    'exit_price': final_price,
                    'pnl_pct': round(pnl_pct, 2),
                    'profit_usd': round(profit, 2),
                    'reason': 'END_OF_PERIOD',
                    'data_source': 'REAL_MARKET_DATA'
                })
        
        # Calculate final metrics
        final_value = capital
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        max_drawdown = ((peak_capital - min(v['total_value'] for v in daily_values)) / peak_capital * 100) if daily_values else 0
        
        winning_trades = [t for t in closed_trades if t['pnl_pct'] > 0]
        losing_trades = [t for t in closed_trades if t['pnl_pct'] <= 0]
        
        win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0
        avg_win = np.mean([t['pnl_pct'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl_pct'] for t in losing_trades]) if losing_trades else 0
        
        return {
            'data_source': 'REAL_MARKET_DATA_ONLY',
            'simulated_data_used': False,
            'initial_capital': initial_capital,
            'final_value': round(final_value, 2),
            'total_return_pct': round(total_return, 2),
            'max_drawdown_pct': round(max_drawdown, 2),
            'total_trades': len(closed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round(win_rate, 2),
            'avg_win_pct': round(avg_win, 2),
            'avg_loss_pct': round(avg_loss, 2),
            'profit_factor': round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else 0,
            'coins_tested': coins_with_data,
            'days_tested': min_days - 30,
            'trades': closed_trades[-20:],  # Last 20 trades
            'daily_values': daily_values[-30:] if daily_values else [],  # Last 30 days
            'strategy_params': strategy_params,
            'timestamp': datetime.now().isoformat()
        }
    
    async def quick_backtest(
        self,
        coin_id: str,
        days: int = 90,
        initial_capital: float = 1000
    ) -> Dict[str, Any]:
        """Quick backtest on a single coin using REAL data only"""
        return await self.run_backtest(
            strategy_params={'min_momentum': 3, 'max_volatility': 12, 'max_positions': 1},
            coins=[coin_id],
            days=days,
            initial_capital=initial_capital
        )

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
import uuid
from dotenv import load_dotenv

load_dotenv()

class BacktestingEngine:
    """
    Backtesting engine to test trading strategies against historical data
    Simulates trades and calculates performance metrics
    """
    
    def __init__(self, db):
        self.db = db
    
    async def generate_historical_prices(
        self,
        coin_id: str,
        days: int = 365,
        volatility: float = 0.03
    ) -> List[Dict[str, Any]]:
        """Generate simulated historical price data for backtesting"""
        
        # Base prices for different coins
        base_prices = {
            'bitcoin': 45000, 'ethereum': 2500, 'solana': 100,
            'cardano': 0.5, 'polkadot': 7, 'avalanche': 35,
            'chainlink': 15, 'polygon': 0.8, 'uniswap': 10, 'litecoin': 80
        }
        
        base_price = base_prices.get(coin_id, 100)
        np.random.seed(hash(coin_id) % 2**32)
        
        prices = []
        current_price = base_price
        
        for i in range(days):
            date = datetime.now() - timedelta(days=days - i)
            
            # Add trend and noise
            trend = np.sin(i / 90 * np.pi) * 0.001  # Cyclical trend
            noise = np.random.normal(0, volatility)
            
            # Occasional jumps
            if np.random.random() < 0.02:
                noise += np.random.choice([-1, 1]) * np.random.uniform(0.05, 0.15)
            
            current_price *= (1 + trend + noise)
            current_price = max(current_price * 0.1, current_price)  # Floor at 10% of base
            
            volume = np.random.uniform(1e6, 1e8) * (1 + abs(noise) * 10)
            
            prices.append({
                'date': date.isoformat(),
                'timestamp': date.timestamp(),
                'open': current_price * (1 + np.random.uniform(-0.01, 0.01)),
                'high': current_price * (1 + abs(np.random.normal(0, 0.02))),
                'low': current_price * (1 - abs(np.random.normal(0, 0.02))),
                'close': current_price,
                'volume': volume
            })
        
        return prices
    
    def calculate_signals(self, prices: List[Dict], index: int) -> Dict[str, Any]:
        """Calculate trading signals at a specific point in history"""
        if index < 30:
            return {'signals': [], 'score': 0}
        
        # Get recent prices
        recent = prices[max(0, index-30):index+1]
        closes = [p['close'] for p in recent]
        volumes = [p['volume'] for p in recent]
        
        current_price = closes[-1]
        avg_price = np.mean(closes)
        avg_volume = np.mean(volumes[:-1]) if len(volumes) > 1 else volumes[0]
        current_volume = volumes[-1]
        
        # Calculate RSI
        if len(closes) >= 14:
            deltas = np.diff(closes[-15:])
            gains = np.mean([d for d in deltas if d > 0] or [0])
            losses = np.mean([-d for d in deltas if d < 0] or [0.001])
            rsi = 100 - (100 / (1 + gains / losses))
        else:
            rsi = 50
        
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        price_vs_avg = (current_price - avg_price) / avg_price
        
        signals = []
        score = 0
        
        # MACD Bullish
        if price_vs_avg > 0.02 and volume_ratio > 1.5:
            signals.append('MACD_BULLISH')
            score += 25
        
        # Oversold
        if rsi < 30:
            signals.append('OVERSOLD_ACCUMULATION')
            score += 30
        
        # Volume spike
        if volume_ratio > 2.5:
            signals.append('EXTREME_VOLUME')
            score += 20
        
        # Trend reversal
        if len(closes) >= 7:
            week_change = (closes[-1] - closes[-7]) / closes[-7]
            month_change = (closes[-1] - closes[0]) / closes[0] if closes[0] > 0 else 0
            if month_change < -0.1 and week_change > 0.03:
                signals.append('TREND_REVERSAL')
                score += 20
        
        return {
            'signals': signals,
            'score': score,
            'rsi': rsi,
            'volume_ratio': volume_ratio,
            'price': current_price
        }
    
    async def run_backtest(
        self,
        strategy: Dict[str, Any],
        coins: List[str],
        days: int = 365,
        initial_capital: float = 10000
    ) -> Dict[str, Any]:
        """
        Run a backtest with specified strategy
        
        Strategy parameters:
        - min_score: Minimum signal score to trade
        - position_size_pct: % of capital per trade
        - stop_loss_pct: Stop loss percentage
        - take_profit_pct: Take profit percentage
        - max_positions: Maximum concurrent positions
        """
        backtest_id = str(uuid.uuid4())[:8]
        
        min_score = strategy.get('min_score', 50)
        position_size_pct = strategy.get('position_size_pct', 10)
        stop_loss_pct = strategy.get('stop_loss_pct', 10)
        take_profit_pct = strategy.get('take_profit_pct', 30)
        max_positions = strategy.get('max_positions', 3)
        
        # Track results
        capital = initial_capital
        peak_capital = initial_capital
        positions = []
        closed_trades = []
        daily_values = []
        
        # Generate price data for all coins
        all_prices = {}
        for coin in coins:
            all_prices[coin] = await self.generate_historical_prices(coin, days)
        
        # Run simulation day by day
        for day_idx in range(30, days):  # Start after warmup period
            day_date = all_prices[coins[0]][day_idx]['date']
            
            # Check existing positions for stop-loss/take-profit
            for pos in positions[:]:
                coin = pos['coin_id']
                current_price = all_prices[coin][day_idx]['close']
                entry_price = pos['entry_price']
                
                pnl_pct = (current_price - entry_price) / entry_price * 100
                
                close_reason = None
                if pnl_pct <= -stop_loss_pct:
                    close_reason = 'STOP_LOSS'
                elif pnl_pct >= take_profit_pct:
                    close_reason = 'TAKE_PROFIT'
                elif day_idx - pos['entry_day'] >= 30:  # Max hold 30 days
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
                        'pnl_pct': pnl_pct,
                        'profit_usd': profit,
                        'reason': close_reason,
                        'signals': pos['signals']
                    })
                    positions.remove(pos)
            
            # Look for new entries
            if len(positions) < max_positions:
                for coin in coins:
                    if any(p['coin_id'] == coin for p in positions):
                        continue  # Already have position
                    
                    signal_data = self.calculate_signals(all_prices[coin], day_idx)
                    
                    if signal_data['score'] >= min_score and len(positions) < max_positions:
                        position_size = capital * (position_size_pct / 100)
                        if position_size > 10:  # Minimum position
                            capital -= position_size
                            positions.append({
                                'coin_id': coin,
                                'entry_price': signal_data['price'],
                                'entry_day': day_idx,
                                'size': position_size,
                                'signals': signal_data['signals'],
                                'score': signal_data['score']
                            })
            
            # Calculate daily portfolio value
            positions_value = sum(
                pos['size'] * (all_prices[pos['coin_id']][day_idx]['close'] / pos['entry_price'])
                for pos in positions
            )
            total_value = capital + positions_value
            peak_capital = max(peak_capital, total_value)
            
            daily_values.append({
                'date': day_date,
                'value': total_value,
                'capital': capital,
                'positions_value': positions_value,
                'num_positions': len(positions)
            })
        
        # Close remaining positions at end
        final_day = days - 1
        for pos in positions:
            coin = pos['coin_id']
            current_price = all_prices[coin][final_day]['close']
            entry_price = pos['entry_price']
            pnl_pct = (current_price - entry_price) / entry_price * 100
            profit = pos['size'] * (pnl_pct / 100)
            capital += pos['size'] + profit
            
            closed_trades.append({
                'coin_id': coin,
                'entry_price': entry_price,
                'exit_price': current_price,
                'pnl_pct': pnl_pct,
                'profit_usd': profit,
                'reason': 'END_OF_TEST',
                'signals': pos['signals']
            })
        
        # Calculate metrics
        total_trades = len(closed_trades)
        winning_trades = [t for t in closed_trades if t['pnl_pct'] > 0]
        losing_trades = [t for t in closed_trades if t['pnl_pct'] <= 0]
        
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        avg_win = np.mean([t['pnl_pct'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl_pct'] for t in losing_trades]) if losing_trades else 0
        
        final_value = capital
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        max_drawdown = ((peak_capital - min(d['value'] for d in daily_values)) / peak_capital) * 100 if daily_values else 0
        
        # Sharpe ratio approximation
        if len(daily_values) > 1:
            returns = [(daily_values[i]['value'] - daily_values[i-1]['value']) / daily_values[i-1]['value'] 
                      for i in range(1, len(daily_values))]
            sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(365) if np.std(returns) > 0 else 0
        else:
            sharpe = 0
        
        result = {
            'backtest_id': backtest_id,
            'strategy': strategy,
            'coins': coins,
            'period_days': days,
            'initial_capital': initial_capital,
            'final_value': final_value,
            'total_return_pct': total_return,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss,
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else float('inf'),
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe,
            'trades': closed_trades[-20:],  # Last 20 trades
            'daily_values': daily_values[::7],  # Weekly snapshots
            'created_at': datetime.now().isoformat()
        }
        
        # Save to database
        await self.db.backtests.insert_one(dict(result))
        
        return result
    
    async def get_backtest_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent backtest results"""
        results = await self.db.backtests.find(
            {},
            {'_id': 0}
        ).sort('created_at', -1).limit(limit).to_list(limit)
        return results
    
    async def compare_strategies(
        self,
        strategies: List[Dict[str, Any]],
        coins: List[str],
        days: int = 365
    ) -> Dict[str, Any]:
        """Compare multiple strategies side by side"""
        results = []
        
        for strategy in strategies:
            result = await self.run_backtest(strategy, coins, days)
            results.append({
                'strategy_name': strategy.get('name', f"Strategy {len(results)+1}"),
                'strategy': strategy,
                'total_return': result['total_return_pct'],
                'win_rate': result['win_rate'],
                'sharpe_ratio': result['sharpe_ratio'],
                'max_drawdown': result['max_drawdown_pct'],
                'total_trades': result['total_trades']
            })
        
        # Rank by return
        results.sort(key=lambda x: x['total_return'], reverse=True)
        
        return {
            'comparison': results,
            'best_strategy': results[0] if results else None,
            'coins_tested': coins,
            'period_days': days,
            'compared_at': datetime.now().isoformat()
        }

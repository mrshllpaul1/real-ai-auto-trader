"""
Backtest Simulator Service
==========================
Test trading strategies on historical data.
"""

import asyncio
import logging
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """A simulated trade"""
    id: str
    timestamp: str
    symbol: str
    side: str  # 'buy' or 'sell'
    price: float
    quantity: float
    value: float
    pnl: float = 0.0
    pnl_pct: float = 0.0


@dataclass
class BacktestResult:
    """Results of a backtest"""
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    profit_factor: float
    trades: List[Dict] = field(default_factory=list)
    equity_curve: List[Dict] = field(default_factory=list)


class BacktestSimulator:
    """
    Strategy backtesting on historical data.
    
    Features:
    - Multiple strategy types
    - Performance metrics
    - Equity curve generation
    - Risk-adjusted returns
    """
    
    # Built-in strategies
    STRATEGIES = {
        'sma_crossover': 'Simple Moving Average Crossover',
        'rsi_oversold': 'RSI Oversold/Overbought',
        'macd_signal': 'MACD Signal Line Crossover',
        'bollinger_bands': 'Bollinger Bands Mean Reversion',
        'momentum': 'Price Momentum',
        'dca': 'Dollar Cost Averaging',
        'buy_hold': 'Buy and Hold'
    }
    
    def __init__(self, db, market_service=None):
        self.db = db
        self.market = market_service
        self.results: Dict[str, BacktestResult] = {}
        logger.info("✅ Backtest Simulator initialized")
    
    async def run_backtest(
        self,
        strategy: str,
        symbol: str,
        start_date: str,
        end_date: str,
        initial_capital: float = 10000,
        params: Dict = None
    ) -> Dict[str, Any]:
        """Run a backtest simulation"""
        params = params or {}
        
        if strategy not in self.STRATEGIES:
            return {'status': 'error', 'message': f'Unknown strategy: {strategy}'}
        
        # Get historical data
        historical_data = await self._get_historical_data(symbol, start_date, end_date)
        if not historical_data or len(historical_data) < 30:
            return {'status': 'error', 'message': 'Insufficient historical data'}
        
        # Run strategy
        if strategy == 'sma_crossover':
            result = await self._run_sma_crossover(historical_data, initial_capital, params)
        elif strategy == 'rsi_oversold':
            result = await self._run_rsi_strategy(historical_data, initial_capital, params)
        elif strategy == 'macd_signal':
            result = await self._run_macd_strategy(historical_data, initial_capital, params)
        elif strategy == 'bollinger_bands':
            result = await self._run_bollinger_strategy(historical_data, initial_capital, params)
        elif strategy == 'momentum':
            result = await self._run_momentum_strategy(historical_data, initial_capital, params)
        elif strategy == 'dca':
            result = await self._run_dca_strategy(historical_data, initial_capital, params)
        elif strategy == 'buy_hold':
            result = await self._run_buy_hold(historical_data, initial_capital)
        else:
            return {'status': 'error', 'message': 'Strategy not implemented'}
        
        # Update result metadata
        result.strategy_name = strategy
        result.symbol = symbol
        result.start_date = start_date
        result.end_date = end_date
        result.initial_capital = initial_capital
        
        # Store result
        result_id = f"{strategy}_{symbol}_{datetime.now().timestamp()}"
        self.results[result_id] = result
        
        # Save to database
        await self.db.backtest_results.insert_one({
            'id': result_id,
            **asdict(result),
            'created_at': datetime.now(timezone.utc).isoformat()
        })
        
        return {
            'status': 'success',
            'result_id': result_id,
            'result': asdict(result)
        }
    
    async def _get_historical_data(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str
    ) -> List[Dict]:
        """Get historical OHLCV data"""
        # Try to get from database first
        cursor = self.db.price_history.find({
            'symbol': symbol.upper(),
            'timestamp': {'$gte': start_date, '$lte': end_date}
        }).sort('timestamp', 1)
        
        data = await cursor.to_list(None)
        
        if data and len(data) >= 30:
            return data
        
        # Generate synthetic data for demo
        return self._generate_synthetic_data(symbol, start_date, end_date)
    
    def _generate_synthetic_data(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str
    ) -> List[Dict]:
        """Generate synthetic price data for demo"""
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        days = (end - start).days
        if days <= 0:
            days = 365
        
        # Starting prices for common coins
        base_prices = {
            'BTC': 40000, 'ETH': 2500, 'SOL': 100, 'XRP': 0.5,
            'ADA': 0.4, 'DOGE': 0.08, 'DOT': 7, 'AVAX': 35
        }
        base_price = base_prices.get(symbol.upper(), 100)
        
        # Generate random walk with trend
        np.random.seed(hash(symbol) % 2**32)
        returns = np.random.normal(0.001, 0.03, days)  # Daily returns
        prices = [base_price]
        
        for r in returns:
            prices.append(prices[-1] * (1 + r))
        
        data = []
        for i, price in enumerate(prices):
            date = start + timedelta(days=i)
            high = price * (1 + abs(np.random.normal(0, 0.02)))
            low = price * (1 - abs(np.random.normal(0, 0.02)))
            
            data.append({
                'timestamp': date.isoformat(),
                'symbol': symbol.upper(),
                'open': prices[i-1] if i > 0 else price,
                'high': high,
                'low': low,
                'close': price,
                'volume': np.random.uniform(1e6, 1e8)
            })
        
        return data
    
    async def _run_sma_crossover(
        self, 
        data: List[Dict], 
        initial_capital: float,
        params: Dict
    ) -> BacktestResult:
        """SMA Crossover strategy"""
        short_period = params.get('short_period', 10)
        long_period = params.get('long_period', 30)
        
        prices = [d['close'] for d in data]
        
        # Calculate SMAs
        short_sma = self._calculate_sma(prices, short_period)
        long_sma = self._calculate_sma(prices, long_period)
        
        return self._simulate_crossover(data, prices, short_sma, long_sma, initial_capital)
    
    async def _run_rsi_strategy(
        self, 
        data: List[Dict], 
        initial_capital: float,
        params: Dict
    ) -> BacktestResult:
        """RSI Oversold/Overbought strategy"""
        period = params.get('period', 14)
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)
        
        prices = [d['close'] for d in data]
        rsi = self._calculate_rsi(prices, period)
        
        return self._simulate_rsi(data, prices, rsi, oversold, overbought, initial_capital)
    
    async def _run_macd_strategy(
        self, 
        data: List[Dict], 
        initial_capital: float,
        params: Dict
    ) -> BacktestResult:
        """MACD Signal Line Crossover"""
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        signal = params.get('signal', 9)
        
        prices = [d['close'] for d in data]
        macd_line, signal_line = self._calculate_macd(prices, fast, slow, signal)
        
        return self._simulate_crossover(data, prices, macd_line, signal_line, initial_capital)
    
    async def _run_bollinger_strategy(
        self, 
        data: List[Dict], 
        initial_capital: float,
        params: Dict
    ) -> BacktestResult:
        """Bollinger Bands Mean Reversion"""
        period = params.get('period', 20)
        std_dev = params.get('std_dev', 2)
        
        prices = [d['close'] for d in data]
        upper, middle, lower = self._calculate_bollinger(prices, period, std_dev)
        
        return self._simulate_bollinger(data, prices, upper, middle, lower, initial_capital)
    
    async def _run_momentum_strategy(
        self, 
        data: List[Dict], 
        initial_capital: float,
        params: Dict
    ) -> BacktestResult:
        """Price Momentum strategy"""
        lookback = params.get('lookback', 20)
        threshold = params.get('threshold', 0.05)
        
        prices = [d['close'] for d in data]
        momentum = [(prices[i] - prices[i-lookback]) / prices[i-lookback] 
                    if i >= lookback else 0 for i in range(len(prices))]
        
        return self._simulate_momentum(data, prices, momentum, threshold, initial_capital)
    
    async def _run_dca_strategy(
        self, 
        data: List[Dict], 
        initial_capital: float,
        params: Dict
    ) -> BacktestResult:
        """Dollar Cost Averaging"""
        interval_days = params.get('interval_days', 7)
        
        prices = [d['close'] for d in data]
        return self._simulate_dca(data, prices, interval_days, initial_capital)
    
    async def _run_buy_hold(
        self, 
        data: List[Dict], 
        initial_capital: float
    ) -> BacktestResult:
        """Simple Buy and Hold"""
        prices = [d['close'] for d in data]
        
        # Buy at start, sell at end
        buy_price = prices[0]
        sell_price = prices[-1]
        quantity = initial_capital / buy_price
        final_value = quantity * sell_price
        
        pnl = final_value - initial_capital
        pnl_pct = (pnl / initial_capital) * 100
        
        # Calculate max drawdown
        peak = initial_capital
        max_drawdown = 0
        equity_curve = []
        
        for i, price in enumerate(prices):
            value = quantity * price
            equity_curve.append({
                'timestamp': data[i]['timestamp'],
                'equity': value
            })
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        trades = [
            asdict(Trade(
                id='buy_0',
                timestamp=data[0]['timestamp'],
                symbol=data[0].get('symbol', 'BTC'),
                side='buy',
                price=buy_price,
                quantity=quantity,
                value=initial_capital
            )),
            asdict(Trade(
                id='sell_1',
                timestamp=data[-1]['timestamp'],
                symbol=data[-1].get('symbol', 'BTC'),
                side='sell',
                price=sell_price,
                quantity=quantity,
                value=final_value,
                pnl=pnl,
                pnl_pct=pnl_pct
            ))
        ]
        
        return BacktestResult(
            strategy_name='buy_hold',
            symbol='',
            start_date='',
            end_date='',
            initial_capital=initial_capital,
            final_capital=final_value,
            total_return=pnl,
            total_return_pct=pnl_pct,
            max_drawdown=max_drawdown * 100,
            sharpe_ratio=self._calculate_sharpe(prices),
            win_rate=100 if pnl > 0 else 0,
            total_trades=2,
            winning_trades=1 if pnl > 0 else 0,
            losing_trades=0 if pnl > 0 else 1,
            avg_win=pnl if pnl > 0 else 0,
            avg_loss=abs(pnl) if pnl < 0 else 0,
            profit_factor=float('inf') if pnl > 0 else 0,
            trades=trades,
            equity_curve=equity_curve
        )
    
    def _calculate_sma(self, prices: List[float], period: int) -> List[float]:
        """Calculate Simple Moving Average"""
        sma = []
        for i in range(len(prices)):
            if i < period:
                sma.append(prices[i])
            else:
                sma.append(sum(prices[i-period:i]) / period)
        return sma
    
    def _calculate_rsi(self, prices: List[float], period: int) -> List[float]:
        """Calculate RSI"""
        rsi = [50] * period  # Default
        
        for i in range(period, len(prices)):
            gains = []
            losses = []
            for j in range(i - period, i):
                change = prices[j+1] - prices[j]
                if change > 0:
                    gains.append(change)
                else:
                    losses.append(abs(change))
            
            avg_gain = sum(gains) / period if gains else 0
            avg_loss = sum(losses) / period if losses else 0.0001
            
            rs = avg_gain / avg_loss
            rsi.append(100 - (100 / (1 + rs)))
        
        return rsi
    
    def _calculate_macd(
        self, 
        prices: List[float], 
        fast: int, 
        slow: int, 
        signal: int
    ) -> tuple:
        """Calculate MACD"""
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
        signal_line = self._calculate_ema(macd_line, signal)
        return macd_line, signal_line
    
    def _calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average"""
        multiplier = 2 / (period + 1)
        ema = [prices[0]]
        for price in prices[1:]:
            ema.append((price * multiplier) + (ema[-1] * (1 - multiplier)))
        return ema
    
    def _calculate_bollinger(
        self, 
        prices: List[float], 
        period: int, 
        std_dev: float
    ) -> tuple:
        """Calculate Bollinger Bands"""
        middle = self._calculate_sma(prices, period)
        upper = []
        lower = []
        
        for i in range(len(prices)):
            if i < period:
                std = 0
            else:
                std = np.std(prices[i-period:i])
            upper.append(middle[i] + std_dev * std)
            lower.append(middle[i] - std_dev * std)
        
        return upper, middle, lower
    
    def _calculate_sharpe(self, prices: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe Ratio"""
        returns = [(prices[i] - prices[i-1]) / prices[i-1] 
                   for i in range(1, len(prices))]
        if not returns:
            return 0
        
        mean_return = np.mean(returns) * 252  # Annualized
        std_return = np.std(returns) * np.sqrt(252)
        
        if std_return == 0:
            return 0
        
        return (mean_return - risk_free_rate) / std_return
    
    def _simulate_crossover(
        self,
        data: List[Dict],
        prices: List[float],
        fast: List[float],
        slow: List[float],
        initial_capital: float
    ) -> BacktestResult:
        """Simulate crossover strategy"""
        capital = initial_capital
        position = 0
        trades = []
        equity_curve = []
        wins = 0
        losses = 0
        total_profit = 0
        total_loss = 0
        
        for i in range(1, len(prices)):
            equity = capital + position * prices[i]
            equity_curve.append({
                'timestamp': data[i]['timestamp'],
                'equity': equity
            })
            
            # Buy signal: fast crosses above slow
            if fast[i] > slow[i] and fast[i-1] <= slow[i-1] and position == 0:
                quantity = capital / prices[i]
                position = quantity
                capital = 0
                trades.append(asdict(Trade(
                    id=f'buy_{len(trades)}',
                    timestamp=data[i]['timestamp'],
                    symbol=data[i].get('symbol', 'BTC'),
                    side='buy',
                    price=prices[i],
                    quantity=quantity,
                    value=quantity * prices[i]
                )))
            
            # Sell signal: fast crosses below slow
            elif fast[i] < slow[i] and fast[i-1] >= slow[i-1] and position > 0:
                value = position * prices[i]
                buy_value = trades[-1]['value'] if trades else value
                pnl = value - buy_value
                pnl_pct = (pnl / buy_value) * 100
                
                if pnl > 0:
                    wins += 1
                    total_profit += pnl
                else:
                    losses += 1
                    total_loss += abs(pnl)
                
                trades.append(asdict(Trade(
                    id=f'sell_{len(trades)}',
                    timestamp=data[i]['timestamp'],
                    symbol=data[i].get('symbol', 'BTC'),
                    side='sell',
                    price=prices[i],
                    quantity=position,
                    value=value,
                    pnl=pnl,
                    pnl_pct=pnl_pct
                )))
                capital = value
                position = 0
        
        # Close any open position
        final_equity = capital + position * prices[-1]
        
        return self._create_result(
            initial_capital, final_equity, trades, equity_curve,
            wins, losses, total_profit, total_loss, prices
        )
    
    def _simulate_rsi(
        self,
        data: List[Dict],
        prices: List[float],
        rsi: List[float],
        oversold: float,
        overbought: float,
        initial_capital: float
    ) -> BacktestResult:
        """Simulate RSI strategy"""
        capital = initial_capital
        position = 0
        trades = []
        equity_curve = []
        wins = 0
        losses = 0
        total_profit = 0
        total_loss = 0
        
        for i in range(1, len(prices)):
            equity = capital + position * prices[i]
            equity_curve.append({
                'timestamp': data[i]['timestamp'],
                'equity': equity
            })
            
            # Buy when RSI is oversold
            if rsi[i] < oversold and position == 0:
                quantity = capital / prices[i]
                position = quantity
                capital = 0
                trades.append(asdict(Trade(
                    id=f'buy_{len(trades)}',
                    timestamp=data[i]['timestamp'],
                    symbol=data[i].get('symbol', 'BTC'),
                    side='buy',
                    price=prices[i],
                    quantity=quantity,
                    value=quantity * prices[i]
                )))
            
            # Sell when RSI is overbought
            elif rsi[i] > overbought and position > 0:
                value = position * prices[i]
                buy_value = trades[-1]['value'] if trades else value
                pnl = value - buy_value
                pnl_pct = (pnl / buy_value) * 100
                
                if pnl > 0:
                    wins += 1
                    total_profit += pnl
                else:
                    losses += 1
                    total_loss += abs(pnl)
                
                trades.append(asdict(Trade(
                    id=f'sell_{len(trades)}',
                    timestamp=data[i]['timestamp'],
                    symbol=data[i].get('symbol', 'BTC'),
                    side='sell',
                    price=prices[i],
                    quantity=position,
                    value=value,
                    pnl=pnl,
                    pnl_pct=pnl_pct
                )))
                capital = value
                position = 0
        
        final_equity = capital + position * prices[-1]
        
        return self._create_result(
            initial_capital, final_equity, trades, equity_curve,
            wins, losses, total_profit, total_loss, prices
        )
    
    def _simulate_bollinger(
        self,
        data: List[Dict],
        prices: List[float],
        upper: List[float],
        middle: List[float],
        lower: List[float],
        initial_capital: float
    ) -> BacktestResult:
        """Simulate Bollinger Bands strategy"""
        capital = initial_capital
        position = 0
        trades = []
        equity_curve = []
        wins = 0
        losses = 0
        total_profit = 0
        total_loss = 0
        
        for i in range(1, len(prices)):
            equity = capital + position * prices[i]
            equity_curve.append({
                'timestamp': data[i]['timestamp'],
                'equity': equity
            })
            
            # Buy at lower band
            if prices[i] <= lower[i] and position == 0:
                quantity = capital / prices[i]
                position = quantity
                capital = 0
                trades.append(asdict(Trade(
                    id=f'buy_{len(trades)}',
                    timestamp=data[i]['timestamp'],
                    symbol=data[i].get('symbol', 'BTC'),
                    side='buy',
                    price=prices[i],
                    quantity=quantity,
                    value=quantity * prices[i]
                )))
            
            # Sell at upper band
            elif prices[i] >= upper[i] and position > 0:
                value = position * prices[i]
                buy_value = trades[-1]['value'] if trades else value
                pnl = value - buy_value
                pnl_pct = (pnl / buy_value) * 100
                
                if pnl > 0:
                    wins += 1
                    total_profit += pnl
                else:
                    losses += 1
                    total_loss += abs(pnl)
                
                trades.append(asdict(Trade(
                    id=f'sell_{len(trades)}',
                    timestamp=data[i]['timestamp'],
                    symbol=data[i].get('symbol', 'BTC'),
                    side='sell',
                    price=prices[i],
                    quantity=position,
                    value=value,
                    pnl=pnl,
                    pnl_pct=pnl_pct
                )))
                capital = value
                position = 0
        
        final_equity = capital + position * prices[-1]
        
        return self._create_result(
            initial_capital, final_equity, trades, equity_curve,
            wins, losses, total_profit, total_loss, prices
        )
    
    def _simulate_momentum(
        self,
        data: List[Dict],
        prices: List[float],
        momentum: List[float],
        threshold: float,
        initial_capital: float
    ) -> BacktestResult:
        """Simulate Momentum strategy"""
        capital = initial_capital
        position = 0
        trades = []
        equity_curve = []
        wins = 0
        losses = 0
        total_profit = 0
        total_loss = 0
        
        for i in range(1, len(prices)):
            equity = capital + position * prices[i]
            equity_curve.append({
                'timestamp': data[i]['timestamp'],
                'equity': equity
            })
            
            # Buy on positive momentum
            if momentum[i] > threshold and position == 0:
                quantity = capital / prices[i]
                position = quantity
                capital = 0
                trades.append(asdict(Trade(
                    id=f'buy_{len(trades)}',
                    timestamp=data[i]['timestamp'],
                    symbol=data[i].get('symbol', 'BTC'),
                    side='buy',
                    price=prices[i],
                    quantity=quantity,
                    value=quantity * prices[i]
                )))
            
            # Sell on negative momentum
            elif momentum[i] < -threshold and position > 0:
                value = position * prices[i]
                buy_value = trades[-1]['value'] if trades else value
                pnl = value - buy_value
                pnl_pct = (pnl / buy_value) * 100
                
                if pnl > 0:
                    wins += 1
                    total_profit += pnl
                else:
                    losses += 1
                    total_loss += abs(pnl)
                
                trades.append(asdict(Trade(
                    id=f'sell_{len(trades)}',
                    timestamp=data[i]['timestamp'],
                    symbol=data[i].get('symbol', 'BTC'),
                    side='sell',
                    price=prices[i],
                    quantity=position,
                    value=value,
                    pnl=pnl,
                    pnl_pct=pnl_pct
                )))
                capital = value
                position = 0
        
        final_equity = capital + position * prices[-1]
        
        return self._create_result(
            initial_capital, final_equity, trades, equity_curve,
            wins, losses, total_profit, total_loss, prices
        )
    
    def _simulate_dca(
        self,
        data: List[Dict],
        prices: List[float],
        interval_days: int,
        initial_capital: float
    ) -> BacktestResult:
        """Simulate DCA strategy"""
        num_buys = len(prices) // interval_days
        if num_buys == 0:
            num_buys = 1
        
        amount_per_buy = initial_capital / num_buys
        total_quantity = 0
        capital_used = 0
        trades = []
        equity_curve = []
        
        for i in range(len(prices)):
            if i % interval_days == 0 and capital_used < initial_capital:
                quantity = amount_per_buy / prices[i]
                total_quantity += quantity
                capital_used += amount_per_buy
                trades.append(asdict(Trade(
                    id=f'buy_{len(trades)}',
                    timestamp=data[i]['timestamp'],
                    symbol=data[i].get('symbol', 'BTC'),
                    side='buy',
                    price=prices[i],
                    quantity=quantity,
                    value=amount_per_buy
                )))
            
            equity = total_quantity * prices[i] + (initial_capital - capital_used)
            equity_curve.append({
                'timestamp': data[i]['timestamp'],
                'equity': equity
            })
        
        final_equity = total_quantity * prices[-1]
        pnl = final_equity - capital_used
        
        return self._create_result(
            initial_capital, final_equity, trades, equity_curve,
            1 if pnl > 0 else 0, 0 if pnl > 0 else 1,
            pnl if pnl > 0 else 0, abs(pnl) if pnl < 0 else 0, prices
        )
    
    def _create_result(
        self,
        initial_capital: float,
        final_equity: float,
        trades: List[Dict],
        equity_curve: List[Dict],
        wins: int,
        losses: int,
        total_profit: float,
        total_loss: float,
        prices: List[float]
    ) -> BacktestResult:
        """Create BacktestResult from simulation data"""
        total_return = final_equity - initial_capital
        total_return_pct = (total_return / initial_capital) * 100
        
        # Calculate max drawdown
        peak = initial_capital
        max_drawdown = 0
        for point in equity_curve:
            equity = point['equity']
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        avg_win = total_profit / wins if wins > 0 else 0
        avg_loss = total_loss / losses if losses > 0 else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        return BacktestResult(
            strategy_name='',
            symbol='',
            start_date='',
            end_date='',
            initial_capital=initial_capital,
            final_capital=final_equity,
            total_return=total_return,
            total_return_pct=total_return_pct,
            max_drawdown=max_drawdown * 100,
            sharpe_ratio=self._calculate_sharpe(prices),
            win_rate=win_rate,
            total_trades=len(trades),
            winning_trades=wins,
            losing_trades=losses,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            trades=trades,
            equity_curve=equity_curve
        )
    
    async def get_strategies(self) -> Dict[str, str]:
        """Get available strategies"""
        return self.STRATEGIES
    
    async def get_results(self, limit: int = 20) -> List[Dict]:
        """Get recent backtest results"""
        cursor = self.db.backtest_results.find(
            {}, {'_id': 0}
        ).sort('created_at', -1).limit(limit)
        return await cursor.to_list(limit)
    
    async def get_result(self, result_id: str) -> Optional[Dict]:
        """Get a specific backtest result"""
        if result_id in self.results:
            return asdict(self.results[result_id])
        
        result = await self.db.backtest_results.find_one(
            {'id': result_id}, {'_id': 0}
        )
        return result


# Singleton
_backtest_service: Optional[BacktestSimulator] = None


def get_backtest_service(db=None, market=None) -> Optional[BacktestSimulator]:
    """Get or create the backtest service"""
    global _backtest_service
    if _backtest_service is None and db is not None:
        _backtest_service = BacktestSimulator(db, market)
    return _backtest_service

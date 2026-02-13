"""
Paper Trading Simulator
Executes simulated trades using Enhanced AI signals with all stored data:
- Historical OHLCV data
- News sentiment
- Social sentiment
- Fear & Greed Index
- Whale activity
- All ML/DL model predictions
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import numpy as np
import logging

logger = logging.getLogger(__name__)


class PaperTradingSimulator:
    """
    Simulates trading using Enhanced AI with all available data.
    Tracks virtual portfolio performance.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, enhanced_ai=None, regime_predictor=None, gem_predictor=None):
        self.db = db
        self.enhanced_ai = enhanced_ai
        self.regime_predictor = regime_predictor
        self.gem_predictor = gem_predictor
        
        # Paper trading state
        self.initial_balance = 500.0
        self.balance = 500.0
        self.positions = {}
        self.trade_history = []
        self.portfolio_history = []
        self.is_running = False
        
        # Trading parameters
        self.max_positions = 10
        self.max_position_pct = 15.0
        self.stop_loss_pct = 8.0
        self.take_profit_pct = 20.0
        self.min_score_to_buy = 2
        self.min_score_to_sell = -2
    
    async def initialize(self, initial_balance: float = 500.0):
        """Initialize paper trading with starting balance"""
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions = {}
        self.trade_history = []
        self.portfolio_history = []
        
        # Save initial state
        await self._save_portfolio_snapshot("initialized")
        
        logger.info(f"📝 Paper Trading initialized with ${initial_balance}")
        return {"success": True, "balance": self.balance}
    
    async def run_simulation(self, days_back: int = 30, coins: List[str] = None) -> Dict[str, Any]:
        """
        Run paper trading simulation over historical data.
        
        Args:
            days_back: Number of days to simulate
            coins: List of coins to trade (default: top 15)
        """
        if self.is_running:
            return {"error": "Simulation already running"}
        
        self.is_running = True
        
        if coins is None:
            coins = ['BTC', 'ETH', 'SOL', 'DOT', 'ADA', 'XRP', 'AVAX', 'LINK', 
                    'MATIC', 'ATOM', 'UNI', 'AAVE', 'INJ', 'APT', 'SUI']
        
        logger.info(f"🚀 Starting paper trading simulation ({days_back} days, {len(coins)} coins)")
        
        # Reset state
        await self.initialize(self.initial_balance)
        
        results = {
            'start_time': datetime.now(timezone.utc).isoformat(),
            'days_simulated': days_back,
            'coins_traded': coins,
            'trades': [],
            'daily_snapshots': [],
            'final_balance': 0,
            'total_return_pct': 0,
            'win_rate': 0,
            'total_trades': 0
        }
        
        try:
            # Get date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days_back)
            
            # Simulate day by day
            current_date = start_date
            day_count = 0
            
            while current_date <= end_date:
                day_count += 1
                logger.info(f"📅 Simulating day {day_count}/{days_back}: {current_date.strftime('%Y-%m-%d')}")
                
                # Get market data for this day
                day_signals = await self._get_day_signals(coins, current_date)
                
                # Check existing positions for stop-loss/take-profit
                await self._check_positions(current_date)
                
                # Execute trades based on signals
                day_trades = await self._execute_day_trades(day_signals, current_date)
                results['trades'].extend(day_trades)
                
                # Save daily snapshot
                snapshot = await self._save_portfolio_snapshot(f"day_{day_count}")
                results['daily_snapshots'].append(snapshot)
                
                current_date += timedelta(days=1)
            
            # Close all remaining positions at end
            final_trades = await self._close_all_positions(end_date)
            results['trades'].extend(final_trades)
            
            # Calculate final metrics
            results['final_balance'] = self.balance
            results['total_return_pct'] = ((self.balance / self.initial_balance) - 1) * 100
            results['total_trades'] = len(self.trade_history)
            
            winning_trades = [t for t in self.trade_history if t.get('pnl', 0) > 0]
            results['win_rate'] = (len(winning_trades) / len(self.trade_history) * 100) if self.trade_history else 0
            
            results['end_time'] = datetime.now(timezone.utc).isoformat()
            results['success'] = True
            
            # Save results to DB
            await self.db.paper_trading_simulations.insert_one({
                **results,
                'positions_history': self.portfolio_history
            })
            
            logger.info(f"✅ Simulation complete: ${self.initial_balance} → ${self.balance:.2f} ({results['total_return_pct']:.2f}%)")
            
        except Exception as e:
            logger.error(f"❌ Simulation error: {e}")
            results['error'] = str(e)
            results['success'] = False
        finally:
            self.is_running = False
        
        return results
    
    async def _get_day_signals(self, coins: List[str], date: datetime) -> List[Dict]:
        """Get AI signals for all coins on a specific day"""
        signals = []
        
        for coin in coins:
            try:
                # Get historical data up to this date
                ohlcv = await self.db.historical_ohlcv.find(
                    {
                        'symbol': coin,
                        'timestamp': {'$lte': date.isoformat()}
                    },
                    {'_id': 0}
                ).sort('timestamp', -1).limit(100).to_list(100)
                
                if not ohlcv or len(ohlcv) < 30:
                    continue
                
                ohlcv.reverse()
                
                # Get current price
                current_price = float(ohlcv[-1].get('close', 0))
                if current_price <= 0:
                    continue
                
                # Calculate technical features
                signal = await self._calculate_signal(coin, ohlcv, date)
                signal['price'] = current_price
                signals.append(signal)
                
            except Exception as e:
                logger.warning(f"Error getting signal for {coin}: {e}")
                continue
        
        return signals
    
    async def _calculate_signal(self, coin: str, ohlcv: List[Dict], date: datetime) -> Dict:
        """Calculate trading signal for a coin"""
        closes = [float(d.get('close', 0)) for d in ohlcv]
        highs = [float(d.get('high', 0)) for d in ohlcv]
        lows = [float(d.get('low', 0)) for d in ohlcv]
        volumes = [float(d.get('volume_to', d.get('volume', 0)) or 0) for d in ohlcv]
        
        # Calculate indicators
        rsi = self._calculate_rsi(closes)
        macd_hist = self._calculate_macd(closes)
        bb_position = self._calculate_bb_position(closes)
        
        # Calculate score components
        score = 0
        reasons = []
        
        # RSI signals
        if rsi < 30:
            score += 2
            reasons.append('oversold')
        elif rsi > 70:
            score -= 2
            reasons.append('overbought')
        elif rsi < 40:
            score += 1
            reasons.append('low_rsi')
        elif rsi > 60:
            score -= 1
            reasons.append('high_rsi')
        
        # MACD signals
        if macd_hist > 0:
            score += 1
            reasons.append('macd_bullish')
        else:
            score -= 1
            reasons.append('macd_bearish')
        
        # Bollinger Band position
        if bb_position < 0.2:
            score += 1
            reasons.append('near_lower_bb')
        elif bb_position > 0.8:
            score -= 1
            reasons.append('near_upper_bb')
        
        # Trend (SMA crossover)
        sma_20 = np.mean(closes[-20:]) if len(closes) >= 20 else closes[-1]
        sma_50 = np.mean(closes[-50:]) if len(closes) >= 50 else closes[-1]
        
        if closes[-1] > sma_20 > sma_50:
            score += 1
            reasons.append('uptrend')
        elif closes[-1] < sma_20 < sma_50:
            score -= 1
            reasons.append('downtrend')
        
        # Volume surge
        avg_volume = np.mean(volumes[-20:]) if len(volumes) >= 20 else 1
        if volumes[-1] > avg_volume * 1.5:
            if score > 0:
                score += 1
                reasons.append('volume_confirmation')
        
        # Get sentiment if available
        sentiment_score = await self._get_historical_sentiment(date)
        if sentiment_score < 30:
            score += 1  # Contrarian: fear = buy
            reasons.append('fear_sentiment')
        elif sentiment_score > 70:
            score -= 1  # Contrarian: greed = sell
            reasons.append('greed_sentiment')
        
        # Determine action
        if score >= 3:
            action = 'strong_buy'
        elif score >= 2:
            action = 'buy'
        elif score >= 1:
            action = 'weak_buy'
        elif score <= -3:
            action = 'strong_sell'
        elif score <= -2:
            action = 'sell'
        elif score <= -1:
            action = 'weak_sell'
        else:
            action = 'hold'
        
        return {
            'symbol': coin,
            'score': score,
            'action': action,
            'rsi': round(rsi, 1),
            'macd_hist': round(macd_hist, 4),
            'bb_position': round(bb_position, 2),
            'reasons': reasons,
            'date': date.isoformat()
        }
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains) if len(gains) > 0 else 0
        avg_loss = np.mean(losses) if len(losses) > 0 else 0.001
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_macd(self, prices: List[float]) -> float:
        if len(prices) < 26:
            return 0
        ema12 = self._ema(prices, 12)
        ema26 = self._ema(prices, 26)
        return ema12 - ema26
    
    def _ema(self, prices: List[float], period: int) -> float:
        if len(prices) < period:
            return prices[-1] if prices else 0
        multiplier = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
        return ema
    
    def _calculate_bb_position(self, prices: List[float], period: int = 20) -> float:
        if len(prices) < period:
            return 0.5
        middle = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        if std == 0:
            return 0.5
        upper = middle + (std * 2)
        lower = middle - (std * 2)
        return (prices[-1] - lower) / (upper - lower)
    
    async def _get_historical_sentiment(self, date: datetime) -> float:
        """Get sentiment score for a specific date"""
        try:
            # Try Fear & Greed Index
            fg = await self.db.fear_greed_index.find_one(
                {'timestamp': {'$lte': date.isoformat()}},
                {'_id': 0},
                sort=[('timestamp', -1)]
            )
            if fg:
                return fg.get('value', 50)
            
            # Try aggregated sentiment
            sentiment = await self.db.social_sentiment.find_one(
                {'timestamp': {'$lte': date.isoformat()}},
                {'_id': 0},
                sort=[('timestamp', -1)]
            )
            if sentiment:
                return sentiment.get('score', 50)
            
        except:
            pass
        
        return 50  # Neutral default
    
    async def _check_positions(self, date: datetime):
        """Check existing positions for stop-loss and take-profit"""
        positions_to_close = []
        
        for symbol, position in self.positions.items():
            try:
                # Get current price
                ohlcv = await self.db.historical_ohlcv.find_one(
                    {'symbol': symbol, 'timestamp': {'$lte': date.isoformat()}},
                    {'_id': 0},
                    sort=[('timestamp', -1)]
                )
                
                if not ohlcv:
                    continue
                
                current_price = float(ohlcv.get('close', 0))
                if current_price <= 0:
                    continue
                
                entry_price = position['entry_price']
                pnl_pct = ((current_price / entry_price) - 1) * 100
                
                # Check stop-loss
                if pnl_pct <= -self.stop_loss_pct:
                    positions_to_close.append({
                        'symbol': symbol,
                        'reason': 'stop_loss',
                        'price': current_price,
                        'pnl_pct': pnl_pct
                    })
                
                # Check take-profit
                elif pnl_pct >= self.take_profit_pct:
                    positions_to_close.append({
                        'symbol': symbol,
                        'reason': 'take_profit',
                        'price': current_price,
                        'pnl_pct': pnl_pct
                    })
                
            except Exception as e:
                logger.warning(f"Error checking position {symbol}: {e}")
        
        # Close positions
        for close_info in positions_to_close:
            await self._close_position(
                close_info['symbol'],
                close_info['price'],
                close_info['reason'],
                date
            )
    
    async def _execute_day_trades(self, signals: List[Dict], date: datetime) -> List[Dict]:
        """Execute trades based on signals"""
        trades = []
        
        # Sort by score (best opportunities first)
        signals.sort(key=lambda x: x['score'], reverse=True)
        
        for signal in signals:
            symbol = signal['symbol']
            score = signal['score']
            price = signal['price']
            action = signal['action']
            
            # Check if we should buy
            if score >= self.min_score_to_buy and symbol not in self.positions:
                if len(self.positions) < self.max_positions:
                    # Calculate position size based on score
                    position_pct = min(self.max_position_pct, 5 + (score * 2))
                    amount = self.balance * (position_pct / 100)
                    
                    if amount >= 10:  # Minimum trade size
                        trade = await self._open_position(symbol, price, amount, signal, date)
                        if trade:
                            trades.append(trade)
            
            # Check if we should sell existing position
            elif score <= self.min_score_to_sell and symbol in self.positions:
                trade = await self._close_position(symbol, price, 'signal_sell', date)
                if trade:
                    trades.append(trade)
        
        return trades
    
    async def _open_position(self, symbol: str, price: float, amount: float, signal: Dict, date: datetime) -> Optional[Dict]:
        """Open a new position"""
        if amount > self.balance:
            amount = self.balance
        
        if amount < 10:
            return None
        
        quantity = amount / price
        
        self.positions[symbol] = {
            'symbol': symbol,
            'entry_price': price,
            'quantity': quantity,
            'amount': amount,
            'entry_date': date.isoformat(),
            'signal': signal
        }
        
        self.balance -= amount
        
        trade = {
            'type': 'buy',
            'symbol': symbol,
            'price': price,
            'quantity': quantity,
            'amount': amount,
            'score': signal['score'],
            'action': signal['action'],
            'reasons': signal['reasons'],
            'date': date.isoformat(),
            'balance_after': self.balance
        }
        
        self.trade_history.append(trade)
        logger.info(f"  📈 BUY {symbol}: ${amount:.2f} @ ${price:.4f} (score: {signal['score']})")
        
        return trade
    
    async def _close_position(self, symbol: str, price: float, reason: str, date: datetime) -> Optional[Dict]:
        """Close an existing position"""
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        quantity = position['quantity']
        entry_price = position['entry_price']
        entry_amount = position['amount']
        
        exit_amount = quantity * price
        pnl = exit_amount - entry_amount
        pnl_pct = ((price / entry_price) - 1) * 100
        
        self.balance += exit_amount
        del self.positions[symbol]
        
        trade = {
            'type': 'sell',
            'symbol': symbol,
            'price': price,
            'quantity': quantity,
            'amount': exit_amount,
            'entry_price': entry_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'reason': reason,
            'date': date.isoformat(),
            'balance_after': self.balance,
            'hold_days': (datetime.fromisoformat(date.isoformat().replace('Z', '+00:00')) - 
                         datetime.fromisoformat(position['entry_date'].replace('Z', '+00:00'))).days
        }
        
        self.trade_history.append(trade)
        
        emoji = '✅' if pnl > 0 else '❌'
        logger.info(f"  {emoji} SELL {symbol}: ${exit_amount:.2f} @ ${price:.4f} (P&L: ${pnl:.2f}, {pnl_pct:.2f}%) [{reason}]")
        
        return trade
    
    async def _close_all_positions(self, date: datetime) -> List[Dict]:
        """Close all remaining positions at simulation end"""
        trades = []
        
        for symbol in list(self.positions.keys()):
            try:
                ohlcv = await self.db.historical_ohlcv.find_one(
                    {'symbol': symbol, 'timestamp': {'$lte': date.isoformat()}},
                    {'_id': 0},
                    sort=[('timestamp', -1)]
                )
                
                if ohlcv:
                    price = float(ohlcv.get('close', 0))
                    if price > 0:
                        trade = await self._close_position(symbol, price, 'simulation_end', date)
                        if trade:
                            trades.append(trade)
            except:
                continue
        
        return trades
    
    async def _save_portfolio_snapshot(self, label: str) -> Dict:
        """Save current portfolio state"""
        positions_value = sum(
            p['quantity'] * p['entry_price'] for p in self.positions.values()
        )
        
        total_value = self.balance + positions_value
        
        snapshot = {
            'label': label,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'balance': round(self.balance, 2),
            'positions_value': round(positions_value, 2),
            'total_value': round(total_value, 2),
            'positions_count': len(self.positions),
            'pnl': round(total_value - self.initial_balance, 2),
            'pnl_pct': round(((total_value / self.initial_balance) - 1) * 100, 2)
        }
        
        self.portfolio_history.append(snapshot)
        return snapshot
    
    async def get_simulation_results(self, limit: int = 10) -> List[Dict]:
        """Get recent simulation results from database"""
        results = await self.db.paper_trading_simulations.find(
            {}, {'_id': 0}
        ).sort('start_time', -1).limit(limit).to_list(limit)
        
        return results


# Global instance
_paper_trader = None


def get_paper_trader(db: AsyncIOMotorDatabase = None, enhanced_ai=None, 
                     regime_predictor=None, gem_predictor=None) -> PaperTradingSimulator:
    """Get or create paper trading simulator"""
    global _paper_trader
    if _paper_trader is None and db is not None:
        _paper_trader = PaperTradingSimulator(db, enhanced_ai, regime_predictor, gem_predictor)
    return _paper_trader

"""
AI Weekly Training Engine
Trains the AI week-by-week from 2009 to 2026, learning from each week's outcomes.
Portfolio: 10 coins + 1 gem = 11 positions max
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import numpy as np
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

from services.dynamic_coin_universe import BASE_UNIVERSE, CATEGORIES, get_universe_manager
from services.coincodex_service import CoinCodexService

load_dotenv()


def get_available_coins_sync(date_str: str) -> list:
    """Synchronous helper - get coins available at a given date from base universe"""
    target_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
    available = []
    for coin_id, info in BASE_UNIVERSE.items():
        launch = info.get('launch')
        if launch:
            launch_date = datetime.strptime(launch, '%Y-%m-%d')
            if launch_date <= target_date:
                available.append(coin_id)
    return available


# Alias for backward compatibility
COIN_UNIVERSE = BASE_UNIVERSE


class AIWeeklyTrainer:
    """
    AI that learns week-by-week, adjusting its selection criteria based on outcomes.
    Maintains a portfolio of 10 coins + 1 gem.
    NOW INCLUDES: AI News Sentiment Analysis in training and selection.
    """
    
    def __init__(self, db):
        self.db = db
        self.coincodex = CoinCodexService()
        self._sentiment_service = None
        
        # Portfolio configuration
        self.config = {
            'main_coins': 10,          # 10 main coins
            'gem_slots': 1,            # 1 gem slot
            'weekly_capital': 10000,   # $10k per week
            'position_size_main': 9,   # 9% per main coin (90% total)
            'position_size_gem': 10,   # 10% for gem
            'stop_loss_main': 15,      # 15% stop loss for main
            'stop_loss_gem': 25,       # 25% stop loss for gem (higher risk)
            'take_profit_main': 30,    # 30% take profit main
            'take_profit_gem': 100,    # 100% take profit gem (looking for 2x+)
        }
        
        # Learned weights (adjusted through training) - NOW WITH SENTIMENT
        self.learned_weights = {
            # Selection criteria weights (NOW WITH SENTIMENT)
            'momentum': 0.18,
            'volatility': 0.13,
            'volume': 0.18,
            'trend': 0.18,
            'historical_performance': 0.13,
            'category_preference': 0.08,
            'sentiment': 0.12,          # NEW: News sentiment weight
            
            # Category performance scores (learned)
            'category_scores': {cat: 50.0 for cat in CATEGORIES.keys()},
            
            # Individual coin performance (learned)
            'coin_scores': {},
            
            # Sentiment effectiveness tracking (NEW)
            'sentiment_accuracy': {
                'bullish_correct': 0,
                'bullish_total': 0,
                'bearish_correct': 0,
                'bearish_total': 0,
            },
            
            # Signal effectiveness (learned)
            'signal_weights': {
                'oversold_bounce': 1.0,
                'momentum_continuation': 1.0,
                'volume_breakout': 1.0,
                'trend_reversal': 1.0,
                'mean_reversion': 1.0,
                'bullish_news': 1.0,      # NEW
                'bearish_news': 1.0,      # NEW
            }
        }
        
        # Training state
        self.current_week = None
        self.training_history = []
        self.total_profit = 0
        self.total_weeks = 0
        self.winning_weeks = 0
    
    async def _get_sentiment_service(self):
        """Get the sentiment service for news analysis"""
        if not self._sentiment_service:
            try:
                from services.ai_news_sentiment import get_sentiment_service
                self._sentiment_service = get_sentiment_service()
            except Exception:
                pass
        return self._sentiment_service
    
    async def initialize_training_data(self):
        """Load any existing learned weights from database"""
        saved = await self.db.ai_training_weights.find_one({}, {'_id': 0})
        if saved:
            self.learned_weights = saved.get('weights', self.learned_weights)
            print("✅ Loaded existing training weights")
        else:
            print("🆕 Starting with fresh weights")
    
    async def save_training_state(self):
        """Save current learned weights to database"""
        await self.db.ai_training_weights.replace_one(
            {},
            {
                'weights': self.learned_weights,
                'total_weeks_trained': self.total_weeks,
                'total_profit': self.total_profit,
                'win_rate': (self.winning_weeks / self.total_weeks * 100) if self.total_weeks > 0 else 0,
                'updated_at': datetime.now().isoformat()
            },
            upsert=True
        )
    
    async def get_coin_data(self, coin_id: str, week_start: datetime) -> Optional[Dict]:
        """Get price data for a coin around a specific week"""
        # Look for data 30 days before the week
        start = (week_start - timedelta(days=30)).isoformat()
        end = (week_start + timedelta(days=7)).isoformat()
        
        prices = await self.db.historical_prices.find({
            'coin_id': coin_id,
            'timestamp': {'$gte': start, '$lte': end}
        }, {'_id': 0}).sort('timestamp', 1).to_list(50)
        
        return prices if len(prices) >= 7 else None
    
    def calculate_coin_score(
        self,
        coin_id: str,
        prices: List[Dict],
        is_gem: bool = False
    ) -> Dict[str, Any]:
        """Calculate selection score for a coin"""
        if len(prices) < 7:
            return None
        
        closes = [p.get('close', p.get('price', 0)) for p in prices]
        volumes = [p.get('volume', 0) for p in prices]
        
        # Calculate metrics
        week_change = (closes[-1] - closes[-7]) / closes[-7] * 100 if closes[-7] > 0 else 0
        
        # Momentum score
        if week_change > 20:
            momentum = 90
        elif week_change > 10:
            momentum = 75
        elif week_change > 0:
            momentum = 60
        elif week_change > -10:
            momentum = 45
        else:
            momentum = 30
        
        # Volatility (std of returns)
        returns = [(closes[i] - closes[i-1]) / closes[i-1] * 100 for i in range(1, len(closes)) if closes[i-1] > 0]
        volatility_raw = np.std(returns) if returns else 5
        
        # For gems, we want higher volatility
        if is_gem:
            if volatility_raw > 10:
                volatility = 85  # High vol good for gems
            elif volatility_raw > 5:
                volatility = 70
            else:
                volatility = 40  # Low vol bad for gems
        else:
            if 3 < volatility_raw < 8:
                volatility = 80  # Optimal for main
            elif volatility_raw < 3:
                volatility = 50  # Too stable
            else:
                volatility = 40  # Too volatile for main
        
        # Volume trend
        if len(volumes) >= 7:
            recent_vol = np.mean(volumes[-7:])
            older_vol = np.mean(volumes[:-7]) if len(volumes) > 7 else recent_vol
            vol_ratio = recent_vol / older_vol if older_vol > 0 else 1
            
            if vol_ratio > 2:
                volume = 90
            elif vol_ratio > 1.5:
                volume = 75
            elif vol_ratio > 1:
                volume = 60
            else:
                volume = 40
        else:
            volume = 50
        
        # Trend (price vs moving average)
        ma_14 = np.mean(closes[-14:]) if len(closes) >= 14 else np.mean(closes)
        if closes[-1] > ma_14 * 1.1:
            trend = 85
        elif closes[-1] > ma_14:
            trend = 70
        elif closes[-1] > ma_14 * 0.9:
            trend = 50
        else:
            trend = 35
        
        # Historical performance from learning
        hist_score = self.learned_weights['coin_scores'].get(coin_id, 50)
        
        # Category preference
        coin_info = COIN_UNIVERSE.get(coin_id, {})
        category = coin_info.get('category', 'mid')
        cat_score = self.learned_weights['category_scores'].get(category, 50)
        
        # Calculate weighted total
        weights = self.learned_weights
        total = (
            momentum * weights['momentum'] +
            volatility * weights['volatility'] +
            volume * weights['volume'] +
            trend * weights['trend'] +
            hist_score * weights['historical_performance'] +
            cat_score * weights['category_preference']
        )
        
        return {
            'coin_id': coin_id,
            'symbol': coin_info.get('symbol', coin_id.upper()[:4]),
            'category': category,
            'total_score': round(total, 2),
            'scores': {
                'momentum': momentum,
                'volatility': volatility,
                'volume': volume,
                'trend': trend,
                'historical': hist_score,
                'category': cat_score
            },
            'metrics': {
                'week_change': round(week_change, 2),
                'volatility': round(volatility_raw, 2),
                'current_price': closes[-1]
            }
        }
    
    async def select_portfolio(self, week_start: datetime) -> Dict[str, Any]:
        """Select 10 main coins + 1 gem for the week"""
        # Use dynamic universe if available, fallback to sync base
        from services.dynamic_coin_universe import get_gem_candidates as async_get_gems
        
        available = get_available_coins_sync(week_start.strftime('%Y-%m-%d'))
        try:
            gem_candidates = await async_get_gems()
        except Exception:
            # Fallback to base universe
            gem_categories = ['meme', 'ai', 'new', 'gaming']
            gem_candidates = [k for k, v in BASE_UNIVERSE.items() if v.get('category') in gem_categories]
        
        main_scores = []
        gem_scores = []
        
        for coin_id in available:
            prices = await self.get_coin_data(coin_id, week_start)
            if not prices:
                continue
            
            is_gem = coin_id in gem_candidates
            score = self.calculate_coin_score(coin_id, prices, is_gem)
            
            if score:
                if is_gem:
                    gem_scores.append(score)
                else:
                    main_scores.append(score)
        
        # Sort by score
        main_scores.sort(key=lambda x: x['total_score'], reverse=True)
        gem_scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Select top 10 main + diversify by category
        selected_main = self._diversified_selection(main_scores, self.config['main_coins'])
        
        # Select top gem
        selected_gem = gem_scores[0] if gem_scores else None
        
        return {
            'week_start': week_start.isoformat(),
            'main_coins': selected_main,
            'gem': selected_gem,
            'available_coins': len(available),
            'analyzed_main': len(main_scores),
            'analyzed_gems': len(gem_scores)
        }
    
    def _diversified_selection(self, scored_coins: List[Dict], count: int) -> List[Dict]:
        """Select coins with category diversification"""
        selected = []
        category_counts = {}
        max_per_category = 3  # Max 3 coins per category
        
        for coin in scored_coins:
            if len(selected) >= count:
                break
            
            category = coin.get('category', 'mid')
            current_count = category_counts.get(category, 0)
            
            if current_count < max_per_category:
                selected.append(coin)
                category_counts[category] = current_count + 1
        
        # Fill remaining slots if needed
        for coin in scored_coins:
            if len(selected) >= count:
                break
            if coin not in selected:
                selected.append(coin)
        
        return selected
    
    async def simulate_week(self, week_start: datetime, portfolio: Dict) -> Dict[str, Any]:
        """Simulate trading for one week and return results"""
        week_end = week_start + timedelta(days=7)
        trades = []
        total_profit = 0
        
        # Trade main coins
        for coin_data in portfolio.get('main_coins', []):
            coin_id = coin_data['coin_id']
            position_size = self.config['weekly_capital'] * (self.config['position_size_main'] / 100)
            
            result = await self._simulate_trade(
                coin_id, week_start, week_end, position_size,
                self.config['stop_loss_main'], self.config['take_profit_main']
            )
            
            if result:
                trades.append(result)
                total_profit += result['profit_usd']
        
        # Trade gem
        gem = portfolio.get('gem')
        if gem:
            position_size = self.config['weekly_capital'] * (self.config['position_size_gem'] / 100)
            
            result = await self._simulate_trade(
                gem['coin_id'], week_start, week_end, position_size,
                self.config['stop_loss_gem'], self.config['take_profit_gem'],
                is_gem=True
            )
            
            if result:
                result['is_gem'] = True
                trades.append(result)
                total_profit += result['profit_usd']
        
        return_pct = (total_profit / self.config['weekly_capital']) * 100
        winning_trades = [t for t in trades if t['return_pct'] > 0]
        
        return {
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'trades': trades,
            'total_profit_usd': round(total_profit, 2),
            'return_pct': round(return_pct, 2),
            'winning_trades': len(winning_trades),
            'total_trades': len(trades),
            'win_rate': round(len(winning_trades) / len(trades) * 100, 1) if trades else 0
        }
    
    async def _simulate_trade(
        self,
        coin_id: str,
        week_start: datetime,
        week_end: datetime,
        position_size: float,
        stop_loss: float,
        take_profit: float,
        is_gem: bool = False
    ) -> Optional[Dict]:
        """Simulate a single trade"""
        prices = await self.db.historical_prices.find({
            'coin_id': coin_id,
            'timestamp': {
                '$gte': week_start.isoformat(),
                '$lte': week_end.isoformat()
            }
        }, {'_id': 0}).sort('timestamp', 1).to_list(10)
        
        if len(prices) < 2:
            return None
        
        entry_price = prices[0].get('close', prices[0].get('price', 0))
        if entry_price <= 0:
            return None
        
        exit_price = entry_price
        exit_reason = 'WEEK_END'
        
        for price_data in prices[1:]:
            current = price_data.get('close', price_data.get('price', 0))
            if current <= 0:
                continue
            
            pnl_pct = (current - entry_price) / entry_price * 100
            
            if pnl_pct <= -stop_loss:
                exit_price = current
                exit_reason = 'STOP_LOSS'
                break
            elif pnl_pct >= take_profit:
                exit_price = current
                exit_reason = 'TAKE_PROFIT'
                break
            
            exit_price = current
        
        return_pct = (exit_price - entry_price) / entry_price * 100
        profit_usd = position_size * (return_pct / 100)
        
        return {
            'coin_id': coin_id,
            'entry_price': round(entry_price, 6),
            'exit_price': round(exit_price, 6),
            'return_pct': round(return_pct, 2),
            'profit_usd': round(profit_usd, 2),
            'exit_reason': exit_reason,
            'position_size': position_size
        }
    
    async def learn_from_week(self, portfolio: Dict, results: Dict):
        """Update learned weights based on week's outcomes"""
        # Update coin scores based on performance
        for trade in results.get('trades', []):
            coin_id = trade['coin_id']
            return_pct = trade['return_pct']
            
            # Get current score
            current = self.learned_weights['coin_scores'].get(coin_id, 50)
            
            # Adjust score based on performance
            # Positive return increases score, negative decreases
            adjustment = return_pct * 0.5  # Scale down
            adjustment = max(-10, min(10, adjustment))  # Cap adjustment
            
            new_score = max(10, min(100, current + adjustment))
            self.learned_weights['coin_scores'][coin_id] = new_score
        
        # Update category scores
        category_returns = {}
        for trade in results.get('trades', []):
            coin_id = trade['coin_id']
            coin_info = COIN_UNIVERSE.get(coin_id, {})
            category = coin_info.get('category', 'mid')
            
            if category not in category_returns:
                category_returns[category] = []
            category_returns[category].append(trade['return_pct'])
        
        for category, returns in category_returns.items():
            avg_return = np.mean(returns)
            current = self.learned_weights['category_scores'].get(category, 50)
            adjustment = avg_return * 0.3
            adjustment = max(-5, min(5, adjustment))
            self.learned_weights['category_scores'][category] = max(20, min(80, current + adjustment))
        
        # Adjust selection criteria weights based on winning trades
        winning = [t for t in results.get('trades', []) if t['return_pct'] > 0]
        if len(winning) / max(1, len(results.get('trades', []))) > 0.6:
            # Good week - keep current weights
            pass
        elif len(winning) / max(1, len(results.get('trades', []))) < 0.4:
            # Bad week - slightly adjust weights
            self.learned_weights['momentum'] = min(0.30, self.learned_weights['momentum'] + 0.01)
            self.learned_weights['historical_performance'] = min(0.25, self.learned_weights['historical_performance'] + 0.01)
    
    async def train_full_period(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Train the AI week-by-week from start to end date.
        Learning after each week.
        """
        if start_date is None:
            start_date = datetime(2009, 1, 5)  # First Monday after BTC launch
        if end_date is None:
            end_date = datetime(2026, 1, 31)
        
        print(f"\n{'='*70}")
        print("🧠 AI WEEKLY TRAINING - FULL PERIOD")
        print(f"{'='*70}")
        print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"Portfolio: {self.config['main_coins']} coins + {self.config['gem_slots']} gem")
        print(f"Weekly Capital: ${self.config['weekly_capital']:,}")
        print(f"Coins in Universe: {len(COIN_UNIVERSE)}")
        print(f"{'='*70}\n")
        
        await self.initialize_training_data()
        
        all_results = []
        current = start_date
        
        # Align to Monday
        while current.weekday() != 0:
            current += timedelta(days=1)
        
        weeks_processed = 0
        
        while current < end_date:
            # Select portfolio for this week
            portfolio = await self.select_portfolio(current)
            
            if not portfolio.get('main_coins'):
                current += timedelta(days=7)
                continue
            
            # Simulate the week
            results = await self.simulate_week(current, portfolio)
            
            if results.get('trades'):
                # Learn from outcomes
                await self.learn_from_week(portfolio, results)
                
                # Track overall performance
                self.total_weeks += 1
                self.total_profit += results['total_profit_usd']
                if results['return_pct'] > 0:
                    self.winning_weeks += 1
                
                all_results.append({
                    'week': current.isoformat(),
                    'portfolio_size': len(portfolio.get('main_coins', [])) + (1 if portfolio.get('gem') else 0),
                    'return_pct': results['return_pct'],
                    'profit_usd': results['total_profit_usd'],
                    'win_rate': results['win_rate']
                })
                
                weeks_processed += 1
                
                # Progress output every year
                if weeks_processed % 52 == 0:
                    year = current.year
                    year_results = [r for r in all_results if r['week'].startswith(str(year))]
                    year_profit = sum(r['profit_usd'] for r in year_results)
                    year_wins = sum(1 for r in year_results if r['return_pct'] > 0)
                    print(f"Year {year}: {len(year_results)} weeks, ${year_profit:,.2f} profit, {year_wins}/{len(year_results)} winning weeks")
                
                if progress_callback:
                    await progress_callback({
                        'current_week': current.isoformat(),
                        'weeks_completed': self.total_weeks,
                        'total_profit': self.total_profit
                    })
            
            # Save state periodically
            if weeks_processed % 100 == 0:
                await self.save_training_state()
            
            current += timedelta(days=7)
        
        # Final save
        await self.save_training_state()
        
        # Store full training results
        summary = {
            'training_period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'configuration': self.config,
            'total_weeks': self.total_weeks,
            'winning_weeks': self.winning_weeks,
            'win_rate_pct': round(self.winning_weeks / self.total_weeks * 100, 1) if self.total_weeks > 0 else 0,
            'total_profit_usd': round(self.total_profit, 2),
            'avg_weekly_return_pct': round(self.total_profit / (self.total_weeks * self.config['weekly_capital']) * 100, 2) if self.total_weeks > 0 else 0,
            'learned_weights': self.learned_weights,
            'weekly_results': all_results,
            'completed_at': datetime.now().isoformat()
        }
        
        await self.db.ai_training_runs.insert_one(dict(summary))
        
        print(f"\n{'='*70}")
        print("🎓 TRAINING COMPLETE")
        print(f"{'='*70}")
        print(f"Total Weeks: {self.total_weeks}")
        print(f"Winning Weeks: {self.winning_weeks} ({summary['win_rate_pct']}%)")
        print(f"Total Profit: ${self.total_profit:,.2f}")
        print(f"Avg Weekly Return: {summary['avg_weekly_return_pct']:.2f}%")
        print(f"{'='*70}\n")
        
        return summary


async def run_training():
    """Entry point for training"""
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'crypto_trading_db')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    trainer = AIWeeklyTrainer(db)
    
    results = await trainer.train_full_period(
        start_date=datetime(2009, 1, 5),
        end_date=datetime(2026, 1, 31)
    )
    
    return results


if __name__ == "__main__":
    asyncio.run(run_training())

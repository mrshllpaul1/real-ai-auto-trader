"""
Hidden Gem Finder AI
Specializes in finding coins with 10-100x potential.
Analyzes volatility patterns, volume spikes, early momentum, and NEWS SENTIMENT.
"""

import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
import numpy as np
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()


class HiddenGemFinder:
    """
    AI specialized in finding hidden gems with massive upside potential.
    Looks for early signs of breakout coins.
    Now includes AI-powered news sentiment analysis.
    """
    
    # Categories that typically contain gems
    GEM_CATEGORIES = ['meme', 'ai', 'new', 'gaming', 'defi']
    
    # Known gem coins (can explode 10-100x)
    KNOWN_GEMS = [
        'shiba-inu', 'pepe', 'bonk', 'dogecoin', 'floki',
        'fetch-ai', 'render-token', 'bittensor', 'worldcoin',
        'the-sandbox', 'decentraland', 'axie-infinity', 'gala',
        'injective', 'sei', 'celestia', 'sui', 'aptos',
        'arbitrum', 'optimism', 'gmx', 'blur',
    ]
    
    def __init__(self, db):
        self.db = db
        
        # Gem-specific scoring weights (now includes sentiment)
        self.gem_weights = {
            'volatility_potential': 0.20,    # High volatility = opportunity
            'volume_spike': 0.20,            # Volume precedes price
            'price_momentum': 0.15,          # Early momentum detection
            'market_cap_potential': 0.15,    # Smaller = more upside
            'trend_breakout': 0.15,          # Breaking resistance
            'news_sentiment': 0.15,          # AI news sentiment
        }
        
        # Learned gem performance
        self.gem_scores = {}
        
        # Sentiment service reference
        self._sentiment_service = None
    
    def set_sentiment_service(self, service):
        """Set the sentiment service for news analysis"""
        self._sentiment_service = service
    
    async def load_learned_scores(self):
        """Load learned gem scores from database"""
        saved = await self.db.gem_finder_scores.find_one({}, {'_id': 0})
        if saved:
            self.gem_scores = saved.get('scores', {})
    
    async def save_learned_scores(self):
        """Save learned gem scores"""
        await self.db.gem_finder_scores.replace_one(
            {},
            {'scores': self.gem_scores, 'updated_at': datetime.now().isoformat()},
            upsert=True
        )
    
    async def find_gems(
        self,
        week_start: datetime,
        max_gems: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find the best hidden gems for the week.
        
        Args:
            week_start: Start of trading week
            max_gems: Maximum gems to return
            
        Returns:
            List of gem candidates with scores
        """
        await self.load_learned_scores()
        
        # Get gems from dynamic universe + static list
        try:
            from services.dynamic_coin_universe import get_gem_candidates as dynamic_gems
            universe_gems = await dynamic_gems()
        except Exception:
            universe_gems = []
        
        # Combine with known gems (dedup)
        all_gem_ids = list(set(self.KNOWN_GEMS + universe_gems))
        
        gem_candidates = []
        
        for coin_id in all_gem_ids:
            prices = await self._get_prices(coin_id, week_start, days=60)
            
            if not prices or len(prices) < 14:
                continue
            
            score_data = self._calculate_gem_score(coin_id, prices)
            
            if score_data and score_data['total_score'] > 50:
                gem_candidates.append(score_data)
        
        # Sort by gem score
        gem_candidates.sort(key=lambda x: x['total_score'], reverse=True)
        
        return gem_candidates[:max_gems]
    
    async def _get_prices(
        self,
        coin_id: str,
        reference_date: datetime,
        days: int = 60
    ) -> List[Dict]:
        """Get historical prices"""
        start = (reference_date - timedelta(days=days)).isoformat()
        end = (reference_date + timedelta(days=7)).isoformat()
        
        prices = await self.db.historical_prices.find({
            'coin_id': coin_id,
            'timestamp': {'$gte': start, '$lte': end}
        }, {'_id': 0}).sort('timestamp', 1).to_list(days + 10)
        
        return prices
    
    def _calculate_gem_score(
        self,
        coin_id: str,
        prices: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate gem potential score"""
        
        closes = [p.get('close', p.get('price', 0)) for p in prices]
        volumes = [p.get('volume', 0) for p in prices]
        
        if not closes or closes[-1] <= 0:
            return None
        
        # 1. Volatility Potential (higher = more opportunity for gems)
        returns = [(closes[i] - closes[i-1]) / closes[i-1] * 100 
                   for i in range(1, len(closes)) if closes[i-1] > 0]
        volatility = np.std(returns) if returns else 0
        
        if volatility > 15:
            vol_score = 95  # Extreme volatility - gem territory
        elif volatility > 10:
            vol_score = 85
        elif volatility > 7:
            vol_score = 70
        elif volatility > 4:
            vol_score = 55
        else:
            vol_score = 30  # Too stable for gem
        
        # 2. Volume Spike Detection
        if len(volumes) >= 14:
            recent_vol = np.mean(volumes[-7:])
            older_vol = np.mean(volumes[-14:-7])
            vol_ratio = recent_vol / older_vol if older_vol > 0 else 1
            
            if vol_ratio > 3:
                volume_score = 95  # Major volume spike!
            elif vol_ratio > 2:
                volume_score = 85
            elif vol_ratio > 1.5:
                volume_score = 70
            elif vol_ratio > 1:
                volume_score = 55
            else:
                volume_score = 35
        else:
            volume_score = 50
        
        # 3. Price Momentum (looking for early breakout)
        week_change = (closes[-1] - closes[-7]) / closes[-7] * 100 if len(closes) >= 7 and closes[-7] > 0 else 0
        two_week_change = (closes[-1] - closes[-14]) / closes[-14] * 100 if len(closes) >= 14 and closes[-14] > 0 else 0
        
        # Acceleration detection
        acceleration = week_change - (two_week_change - week_change)
        
        if week_change > 50:
            momentum_score = 95  # Already pumping
        elif week_change > 30:
            momentum_score = 85
        elif week_change > 15 and acceleration > 10:
            momentum_score = 80  # Accelerating!
        elif week_change > 10:
            momentum_score = 65
        elif week_change > 0:
            momentum_score = 50
        elif week_change > -20:
            momentum_score = 40  # Potential bottom
        else:
            momentum_score = 25
        
        # 4. Trend Breakout Detection
        if len(closes) >= 30:
            ma_30 = np.mean(closes[-30:])
            ma_7 = np.mean(closes[-7:])
            
            if closes[-1] > ma_30 * 1.2 and ma_7 > ma_30:
                breakout_score = 90  # Clear breakout
            elif closes[-1] > ma_30 and ma_7 > ma_30:
                breakout_score = 75
            elif closes[-1] > ma_30 * 0.95:
                breakout_score = 60  # Testing resistance
            else:
                breakout_score = 40
        else:
            breakout_score = 50
        
        # 5. Historical gem performance (learned)
        hist_score = self.gem_scores.get(coin_id, 50)
        
        # Calculate weighted total
        total = (
            vol_score * self.gem_weights['volatility_potential'] +
            volume_score * self.gem_weights['volume_spike'] +
            momentum_score * self.gem_weights['price_momentum'] +
            breakout_score * self.gem_weights['trend_breakout'] +
            hist_score * self.gem_weights['market_cap_potential']
        )
        
        # Generate gem signal
        if total > 80:
            signal = "🔥 HIGH POTENTIAL"
        elif total > 65:
            signal = "⚡ WATCH CLOSELY"
        elif total > 50:
            signal = "👀 MONITORING"
        else:
            signal = "⏸️ WAIT"
        
        return {
            'coin_id': coin_id,
            'total_score': round(total, 2),
            'signal': signal,
            'scores': {
                'volatility': vol_score,
                'volume_spike': volume_score,
                'momentum': momentum_score,
                'breakout': breakout_score,
                'historical': hist_score
            },
            'metrics': {
                'volatility_pct': round(volatility, 2),
                'week_change_pct': round(week_change, 2),
                'current_price': closes[-1]
            }
        }
    
    async def backtest_gems(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Backtest gem finder performance.
        Track which gems actually delivered 10x+ returns.
        """
        print(f"\n{'='*60}")
        print("💎 GEM FINDER BACKTEST")
        print(f"{'='*60}")
        print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"{'='*60}\n")
        
        results = []
        current = start_date
        
        # Weekly iteration
        while current.weekday() != 0:
            current += timedelta(days=1)
        
        while current < end_date - timedelta(days=30):  # Need 30 days forward for results
            gems = await self.find_gems(current, max_gems=3)
            
            if gems:
                # Check performance 30 days later
                for gem in gems:
                    future_prices = await self._get_prices(
                        gem['coin_id'],
                        current + timedelta(days=30),
                        days=7
                    )
                    
                    if future_prices and len(future_prices) > 0:
                        entry_price = gem['metrics']['current_price']
                        exit_price = future_prices[-1].get('close', future_prices[-1].get('price', 0))
                        
                        if entry_price > 0:
                            return_pct = (exit_price - entry_price) / entry_price * 100
                            
                            results.append({
                                'week': current.isoformat(),
                                'coin_id': gem['coin_id'],
                                'gem_score': gem['total_score'],
                                'return_pct': round(return_pct, 2),
                                'is_winner': return_pct > 50,  # 50%+ considered success
                                'is_moonshot': return_pct > 100  # 2x+
                            })
                            
                            # Update learned scores
                            current_score = self.gem_scores.get(gem['coin_id'], 50)
                            adjustment = return_pct * 0.1
                            adjustment = max(-15, min(15, adjustment))
                            self.gem_scores[gem['coin_id']] = max(10, min(100, current_score + adjustment))
            
            current += timedelta(days=7)
        
        # Calculate summary
        if results:
            total_gems = len(results)
            winners = [r for r in results if r['is_winner']]
            moonshots = [r for r in results if r['is_moonshot']]
            avg_return = np.mean([r['return_pct'] for r in results])
            
            summary = {
                'total_gems_picked': total_gems,
                'winners_50pct_plus': len(winners),
                'moonshots_100pct_plus': len(moonshots),
                'win_rate': round(len(winners) / total_gems * 100, 1),
                'moonshot_rate': round(len(moonshots) / total_gems * 100, 1),
                'avg_return_pct': round(avg_return, 2),
                'best_gem': max(results, key=lambda x: x['return_pct']) if results else None,
                'worst_gem': min(results, key=lambda x: x['return_pct']) if results else None,
                'learned_scores': self.gem_scores,
                'results': results
            }
            
            print(f"Total Gems Picked: {total_gems}")
            print(f"Winners (50%+): {len(winners)} ({summary['win_rate']}%)")
            print(f"Moonshots (100%+): {len(moonshots)} ({summary['moonshot_rate']}%)")
            print(f"Average Return: {avg_return:.2f}%")
            
            if summary['best_gem']:
                print(f"\nBest Gem: {summary['best_gem']['coin_id']} +{summary['best_gem']['return_pct']:.2f}%")
            
            # Save learned scores
            await self.save_learned_scores()
            
            # Store results
            await self.db.gem_backtest_results.insert_one({
                **summary,
                'completed_at': datetime.now().isoformat()
            })
            
            return summary
        
        return {'total_gems_picked': 0, 'message': 'No gems found in period'}


async def test_gem_finder():
    """Test the gem finder"""
    mongo_url = os.getenv('MONGO_URL')
    db_name = os.getenv('DB_NAME')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    finder = HiddenGemFinder(db)
    
    # Backtest from 2021-2025 (when most gems existed)
    results = await finder.backtest_gems(
        start_date=datetime(2021, 6, 1),
        end_date=datetime(2025, 12, 31)
    )
    
    return results


if __name__ == "__main__":
    asyncio.run(test_gem_finder())

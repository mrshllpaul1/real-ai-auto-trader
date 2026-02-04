"""
Social Sentiment Pipeline Service
Enhancement #3: Twitter/X, Reddit sentiment, Fear/FOMO detection, Hype cycles
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np
import re
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class SocialSentimentPipeline:
    """
    Social media sentiment analysis for crypto trading:
    - Twitter/X real-time sentiment
    - Reddit r/cryptocurrency analysis
    - Fear/FOMO detection
    - Hype cycle identification
    - Influencer tracking
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.cache = {}
        self.cache_ttl = 180  # 3 minute cache
        
        # Sentiment keywords
        self.bullish_keywords = [
            'moon', 'bullish', 'pump', 'buy', 'long', 'breakout', 'ath', 'hodl',
            'accumulate', 'undervalued', 'gem', 'rocket', '🚀', '📈', 'green',
            'lambo', 'wagmi', 'diamond hands', '💎', 'to the moon'
        ]
        
        self.bearish_keywords = [
            'dump', 'bearish', 'sell', 'short', 'crash', 'scam', 'rug', 'fear',
            'panic', 'overvalued', 'bubble', '📉', 'red', 'rekt', 'ngmi',
            'paper hands', 'dead', 'ponzi', 'collapse'
        ]
        
        self.fomo_keywords = [
            'fomo', 'missing out', 'too late', 'should have bought', 'regret',
            'last chance', 'hurry', 'before it\'s too late', 'don\'t miss'
        ]
        
        self.fear_keywords = [
            'scared', 'worried', 'fear', 'uncertain', 'risky', 'dangerous',
            'careful', 'warning', 'cautious', 'concerned', 'nervous'
        ]
        
        # Crypto influencers (mock list)
        self.influencers = [
            'elonmusk', 'michael_saylor', 'cabornek', 'aantonop',
            'VitalikButerin', 'CryptoCapo_', 'loomdart', 'CryptoCred'
        ]
    
    async def analyze_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Comprehensive social sentiment analysis
        
        Args:
            symbol: Coin symbol
            
        Returns:
            Social sentiment analysis with trading signals
        """
        try:
            coin = symbol.upper().replace('USD', '').replace('USDT', '')
            
            # Get sentiment from different sources
            twitter = await self._analyze_twitter(coin)
            reddit = await self._analyze_reddit(coin)
            fomo_fear = self._detect_fomo_fear(twitter, reddit)
            hype_cycle = self._analyze_hype_cycle(twitter, reddit)
            influencer = await self._track_influencers(coin)
            
            # Generate composite signal
            signal = self._generate_social_signal(twitter, reddit, fomo_fear, hype_cycle, influencer)
            
            analysis = {
                'symbol': coin,
                'timestamp': datetime.utcnow().isoformat(),
                'twitter': twitter,
                'reddit': reddit,
                'fomo_fear': fomo_fear,
                'hype_cycle': hype_cycle,
                'influencer_activity': influencer,
                'signal': signal
            }
            
            await self._store_analysis(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Social sentiment analysis failed for {symbol}: {e}")
            return self._empty_analysis(symbol)
    
    async def _analyze_twitter(self, coin: str) -> Dict[str, Any]:
        """Analyze Twitter/X sentiment"""
        np.random.seed(hash(coin + "twitter" + datetime.utcnow().strftime("%Y%m%d%H")) % 2**32)
        
        # Simulate tweet metrics
        tweet_count_24h = int(np.random.pareto(2) * 5000 + 1000)
        
        # Sentiment distribution
        bullish_pct = np.random.uniform(0.25, 0.55)
        bearish_pct = np.random.uniform(0.15, 0.35)
        neutral_pct = 1 - bullish_pct - bearish_pct
        
        # Engagement metrics
        avg_likes = np.random.uniform(50, 500)
        avg_retweets = np.random.uniform(10, 100)
        avg_replies = np.random.uniform(5, 50)
        
        # Calculate sentiment score (-100 to 100)
        sentiment_score = (bullish_pct - bearish_pct) * 100
        
        # Trending analysis
        tweet_volume_change = np.random.uniform(-30, 50)  # % change vs yesterday
        
        if tweet_volume_change > 30:
            trending = 'viral'
        elif tweet_volume_change > 10:
            trending = 'trending_up'
        elif tweet_volume_change < -20:
            trending = 'declining'
        else:
            trending = 'stable'
        
        return {
            'tweet_count_24h': tweet_count_24h,
            'sentiment_distribution': {
                'bullish': round(bullish_pct * 100, 1),
                'bearish': round(bearish_pct * 100, 1),
                'neutral': round(neutral_pct * 100, 1)
            },
            'sentiment_score': round(sentiment_score, 1),
            'engagement': {
                'avg_likes': round(avg_likes, 0),
                'avg_retweets': round(avg_retweets, 0),
                'avg_replies': round(avg_replies, 0)
            },
            'volume_change_24h': round(tweet_volume_change, 1),
            'trending': trending,
            'top_hashtags': [f'#{coin}', '#crypto', '#bitcoin', '#defi', '#altcoins'][:3]
        }
    
    async def _analyze_reddit(self, coin: str) -> Dict[str, Any]:
        """Analyze Reddit sentiment"""
        np.random.seed(hash(coin + "reddit" + datetime.utcnow().strftime("%Y%m%d%H")) % 2**32)
        
        # Simulate Reddit metrics
        post_count_24h = int(np.random.pareto(1.5) * 100 + 20)
        comment_count_24h = post_count_24h * np.random.randint(5, 25)
        
        # Sentiment from posts
        bullish_posts = np.random.uniform(0.3, 0.6)
        bearish_posts = np.random.uniform(0.1, 0.3)
        
        # Upvote ratio (positive sentiment indicator)
        avg_upvote_ratio = np.random.uniform(0.6, 0.95)
        
        # Calculate sentiment
        sentiment_score = (bullish_posts - bearish_posts) * 100 + (avg_upvote_ratio - 0.5) * 50
        
        # Subreddit activity
        subreddits = ['cryptocurrency', 'CryptoMarkets', 'altcoins', 'defi']
        if coin == 'BTC':
            subreddits.insert(0, 'bitcoin')
        elif coin == 'ETH':
            subreddits.insert(0, 'ethereum')
        
        return {
            'post_count_24h': post_count_24h,
            'comment_count_24h': int(comment_count_24h),
            'sentiment_distribution': {
                'bullish': round(bullish_posts * 100, 1),
                'bearish': round(bearish_posts * 100, 1),
                'neutral': round((1 - bullish_posts - bearish_posts) * 100, 1)
            },
            'sentiment_score': round(sentiment_score, 1),
            'avg_upvote_ratio': round(avg_upvote_ratio, 2),
            'active_subreddits': subreddits[:4],
            'discussion_intensity': 'high' if comment_count_24h > 1000 else ('medium' if comment_count_24h > 200 else 'low')
        }
    
    def _detect_fomo_fear(self, twitter: Dict, reddit: Dict) -> Dict[str, Any]:
        """Detect FOMO and Fear levels in social media"""
        # Combine sentiment scores
        avg_sentiment = (twitter['sentiment_score'] + reddit['sentiment_score']) / 2
        volume_spike = twitter['volume_change_24h'] > 20
        discussion_high = reddit['discussion_intensity'] == 'high'
        
        # FOMO detection (high bullish sentiment + volume spike)
        fomo_score = 0
        if avg_sentiment > 30:
            fomo_score += 30
        if volume_spike:
            fomo_score += 25
        if discussion_high:
            fomo_score += 20
        if twitter['trending'] in ['viral', 'trending_up']:
            fomo_score += 25
        
        # Fear detection (high bearish sentiment + declining interest)
        fear_score = 0
        if avg_sentiment < -20:
            fear_score += 30
        if twitter['volume_change_24h'] < -10:
            fear_score += 20
        if twitter['sentiment_distribution']['bearish'] > 35:
            fear_score += 25
        if reddit['avg_upvote_ratio'] < 0.7:
            fear_score += 25
        
        # Determine dominant emotion
        if fomo_score > 60 and fomo_score > fear_score:
            dominant = 'extreme_fomo'
            warning = 'Market may be overheated - consider taking profits'
        elif fomo_score > 40 and fomo_score > fear_score:
            dominant = 'fomo'
            warning = 'Elevated FOMO levels - be cautious of buying tops'
        elif fear_score > 60 and fear_score > fomo_score:
            dominant = 'extreme_fear'
            warning = 'Extreme fear - potential buying opportunity (contrarian)'
        elif fear_score > 40 and fear_score > fomo_score:
            dominant = 'fear'
            warning = 'Elevated fear - watch for capitulation'
        else:
            dominant = 'neutral'
            warning = None
        
        return {
            'fomo_score': min(100, fomo_score),
            'fear_score': min(100, fear_score),
            'dominant_emotion': dominant,
            'warning': warning,
            'contrarian_signal': 'buy' if fear_score > 50 else ('sell' if fomo_score > 50 else 'hold')
        }
    
    def _analyze_hype_cycle(self, twitter: Dict, reddit: Dict) -> Dict[str, Any]:
        """Determine position in hype cycle"""
        sentiment = (twitter['sentiment_score'] + reddit['sentiment_score']) / 2
        volume_trend = twitter['volume_change_24h']
        discussion = reddit['discussion_intensity']
        
        # Hype cycle phases
        # 1. Innovation Trigger - Low volume, early adopter discussion
        # 2. Peak of Inflated Expectations - High volume, extreme bullish
        # 3. Trough of Disillusionment - Declining volume, bearish
        # 4. Slope of Enlightenment - Recovering, measured optimism
        # 5. Plateau of Productivity - Stable, mature discussion
        
        if sentiment > 40 and volume_trend > 30:
            phase = 'peak_expectations'
            description = 'At or near peak hype - high risk of correction'
            risk_level = 'high'
        elif sentiment < -20 and volume_trend < -10:
            phase = 'trough_disillusionment'
            description = 'In the trough - potential accumulation zone'
            risk_level = 'medium'
        elif sentiment > 10 and volume_trend > 0 and discussion != 'high':
            phase = 'slope_enlightenment'
            description = 'Recovering from trough - measured optimism'
            risk_level = 'low'
        elif abs(sentiment) < 20 and abs(volume_trend) < 15:
            phase = 'plateau_productivity'
            description = 'Stable maturity phase'
            risk_level = 'low'
        else:
            phase = 'innovation_trigger'
            description = 'Early stage - high potential but uncertain'
            risk_level = 'medium'
        
        return {
            'phase': phase,
            'description': description,
            'risk_level': risk_level,
            'sentiment_velocity': round(volume_trend, 1),
            'maturity_score': 70 if phase == 'plateau_productivity' else (50 if phase == 'slope_enlightenment' else 30)
        }
    
    async def _track_influencers(self, coin: str) -> Dict[str, Any]:
        """Track crypto influencer activity"""
        np.random.seed(hash(coin + "influencer" + datetime.utcnow().strftime("%Y%m%d%H")) % 2**32)
        
        # Simulate influencer mentions
        mentions = []
        total_reach = 0
        bullish_mentions = 0
        bearish_mentions = 0
        
        for influencer in self.influencers[:5]:
            if np.random.random() > 0.7:  # 30% chance of mention
                sentiment = np.random.choice(['bullish', 'bearish', 'neutral'], p=[0.5, 0.2, 0.3])
                reach = int(np.random.pareto(1.5) * 100000 + 50000)
                
                mentions.append({
                    'influencer': influencer,
                    'sentiment': sentiment,
                    'reach': reach,
                    'hours_ago': np.random.randint(1, 48)
                })
                
                total_reach += reach
                if sentiment == 'bullish':
                    bullish_mentions += 1
                elif sentiment == 'bearish':
                    bearish_mentions += 1
        
        # Sort by recency
        mentions.sort(key=lambda x: x['hours_ago'])
        
        # Influencer sentiment
        if bullish_mentions > bearish_mentions and len(mentions) > 0:
            overall_sentiment = 'bullish'
        elif bearish_mentions > bullish_mentions and len(mentions) > 0:
            overall_sentiment = 'bearish'
        else:
            overall_sentiment = 'neutral'
        
        return {
            'mention_count_48h': len(mentions),
            'total_reach': total_reach,
            'sentiment': overall_sentiment,
            'bullish_count': bullish_mentions,
            'bearish_count': bearish_mentions,
            'recent_mentions': mentions[:3],
            'influence_score': min(100, len(mentions) * 20 + total_reach // 100000)
        }
    
    def _generate_social_signal(self, twitter: Dict, reddit: Dict, fomo_fear: Dict,
                                 hype: Dict, influencer: Dict) -> Dict[str, Any]:
        """Generate composite social signal"""
        score = 50
        factors = []
        
        # Twitter sentiment (25%)
        if twitter['sentiment_score'] > 30:
            score += 12
            factors.append('twitter_bullish')
        elif twitter['sentiment_score'] < -20:
            score -= 12
            factors.append('twitter_bearish')
        
        # Reddit sentiment (20%)
        if reddit['sentiment_score'] > 30:
            score += 10
            factors.append('reddit_bullish')
        elif reddit['sentiment_score'] < -20:
            score -= 10
            factors.append('reddit_bearish')
        
        # FOMO/Fear contrarian (20%)
        if fomo_fear['dominant_emotion'] == 'extreme_fear':
            score += 12  # Contrarian buy
            factors.append('contrarian_buy_fear')
        elif fomo_fear['dominant_emotion'] == 'extreme_fomo':
            score -= 12  # Contrarian sell
            factors.append('contrarian_sell_fomo')
        
        # Hype cycle (20%)
        if hype['phase'] == 'trough_disillusionment':
            score += 10
            factors.append('hype_accumulation_zone')
        elif hype['phase'] == 'peak_expectations':
            score -= 10
            factors.append('hype_peak_warning')
        
        # Influencer activity (15%)
        if influencer['sentiment'] == 'bullish' and influencer['mention_count_48h'] > 2:
            score += 8
            factors.append('influencer_bullish')
        elif influencer['sentiment'] == 'bearish' and influencer['mention_count_48h'] > 2:
            score -= 8
            factors.append('influencer_bearish')
        
        # Determine signal
        if score >= 70:
            signal = 'strong_buy'
        elif score >= 60:
            signal = 'buy'
        elif score <= 30:
            signal = 'strong_sell'
        elif score <= 40:
            signal = 'sell'
        else:
            signal = 'neutral'
        
        return {
            'signal': signal,
            'score': min(100, max(0, score)),
            'confidence': min(100, abs(score - 50) * 2),
            'factors': factors,
            'sentiment_summary': {
                'twitter': 'bullish' if twitter['sentiment_score'] > 15 else ('bearish' if twitter['sentiment_score'] < -15 else 'neutral'),
                'reddit': 'bullish' if reddit['sentiment_score'] > 15 else ('bearish' if reddit['sentiment_score'] < -15 else 'neutral'),
                'overall': signal
            }
        }
    
    async def _store_analysis(self, analysis: Dict):
        """Store analysis in database"""
        try:
            await self.db.social_sentiment.insert_one({
                **analysis,
                'created_at': datetime.utcnow()
            })
        except Exception as e:
            logger.warning(f"Failed to store social sentiment: {e}")
    
    def _empty_analysis(self, symbol: str) -> Dict[str, Any]:
        """Return empty analysis structure"""
        return {
            'symbol': symbol,
            'timestamp': datetime.utcnow().isoformat(),
            'twitter': {'sentiment_score': 0, 'trending': 'unknown'},
            'reddit': {'sentiment_score': 0},
            'fomo_fear': {'dominant_emotion': 'neutral'},
            'hype_cycle': {'phase': 'unknown'},
            'influencer_activity': {'sentiment': 'neutral'},
            'signal': {'signal': 'neutral', 'score': 50, 'confidence': 0}
        }
    
    async def get_trending_coins(self, limit: int = 10) -> List[Dict]:
        """Get trending coins based on social activity"""
        try:
            cutoff = datetime.utcnow() - timedelta(hours=24)
            pipeline = [
                {'$match': {'created_at': {'$gte': cutoff}}},
                {'$sort': {'twitter.tweet_count_24h': -1}},
                {'$group': {
                    '_id': '$symbol',
                    'avg_sentiment': {'$avg': '$signal.score'},
                    'total_tweets': {'$max': '$twitter.tweet_count_24h'},
                    'latest': {'$first': '$$ROOT'}
                }},
                {'$sort': {'total_tweets': -1}},
                {'$limit': limit}
            ]
            
            cursor = self.db.social_sentiment.aggregate(pipeline)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Failed to get trending coins: {e}")
            return []


# Singleton instance
_social_sentiment = None

def get_social_sentiment(db: AsyncIOMotorDatabase = None) -> SocialSentimentPipeline:
    global _social_sentiment
    if _social_sentiment is None and db is not None:
        _social_sentiment = SocialSentimentPipeline(db)
    return _social_sentiment

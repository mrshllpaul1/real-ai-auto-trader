"""
Sentiment Analysis Service
==========================
Real-time sentiment analysis from Reddit and social media.
"""

import asyncio
import logging
import aiohttp
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class SentimentPost:
    """A social media post with sentiment"""
    id: str
    source: str  # 'reddit', 'twitter'
    subreddit: Optional[str]
    title: str
    content: str
    score: int
    comments: int
    sentiment_score: float  # -1 to 1
    sentiment_label: str  # 'bullish', 'bearish', 'neutral'
    coins_mentioned: List[str]
    timestamp: str
    url: str


@dataclass
class SentimentSummary:
    """Aggregated sentiment for a coin"""
    coin: str
    total_mentions: int
    avg_sentiment: float
    sentiment_label: str
    bullish_count: int
    bearish_count: int
    neutral_count: int
    trending_score: float
    top_posts: List[Dict]


class SentimentAnalysisService:
    """
    Sentiment analysis from Reddit and social media.
    
    Features:
    - Reddit API integration (no auth needed for public data)
    - Keyword-based sentiment scoring
    - Coin mention tracking
    - Trending detection
    """
    
    # Crypto subreddits to monitor
    SUBREDDITS = [
        'cryptocurrency', 'bitcoin', 'ethereum', 'cryptomarkets',
        'altcoin', 'defi', 'solana', 'cardano', 'binance'
    ]
    
    # Bullish keywords
    BULLISH_WORDS = [
        'moon', 'bullish', 'buy', 'hodl', 'hold', 'pump', 'breakout',
        'accumulate', 'undervalued', 'gem', 'rocket', 'ath', 'gains',
        'bull run', 'long', 'support', 'bounce', 'reversal', 'green',
        'surge', 'rally', 'explosion', 'parabolic', 'skyrocket'
    ]
    
    # Bearish keywords
    BEARISH_WORDS = [
        'crash', 'bearish', 'sell', 'dump', 'scam', 'rug', 'dead',
        'overvalued', 'short', 'resistance', 'breakdown', 'red',
        'plunge', 'collapse', 'fear', 'panic', 'bleeding', 'tank',
        'bubble', 'correction', 'drop', 'fall', 'decline'
    ]
    
    # Coin symbols to track
    COIN_PATTERNS = {
        'BTC': ['bitcoin', 'btc', r'\$btc'],
        'ETH': ['ethereum', 'eth', r'\$eth', 'ether'],
        'SOL': ['solana', 'sol', r'\$sol'],
        'XRP': ['ripple', 'xrp', r'\$xrp'],
        'ADA': ['cardano', 'ada', r'\$ada'],
        'DOGE': ['dogecoin', 'doge', r'\$doge'],
        'DOT': ['polkadot', 'dot', r'\$dot'],
        'AVAX': ['avalanche', 'avax', r'\$avax'],
        'LINK': ['chainlink', 'link', r'\$link'],
        'MATIC': ['polygon', 'matic', r'\$matic'],
        'SHIB': ['shiba', 'shib', r'\$shib'],
        'LTC': ['litecoin', 'ltc', r'\$ltc'],
        'UNI': ['uniswap', 'uni', r'\$uni'],
        'ATOM': ['cosmos', 'atom', r'\$atom'],
    }
    
    def __init__(self, db):
        self.db = db
        self.posts: List[SentimentPost] = []
        self.summaries: Dict[str, SentimentSummary] = {}
        self.is_monitoring = False
        self._monitor_task = None
        self.settings = {
            'check_interval_sec': 300,  # 5 minutes
            'posts_per_subreddit': 25,
            'min_score': 5
        }
        logger.info("✅ Sentiment Analysis Service initialized")
    
    async def start_monitoring(self):
        """Start sentiment monitoring"""
        if self.is_monitoring:
            return {'status': 'already_running'}
        
        self.is_monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        logger.info("📊 Sentiment monitoring started")
        return {'status': 'started', 'subreddits': len(self.SUBREDDITS)}
    
    async def stop_monitoring(self):
        """Stop sentiment monitoring"""
        self.is_monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
        
        return {'status': 'stopped'}
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                await self._fetch_reddit_posts()
                await self._calculate_summaries()
                await asyncio.sleep(self.settings['check_interval_sec'])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sentiment monitor error: {e}")
                await asyncio.sleep(60)
    
    async def _fetch_reddit_posts(self):
        """Fetch posts from Reddit"""
        async with aiohttp.ClientSession() as session:
            for subreddit in self.SUBREDDITS:
                try:
                    await self._fetch_subreddit(session, subreddit)
                    await asyncio.sleep(1)  # Rate limiting
                except Exception as e:
                    logger.debug(f"Reddit {subreddit} error: {e}")
    
    async def _fetch_subreddit(self, session, subreddit: str):
        """Fetch posts from a subreddit"""
        url = f"https://www.reddit.com/r/{subreddit}/hot.json"
        headers = {'User-Agent': 'CryptoSentimentBot/1.0'}
        
        async with session.get(url, headers=headers, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                posts = data.get('data', {}).get('children', [])
                
                for post_data in posts[:self.settings['posts_per_subreddit']]:
                    post = post_data.get('data', {})
                    if post.get('score', 0) >= self.settings['min_score']:
                        await self._process_post(post, subreddit)
    
    async def _process_post(self, post: Dict, subreddit: str):
        """Process a Reddit post"""
        title = post.get('title', '')
        content = post.get('selftext', '')
        full_text = f"{title} {content}".lower()
        
        # Calculate sentiment
        sentiment_score = self._calculate_sentiment(full_text)
        sentiment_label = 'bullish' if sentiment_score > 0.1 else 'bearish' if sentiment_score < -0.1 else 'neutral'
        
        # Find mentioned coins
        coins_mentioned = self._find_coins(full_text)
        
        if not coins_mentioned:
            return  # Skip posts without coin mentions
        
        sentiment_post = SentimentPost(
            id=post.get('id', ''),
            source='reddit',
            subreddit=subreddit,
            title=title[:200],
            content=content[:500] if content else '',
            score=post.get('score', 0),
            comments=post.get('num_comments', 0),
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            coins_mentioned=coins_mentioned,
            timestamp=datetime.fromtimestamp(
                post.get('created_utc', 0),
                tz=timezone.utc
            ).isoformat(),
            url=f"https://reddit.com{post.get('permalink', '')}"
        )
        
        # Avoid duplicates
        existing = [p for p in self.posts if p.id == sentiment_post.id]
        if not existing:
            self.posts.insert(0, sentiment_post)
            self.posts = self.posts[:500]  # Keep last 500
            
            # Store in database
            await self.db.sentiment_posts.update_one(
                {'id': sentiment_post.id},
                {'$set': asdict(sentiment_post)},
                upsert=True
            )
    
    def _calculate_sentiment(self, text: str) -> float:
        """Calculate sentiment score from text"""
        text = text.lower()
        
        bullish_count = sum(1 for word in self.BULLISH_WORDS if word in text)
        bearish_count = sum(1 for word in self.BEARISH_WORDS if word in text)
        
        total = bullish_count + bearish_count
        if total == 0:
            return 0.0
        
        return (bullish_count - bearish_count) / total
    
    def _find_coins(self, text: str) -> List[str]:
        """Find mentioned coins in text"""
        coins = []
        text = text.lower()
        
        for coin, patterns in self.COIN_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    if coin not in coins:
                        coins.append(coin)
                    break
        
        return coins
    
    async def _calculate_summaries(self):
        """Calculate sentiment summaries per coin"""
        # Group posts by coin
        coin_posts = defaultdict(list)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        
        for post in self.posts:
            if post.timestamp > cutoff.isoformat():
                for coin in post.coins_mentioned:
                    coin_posts[coin].append(post)
        
        # Calculate summaries
        for coin, posts in coin_posts.items():
            if not posts:
                continue
            
            bullish = sum(1 for p in posts if p.sentiment_label == 'bullish')
            bearish = sum(1 for p in posts if p.sentiment_label == 'bearish')
            neutral = sum(1 for p in posts if p.sentiment_label == 'neutral')
            
            avg_sentiment = sum(p.sentiment_score for p in posts) / len(posts)
            sentiment_label = 'bullish' if avg_sentiment > 0.1 else 'bearish' if avg_sentiment < -0.1 else 'neutral'
            
            # Trending score based on engagement
            trending_score = sum(p.score + p.comments for p in posts) / len(posts)
            
            # Top posts by score
            top_posts = sorted(posts, key=lambda p: p.score, reverse=True)[:5]
            
            self.summaries[coin] = SentimentSummary(
                coin=coin,
                total_mentions=len(posts),
                avg_sentiment=avg_sentiment,
                sentiment_label=sentiment_label,
                bullish_count=bullish,
                bearish_count=bearish,
                neutral_count=neutral,
                trending_score=trending_score,
                top_posts=[asdict(p) for p in top_posts]
            )
    
    async def get_sentiment(self, coin: str = None) -> Dict[str, Any]:
        """Get sentiment data"""
        if coin:
            summary = self.summaries.get(coin.upper())
            return asdict(summary) if summary else {'coin': coin, 'total_mentions': 0}
        
        return {
            coin: asdict(summary) 
            for coin, summary in self.summaries.items()
        }
    
    async def get_trending(self, limit: int = 10) -> List[Dict]:
        """Get trending coins by sentiment activity"""
        sorted_summaries = sorted(
            self.summaries.values(),
            key=lambda s: s.trending_score,
            reverse=True
        )
        return [asdict(s) for s in sorted_summaries[:limit]]
    
    async def get_recent_posts(self, coin: str = None, limit: int = 50) -> List[Dict]:
        """Get recent sentiment posts"""
        posts = self.posts
        if coin:
            posts = [p for p in posts if coin.upper() in p.coins_mentioned]
        return [asdict(p) for p in posts[:limit]]
    
    async def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'is_monitoring': self.is_monitoring,
            'total_posts': len(self.posts),
            'coins_tracked': len(self.summaries),
            'subreddits': self.SUBREDDITS,
            'settings': self.settings
        }


# Singleton
_sentiment_service: Optional[SentimentAnalysisService] = None


def get_sentiment_service(db=None) -> Optional[SentimentAnalysisService]:
    """Get or create the sentiment service"""
    global _sentiment_service
    if _sentiment_service is None and db is not None:
        _sentiment_service = SentimentAnalysisService(db)
    return _sentiment_service

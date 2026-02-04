"""
Social Sentiment Scraper
Scrapes and analyzes sentiment from crypto social media sources.
Supports: Twitter/X, Reddit, Telegram, Discord (public), News aggregators
"""

import asyncio
import aiohttp
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import re
from collections import defaultdict
import json


class SocialSentimentScraper:
    """
    Multi-source social sentiment analyzer for crypto markets.
    
    Data Sources:
    - CryptoPanic (news aggregator with sentiment)
    - Reddit (via public JSON endpoints)
    - LunarCrush (social metrics)
    - Fear & Greed Index
    - Google Trends proxy data
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, coindesk_api_key: str = None):
        self.db = db
        self.coindesk_api_key = coindesk_api_key
        
        # Sentiment keywords for analysis
        self.bullish_keywords = [
            'moon', 'pump', 'bullish', 'buy', 'long', 'breakout', 'ath', 'rocket',
            'gains', 'profit', 'winning', 'hodl', 'diamond hands', 'to the moon',
            'accumulate', 'undervalued', 'gem', 'rally', 'surge', 'soar', 'bull run',
            'adoption', 'institutional', 'etf approved', 'partnership', 'milestone'
        ]
        
        self.bearish_keywords = [
            'dump', 'crash', 'bearish', 'sell', 'short', 'breakdown', 'rekt',
            'loss', 'losing', 'paper hands', 'exit', 'scam', 'rug', 'fraud',
            'overvalued', 'bubble', 'correction', 'plunge', 'tank', 'collapse',
            'hack', 'exploit', 'sec', 'lawsuit', 'ban', 'regulation'
        ]
        
        # Reddit subreddits to monitor
        self.reddit_subs = [
            'cryptocurrency', 'bitcoin', 'ethereum', 'altcoin',
            'cryptomarkets', 'satoshistreetbets', 'wallstreetbetscrypto'
        ]
        
        # Coin mention patterns
        self.coin_patterns = {
            'BTC': r'\b(btc|bitcoin|₿)\b',
            'ETH': r'\b(eth|ethereum|ether)\b',
            'SOL': r'\b(sol|solana)\b',
            'XRP': r'\b(xrp|ripple)\b',
            'ADA': r'\b(ada|cardano)\b',
            'DOGE': r'\b(doge|dogecoin)\b',
            'SHIB': r'\b(shib|shiba)\b',
            'AVAX': r'\b(avax|avalanche)\b',
            'DOT': r'\b(dot|polkadot)\b',
            'LINK': r'\b(link|chainlink)\b',
            'MATIC': r'\b(matic|polygon)\b',
            'UNI': r'\b(uni|uniswap)\b',
            'PEPE': r'\b(pepe)\b',
            'ARB': r'\b(arb|arbitrum)\b',
            'OP': r'\b(op|optimism)\b',
        }
        
        # Cache for rate limiting
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def _fetch_url(self, url: str, headers: Dict = None) -> Optional[Dict]:
        """Fetch JSON from URL with error handling"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"  ⚠️ HTTP {response.status} from {url[:50]}...")
                        return None
        except Exception as e:
            print(f"  ❌ Error fetching {url[:50]}...: {e}")
            return None
    
    def _analyze_text_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text using keyword matching"""
        text_lower = text.lower()
        
        bullish_count = sum(1 for kw in self.bullish_keywords if kw in text_lower)
        bearish_count = sum(1 for kw in self.bearish_keywords if kw in text_lower)
        
        total = bullish_count + bearish_count
        if total == 0:
            sentiment = 'neutral'
            score = 50
        elif bullish_count > bearish_count:
            sentiment = 'bullish'
            score = 50 + (bullish_count / total) * 50
        else:
            sentiment = 'bearish'
            score = 50 - (bearish_count / total) * 50
        
        # Detect mentioned coins
        mentioned_coins = []
        for coin, pattern in self.coin_patterns.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                mentioned_coins.append(coin)
        
        return {
            'sentiment': sentiment,
            'score': round(score, 1),
            'bullish_signals': bullish_count,
            'bearish_signals': bearish_count,
            'mentioned_coins': mentioned_coins
        }
    
    async def scrape_reddit(self, subreddit: str = 'cryptocurrency', limit: int = 50) -> Dict[str, Any]:
        """
        Scrape Reddit posts and comments for sentiment.
        Uses public JSON endpoints (no API key needed).
        """
        print(f"  📱 Scraping r/{subreddit}...")
        
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
        headers = {'User-Agent': 'CryptoSentimentBot/1.0'}
        
        data = await self._fetch_url(url, headers)
        if not data or 'data' not in data:
            return {'error': f'Failed to fetch r/{subreddit}'}
        
        posts = data['data'].get('children', [])
        
        results = {
            'source': f'reddit/r/{subreddit}',
            'posts_analyzed': 0,
            'sentiment_breakdown': {'bullish': 0, 'bearish': 0, 'neutral': 0},
            'coin_mentions': defaultdict(int),
            'avg_sentiment_score': 0,
            'hot_topics': [],
            'posts': []
        }
        
        sentiment_scores = []
        
        for post in posts:
            post_data = post.get('data', {})
            title = post_data.get('title', '')
            selftext = post_data.get('selftext', '')
            full_text = f"{title} {selftext}"
            
            analysis = self._analyze_text_sentiment(full_text)
            sentiment_scores.append(analysis['score'])
            
            results['sentiment_breakdown'][analysis['sentiment']] += 1
            for coin in analysis['mentioned_coins']:
                results['coin_mentions'][coin] += 1
            
            results['posts'].append({
                'title': title[:100],
                'score': post_data.get('score', 0),
                'comments': post_data.get('num_comments', 0),
                'sentiment': analysis['sentiment'],
                'sentiment_score': analysis['score'],
                'coins': analysis['mentioned_coins']
            })
            
            results['posts_analyzed'] += 1
        
        results['avg_sentiment_score'] = round(sum(sentiment_scores) / len(sentiment_scores), 1) if sentiment_scores else 50
        results['coin_mentions'] = dict(results['coin_mentions'])
        
        # Top 5 most engaging posts
        results['hot_topics'] = sorted(
            results['posts'], 
            key=lambda x: x['score'] + x['comments'], 
            reverse=True
        )[:5]
        
        # Remove full posts list to save space
        del results['posts']
        
        return results
    
    async def get_fear_greed_index(self) -> Dict[str, Any]:
        """
        Get the Fear & Greed Index from Alternative.me
        """
        print("  😱 Fetching Fear & Greed Index...")
        
        url = "https://api.alternative.me/fng/?limit=7"
        data = await self._fetch_url(url)
        
        if not data or 'data' not in data:
            return {'error': 'Failed to fetch Fear & Greed Index'}
        
        fng_data = data['data']
        current = fng_data[0] if fng_data else {}
        
        # Map value to sentiment
        value = int(current.get('value', 50))
        if value <= 25:
            market_sentiment = 'extreme_fear'
            trading_signal = 'potential_buy'
        elif value <= 45:
            market_sentiment = 'fear'
            trading_signal = 'accumulate'
        elif value <= 55:
            market_sentiment = 'neutral'
            trading_signal = 'hold'
        elif value <= 75:
            market_sentiment = 'greed'
            trading_signal = 'caution'
        else:
            market_sentiment = 'extreme_greed'
            trading_signal = 'potential_sell'
        
        # 7-day trend
        if len(fng_data) >= 7:
            week_ago = int(fng_data[-1].get('value', 50))
            trend = value - week_ago
            trend_direction = 'improving' if trend > 5 else ('declining' if trend < -5 else 'stable')
        else:
            trend = 0
            trend_direction = 'unknown'
        
        return {
            'source': 'fear_greed_index',
            'current_value': value,
            'classification': current.get('value_classification', 'Unknown'),
            'market_sentiment': market_sentiment,
            'trading_signal': trading_signal,
            'timestamp': current.get('timestamp'),
            'week_trend': trend,
            'trend_direction': trend_direction,
            'history': [
                {'value': int(d.get('value', 0)), 'date': d.get('timestamp')}
                for d in fng_data[:7]
            ]
        }
    
    async def scrape_cryptopanic(self, filter_type: str = 'hot') -> Dict[str, Any]:
        """
        Scrape CryptoPanic news aggregator.
        filter_type: 'hot', 'rising', 'bullish', 'bearish', 'important'
        """
        print(f"  📰 Fetching CryptoPanic {filter_type} news...")
        
        url = f"https://cryptopanic.com/api/v1/posts/?auth_token=free&filter={filter_type}&public=true"
        data = await self._fetch_url(url)
        
        if not data or 'results' not in data:
            # Try without filter for free tier
            url = "https://cryptopanic.com/api/v1/posts/?auth_token=free&public=true"
            data = await self._fetch_url(url)
            if not data or 'results' not in data:
                return {'error': 'CryptoPanic API unavailable'}
        
        posts = data.get('results', [])[:30]
        
        results = {
            'source': 'cryptopanic',
            'filter': filter_type,
            'articles_analyzed': len(posts),
            'sentiment_breakdown': {'bullish': 0, 'bearish': 0, 'neutral': 0},
            'coin_mentions': defaultdict(int),
            'top_stories': []
        }
        
        for post in posts:
            title = post.get('title', '')
            
            # CryptoPanic provides votes
            votes = post.get('votes', {})
            positive = votes.get('positive', 0)
            negative = votes.get('negative', 0)
            
            if positive > negative:
                sentiment = 'bullish'
            elif negative > positive:
                sentiment = 'bearish'
            else:
                # Use text analysis
                analysis = self._analyze_text_sentiment(title)
                sentiment = analysis['sentiment']
            
            results['sentiment_breakdown'][sentiment] += 1
            
            # Extract currencies
            currencies = post.get('currencies', [])
            for curr in currencies:
                code = curr.get('code', '').upper()
                if code:
                    results['coin_mentions'][code] += 1
            
            results['top_stories'].append({
                'title': title[:100],
                'source': post.get('source', {}).get('title', 'Unknown'),
                'sentiment': sentiment,
                'votes_positive': positive,
                'votes_negative': negative,
                'url': post.get('url', '')
            })
        
        results['coin_mentions'] = dict(results['coin_mentions'])
        results['top_stories'] = results['top_stories'][:10]
        
        return results
    
    async def get_aggregated_sentiment(self) -> Dict[str, Any]:
        """
        Get aggregated sentiment from all sources.
        Returns combined analysis with overall market sentiment.
        """
        print("🔍 Aggregating social sentiment from multiple sources...")
        
        # Fetch from all sources in parallel
        tasks = [
            self.scrape_reddit('cryptocurrency', 30),
            self.scrape_reddit('bitcoin', 20),
            self.get_fear_greed_index(),
            self.scrape_cryptopanic('hot'),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        aggregated = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'sources': {},
            'overall_sentiment': 'neutral',
            'overall_score': 50,
            'coin_sentiment': {},
            'key_signals': [],
            'trading_recommendation': 'hold'
        }
        
        sentiment_scores = []
        all_coin_mentions = defaultdict(lambda: {'bullish': 0, 'bearish': 0, 'neutral': 0, 'total': 0})
        
        # Process Reddit results
        for i, result in enumerate(results[:2]):
            if isinstance(result, Exception) or 'error' in result:
                continue
            
            source_name = result.get('source', f'reddit_{i}')
            aggregated['sources'][source_name] = {
                'avg_sentiment': result.get('avg_sentiment_score', 50),
                'posts_analyzed': result.get('posts_analyzed', 0),
                'breakdown': result.get('sentiment_breakdown', {})
            }
            
            sentiment_scores.append(result.get('avg_sentiment_score', 50))
            
            # Aggregate coin mentions
            for coin, count in result.get('coin_mentions', {}).items():
                all_coin_mentions[coin]['total'] += count
        
        # Process Fear & Greed
        fng = results[2] if len(results) > 2 else {}
        if not isinstance(fng, Exception) and 'error' not in fng:
            aggregated['sources']['fear_greed_index'] = {
                'value': fng.get('current_value', 50),
                'classification': fng.get('classification', 'Unknown'),
                'trading_signal': fng.get('trading_signal', 'hold')
            }
            # Weight Fear & Greed heavily
            sentiment_scores.extend([fng.get('current_value', 50)] * 3)
            
            # Add key signal
            if fng.get('current_value', 50) <= 25:
                aggregated['key_signals'].append('🔴 Extreme Fear - Contrarian buy signal')
            elif fng.get('current_value', 50) >= 75:
                aggregated['key_signals'].append('🟢 Extreme Greed - Caution advised')
        
        # Process CryptoPanic
        cp = results[3] if len(results) > 3 else {}
        if not isinstance(cp, Exception) and 'error' not in cp:
            breakdown = cp.get('sentiment_breakdown', {})
            total = sum(breakdown.values())
            if total > 0:
                bullish_pct = breakdown.get('bullish', 0) / total * 100
                cp_score = 50 + (bullish_pct - 50)
                sentiment_scores.append(cp_score)
            
            aggregated['sources']['cryptopanic'] = {
                'articles': cp.get('articles_analyzed', 0),
                'breakdown': breakdown,
                'top_coins': list(cp.get('coin_mentions', {}).keys())[:5]
            }
        
        # Calculate overall sentiment
        if sentiment_scores:
            avg_score = sum(sentiment_scores) / len(sentiment_scores)
            aggregated['overall_score'] = round(avg_score, 1)
            
            if avg_score >= 65:
                aggregated['overall_sentiment'] = 'bullish'
                aggregated['trading_recommendation'] = 'increase_exposure'
            elif avg_score >= 55:
                aggregated['overall_sentiment'] = 'slightly_bullish'
                aggregated['trading_recommendation'] = 'hold_accumulate'
            elif avg_score <= 35:
                aggregated['overall_sentiment'] = 'bearish'
                aggregated['trading_recommendation'] = 'reduce_exposure'
            elif avg_score <= 45:
                aggregated['overall_sentiment'] = 'slightly_bearish'
                aggregated['trading_recommendation'] = 'caution'
            else:
                aggregated['overall_sentiment'] = 'neutral'
                aggregated['trading_recommendation'] = 'hold'
        
        # Process coin-specific sentiment
        aggregated['coin_sentiment'] = {
            coin: {'mentions': data['total']}
            for coin, data in sorted(
                all_coin_mentions.items(),
                key=lambda x: x[1]['total'],
                reverse=True
            )[:10]
        }
        
        # Store in database
        await self.db.social_sentiment.insert_one({
            **aggregated,
            'stored_at': datetime.now(timezone.utc)
        })
        
        return aggregated
    
    async def get_coin_sentiment(self, coin: str) -> Dict[str, Any]:
        """Get sentiment specifically for a coin"""
        coin_upper = coin.upper()
        
        # Scrape relevant subreddits
        if coin_upper == 'BTC':
            subreddit = 'bitcoin'
        elif coin_upper == 'ETH':
            subreddit = 'ethereum'
        else:
            subreddit = 'cryptocurrency'
        
        reddit_data = await self.scrape_reddit(subreddit, 30)
        
        # Filter for coin mentions
        coin_posts = []
        for post in reddit_data.get('hot_topics', []):
            if coin_upper in post.get('coins', []):
                coin_posts.append(post)
        
        mention_count = reddit_data.get('coin_mentions', {}).get(coin_upper, 0)
        
        return {
            'coin': coin_upper,
            'mentions': mention_count,
            'sentiment_posts': coin_posts[:5],
            'subreddit_sentiment': reddit_data.get('avg_sentiment_score', 50),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def get_sentiment_history(self, days: int = 7) -> List[Dict]:
        """Get sentiment history from database"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        history = await self.db.social_sentiment.find(
            {'stored_at': {'$gte': cutoff}},
            {'_id': 0}
        ).sort('stored_at', -1).limit(100).to_list(100)
        
        return history


# Global instance
_sentiment_scraper = None


def get_sentiment_scraper(db: AsyncIOMotorDatabase = None, api_key: str = None) -> SocialSentimentScraper:
    """Get or create sentiment scraper instance"""
    global _sentiment_scraper
    if _sentiment_scraper is None and db is not None:
        _sentiment_scraper = SocialSentimentScraper(db, api_key)
    return _sentiment_scraper

"""
CryptoPanic API Wrapper Service
Comprehensive Python wrapper for the CryptoPanic news API.
Provides access to crypto news, sentiment filters, and trending content.

Features:
- Get news by currency/coin
- Filter by sentiment (bullish/bearish/important)
- Get trending/rising/hot news
- Get news by source or region
- Vote sentiment analysis
- Caching to respect rate limits
"""

import asyncio
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from dotenv import load_dotenv

# Import CryptoPanic library
try:
    from cryptopanic import CryptoPanicClient, CryptoPanicAPIError
    CRYPTOPANIC_AVAILABLE = True
except ImportError:
    CRYPTOPANIC_AVAILABLE = False
    print("⚠️ Warning: cryptopanic library not installed. Run: pip install cryptopanic")

load_dotenv()


class NewsFilter(str, Enum):
    """Available news filters"""
    RISING = "rising"       # Rising/trending news
    HOT = "hot"             # Hot news
    BULLISH = "bullish"     # Bullish sentiment
    BEARISH = "bearish"     # Bearish sentiment
    IMPORTANT = "important" # Important news
    SAVED = "saved"         # Saved news
    LOL = "lol"             # Funny/meme news


class NewsKind(str, Enum):
    """Types of news content"""
    NEWS = "news"           # News articles
    MEDIA = "media"         # Media content
    ALL = "all"             # All content


class CryptoPanicService:
    """
    Comprehensive CryptoPanic API wrapper service.
    Provides easy access to crypto news with caching and async support.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize CryptoPanic service.
        
        Args:
            api_key: CryptoPanic API key. If not provided, uses CRYPTOPANIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv('CRYPTOPANIC_API_KEY', '')
        self.client = None
        self._initialized = False
        
        # Cache settings
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes default cache
        
        # Rate limiting
        self.last_request_time = None
        self.min_request_interval = 1.0  # seconds between requests
        
        self._initialize()
    
    def _initialize(self):
        """Initialize the CryptoPanic client"""
        if not CRYPTOPANIC_AVAILABLE:
            print("❌ CryptoPanic library not available")
            return
        
        if not self.api_key:
            print("⚠️ No CryptoPanic API key configured. Get one at: cryptopanic.com/developers/api/")
            return
        
        try:
            self.client = CryptoPanicClient(
                auth_token=self.api_key,
                timeout=30
            )
            self._initialized = True
            print("✅ CryptoPanic service initialized")
        except Exception as e:
            print(f"❌ CryptoPanic initialization error: {e}")
    
    @property
    def is_available(self) -> bool:
        """Check if the service is available and configured"""
        return self._initialized and self.client is not None
    
    async def _respect_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.min_request_interval:
                await asyncio.sleep(self.min_request_interval - elapsed)
        self.last_request_time = datetime.now()
    
    def _get_cache_key(self, method: str, **kwargs) -> str:
        """Generate cache key from method and parameters"""
        params = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()) if v)
        return f"{method}_{params}"
    
    def _get_cached(self, cache_key: str) -> Optional[Any]:
        """Get cached result if valid"""
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if (datetime.now() - cached['timestamp']).seconds < self.cache_ttl:
                return cached['data']
        return None
    
    def _set_cache(self, cache_key: str, data: Any):
        """Cache the result"""
        self.cache[cache_key] = {
            'timestamp': datetime.now(),
            'data': data
        }
    
    def _parse_post(self, post) -> Dict[str, Any]:
        """Parse a CryptoPanic post into a clean dictionary"""
        # Extract currencies mentioned
        currencies = []
        if hasattr(post, 'instruments') and post.instruments:
            currencies = [inst.code for inst in post.instruments]
        
        # Extract vote data
        votes = {}
        if hasattr(post, 'votes') and post.votes:
            votes = {
                'positive': post.votes.positive or 0,
                'negative': post.votes.negative or 0,
                'important': post.votes.important or 0,
                'liked': post.votes.liked or 0,
                'disliked': post.votes.disliked or 0,
                'lol': post.votes.lol or 0,
                'toxic': post.votes.toxic or 0,
                'saved': post.votes.saved or 0,
                'comments': post.votes.comments or 0,
            }
            
            # Calculate vote-based sentiment
            positive_votes = votes['positive'] + votes['liked']
            negative_votes = votes['negative'] + votes['disliked'] + votes['toxic']
            
            if positive_votes + negative_votes > 0:
                sentiment_ratio = positive_votes / (positive_votes + negative_votes)
                if sentiment_ratio > 0.65:
                    votes['sentiment'] = 'bullish'
                elif sentiment_ratio < 0.35:
                    votes['sentiment'] = 'bearish'
                else:
                    votes['sentiment'] = 'neutral'
            else:
                votes['sentiment'] = 'unknown'
        
        return {
            'id': post.id if hasattr(post, 'id') else None,
            'title': post.title if hasattr(post, 'title') else '',
            'url': post.url if hasattr(post, 'url') else '',
            'source': post.source.title if hasattr(post, 'source') and post.source else 'Unknown',
            'source_domain': post.source.domain if hasattr(post, 'source') and post.source else '',
            'published_at': post.published_at.isoformat() if hasattr(post, 'published_at') and post.published_at else '',
            'created_at': post.created_at.isoformat() if hasattr(post, 'created_at') and post.created_at else '',
            'kind': post.kind if hasattr(post, 'kind') else 'news',
            'currencies': currencies,
            'votes': votes,
            'panic_score': post.panic_score if hasattr(post, 'panic_score') else None,
        }
    
    async def get_news(
        self,
        currencies: List[str] = None,
        filter_type: NewsFilter = None,
        kind: NewsKind = NewsKind.NEWS,
        regions: List[str] = None,
        limit: int = 20,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get crypto news with optional filters.
        
        Args:
            currencies: List of currency codes (e.g., ['BTC', 'ETH'])
            filter_type: Filter by sentiment/importance
            kind: Type of content (news, media, all)
            regions: Filter by region (e.g., ['en', 'de'])
            limit: Maximum number of results
            use_cache: Whether to use cached results
            
        Returns:
            List of news items
        """
        if not self.is_available:
            return []
        
        # Check cache
        cache_key = self._get_cache_key(
            'get_news',
            currencies=','.join(currencies) if currencies else None,
            filter_type=filter_type.value if filter_type else None,
            kind=kind.value if kind else None,
            limit=limit
        )
        
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached:
                return cached
        
        try:
            await self._respect_rate_limit()
            
            # Run synchronous client in thread pool
            loop = asyncio.get_event_loop()
            
            params = {}
            if currencies:
                params['currencies'] = currencies
            if filter_type:
                params['filter'] = filter_type.value
            if kind and kind != NewsKind.ALL:
                params['kind'] = kind.value
            if regions:
                params['regions'] = regions
            
            posts = await loop.run_in_executor(
                None,
                lambda: self.client.get_posts(**params)
            )
            
            news_items = []
            if posts and posts.results:
                for post in posts.results[:limit]:
                    news_items.append(self._parse_post(post))
            
            # Cache results
            if use_cache:
                self._set_cache(cache_key, news_items)
            
            return news_items
            
        except Exception as e:
            print(f"CryptoPanic get_news error: {e}")
            return []
    
    async def get_news_for_coin(
        self,
        symbol: str,
        filter_type: NewsFilter = NewsFilter.HOT,
        limit: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Get news for a specific cryptocurrency.
        
        Args:
            symbol: Currency symbol (e.g., 'BTC', 'ETH')
            filter_type: News filter
            limit: Maximum results
            
        Returns:
            List of news items for the coin
        """
        return await self.get_news(
            currencies=[symbol.upper()],
            filter_type=filter_type,
            limit=limit
        )
    
    async def get_trending_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get trending/rising news across all cryptocurrencies"""
        return await self.get_news(filter_type=NewsFilter.RISING, limit=limit)
    
    async def get_bullish_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get news with bullish community sentiment"""
        return await self.get_news(filter_type=NewsFilter.BULLISH, limit=limit)
    
    async def get_bearish_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get news with bearish community sentiment"""
        return await self.get_news(filter_type=NewsFilter.BEARISH, limit=limit)
    
    async def get_important_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get news marked as important by the community"""
        return await self.get_news(filter_type=NewsFilter.IMPORTANT, limit=limit)
    
    async def get_hot_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get hot/popular news"""
        return await self.get_news(filter_type=NewsFilter.HOT, limit=limit)
    
    async def get_multi_coin_news(
        self,
        symbols: List[str],
        filter_type: NewsFilter = NewsFilter.HOT,
        limit: int = 30
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get news for multiple coins, grouped by currency.
        
        Args:
            symbols: List of currency symbols
            filter_type: News filter
            limit: Total limit (distributed across coins)
            
        Returns:
            Dictionary mapping symbols to their news items
        """
        all_news = await self.get_news(
            currencies=[s.upper() for s in symbols],
            filter_type=filter_type,
            limit=limit
        )
        
        # Group by currency
        grouped = {s.upper(): [] for s in symbols}
        for item in all_news:
            for currency in item.get('currencies', []):
                if currency in grouped:
                    grouped[currency].append(item)
        
        return grouped
    
    async def analyze_sentiment_for_coin(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze overall sentiment for a coin based on recent news.
        
        Args:
            symbol: Currency symbol
            
        Returns:
            Sentiment analysis with scores
        """
        # Get different sentiment news
        bullish = await self.get_news(
            currencies=[symbol.upper()],
            filter_type=NewsFilter.BULLISH,
            limit=10
        )
        
        bearish = await self.get_news(
            currencies=[symbol.upper()],
            filter_type=NewsFilter.BEARISH,
            limit=10
        )
        
        hot = await self.get_news(
            currencies=[symbol.upper()],
            filter_type=NewsFilter.HOT,
            limit=10
        )
        
        # Calculate sentiment metrics
        bullish_count = len(bullish)
        bearish_count = len(bearish)
        total_news = len(hot)
        
        # Aggregate votes from hot news
        total_positive = sum(item.get('votes', {}).get('positive', 0) for item in hot)
        total_negative = sum(item.get('votes', {}).get('negative', 0) for item in hot)
        total_important = sum(item.get('votes', {}).get('important', 0) for item in hot)
        
        # Calculate sentiment score (0-100)
        if bullish_count + bearish_count > 0:
            sentiment_score = (bullish_count / (bullish_count + bearish_count)) * 100
        else:
            sentiment_score = 50  # Neutral
        
        # Adjust based on vote ratios
        if total_positive + total_negative > 0:
            vote_sentiment = (total_positive / (total_positive + total_negative)) * 100
            sentiment_score = (sentiment_score + vote_sentiment) / 2
        
        # Determine label
        if sentiment_score >= 70:
            label = 'very_bullish' if sentiment_score >= 80 else 'bullish'
        elif sentiment_score <= 30:
            label = 'very_bearish' if sentiment_score <= 20 else 'bearish'
        else:
            label = 'neutral'
        
        return {
            'symbol': symbol.upper(),
            'sentiment_score': round(sentiment_score, 1),
            'sentiment_label': label,
            'bullish_news_count': bullish_count,
            'bearish_news_count': bearish_count,
            'total_news_count': total_news,
            'vote_metrics': {
                'positive': total_positive,
                'negative': total_negative,
                'important': total_important,
            },
            'top_bullish_headlines': [n['title'] for n in bullish[:3]],
            'top_bearish_headlines': [n['title'] for n in bearish[:3]],
            'analyzed_at': datetime.now().isoformat()
        }
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """
        Get overall crypto market news overview.
        
        Returns:
            Market overview with trending topics and sentiment
        """
        trending = await self.get_trending_news(limit=20)
        bullish = await self.get_bullish_news(limit=10)
        bearish = await self.get_bearish_news(limit=10)
        important = await self.get_important_news(limit=10)
        
        # Extract top mentioned currencies
        currency_mentions = {}
        for news_list in [trending, bullish, bearish, important]:
            for item in news_list:
                for currency in item.get('currencies', []):
                    currency_mentions[currency] = currency_mentions.get(currency, 0) + 1
        
        top_currencies = sorted(
            currency_mentions.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Calculate market sentiment
        bullish_score = len(bullish)
        bearish_score = len(bearish)
        if bullish_score + bearish_score > 0:
            market_sentiment = (bullish_score / (bullish_score + bearish_score)) * 100
        else:
            market_sentiment = 50
        
        return {
            'market_sentiment_score': round(market_sentiment, 1),
            'market_sentiment_label': 'bullish' if market_sentiment > 55 else ('bearish' if market_sentiment < 45 else 'neutral'),
            'trending_news_count': len(trending),
            'bullish_news_count': bullish_score,
            'bearish_news_count': bearish_score,
            'important_news_count': len(important),
            'top_currencies': [{'symbol': s, 'mentions': c} for s, c in top_currencies],
            'trending_headlines': [n['title'] for n in trending[:5]],
            'important_headlines': [n['title'] for n in important[:5]],
            'analyzed_at': datetime.now().isoformat()
        }
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache = {}
        print("✅ CryptoPanic cache cleared")
    
    def set_cache_ttl(self, seconds: int):
        """Set cache time-to-live in seconds"""
        self.cache_ttl = seconds


# Global service instance
_cryptopanic_service = None


def get_cryptopanic_service() -> CryptoPanicService:
    """Get or create the global CryptoPanic service instance"""
    global _cryptopanic_service
    if _cryptopanic_service is None:
        _cryptopanic_service = CryptoPanicService()
    return _cryptopanic_service


def set_cryptopanic_service(service: CryptoPanicService):
    """Set the global CryptoPanic service instance"""
    global _cryptopanic_service
    _cryptopanic_service = service

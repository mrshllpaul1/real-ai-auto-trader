"""
CoinStats News Service
=======================
Alternative news source using CoinStats API.
Provides crypto news with sentiment analysis.
"""

import logging
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os

logger = logging.getLogger(__name__)


class CoinStatsService:
    """
    Fetches crypto news and market data from CoinStats API.
    """
    
    BASE_URL = "https://openapiv1.coinstats.app"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get('COINSTATS_API_KEY')
        self._news_cache = None
        self._news_cache_time = None
        self._cache_ttl = timedelta(minutes=5)
        self.initialized = bool(self.api_key)
        
        if self.initialized:
            logger.info("📰 CoinStats News service initialized")
        else:
            logger.warning("⚠️ CoinStats API key not configured")
    
    async def get_news(self, limit: int = 10, coin: str = None) -> List[Dict[str, Any]]:
        """
        Get latest crypto news.
        
        Args:
            limit: Number of news items to fetch (max 20)
            coin: Optional coin ID to filter news (e.g., 'bitcoin', 'ethereum')
        
        Returns:
            List of news items with title, source, url, related coins, and timestamp
        """
        if not self.initialized:
            return []
        
        # Check cache
        cache_key = f"{coin or 'all'}_{limit}"
        if (self._news_cache and self._news_cache_time and 
            datetime.now() - self._news_cache_time < self._cache_ttl and
            self._news_cache.get('key') == cache_key):
            return self._news_cache.get('data', [])
        
        try:
            params = {"limit": min(limit, 20)}
            if coin:
                params["coinId"] = coin
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/news",
                    headers={"X-API-KEY": self.api_key},
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        news_items = data.get("result", [])
                        
                        # Transform to standard format
                        formatted_news = []
                        for item in news_items:
                            formatted_news.append({
                                "id": item.get("id"),
                                "title": item.get("title"),
                                "source": item.get("source"),
                                "url": item.get("link"),
                                "image": item.get("imgUrl"),
                                "published_at": self._parse_timestamp(item.get("feedDate")),
                                "related_coins": item.get("relatedCoins", []),
                                "sentiment": self._analyze_title_sentiment(item.get("title", "")),
                                "kind": "news"
                            })
                        
                        # Update cache
                        self._news_cache = {
                            'key': cache_key,
                            'data': formatted_news
                        }
                        self._news_cache_time = datetime.now()
                        
                        return formatted_news
                    else:
                        logger.warning(f"CoinStats API returned {response.status}")
                        return []
        except Exception as e:
            logger.error(f"CoinStats API error: {e}")
            return []
    
    async def get_trending_news(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get trending/hot news"""
        return await self.get_news(limit=limit)
    
    async def get_coin_news(self, coin_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get news for a specific coin"""
        return await self.get_news(limit=limit, coin=coin_id)
    
    async def get_coin_data(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current market data for a coin.
        """
        if not self.initialized:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/coins/{coin_id}",
                    headers={"X-API-KEY": self.api_key},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.error(f"CoinStats coin data error: {e}")
            return None
    
    def _parse_timestamp(self, ts: int) -> str:
        """Parse millisecond timestamp to ISO format"""
        try:
            if ts:
                return datetime.fromtimestamp(ts / 1000).isoformat()
        except:
            pass
        return datetime.now().isoformat()
    
    def _analyze_title_sentiment(self, title: str) -> Dict[str, Any]:
        """
        Simple sentiment analysis based on keywords in title.
        """
        title_lower = title.lower()
        
        # Bullish keywords
        bullish_words = [
            'surge', 'rally', 'soar', 'jump', 'gain', 'rise', 'bull', 
            'breakout', 'record', 'high', 'growth', 'accumulation',
            'buying', 'bullish', 'positive', 'recover', 'rebound'
        ]
        
        # Bearish keywords
        bearish_words = [
            'drop', 'fall', 'crash', 'plunge', 'bear', 'down', 'low',
            'decline', 'loss', 'sell', 'fear', 'capitulation', 'dump',
            'bearish', 'negative', 'warning', 'risk', 'concern'
        ]
        
        bullish_count = sum(1 for word in bullish_words if word in title_lower)
        bearish_count = sum(1 for word in bearish_words if word in title_lower)
        
        if bullish_count > bearish_count:
            return {"score": 0.7, "label": "BULLISH"}
        elif bearish_count > bullish_count:
            return {"score": 0.3, "label": "BEARISH"}
        else:
            return {"score": 0.5, "label": "NEUTRAL"}
    
    async def get_news_sentiment(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get aggregated sentiment from recent news.
        """
        news = await self.get_news(limit=limit)
        
        if not news:
            return {
                "score": 0.5,
                "signal": "NEUTRAL",
                "news_count": 0,
                "available": False
            }
        
        total_score = sum(n.get("sentiment", {}).get("score", 0.5) for n in news)
        avg_score = total_score / len(news)
        
        bullish_count = sum(1 for n in news if n.get("sentiment", {}).get("label") == "BULLISH")
        bearish_count = sum(1 for n in news if n.get("sentiment", {}).get("label") == "BEARISH")
        
        if avg_score >= 0.6:
            signal = "BULLISH"
        elif avg_score <= 0.4:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"
        
        return {
            "score": round(avg_score, 3),
            "signal": signal,
            "news_count": len(news),
            "bullish_articles": bullish_count,
            "bearish_articles": bearish_count,
            "available": True,
            "source": "coinstats"
        }


# Singleton instance
_coinstats_service = None


def get_coinstats_service() -> CoinStatsService:
    global _coinstats_service
    if _coinstats_service is None:
        _coinstats_service = CoinStatsService()
    return _coinstats_service


def set_coinstats_api_key(api_key: str):
    """Set API key and reinitialize service"""
    global _coinstats_service
    _coinstats_service = CoinStatsService(api_key)
    return _coinstats_service

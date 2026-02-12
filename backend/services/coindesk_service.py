"""
CoinDesk API Service
Provides news articles, market data, and crypto insights from CoinDesk.
API Key budget: 11,000 credits/month
"""

import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from httpx import AsyncClient
import time

# API Configuration
COINDESK_API_KEY = os.getenv('COINDESK_API_KEY', '')
COINDESK_BASE_URL = "https://data-api.coindesk.com"

# Cache configuration
_cache = {
    "news": {"data": None, "timestamp": 0, "ttl": 300},  # 5 min cache
    "categories": {"data": None, "timestamp": 0, "ttl": 3600},  # 1 hour cache
    "sources": {"data": None, "timestamp": 0, "ttl": 3600},  # 1 hour cache
}

# Monthly credit tracking
_credit_tracker = {
    "used": 0,
    "limit": 11000,
    "reset_date": None
}


def _check_cache(key: str) -> Optional[Any]:
    """Check if cached data is still valid"""
    cache_entry = _cache.get(key)
    if cache_entry and cache_entry["data"]:
        if time.time() - cache_entry["timestamp"] < cache_entry["ttl"]:
            return cache_entry["data"]
    return None


def _set_cache(key: str, data: Any):
    """Set cache data"""
    if key in _cache:
        _cache[key]["data"] = data
        _cache[key]["timestamp"] = time.time()


def _track_credits(credits_used: int = 1):
    """Track API credit usage"""
    # Reset counter monthly
    now = datetime.now(timezone.utc)
    if _credit_tracker["reset_date"] is None or now.month != _credit_tracker["reset_date"].month:
        _credit_tracker["used"] = 0
        _credit_tracker["reset_date"] = now
    
    _credit_tracker["used"] += credits_used


def get_credit_status() -> Dict[str, Any]:
    """Get current credit usage status"""
    return {
        "used": _credit_tracker["used"],
        "limit": _credit_tracker["limit"],
        "remaining": _credit_tracker["limit"] - _credit_tracker["used"],
        "reset_date": _credit_tracker["reset_date"].isoformat() if _credit_tracker["reset_date"] else None
    }


class CoinDeskService:
    """CoinDesk API client for news and market data"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or COINDESK_API_KEY
        self.base_url = COINDESK_BASE_URL
        
    async def _request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make authenticated request to CoinDesk API"""
        if not self.api_key:
            return {"error": "CoinDesk API key not configured"}
        
        url = f"{self.base_url}{endpoint}"
        
        if params is None:
            params = {}
        params["api_key"] = self.api_key
        
        try:
            async with AsyncClient(timeout=30) as client:
                response = await client.get(url, params=params)
                _track_credits(1)  # Track credit usage
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    return {"error": "Rate limit exceeded", "status": 429}
                else:
                    return {"error": f"API error: {response.status_code}", "status": response.status_code}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_latest_news(
        self,
        lang: str = "EN",
        limit: int = 20,
        categories: List[str] = None,
        source_ids: List[int] = None
    ) -> Dict[str, Any]:
        """
        Get latest news articles from CoinDesk.
        
        Args:
            lang: Language code (EN, ES, FR, TR, JP, PT)
            limit: Number of articles (1-100)
            categories: Filter by category names
            source_ids: Filter by source IDs
        
        Returns:
            Dict with articles list and metadata
        """
        # Check cache first
        cache_key = f"news_{lang}_{limit}"
        cached = _check_cache(cache_key)
        if cached:
            return cached
        
        params = {
            "lang": lang,
            "limit": min(limit, 100)
        }
        
        if categories:
            params["categories"] = ",".join(categories)
        if source_ids:
            params["source_ids"] = ",".join(map(str, source_ids))
        
        result = await self._request("/news/v1/article/list", params)
        
        if "Data" in result:
            articles = []
            for article in result.get("Data", []):
                articles.append({
                    "id": article.get("ID"),
                    "title": article.get("TITLE", ""),
                    "subtitle": article.get("SUBTITLE", ""),
                    "body": article.get("BODY", ""),
                    "url": article.get("URL", ""),
                    "image_url": article.get("IMAGE_URL", ""),
                    "authors": article.get("AUTHORS", ""),
                    "published_at": article.get("PUBLISHED_ON"),
                    "published_at_iso": datetime.fromtimestamp(
                        article.get("PUBLISHED_ON", 0), tz=timezone.utc
                    ).isoformat() if article.get("PUBLISHED_ON") else None,
                    "sentiment": article.get("SENTIMENT", "NEUTRAL"),
                    "source": article.get("SOURCE_DATA", {}).get("NAME", "CoinDesk"),
                    "source_id": article.get("SOURCE_ID"),
                    "categories": [
                        cat.get("NAME") for cat in article.get("CATEGORY_DATA", [])
                    ],
                    "keywords": article.get("KEYWORDS", "").split(",") if article.get("KEYWORDS") else [],
                    "score": article.get("SCORE", 0),
                    "upvotes": article.get("UPVOTES", 0),
                    "downvotes": article.get("DOWNVOTES", 0)
                })
            
            response = {
                "articles": articles,
                "count": len(articles),
                "source": "coindesk",
                "cached": False,
                "credits_used": 1,
                "credits_remaining": _credit_tracker["limit"] - _credit_tracker["used"]
            }
            
            # Cache the response
            _set_cache(cache_key, response)
            response["cached"] = False
            return response
        
        return result
    
    async def get_news_categories(self) -> Dict[str, Any]:
        """Get available news categories"""
        cached = _check_cache("categories")
        if cached:
            return cached
        
        result = await self._request("/news/v1/category/list", {"lang": "EN"})
        
        if "Data" in result:
            categories = [
                {
                    "id": cat.get("ID"),
                    "name": cat.get("NAME"),
                    "description": cat.get("DESCRIPTION", "")
                }
                for cat in result.get("Data", [])
            ]
            response = {"categories": categories, "count": len(categories)}
            _set_cache("categories", response)
            return response
        
        return result
    
    async def get_news_sources(self) -> Dict[str, Any]:
        """Get available news sources"""
        cached = _check_cache("sources")
        if cached:
            return cached
        
        result = await self._request("/news/v1/source/list", {"lang": "EN"})
        
        if "Data" in result:
            sources = [
                {
                    "id": src.get("ID"),
                    "name": src.get("NAME"),
                    "url": src.get("URL", ""),
                    "lang": src.get("LANG", "EN")
                }
                for src in result.get("Data", [])
            ]
            response = {"sources": sources, "count": len(sources)}
            _set_cache("sources", response)
            return response
        
        return result
    
    async def get_news_by_sentiment(self, sentiment: str = "POSITIVE", limit: int = 10) -> Dict[str, Any]:
        """
        Get news filtered by sentiment (POSITIVE, NEGATIVE, NEUTRAL)
        Note: This filters client-side since API doesn't support sentiment filter
        """
        # Get more articles and filter
        all_news = await self.get_latest_news(limit=100)
        
        if "articles" in all_news:
            filtered = [
                article for article in all_news["articles"]
                if article.get("sentiment", "").upper() == sentiment.upper()
            ][:limit]
            
            return {
                "articles": filtered,
                "count": len(filtered),
                "sentiment_filter": sentiment,
                "source": "coindesk"
            }
        
        return all_news
    
    async def get_crypto_specific_news(self, coin_symbol: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get news related to a specific cryptocurrency.
        Searches keywords and title for coin mentions.
        """
        all_news = await self.get_latest_news(limit=100)
        
        symbol_upper = coin_symbol.upper()
        symbol_lower = coin_symbol.lower()
        
        # Common coin name mappings
        coin_names = {
            "BTC": ["bitcoin", "btc"],
            "ETH": ["ethereum", "eth", "ether"],
            "SOL": ["solana", "sol"],
            "XRP": ["ripple", "xrp"],
            "DOT": ["polkadot", "dot"],
            "ADA": ["cardano", "ada"],
            "DOGE": ["dogecoin", "doge"],
            "SHIB": ["shiba", "shib"],
            "AVAX": ["avalanche", "avax"],
            "LINK": ["chainlink", "link"],
            "UNI": ["uniswap", "uni"],
            "AAVE": ["aave"],
            "APT": ["aptos", "apt"],
            "SUI": ["sui"],
        }
        
        search_terms = coin_names.get(symbol_upper, [symbol_lower])
        search_terms.append(symbol_lower)
        
        if "articles" in all_news:
            filtered = []
            for article in all_news["articles"]:
                title = article.get("title", "").lower()
                body = article.get("body", "").lower()
                keywords = " ".join(article.get("keywords", [])).lower()
                
                if any(term in title or term in body or term in keywords for term in search_terms):
                    filtered.append(article)
                
                if len(filtered) >= limit:
                    break
            
            return {
                "articles": filtered,
                "count": len(filtered),
                "coin": coin_symbol.upper(),
                "source": "coindesk"
            }
        
        return all_news
    
    async def get_market_sentiment_summary(self) -> Dict[str, Any]:
        """
        Analyze overall market sentiment from recent news.
        Returns sentiment distribution and key themes.
        """
        news = await self.get_latest_news(limit=50)
        
        if "articles" not in news:
            return {"error": "Could not fetch news for analysis"}
        
        articles = news["articles"]
        
        # Count sentiments
        sentiment_counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
        for article in articles:
            sentiment = article.get("sentiment", "NEUTRAL").upper()
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1
            else:
                sentiment_counts["NEUTRAL"] += 1
        
        total = len(articles)
        
        # Calculate percentages
        sentiment_pct = {
            k: round(v / total * 100, 1) if total > 0 else 0
            for k, v in sentiment_counts.items()
        }
        
        # Determine overall sentiment
        if sentiment_pct["POSITIVE"] > sentiment_pct["NEGATIVE"] + 10:
            overall = "BULLISH"
        elif sentiment_pct["NEGATIVE"] > sentiment_pct["POSITIVE"] + 10:
            overall = "BEARISH"
        else:
            overall = "NEUTRAL"
        
        # Extract top categories/themes
        category_counts = {}
        for article in articles:
            for cat in article.get("categories", []):
                category_counts[cat] = category_counts.get(cat, 0) + 1
        
        top_themes = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "overall_sentiment": overall,
            "sentiment_distribution": sentiment_pct,
            "sentiment_counts": sentiment_counts,
            "articles_analyzed": total,
            "top_themes": [{"theme": t[0], "count": t[1]} for t in top_themes],
            "source": "coindesk",
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }


# CryptoCompare Historical Data Service
class CryptoCompareHistoricalService:
    """
    CryptoCompare Historical Data API client.
    Uses the same API key as CoinDesk (they share the platform).
    Provides historical OHLCV data for AI training.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or COINDESK_API_KEY
        self.base_url = "https://min-api.cryptocompare.com/data/v2"
        
        # Cache for historical data
        self._hist_cache = {}
        self._cache_ttl = 3600  # 1 hour cache for historical data
        
    async def _request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make authenticated request to CryptoCompare API"""
        if not self.api_key:
            return {"error": "CryptoCompare API key not configured"}
        
        url = f"{self.base_url}{endpoint}"
        
        if params is None:
            params = {}
        params["api_key"] = self.api_key
        
        try:
            async with AsyncClient(timeout=60) as client:
                response = await client.get(url, params=params)
                _track_credits(1)  # Track credit usage
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    return {"error": "Rate limit exceeded", "status": 429}
                else:
                    return {"error": f"API error: {response.status_code}", "status": response.status_code}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_historical_daily(
        self,
        coin_symbol: str,
        to_symbol: str = "USD",
        limit: int = 2000,
        to_ts: int = None
    ) -> Dict[str, Any]:
        """
        Get historical daily OHLCV data for a coin.
        
        Args:
            coin_symbol: Cryptocurrency symbol (e.g., BTC, ETH)
            to_symbol: Target currency (default: USD)
            limit: Number of days (max 2000)
            to_ts: Unix timestamp to get data up to (optional)
        
        Returns:
            Dict with OHLCV data array
        """
        cache_key = f"daily_{coin_symbol}_{to_symbol}_{limit}_{to_ts or 'latest'}"
        
        # Check cache
        if cache_key in self._hist_cache:
            cached = self._hist_cache[cache_key]
            if time.time() - cached["timestamp"] < self._cache_ttl:
                return cached["data"]
        
        params = {
            "fsym": coin_symbol.upper(),
            "tsym": to_symbol.upper(),
            "limit": min(limit, 2000)
        }
        
        if to_ts:
            params["toTs"] = to_ts
        
        result = await self._request("/histoday", params)
        
        if "Data" in result and "Data" in result["Data"]:
            ohlcv_data = []
            for candle in result["Data"]["Data"]:
                ohlcv_data.append({
                    "timestamp": candle.get("time"),
                    "date": datetime.fromtimestamp(candle.get("time", 0), tz=timezone.utc).isoformat(),
                    "open": candle.get("open", 0),
                    "high": candle.get("high", 0),
                    "low": candle.get("low", 0),
                    "close": candle.get("close", 0),
                    "volume_from": candle.get("volumefrom", 0),
                    "volume_to": candle.get("volumeto", 0)
                })
            
            response = {
                "symbol": coin_symbol.upper(),
                "to_symbol": to_symbol.upper(),
                "timeframe": "daily",
                "data": ohlcv_data,
                "count": len(ohlcv_data),
                "time_from": ohlcv_data[0]["date"] if ohlcv_data else None,
                "time_to": ohlcv_data[-1]["date"] if ohlcv_data else None,
                "source": "cryptocompare"
            }
            
            # Cache the response
            self._hist_cache[cache_key] = {
                "data": response,
                "timestamp": time.time()
            }
            
            return response
        
        return result
    
    async def get_historical_hourly(
        self,
        coin_symbol: str,
        to_symbol: str = "USD",
        limit: int = 2000,
        to_ts: int = None
    ) -> Dict[str, Any]:
        """
        Get historical hourly OHLCV data for a coin.
        
        Args:
            coin_symbol: Cryptocurrency symbol (e.g., BTC, ETH)
            to_symbol: Target currency (default: USD)
            limit: Number of hours (max 2000)
            to_ts: Unix timestamp to get data up to (optional)
        
        Returns:
            Dict with OHLCV data array
        """
        cache_key = f"hourly_{coin_symbol}_{to_symbol}_{limit}_{to_ts or 'latest'}"
        
        # Check cache
        if cache_key in self._hist_cache:
            cached = self._hist_cache[cache_key]
            if time.time() - cached["timestamp"] < self._cache_ttl:
                return cached["data"]
        
        params = {
            "fsym": coin_symbol.upper(),
            "tsym": to_symbol.upper(),
            "limit": min(limit, 2000)
        }
        
        if to_ts:
            params["toTs"] = to_ts
        
        result = await self._request("/histohour", params)
        
        if "Data" in result and "Data" in result["Data"]:
            ohlcv_data = []
            for candle in result["Data"]["Data"]:
                ohlcv_data.append({
                    "timestamp": candle.get("time"),
                    "date": datetime.fromtimestamp(candle.get("time", 0), tz=timezone.utc).isoformat(),
                    "open": candle.get("open", 0),
                    "high": candle.get("high", 0),
                    "low": candle.get("low", 0),
                    "close": candle.get("close", 0),
                    "volume_from": candle.get("volumefrom", 0),
                    "volume_to": candle.get("volumeto", 0)
                })
            
            response = {
                "symbol": coin_symbol.upper(),
                "to_symbol": to_symbol.upper(),
                "timeframe": "hourly",
                "data": ohlcv_data,
                "count": len(ohlcv_data),
                "time_from": ohlcv_data[0]["date"] if ohlcv_data else None,
                "time_to": ohlcv_data[-1]["date"] if ohlcv_data else None,
                "source": "cryptocompare"
            }
            
            # Cache the response
            self._hist_cache[cache_key] = {
                "data": response,
                "timestamp": time.time()
            }
            
            return response
        
        return result
    
    async def get_full_history(
        self,
        coin_symbol: str,
        to_symbol: str = "USD",
        max_days: int = 5000
    ) -> Dict[str, Any]:
        """
        Get full historical data by fetching multiple batches.
        Useful for AI training on long-term data.
        
        Args:
            coin_symbol: Cryptocurrency symbol
            to_symbol: Target currency
            max_days: Maximum number of days to fetch (fetched in 2000-day batches)
        
        Returns:
            Dict with combined OHLCV data
        """
        all_data = []
        current_ts = None
        batches_fetched = 0
        max_batches = (max_days // 2000) + 1
        
        while batches_fetched < max_batches:
            result = await self.get_historical_daily(
                coin_symbol=coin_symbol,
                to_symbol=to_symbol,
                limit=2000,
                to_ts=current_ts
            )
            
            if "error" in result or "data" not in result or len(result.get("data", [])) == 0:
                break
            
            batch_data = result["data"]
            
            # Prepend older data (API returns newest to oldest when using toTs)
            all_data = batch_data + all_data
            
            # Get the oldest timestamp for next batch
            if batch_data:
                current_ts = batch_data[0]["timestamp"] - 86400  # Go back 1 day
            
            batches_fetched += 1
            
            # If we got less than limit, we've reached the beginning
            if len(batch_data) < 2000:
                break
            
            # Brief delay to respect rate limits
            await asyncio.sleep(0.2)
        
        # Remove duplicates and sort
        seen_timestamps = set()
        unique_data = []
        for candle in sorted(all_data, key=lambda x: x["timestamp"]):
            if candle["timestamp"] not in seen_timestamps:
                seen_timestamps.add(candle["timestamp"])
                unique_data.append(candle)
        
        return {
            "symbol": coin_symbol.upper(),
            "to_symbol": to_symbol.upper(),
            "timeframe": "daily",
            "data": unique_data,
            "count": len(unique_data),
            "batches_fetched": batches_fetched,
            "time_from": unique_data[0]["date"] if unique_data else None,
            "time_to": unique_data[-1]["date"] if unique_data else None,
            "source": "cryptocompare"
        }


# Singleton instances
_coindesk_service = None
_cryptocompare_service = None

def get_coindesk_service() -> CoinDeskService:
    """Get or create CoinDesk service instance"""
    global _coindesk_service
    if _coindesk_service is None:
        _coindesk_service = CoinDeskService()
    return _coindesk_service


def get_cryptocompare_service() -> CryptoCompareHistoricalService:
    """Get or create CryptoCompare historical service instance"""
    global _cryptocompare_service
    if _cryptocompare_service is None:
        _cryptocompare_service = CryptoCompareHistoricalService()
    return _cryptocompare_service

"""
AI News Sentiment Analysis Service
Provides real-time sentiment analysis for crypto coins using news data and LLM analysis.
Integrates with training, gem finding, coin selection, strategy execution, and discovery.
Uses the CryptoPanic library for news feeds.
"""

import asyncio
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
import httpx
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Import CryptoPanic library
try:
    from cryptopanic import CryptoPanicClient, CryptoPanicAPIError
    CRYPTOPANIC_AVAILABLE = True
except ImportError:
    CRYPTOPANIC_AVAILABLE = False
    print("Warning: cryptopanic library not installed")

load_dotenv()


class AINewsSentimentService:
    """
    AI-powered news sentiment analysis for crypto coins.
    Uses CryptoPanic API library for news and Emergent LLM for sentiment analysis.
    """
    
    def __init__(self, db, historical_tracker=None):
        self.db = db
        self.api_key = os.getenv('EMERGENT_LLM_KEY')
        self.cryptopanic_key = os.getenv('CRYPTOPANIC_API_KEY', '')
        
        # Initialize CryptoPanic client if available
        self.cryptopanic_client = None
        if CRYPTOPANIC_AVAILABLE and self.cryptopanic_key:
            try:
                self.cryptopanic_client = CryptoPanicClient(
                    auth_token=self.cryptopanic_key,
                    timeout=30
                )
                print("✅ CryptoPanic client initialized")
            except Exception as e:
                print(f"CryptoPanic init error: {e}")
        
        # Historical sentiment tracker integration
        self.historical_tracker = historical_tracker
        
        # Cache settings
        self.cache_ttl = 3600  # 1 hour cache
        self.sentiment_cache = {}
        
        # Sentiment thresholds
        self.thresholds = {
            'very_bullish': 80,
            'bullish': 60,
            'neutral_high': 50,
            'neutral_low': 40,
            'bearish': 30,
            'very_bearish': 0
        }
    
    async def get_coin_sentiment(self, coin_id: str, symbol: str = None) -> Dict[str, Any]:
        """
        Get comprehensive sentiment analysis for a coin.
        Returns cached result if available and fresh.
        """
        cache_key = f"sentiment_{coin_id}"
        
        # Check cache
        if cache_key in self.sentiment_cache:
            cached = self.sentiment_cache[cache_key]
            if (datetime.now() - cached['timestamp']).seconds < self.cache_ttl:
                return cached['data']
        
        # Fetch fresh sentiment
        sentiment = await self._analyze_coin_sentiment(coin_id, symbol)
        
        # Cache result
        self.sentiment_cache[cache_key] = {
            'timestamp': datetime.now(),
            'data': sentiment
        }
        
        # Store in database for history
        await self._store_sentiment(coin_id, sentiment)
        
        return sentiment
    
    async def get_batch_sentiment(self, coins: List[Dict[str, str]]) -> Dict[str, Dict]:
        """
        Get sentiment for multiple coins efficiently.
        Args:
            coins: List of {'coin_id': 'bitcoin', 'symbol': 'BTC'}
        """
        results = {}
        
        # Process in batches of 5 to avoid rate limits
        batch_size = 5
        for i in range(0, len(coins), batch_size):
            batch = coins[i:i + batch_size]
            tasks = [
                self.get_coin_sentiment(c['coin_id'], c.get('symbol'))
                for c in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for j, result in enumerate(batch_results):
                coin_id = batch[j]['coin_id']
                if isinstance(result, Exception):
                    results[coin_id] = self._get_neutral_sentiment(coin_id)
                else:
                    results[coin_id] = result
            
            # Small delay between batches
            if i + batch_size < len(coins):
                await asyncio.sleep(0.5)
        
        return results
    
    async def _analyze_coin_sentiment(self, coin_id: str, symbol: str = None) -> Dict[str, Any]:
        """
        Perform full sentiment analysis for a coin.
        """
        # Fetch news
        news_items = await self._fetch_coin_news(coin_id, symbol)
        
        if not news_items:
            return self._get_neutral_sentiment(coin_id, "No recent news found")
        
        # Analyze with AI
        ai_analysis = await self._ai_analyze_news(coin_id, symbol, news_items)
        
        return {
            'coin_id': coin_id,
            'symbol': symbol,
            'score': ai_analysis['score'],
            'label': ai_analysis['label'],
            'confidence': ai_analysis['confidence'],
            'summary': ai_analysis['summary'],
            'key_factors': ai_analysis['key_factors'],
            'news_count': len(news_items),
            'recent_headlines': [n['title'] for n in news_items[:5]],
            'bullish_signals': ai_analysis.get('bullish_signals', []),
            'bearish_signals': ai_analysis.get('bearish_signals', []),
            'analyzed_at': datetime.now().isoformat()
        }
    
    async def _fetch_coin_news(self, coin_id: str, symbol: str = None) -> List[Dict]:
        """
        Fetch recent news for a coin from multiple sources.
        """
        news_items = []
        
        # Try CryptoPanic first (now uses the library)
        if self.cryptopanic_key or self.cryptopanic_client:
            cryptopanic_news = await self._fetch_cryptopanic_news(symbol or coin_id)
            news_items.extend(cryptopanic_news)
        
        # Fallback to CoinGecko news if no CryptoPanic news
        if len(news_items) < 5:
            coingecko_news = await self._fetch_coingecko_news(coin_id)
            news_items.extend(coingecko_news)
        
        # Deduplicate by title similarity
        seen_titles = set()
        unique_news = []
        for item in news_items:
            title_key = item['title'][:50].lower()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(item)
        
        # Sort by date, newest first
        unique_news.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        
        return unique_news[:15]  # Limit to 15 most recent
    
    async def get_trending_news(self, limit: int = 20) -> List[Dict]:
        """
        Get trending/rising crypto news from CryptoPanic.
        Useful for discovering market-moving events.
        """
        if not self.cryptopanic_client:
            return []
        
        try:
            loop = asyncio.get_event_loop()
            posts = await loop.run_in_executor(
                None,
                lambda: self.cryptopanic_client.get_posts(
                    filter="rising"
                )
            )
            
            news_items = []
            if posts and posts.results:
                for post in posts.results[:limit]:
                    # Extract currencies mentioned
                    currencies = []
                    if post.instruments:
                        currencies = [inst.code for inst in post.instruments]
                    
                    news_items.append({
                        'title': post.title,
                        'source': post.source.title if post.source else 'Unknown',
                        'published_at': post.published_at.isoformat() if post.published_at else '',
                        'url': post.url,
                        'kind': post.kind,
                        'panic_score': post.panic_score,
                        'currencies': currencies,
                        'votes': {
                            'positive': post.votes.positive if post.votes else 0,
                            'negative': post.votes.negative if post.votes else 0,
                            'important': post.votes.important if post.votes else 0,
                        }
                    })
            
            return news_items
            
        except Exception as e:
            print(f"Trending news error: {e}")
            return []
    
    async def get_bullish_bearish_news(self, filter_type: str = 'bullish') -> Dict[str, Any]:
        """
        Get news filtered by community sentiment (bullish or bearish).
        """
        if not self.cryptopanic_client:
            return {'news': [], 'filter': filter_type, 'count': 0}
        
        try:
            loop = asyncio.get_event_loop()
            posts = await loop.run_in_executor(
                None,
                lambda: self.cryptopanic_client.get_posts(
                    filter=filter_type  # "bullish" or "bearish"
                )
            )
            
            news_items = []
            if posts and posts.results:
                for post in posts.results[:20]:
                    currencies = []
                    if post.instruments:
                        currencies = [inst.code for inst in post.instruments]
                    
                    news_items.append({
                        'title': post.title,
                        'source': post.source.title if post.source else 'Unknown',
                        'published_at': post.published_at.isoformat() if post.published_at else '',
                        'currencies': currencies,
                        'panic_score': post.panic_score,
                    })
            
            return {
                'news': news_items,
                'filter': filter_type,
                'count': len(news_items)
            }
            
        except Exception as e:
            print(f"Bullish/bearish news error: {e}")
            return {'news': [], 'filter': filter_type, 'count': 0, 'error': str(e)}
    
    async def _fetch_cryptopanic_news(self, query: str) -> List[Dict]:
        """Fetch news from CryptoPanic using the official library"""
        news_items = []
        
        # Try using the CryptoPanic library first
        if self.cryptopanic_client:
            try:
                # Run in thread pool since the library is synchronous
                loop = asyncio.get_event_loop()
                posts = await loop.run_in_executor(
                    None,
                    lambda: self.cryptopanic_client.get_posts(
                        currencies=[query.upper()],
                        filter="hot"
                    )
                )
                
                if posts and posts.results:
                    for post in posts.results[:15]:
                        # Calculate sentiment from votes
                        votes = post.votes
                        vote_sentiment = 'neutral'
                        if votes:
                            pos_neg_ratio = (votes.positive + votes.liked) / max(1, votes.negative + votes.disliked + 1)
                            if pos_neg_ratio > 2:
                                vote_sentiment = 'bullish'
                            elif pos_neg_ratio < 0.5:
                                vote_sentiment = 'bearish'
                        
                        news_items.append({
                            'title': post.title,
                            'source': post.source.title if post.source else 'Unknown',
                            'published_at': post.published_at.isoformat() if post.published_at else '',
                            'url': post.url,
                            'kind': post.kind,
                            'panic_score': post.panic_score,
                            'vote_sentiment': vote_sentiment,
                            'votes': {
                                'positive': votes.positive if votes else 0,
                                'negative': votes.negative if votes else 0,
                                'important': votes.important if votes else 0,
                                'liked': votes.liked if votes else 0,
                                'disliked': votes.disliked if votes else 0,
                                'comments': votes.comments if votes else 0
                            }
                        })
                    
                    print(f"✅ CryptoPanic: Fetched {len(news_items)} news for {query}")
                    return news_items
                    
            except Exception as e:
                print(f"CryptoPanic library error: {e}")
        
        # Fallback to direct API call if library fails
        if self.cryptopanic_key:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    response = await client.get(
                        "https://cryptopanic.com/api/v1/posts/",
                        params={
                            'auth_token': self.cryptopanic_key,
                            'currencies': query.upper(),
                            'kind': 'news',
                            'filter': 'hot'
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        for item in data.get('results', []):
                            news_items.append({
                                'title': item.get('title', ''),
                                'source': item.get('source', {}).get('title', 'Unknown'),
                                'published_at': item.get('published_at', ''),
                                'url': item.get('url', ''),
                                'votes': item.get('votes', {})
                            })
            except Exception as e:
                print(f"CryptoPanic API fallback error: {e}")
        
        return news_items
    
    async def _fetch_coingecko_news(self, coin_id: str) -> List[Dict]:
        """Fetch news/status updates from CoinGecko"""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Get coin status updates which often contain news
                response = await client.get(
                    f"https://api.coingecko.com/api/v3/coins/{coin_id}",
                    params={'localization': False, 'tickers': False, 'community_data': True}
                )
                if response.status_code == 200:
                    data = response.json()
                    # Extract any available updates
                    updates = data.get('status_updates', [])
                    return [
                        {
                            'title': u.get('description', '')[:200],
                            'source': 'CoinGecko',
                            'published_at': u.get('created_at', ''),
                            'url': '',
                            'category': u.get('category', '')
                        }
                        for u in updates[:10]
                    ]
        except Exception as e:
            print(f"CoinGecko news fetch error: {e}")
        return []
    
    async def _ai_analyze_news(self, coin_id: str, symbol: str, news_items: List[Dict]) -> Dict:
        """
        Use AI to analyze news sentiment.
        """
        if not self.api_key:
            return self._get_rule_based_sentiment(news_items)
        
        try:
            # Prepare news summary for AI
            news_text = "\n".join([
                f"- {item['title']} (Source: {item.get('source', 'Unknown')})"
                for item in news_items[:10]
            ])
            
            prompt = f"""Analyze the following crypto news headlines for {symbol or coin_id} and provide a sentiment analysis.

NEWS HEADLINES:
{news_text}

Provide your analysis in this exact JSON format:
{{
    "score": <number 0-100, where 0=very bearish, 50=neutral, 100=very bullish>,
    "label": "<one of: very_bearish, bearish, neutral, bullish, very_bullish>",
    "confidence": <number 0-100 indicating how confident you are>,
    "summary": "<brief 1-2 sentence summary of overall sentiment>",
    "key_factors": ["<factor 1>", "<factor 2>", "<factor 3>"],
    "bullish_signals": ["<signal 1>", "<signal 2>"],
    "bearish_signals": ["<signal 1>", "<signal 2>"]
}}

Focus on:
- Price movement implications
- Partnership/adoption news
- Technical developments
- Regulatory news
- Market sentiment indicators

Return ONLY the JSON, no other text."""

            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"sentiment_{coin_id}_{datetime.now().strftime('%Y%m%d%H%M')}",
                system_message="You are a crypto market analyst specializing in news sentiment analysis. Always respond with valid JSON only."
            ).with_model("openai", "gpt-5.2")
            
            response = await chat.send_message(UserMessage(text=prompt))
            
            # Parse AI response
            import json
            # Clean response - remove markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith('```'):
                clean_response = clean_response.split('```')[1]
                if clean_response.startswith('json'):
                    clean_response = clean_response[4:]
            clean_response = clean_response.strip()
            
            analysis = json.loads(clean_response)
            
            return {
                'score': min(100, max(0, analysis.get('score', 50))),
                'label': analysis.get('label', 'neutral'),
                'confidence': min(100, max(0, analysis.get('confidence', 50))),
                'summary': analysis.get('summary', 'No analysis available'),
                'key_factors': analysis.get('key_factors', [])[:5],
                'bullish_signals': analysis.get('bullish_signals', [])[:3],
                'bearish_signals': analysis.get('bearish_signals', [])[:3]
            }
            
        except Exception as e:
            print(f"AI sentiment analysis error for {coin_id}: {e}")
            return self._get_rule_based_sentiment(news_items)
    
    def _get_rule_based_sentiment(self, news_items: List[Dict]) -> Dict:
        """
        Fallback rule-based sentiment when AI is unavailable.
        """
        bullish_keywords = [
            'surge', 'rally', 'bullish', 'breakout', 'partnership', 'adoption',
            'upgrade', 'launch', 'milestone', 'record', 'growth', 'soar',
            'moon', 'pump', 'gain', 'rise', 'positive', 'buy', 'accumulate'
        ]
        
        bearish_keywords = [
            'crash', 'dump', 'bearish', 'plunge', 'hack', 'scam', 'fraud',
            'regulation', 'ban', 'lawsuit', 'investigation', 'sell', 'drop',
            'fall', 'decline', 'negative', 'concern', 'risk', 'warning'
        ]
        
        bullish_count = 0
        bearish_count = 0
        bullish_signals = []
        bearish_signals = []
        
        for item in news_items:
            title_lower = item['title'].lower()
            
            for keyword in bullish_keywords:
                if keyword in title_lower:
                    bullish_count += 1
                    if len(bullish_signals) < 3:
                        bullish_signals.append(f"'{keyword}' mentioned in news")
                    break
            
            for keyword in bearish_keywords:
                if keyword in title_lower:
                    bearish_count += 1
                    if len(bearish_signals) < 3:
                        bearish_signals.append(f"'{keyword}' mentioned in news")
                    break
        
        total = bullish_count + bearish_count
        if total == 0:
            score = 50
            label = 'neutral'
        else:
            score = int((bullish_count / total) * 100)
            if score >= 70:
                label = 'bullish' if score < 85 else 'very_bullish'
            elif score <= 30:
                label = 'bearish' if score > 15 else 'very_bearish'
            else:
                label = 'neutral'
        
        return {
            'score': score,
            'label': label,
            'confidence': min(80, total * 10),
            'summary': f"Rule-based analysis: {bullish_count} bullish signals, {bearish_count} bearish signals",
            'key_factors': [f"{bullish_count} bullish indicators", f"{bearish_count} bearish indicators"],
            'bullish_signals': bullish_signals,
            'bearish_signals': bearish_signals
        }
    
    def _get_neutral_sentiment(self, coin_id: str, reason: str = "Insufficient data") -> Dict:
        """Return neutral sentiment when analysis isn't possible."""
        return {
            'coin_id': coin_id,
            'score': 50,
            'label': 'neutral',
            'confidence': 20,
            'summary': reason,
            'key_factors': ['No recent news available'],
            'news_count': 0,
            'recent_headlines': [],
            'bullish_signals': [],
            'bearish_signals': [],
            'analyzed_at': datetime.now().isoformat()
        }
    
    async def _store_sentiment(self, coin_id: str, sentiment: Dict):
        """Store sentiment analysis in database for historical tracking."""
        record = {
            'coin_id': coin_id,
            'score': sentiment['score'],
            'label': sentiment['label'],
            'confidence': sentiment['confidence'],
            'summary': sentiment.get('summary', ''),
            'timestamp': datetime.now().isoformat()
        }
        await self.db.sentiment_history.insert_one(record)
        
        # Also store in historical tracker if available
        if self.historical_tracker:
            try:
                await self.historical_tracker.store_sentiment(
                    coin_id=coin_id,
                    sentiment_data=sentiment,
                    metadata={'source': 'ai_news_sentiment'}
                )
            except Exception as e:
                print(f"Failed to store in historical tracker: {e}")
    
    async def get_sentiment_history(self, coin_id: str, days: int = 7) -> List[Dict]:
        """Get historical sentiment data for a coin."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        history = await self.db.sentiment_history.find(
            {'coin_id': coin_id, 'timestamp': {'$gte': cutoff}},
            {'_id': 0}
        ).sort('timestamp', -1).to_list(100)
        return history
    
    async def get_market_sentiment(self) -> Dict[str, Any]:
        """
        Get overall market sentiment by analyzing top coins.
        """
        top_coins = [
            {'coin_id': 'bitcoin', 'symbol': 'BTC'},
            {'coin_id': 'ethereum', 'symbol': 'ETH'},
            {'coin_id': 'binancecoin', 'symbol': 'BNB'},
            {'coin_id': 'solana', 'symbol': 'SOL'},
            {'coin_id': 'ripple', 'symbol': 'XRP'}
        ]
        
        sentiments = await self.get_batch_sentiment(top_coins)
        
        # Calculate weighted average (BTC and ETH weighted more)
        weights = {'bitcoin': 0.3, 'ethereum': 0.25, 'binancecoin': 0.15, 'solana': 0.15, 'ripple': 0.15}
        
        total_score = 0
        total_confidence = 0
        
        for coin_id, sentiment in sentiments.items():
            weight = weights.get(coin_id, 0.1)
            total_score += sentiment['score'] * weight
            total_confidence += sentiment['confidence'] * weight
        
        avg_score = total_score
        
        if avg_score >= 70:
            market_label = 'bullish'
        elif avg_score <= 30:
            market_label = 'bearish'
        else:
            market_label = 'neutral'
        
        return {
            'market_score': round(avg_score, 1),
            'market_label': market_label,
            'confidence': round(total_confidence, 1),
            'coin_sentiments': sentiments,
            'analyzed_at': datetime.now().isoformat()
        }
    
    def calculate_sentiment_adjustment(self, base_score: float, sentiment: Dict) -> float:
        """
        Calculate score adjustment based on sentiment.
        Used by other services to modify their scores.
        
        Args:
            base_score: Original score (0-100)
            sentiment: Sentiment analysis result
        
        Returns:
            Adjusted score (0-100)
        """
        sentiment_score = sentiment.get('score', 50)
        confidence = sentiment.get('confidence', 50) / 100
        
        # Calculate adjustment (-20 to +20 based on sentiment deviation from neutral)
        deviation = (sentiment_score - 50) / 50  # -1 to +1
        max_adjustment = 20
        
        adjustment = deviation * max_adjustment * confidence
        
        adjusted_score = base_score + adjustment
        return max(0, min(100, adjusted_score))


# Global instance
_sentiment_service = None

def get_sentiment_service():
    global _sentiment_service
    return _sentiment_service

def set_sentiment_service(service):
    global _sentiment_service
    _sentiment_service = service

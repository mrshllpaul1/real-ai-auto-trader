import httpx
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv()

class CryptoNewsAggregator:
    """
    Aggregates cryptocurrency news from multiple sources with fallbacks
    """
    
    def __init__(self):
        self.llm_api_key = os.getenv('EMERGENT_LLM_KEY')
        self.news_sources = {
            'free_crypto_news': 'https://news-crypto.vercel.app/api',  # Free, no API key required
            'cryptopanic': 'https://cryptopanic.com/api/v1',
            'coinmarketcap': 'https://pro-api.coinmarketcap.com/v1'
        }
        self.cmc_api_key = os.getenv('COINMARKETCAP_API_KEY')
        # In-memory cache to reduce API calls
        self._news_cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def get_free_crypto_news(self, currencies: List[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
        """Get news from free-crypto-news API (no API key required)"""
        try:
            # Check cache first
            cache_key = f"free_news_{','.join(currencies or ['all'])}_{limit}"
            cached = self._get_cached(cache_key)
            if cached:
                return cached
            
            # Build params - use category filter if currency specified
            params = {'limit': min(limit, 50)}
            
            # Map common currency names to API categories
            category_map = {
                'bitcoin': 'bitcoin',
                'btc': 'bitcoin',
                'ethereum': 'ethereum',
                'eth': 'ethereum',
                'solana': 'altcoins',
                'sol': 'altcoins',
                'defi': 'defi',
                'nft': 'nft',
            }
            
            if currencies and len(currencies) == 1:
                category = category_map.get(currencies[0].lower())
                if category:
                    params['category'] = category
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.news_sources['free_crypto_news']}/news",
                    params=params,
                    timeout=15.0
                )
                
                if response.status_code != 200:
                    print(f"Free Crypto News API returned {response.status_code}")
                    return []
                
                data = response.json()
                articles = data.get('articles', [])[:limit]
                
                result = [
                    {
                        'title': item.get('title', ''),
                        'description': item.get('description', ''),
                        'published_at': item.get('pubDate', ''),
                        'source': item.get('source', 'Crypto News'),
                        'url': item.get('link', ''),
                        'category': item.get('category', 'crypto'),
                        'time_ago': item.get('timeAgo', ''),
                        'sentiment': self._infer_sentiment_from_title(
                            item.get('title', ''),
                            item.get('description', '')
                        ),
                        'aggregator': 'free_crypto_news',
                        'currencies': self._extract_currencies_from_text(item.get('title', '') + ' ' + item.get('description', ''))
                    }
                    for item in articles
                ]
                
                # Cache the result
                self._set_cache(cache_key, result)
                return result
                
        except Exception as e:
            print(f"Free Crypto News error: {str(e)}")
            return []
    
    def _infer_sentiment_from_title(self, title: str, description: str = "") -> str:
        """Infer basic sentiment from news title and description"""
        text_lower = f"{title} {description}".lower()
        
        positive_keywords = ['surge', 'soar', 'rally', 'gains', 'bull', 'rise', 'up', 'growth', 
                           'adoption', 'partnership', 'launch', 'breakthrough', 'record', 'high']
        negative_keywords = ['crash', 'drop', 'fall', 'plunge', 'bear', 'down', 'loss', 'hack', 
                           'exploit', 'scam', 'fraud', 'lawsuit', 'ban', 'warning', 'risk']
        
        positive_count = sum(1 for kw in positive_keywords if kw in text_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        return 'neutral'
    
    def _extract_currencies_from_text(self, text: str) -> List[str]:
        """Extract cryptocurrency mentions from text"""
        currencies = []
        text_upper = text.upper()
        
        crypto_keywords = {
            'BITCOIN': 'BTC', 'BTC': 'BTC',
            'ETHEREUM': 'ETH', 'ETH': 'ETH',
            'SOLANA': 'SOL', 'SOL': 'SOL',
            'CARDANO': 'ADA', 'ADA': 'ADA',
            'POLKADOT': 'DOT', 'DOT': 'DOT',
            'CHAINLINK': 'LINK', 'LINK': 'LINK',
            'AVALANCHE': 'AVAX', 'AVAX': 'AVAX',
            'POLYGON': 'MATIC', 'MATIC': 'MATIC',
            'XRP': 'XRP', 'RIPPLE': 'XRP',
            'DOGECOIN': 'DOGE', 'DOGE': 'DOGE',
        }
        
        for keyword, symbol in crypto_keywords.items():
            if keyword in text_upper and symbol not in currencies:
                currencies.append(symbol)
        
        return currencies
    
    def _get_cached(self, key: str) -> Any:
        """Get item from cache if not expired"""
        if key in self._news_cache:
            item, timestamp = self._news_cache[key]
            if (datetime.now() - timestamp).total_seconds() < self._cache_ttl:
                return item
            del self._news_cache[key]
        return None
    
    def _set_cache(self, key: str, value: Any):
        """Set item in cache"""
        self._news_cache[key] = (value, datetime.now())
    
    async def get_cryptopanic_news(self, currencies: List[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get news from CryptoPanic"""
        try:
            params = {
                'auth_token': 'free',
                'public': 'true',
                'kind': 'news'
            }
            
            if currencies:
                params['currencies'] = ','.join([c.upper() for c in currencies])
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.news_sources['cryptopanic']}/posts/",
                    params=params,
                    timeout=15.0
                )
                
                if response.status_code != 200:
                    return []
                
                data = response.json()
                results = data.get('results', [])[:limit]
                
                return [
                    {
                        'title': item.get('title', ''),
                        'published_at': item.get('published_at', ''),
                        'source': item.get('source', {}).get('title', 'CryptoPanic'),
                        'url': item.get('url', ''),
                        'currencies': [c['code'] for c in item.get('currencies', [])],
                        'kind': item.get('kind', 'news'),
                        'sentiment': self._extract_sentiment_from_votes(item.get('votes', {})),
                        'aggregator': 'cryptopanic'
                    }
                    for item in results
                ]
        except Exception as e:
            print(f"CryptoPanic error: {str(e)}")
            return []
    
    async def get_coinmarketcap_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get news from CoinMarketCap (fallback source)"""
        try:
            if not self.cmc_api_key:
                return []  # Return empty if no API key - NEVER use simulated data
            
            headers = {'X-CMC_PRO_API_KEY': self.cmc_api_key}
            
            async with httpx.AsyncClient() as client:
                # CMC doesn't have news API in basic tier, use trending
                response = await client.get(
                    f"{self.news_sources['coinmarketcap']}/cryptocurrency/trending/latest",
                    headers=headers,
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    coins = data.get('data', [])[:limit]
                    
                    return [
                        {
                            'title': f"{coin.get('name', 'Crypto')} is trending - {coin.get('symbol', '')}",
                            'description': f"Rank #{coin.get('rank', '?')} with ${coin.get('quote', {}).get('USD', {}).get('market_cap', 0):,.0f} market cap",
                            'published_at': datetime.now().isoformat(),
                            'source': 'CoinMarketCap Trending',
                            'url': f"https://coinmarketcap.com/currencies/{coin.get('slug', '')}",
                            'sentiment': 'positive' if coin.get('quote', {}).get('USD', {}).get('percent_change_24h', 0) > 0 else 'negative',
                            'aggregator': 'coinmarketcap'
                        }
                        for coin in coins
                    ]
                
                return await self._get_unavailable_news_response(limit)
        except Exception as e:
            print(f"CMC news error: {str(e)}")
            return await self._get_unavailable_news_response(limit)
    
    async def _get_unavailable_news_response(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Return empty list when all news APIs fail.
        NEVER returns simulated or fake news - only real news data is used.
        """
        return []
    
    def _extract_sentiment_from_votes(self, votes: Dict) -> str:
        """Extract sentiment from CryptoPanic votes"""
        positive = votes.get('positive', 0)
        negative = votes.get('negative', 0)
        
        if positive > negative * 2:
            return 'positive'
        elif negative > positive * 2:
            return 'negative'
        return 'neutral'
    
    async def get_coingecko_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get status updates from CoinGecko"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.news_sources['coingecko']}/status_updates",
                    params={'category': 'general', 'per_page': limit},
                    timeout=15.0
                )
                
                if response.status_code != 200:
                    return []
                
                data = response.json()
                updates = data.get('status_updates', [])[:limit]
                
                return [
                    {
                        'title': update.get('project', {}).get('name', 'Crypto Update'),
                        'description': update.get('description', ''),
                        'published_at': update.get('created_at', ''),
                        'source': 'CoinGecko',
                        'url': update.get('project', {}).get('id', ''),
                        'category': update.get('category', 'general'),
                        'aggregator': 'coingecko'
                    }
                    for update in updates
                ]
        except Exception as e:
            print(f"CoinGecko news error: {str(e)}")
            return []
    
    async def get_aggregated_news(
        self,
        currencies: List[str] = None,
        limit_per_source: int = 25
    ) -> List[Dict[str, Any]]:
        """Get aggregated news from all sources with fallbacks"""
        # Primary source: Free Crypto News API (most reliable, no API key needed)
        free_news = await self.get_free_crypto_news(currencies, limit_per_source)
        
        # Secondary sources as fallback
        cryptopanic_news = []
        cmc_news = []
        
        # Only fetch from secondary sources if primary returned few results
        if len(free_news) < 10:
            cryptopanic_news = await self.get_cryptopanic_news(currencies, limit_per_source)
            cmc_news = await self.get_coinmarketcap_news(limit_per_source)
        
        # Combine all sources
        all_news = free_news + cryptopanic_news + cmc_news
        
        # If no real news found, return empty (NEVER use simulated data)
        if len(all_news) == 0:
            print("Warning: All news APIs failed, returning empty list (no simulated data allowed)")
            all_news = []
        
        # Sort by published date (most recent first)
        all_news.sort(
            key=lambda x: x.get('published_at', ''),
            reverse=True
        )
        
        return all_news[:50]
    
    async def analyze_news_sentiment(
        self,
        news_items: List[Dict[str, Any]],
        coin_id: str
    ) -> Dict[str, Any]:
        """Use AI to analyze overall news sentiment for a cryptocurrency"""
        try:
            # Filter news relevant to the coin
            relevant_news = [
                item for item in news_items
                if not item.get('currencies') or 
                coin_id.upper() in [c.upper() for c in item.get('currencies', [])] or
                coin_id.lower() in item.get('title', '').lower() or
                coin_id.lower() in item.get('description', '').lower()
            ][:10]
            
            if not relevant_news:
                return {
                    'sentiment': 'neutral',
                    'confidence': 0,
                    'summary': 'No recent news found',
                    'news_count': 0
                }
            
            # Prepare news summary for AI analysis
            news_summary = "\n".join([
                f"- {item.get('title', '')} ({item.get('published_at', '')[:10]})"
                for item in relevant_news
            ])
            
            chat = LlmChat(
                api_key=self.llm_api_key,
                session_id=f"news_sentiment_{coin_id}_{datetime.now().timestamp()}",
                system_message="You are an expert cryptocurrency market analyst specializing in news sentiment analysis. Analyze news objectively and provide clear, actionable insights."
            ).with_model("openai", "gpt-5.2")
            
            prompt = f"""
Analyze the following recent news about {coin_id.upper()} and provide sentiment analysis:

Recent News Headlines:
{news_summary}

Provide:
1. Overall Sentiment (positive/negative/neutral)
2. Confidence Score (0-100)
3. Key Themes (3-5 bullet points)
4. Market Impact Assessment (bullish/bearish/neutral)
5. Short Summary (2-3 sentences)

Be objective and focus on market-moving information.
"""
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            # Enhanced sentiment scoring with keyword and recency weighting
            scored_items = [self._score_news_item(item) for item in relevant_news]
            if scored_items:
                sentiment_score = sum(score for score, _ in scored_items) / len(scored_items)
            else:
                sentiment_score = 0.0
            
            positive_count = sum(1 for _, label in scored_items if label == 'positive')
            negative_count = sum(1 for _, label in scored_items if label == 'negative')
            neutral_count = len(scored_items) - positive_count - negative_count
            
            sentiment_label = (
                'positive' if sentiment_score > 0.15
                else 'negative' if sentiment_score < -0.15
                else 'neutral'
            )
            
            coverage_factor = min(1.0, len(relevant_news) / 8)  # more articles -> higher confidence
            confidence = round(
                min(1.0, abs(sentiment_score) * 0.7 + coverage_factor * 0.3) * 100,
                1
            )
            
            return {
                'sentiment': sentiment_label,
                'sentiment_score': round((sentiment_score + 1) * 50, 1),  # -1..1 -> 0..100
                'confidence': confidence,
                'ai_analysis': response,
                'news_count': len(relevant_news),
                'analyzed_at': datetime.now().isoformat(),
                'recent_headlines': [item.get('title') for item in relevant_news[:5]],
                'positive_articles': positive_count,
                'negative_articles': negative_count,
                'neutral_articles': neutral_count
            }
        except Exception as e:
            print(f"Sentiment analysis error: {str(e)}")
            return {
                'sentiment': 'neutral',
                'confidence': 0,
                'summary': f'Analysis error: {str(e)}',
                'news_count': 0
            }
    
    def _calculate_sentiment_score(self, news_items: List[Dict[str, Any]]) -> float:
        """Calculate numerical sentiment score from news items"""
        if not news_items:
            return 0.0
        
        scores = []
        for item in news_items:
            score, _ = self._score_news_item(item)
            scores.append(score)
        
        return sum(scores) / len(scores) if scores else 0.0

    def _score_news_item(self, item: Dict[str, Any]) -> Tuple[float, str]:
        """
        Score a news item using keyword cues, provided sentiment, and recency weighting.
        Returns tuple of (score -1..1, label).
        """
        sentiment_map = {'positive': 0.6, 'negative': -0.6, 'neutral': 0.0}
        positive_keywords = [
            'surge', 'soar', 'rally', 'gains', 'bull', 'rise', 'up', 'growth',
            'adoption', 'partnership', 'launch', 'breakthrough', 'record', 'high',
            'upgrade', 'etf approval', 'integration', 'listing', 'support'
        ]
        negative_keywords = [
            'crash', 'drop', 'fall', 'plunge', 'bear', 'down', 'loss', 'hack',
            'exploit', 'scam', 'fraud', 'lawsuit', 'ban', 'warning', 'risk',
            'delist', 'halt', 'investigation', 'shutdown'
        ]
        
        text = f"{item.get('title', '')} {item.get('description', '')}".lower()
        base_score = sentiment_map.get(item.get('sentiment', 'neutral'), 0.0)
        
        keyword_score = 0.0
        if any(kw in text for kw in positive_keywords):
            keyword_score += 0.25
        if any(kw in text for kw in negative_keywords):
            keyword_score -= 0.25
        
        combined = max(-1.0, min(1.0, base_score + keyword_score))
        
        # Recency weighting (newer news gets higher weight)
        weight = 1.0
        published_at = item.get('published_at') or item.get('pubDate')
        if published_at:
            try:
                news_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                hours_old = max(0, (datetime.now(news_time.tzinfo) - news_time).total_seconds() / 3600)
                weight = max(0.4, 1 - min(hours_old, 72) / 120)  # decay over 3 days
            except Exception:
                weight = 1.0
        
        weighted_score = combined * weight
        label = 'positive' if weighted_score > 0.05 else 'negative' if weighted_score < -0.05 else 'neutral'
        
        return weighted_score, label
    
    async def get_market_moving_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get high-impact market-moving news"""
        all_news = await self.get_aggregated_news(limit_per_source=50)
        
        # Filter for high-impact news
        market_moving = [
            item for item in all_news
            if any(keyword in item.get('title', '').lower() for keyword in [
                'breaking', 'sec', 'regulation', 'etf', 'adoption',
                'hack', 'exploit', 'lawsuit', 'partnership', 'integration',
                'listing', 'delisting', 'upgrade', 'fork', 'halving'
            ])
        ]
        
        return market_moving[:limit]

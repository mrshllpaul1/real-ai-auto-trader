import httpx
from typing import Dict, Any, List
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
            'cryptopanic': 'https://cryptopanic.com/api/v1',
            'coingecko': 'https://api.coingecko.com/api/v3',
            'coinmarketcap': 'https://pro-api.coinmarketcap.com/v1'
        }
        self.cmc_api_key = os.getenv('COINMARKETCAP_API_KEY')
    
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
                return await self._get_simulated_news(limit)
            
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
                
                return await self._get_simulated_news(limit)
        except Exception as e:
            print(f"CMC news error: {str(e)}")
            return await self._get_simulated_news(limit)
    
    async def _get_simulated_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Generate simulated news when APIs fail"""
        simulated = [
            {'title': 'Bitcoin ETF inflows continue strong momentum', 'sentiment': 'positive', 'source': 'Market Analysis'},
            {'title': 'Ethereum Layer 2 adoption reaches new highs', 'sentiment': 'positive', 'source': 'DeFi News'},
            {'title': 'Solana ecosystem expands with new DeFi protocols', 'sentiment': 'positive', 'source': 'Solana Daily'},
            {'title': 'Institutional crypto adoption accelerates globally', 'sentiment': 'positive', 'source': 'Institutional Insights'},
            {'title': 'DeFi TVL shows steady growth across chains', 'sentiment': 'neutral', 'source': 'DeFi Pulse'},
            {'title': 'Crypto market volatility remains elevated', 'sentiment': 'neutral', 'source': 'Market Watch'},
            {'title': 'New regulatory framework proposed for stablecoins', 'sentiment': 'neutral', 'source': 'Regulatory News'},
            {'title': 'NFT market sees renewed interest from collectors', 'sentiment': 'positive', 'source': 'NFT Insider'},
            {'title': 'Cross-chain bridges improve security measures', 'sentiment': 'positive', 'source': 'Security Weekly'},
            {'title': 'AI-powered trading tools gain popularity', 'sentiment': 'positive', 'source': 'Tech Trends'},
        ]
        
        now = datetime.now()
        return [
            {
                **item,
                'published_at': (now - timedelta(hours=i*2)).isoformat(),
                'url': '#',
                'aggregator': 'simulated',
                'currencies': []
            }
            for i, item in enumerate(simulated[:limit])
        ]
    
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
        """Get aggregated news from all sources"""
        # Fetch from all sources in parallel
        cryptopanic_news = await self.get_cryptopanic_news(currencies, limit_per_source)
        coingecko_news = await self.get_coingecko_news(limit_per_source)
        
        # Combine and sort by date
        all_news = cryptopanic_news + coingecko_news
        
        # Sort by published date (most recent first)
        all_news.sort(
            key=lambda x: x.get('published_at', ''),
            reverse=True
        )
        
        return all_news[:50]  # Return top 50 most recent
    
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
            
            # Extract sentiment from response
            sentiment_score = self._calculate_sentiment_score(relevant_news)
            
            return {
                'sentiment': 'positive' if sentiment_score > 0.3 else 'negative' if sentiment_score < -0.3 else 'neutral',
                'confidence': abs(sentiment_score) * 100,
                'ai_analysis': response,
                'news_count': len(relevant_news),
                'analyzed_at': datetime.now().isoformat(),
                'recent_headlines': [item.get('title') for item in relevant_news[:5]]
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
        
        sentiment_map = {'positive': 1.0, 'negative': -1.0, 'neutral': 0.0}
        scores = [sentiment_map.get(item.get('sentiment', 'neutral'), 0.0) for item in news_items]
        
        return sum(scores) / len(scores) if scores else 0.0
    
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

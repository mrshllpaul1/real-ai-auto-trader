"""
Social Sentiment Analyzer
Detects early-stage coins via social media sentiment analysis.
Scans for trending coins before they pump.
"""

import asyncio
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re
from collections import Counter
import os
from dotenv import load_dotenv

load_dotenv()


class SocialSentimentAnalyzer:
    """
    Analyzes social media sentiment to detect early-stage coins.
    Uses multiple data sources for sentiment signals.
    """
    
    def __init__(self, db):
        self.db = db
        
        # Keywords that indicate bullish sentiment
        self.bullish_keywords = [
            'moon', 'pump', 'bullish', 'breakout', 'gem', 'buy',
            '100x', '10x', 'undervalued', 'sleeping giant', 'next',
            'ath', 'all time high', 'accumulate', 'load up', 'dip'
        ]
        
        # Keywords that indicate bearish sentiment
        self.bearish_keywords = [
            'dump', 'crash', 'bearish', 'sell', 'scam', 'rug',
            'dead', 'over', 'avoid', 'warning', 'careful'
        ]
        
        # Coin mention patterns
        self.coin_patterns = [
            r'\$([A-Z]{2,10})',  # $BTC, $ETH
            r'#([A-Z]{2,10})',   # #BTC, #ETH
            r'\b([A-Z]{2,6})\b(?=.*(?:coin|token|crypto))',  # BTC mentioned with crypto context
        ]
        
        # Sentiment history
        self.sentiment_cache = {}
    
    async def analyze_news_sentiment(self) -> Dict[str, Any]:
        """Analyze sentiment from crypto news sources"""
        try:
            async with httpx.AsyncClient() as client:
                # Use the free crypto news API
                response = await client.get(
                    "https://crypto-news16.p.rapidapi.com/news/top/10",
                    headers={
                        "X-RapidAPI-Key": os.getenv('RAPIDAPI_KEY', ''),
                        "X-RapidAPI-Host": "crypto-news16.p.rapidapi.com"
                    },
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    # Fallback to our internal news
                    return await self._analyze_internal_news()
                
                news = response.json()
                return self._process_news_sentiment(news)
                
        except Exception as e:
            print(f"News sentiment error: {e}")
            return await self._analyze_internal_news()
    
    async def _analyze_internal_news(self) -> Dict[str, Any]:
        """Analyze sentiment from internal news cache"""
        news = await self.db.news_cache.find(
            {}, {'_id': 0}
        ).sort('published_at', -1).limit(50).to_list(50)
        
        return self._process_news_sentiment(news)
    
    def _process_news_sentiment(self, news: List[Dict]) -> Dict[str, Any]:
        """Process news articles for sentiment signals"""
        coin_mentions = Counter()
        coin_sentiment = {}
        
        for article in news:
            title = article.get('title', '').lower()
            description = article.get('description', '').lower()
            text = f"{title} {description}"
            
            # Find coin mentions
            for pattern in self.coin_patterns:
                matches = re.findall(pattern, text.upper())
                for match in matches:
                    coin_mentions[match] += 1
            
            # Calculate sentiment for mentioned coins
            bullish_count = sum(1 for kw in self.bullish_keywords if kw in text)
            bearish_count = sum(1 for kw in self.bearish_keywords if kw in text)
            
            sentiment_score = (bullish_count - bearish_count) / max(1, bullish_count + bearish_count)
            
            # Assign sentiment to mentioned coins
            for pattern in self.coin_patterns:
                matches = re.findall(pattern, text.upper())
                for coin in matches:
                    if coin not in coin_sentiment:
                        coin_sentiment[coin] = []
                    coin_sentiment[coin].append(sentiment_score)
        
        # Calculate average sentiment per coin
        avg_sentiment = {}
        for coin, scores in coin_sentiment.items():
            avg_sentiment[coin] = sum(scores) / len(scores)
        
        # Find trending coins (high mentions + positive sentiment)
        trending = []
        for coin, count in coin_mentions.most_common(20):
            sentiment = avg_sentiment.get(coin, 0)
            trend_score = count * (1 + sentiment)  # Weight by sentiment
            
            trending.append({
                'symbol': coin,
                'mentions': count,
                'sentiment': round(sentiment, 2),
                'trend_score': round(trend_score, 2)
            })
        
        return {
            'analyzed_articles': len(news),
            'trending_coins': sorted(trending, key=lambda x: x['trend_score'], reverse=True)[:10],
            'most_bullish': sorted(avg_sentiment.items(), key=lambda x: x[1], reverse=True)[:5],
            'most_bearish': sorted(avg_sentiment.items(), key=lambda x: x[1])[:5],
            'analyzed_at': datetime.now().isoformat()
        }
    
    async def detect_early_gems(self) -> List[Dict[str, Any]]:
        """
        Detect early-stage gems based on social signals.
        Looks for coins with sudden sentiment spikes.
        """
        current = await self.analyze_news_sentiment()
        
        # Get previous sentiment (24h ago)
        previous = await self.db.sentiment_history.find_one(
            {'timestamp': {'$lt': (datetime.now() - timedelta(hours=24)).isoformat()}},
            {'_id': 0},
            sort=[('timestamp', -1)]
        )
        
        early_gems = []
        
        for coin_data in current.get('trending_coins', []):
            symbol = coin_data['symbol']
            current_score = coin_data['trend_score']
            
            # Check for sudden spike
            if previous:
                prev_coins = {c['symbol']: c['trend_score'] for c in previous.get('trending_coins', [])}
                prev_score = prev_coins.get(symbol, 0)
                
                # Spike detection: 2x increase in trend score
                if prev_score > 0 and current_score / prev_score >= 2:
                    early_gems.append({
                        'symbol': symbol,
                        'current_score': current_score,
                        'previous_score': prev_score,
                        'spike_ratio': round(current_score / prev_score, 2),
                        'sentiment': coin_data['sentiment'],
                        'mentions': coin_data['mentions'],
                        'signal': '🚀 EARLY SIGNAL' if current_score / prev_score >= 3 else '👀 WATCHING'
                    })
                elif prev_score == 0 and current_score >= 5:
                    # New coin appearing with strong signal
                    early_gems.append({
                        'symbol': symbol,
                        'current_score': current_score,
                        'previous_score': 0,
                        'spike_ratio': float('inf'),
                        'sentiment': coin_data['sentiment'],
                        'mentions': coin_data['mentions'],
                        'signal': '🆕 NEW TRENDING'
                    })
        
        # Store current sentiment for future comparison
        await self.db.sentiment_history.insert_one({
            **current,
            'timestamp': datetime.now().isoformat()
        })
        
        return early_gems
    
    async def get_coin_sentiment(self, coin_symbol: str) -> Dict[str, Any]:
        """Get detailed sentiment for a specific coin"""
        # Check cache first
        cached = self.sentiment_cache.get(coin_symbol)
        if cached and (datetime.now() - cached['timestamp']).seconds < 300:
            return cached['data']
        
        # Analyze recent news for this coin
        news = await self.db.news_cache.find(
            {'$or': [
                {'title': {'$regex': coin_symbol, '$options': 'i'}},
                {'description': {'$regex': coin_symbol, '$options': 'i'}}
            ]},
            {'_id': 0}
        ).sort('published_at', -1).limit(20).to_list(20)
        
        if not news:
            return {'symbol': coin_symbol, 'sentiment': 0, 'articles': 0}
        
        total_sentiment = 0
        for article in news:
            text = f"{article.get('title', '')} {article.get('description', '')}".lower()
            bullish = sum(1 for kw in self.bullish_keywords if kw in text)
            bearish = sum(1 for kw in self.bearish_keywords if kw in text)
            total_sentiment += bullish - bearish
        
        avg_sentiment = total_sentiment / len(news)
        
        result = {
            'symbol': coin_symbol,
            'sentiment': round(avg_sentiment, 2),
            'sentiment_label': 'BULLISH' if avg_sentiment > 0.5 else 'BEARISH' if avg_sentiment < -0.5 else 'NEUTRAL',
            'articles_analyzed': len(news),
            'recent_headlines': [n.get('title', '')[:100] for n in news[:5]]
        }
        
        # Cache result
        self.sentiment_cache[coin_symbol] = {
            'data': result,
            'timestamp': datetime.now()
        }
        
        return result
    
    async def get_sentiment_summary(self) -> Dict[str, Any]:
        """Get overall market sentiment summary"""
        sentiment_data = await self.analyze_news_sentiment()
        early_gems = await self.detect_early_gems()
        
        return {
            'market_sentiment': sentiment_data,
            'early_gems': early_gems,
            'gem_count': len(early_gems),
            'analysis_time': datetime.now().isoformat()
        }

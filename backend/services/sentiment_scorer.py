"""
Sentiment Scoring Service
=========================
Aggregates sentiment from multiple sources and provides scores for AI trading decisions.
Now includes Fear & Greed Index as primary sentiment source.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class SentimentScorer:
    """
    Aggregates sentiment data and provides normalized scores for trading decisions.
    """
    
    # Sentiment weight factors (updated with fear_greed)
    WEIGHTS = {
        'fear_greed': 0.35,  # Fear & Greed Index (primary)
        'technical': 0.30,   # Technical indicators (RSI, MACD)
        'volume': 0.20,      # Volume analysis
        'news': 0.15         # CryptoPanic news sentiment (when available)
    }
    
    # Sentiment thresholds
    BULLISH_THRESHOLD = 0.6
    BEARISH_THRESHOLD = 0.4
    
    def __init__(self, db=None):
        self.db = db
        self.sentiment_cache = {}
        self.cache_ttl = timedelta(minutes=5)
        self._last_update = {}
        self._fear_greed_cache = None
        logger.info("📊 Sentiment Scorer initialized")
    
    async def get_coin_sentiment(
        self,
        symbol: str,
        include_sources: bool = False
    ) -> Dict[str, Any]:
        """
        Get aggregated sentiment score for a coin.
        
        Returns:
            {
                "symbol": "BTC",
                "score": 0.65,  # 0-1 scale, >0.6 bullish, <0.4 bearish
                "signal": "BULLISH",
                "confidence": 0.8,
                "sources": {...}  # if include_sources=True
            }
        """
        # Check cache
        cache_key = symbol.upper().replace('/USD', '').replace('USD', '')
        if cache_key in self.sentiment_cache:
            cached = self.sentiment_cache[cache_key]
            if datetime.now() - cached['timestamp'] < self.cache_ttl:
                return cached['data']
        
        # Collect sentiment from sources
        sources = {}
        
        # Fear & Greed Index (primary source - always available)
        fear_greed_score = await self._get_fear_greed_sentiment()
        sources['fear_greed'] = fear_greed_score
        
        # Technical sentiment (RSI, MACD based)
        tech_score = await self._get_technical_sentiment(cache_key)
        sources['technical'] = tech_score
        
        # Volume analysis
        volume_score = await self._get_volume_sentiment(cache_key)
        sources['volume'] = volume_score
        
        # News sentiment (CryptoPanic - may be unavailable)
        news_score = await self._get_news_sentiment(cache_key)
        sources['news'] = news_score
        
        # Calculate weighted score
        total_score = 0
        total_weight = 0
        
        for source, data in sources.items():
            if data['available']:
                weight = self.WEIGHTS.get(source, 0.1)
                total_score += data['score'] * weight * data['confidence']
                total_weight += weight * data['confidence']
        
        if total_weight > 0:
            final_score = total_score / total_weight
        else:
            final_score = 0.5  # Neutral
        
        # Determine signal
        if final_score >= self.BULLISH_THRESHOLD:
            signal = "BULLISH"
        elif final_score <= self.BEARISH_THRESHOLD:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"
        
        # Calculate overall confidence
        available_sources = sum(1 for s in sources.values() if s['available'])
        confidence = (available_sources / len(sources)) * 0.5 + 0.5
        
        result = {
            "symbol": cache_key,
            "score": round(final_score, 3),
            "signal": signal,
            "confidence": round(confidence, 2),
            "updated_at": datetime.now().isoformat()
        }
        
        if include_sources:
            result["sources"] = sources
        
        # Cache result
        self.sentiment_cache[cache_key] = {
            'timestamp': datetime.now(),
            'data': result
        }
        
        return result
    
    async def _get_fear_greed_sentiment(self) -> Dict[str, Any]:
        """Get sentiment from Fear & Greed Index (primary source)"""
        try:
            from services.fear_greed_service import get_fear_greed_service
            service = get_fear_greed_service()
            
            data = await service.get_current_index()
            
            if not data or data.get('value') is None:
                return {'score': 0.5, 'confidence': 0, 'available': False}
            
            # Convert 0-100 index to 0-1 score
            # Fear (0-49) = bearish, Greed (51-100) = bullish
            value = data['value']
            score = value / 100  # Direct mapping: 0=extreme fear, 100=extreme greed
            
            # Determine signal
            signal = data.get('signal', 'NEUTRAL')
            
            return {
                'score': score,
                'confidence': 0.85,  # High confidence - reliable indicator
                'available': True,
                'value': value,
                'classification': data.get('classification'),
                'signal': signal,
                'recommendation': data.get('recommendation', {})
            }
            
        except Exception as e:
            logger.debug(f"Fear & Greed sentiment error: {e}")
            return {'score': 0.5, 'confidence': 0, 'available': False}
    
    async def _get_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get sentiment from news sources"""
        try:
            from services.cryptopanic_service import get_cryptopanic_service
            service = get_cryptopanic_service()
            
            if not service or not service.initialized:
                return {'score': 0.5, 'confidence': 0, 'available': False}
            
            # Get recent news
            news = await asyncio.to_thread(
                service.get_currency_news,
                symbol.lower(),
                limit=10
            )
            
            if not news:
                return {'score': 0.5, 'confidence': 0.3, 'available': True}
            
            # Analyze sentiment from news
            positive = 0
            negative = 0
            
            for item in news:
                # Check for sentiment indicators
                title_lower = item.get('title', '').lower()
                
                # Bullish keywords
                bullish_words = ['surge', 'rally', 'gain', 'rise', 'bull', 'up', 
                               'high', 'record', 'breakout', 'positive', 'growth']
                # Bearish keywords
                bearish_words = ['drop', 'fall', 'crash', 'bear', 'down', 'low',
                               'decline', 'loss', 'negative', 'fear', 'sell']
                
                for word in bullish_words:
                    if word in title_lower:
                        positive += 1
                        break
                
                for word in bearish_words:
                    if word in title_lower:
                        negative += 1
                        break
            
            total = positive + negative
            if total > 0:
                score = (positive / total) * 0.4 + 0.3  # Normalize to 0.3-0.7 range
            else:
                score = 0.5
            
            return {
                'score': score,
                'confidence': min(total / 5, 1),  # More news = higher confidence
                'available': True,
                'news_count': len(news)
            }
            
        except Exception as e:
            logger.debug(f"News sentiment error: {e}")
            return {'score': 0.5, 'confidence': 0, 'available': False}
    
    async def _get_technical_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get sentiment from technical indicators"""
        try:
            from services.market_service import get_market_service
            market = get_market_service()
            
            if not market:
                return {'score': 0.5, 'confidence': 0, 'available': False}
            
            # Get technical indicators
            data = await asyncio.to_thread(
                market.get_detailed_coin_data,
                symbol.lower()
            )
            
            if not data:
                return {'score': 0.5, 'confidence': 0.3, 'available': True}
            
            score = 0.5
            signals = 0
            
            # RSI analysis
            rsi = data.get('rsi_14', 50)
            if rsi < 30:
                score += 0.15  # Oversold = bullish
                signals += 1
            elif rsi > 70:
                score -= 0.15  # Overbought = bearish
                signals += 1
            
            # Price change analysis
            change_24h = data.get('price_change_percentage_24h', 0)
            if change_24h > 5:
                score += 0.1
                signals += 1
            elif change_24h < -5:
                score -= 0.1
                signals += 1
            
            # Market cap trend
            change_7d = data.get('price_change_percentage_7d', 0)
            if change_7d > 10:
                score += 0.05
                signals += 1
            elif change_7d < -10:
                score -= 0.05
                signals += 1
            
            # Clamp score to valid range
            score = max(0.1, min(0.9, score))
            
            return {
                'score': score,
                'confidence': 0.7 if signals > 0 else 0.5,
                'available': True,
                'rsi': rsi
            }
            
        except Exception as e:
            logger.debug(f"Technical sentiment error: {e}")
            return {'score': 0.5, 'confidence': 0, 'available': False}
    
    async def _get_volume_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get sentiment from volume analysis"""
        try:
            from services.market_service import get_market_service
            market = get_market_service()
            
            if not market:
                return {'score': 0.5, 'confidence': 0, 'available': False}
            
            data = await asyncio.to_thread(
                market.get_detailed_coin_data,
                symbol.lower()
            )
            
            if not data:
                return {'score': 0.5, 'confidence': 0.3, 'available': True}
            
            # Volume analysis
            volume_24h = data.get('total_volume', 0)
            market_cap = data.get('market_cap', 1)
            
            if market_cap > 0:
                volume_ratio = volume_24h / market_cap
            else:
                volume_ratio = 0
            
            # High volume = more activity = slightly bullish
            if volume_ratio > 0.3:
                score = 0.65
            elif volume_ratio > 0.1:
                score = 0.55
            else:
                score = 0.5
            
            return {
                'score': score,
                'confidence': 0.6,
                'available': True,
                'volume_ratio': volume_ratio
            }
            
        except Exception as e:
            logger.debug(f"Volume sentiment error: {e}")
            return {'score': 0.5, 'confidence': 0, 'available': False}
    
    async def get_market_sentiment(self) -> Dict[str, Any]:
        """
        Get overall market sentiment including Fear & Greed Index.
        """
        # Get Fear & Greed Index first (market-wide indicator)
        fear_greed = await self._get_fear_greed_sentiment()
        
        top_coins = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA']
        
        sentiments = []
        for coin in top_coins:
            try:
                sent = await self.get_coin_sentiment(coin)
                sentiments.append(sent)
            except Exception:
                continue
        
        if not sentiments:
            # Use Fear & Greed as fallback
            if fear_greed.get('available'):
                return {
                    'overall_score': fear_greed['score'],
                    'signal': fear_greed.get('signal', 'NEUTRAL'),
                    'fear_greed_index': fear_greed.get('value'),
                    'fear_greed_classification': fear_greed.get('classification'),
                    'coins_analyzed': 0,
                    'updated_at': datetime.now().isoformat()
                }
            return {
                'overall_score': 0.5,
                'signal': 'NEUTRAL',
                'coins_analyzed': 0
            }
        
        avg_score = sum(s['score'] for s in sentiments) / len(sentiments)
        
        if avg_score >= self.BULLISH_THRESHOLD:
            signal = "BULLISH"
        elif avg_score <= self.BEARISH_THRESHOLD:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"
        
        result = {
            'overall_score': round(avg_score, 3),
            'signal': signal,
            'coins_analyzed': len(sentiments),
            'breakdown': {s['symbol']: s['signal'] for s in sentiments},
            'updated_at': datetime.now().isoformat()
        }
        
        # Add Fear & Greed Index data
        if fear_greed.get('available'):
            result['fear_greed_index'] = fear_greed.get('value')
            result['fear_greed_classification'] = fear_greed.get('classification')
            result['fear_greed_recommendation'] = fear_greed.get('recommendation', {}).get('action')
        
        return result
        }
    
    def get_trading_recommendation(
        self,
        sentiment_score: float,
        current_position: float = 0
    ) -> Dict[str, Any]:
        """
        Get trading recommendation based on sentiment.
        
        Args:
            sentiment_score: 0-1 sentiment score
            current_position: Current position size (-1 to 1)
        
        Returns:
            {
                "action": "BUY" | "SELL" | "HOLD",
                "size_adjustment": 0.1,  # Position size change
                "reason": "Strong bullish sentiment"
            }
        """
        if sentiment_score >= 0.7:
            if current_position < 0.5:
                return {
                    "action": "BUY",
                    "size_adjustment": 0.2,
                    "reason": "Strong bullish sentiment"
                }
        elif sentiment_score <= 0.3:
            if current_position > -0.5:
                return {
                    "action": "SELL",
                    "size_adjustment": -0.2,
                    "reason": "Strong bearish sentiment"
                }
        elif 0.4 <= sentiment_score <= 0.6:
            return {
                "action": "HOLD",
                "size_adjustment": 0,
                "reason": "Neutral sentiment"
            }
        
        # Mixed signals
        return {
            "action": "HOLD",
            "size_adjustment": 0,
            "reason": "Mixed sentiment signals"
        }


# Singleton instance
_sentiment_scorer = None


def get_sentiment_scorer(db=None) -> SentimentScorer:
    global _sentiment_scorer
    if _sentiment_scorer is None:
        _sentiment_scorer = SentimentScorer(db)
    return _sentiment_scorer

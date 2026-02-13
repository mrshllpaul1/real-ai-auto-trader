"""
Consolidated Sentiment Service
==============================
Combines all sentiment and social analysis:
- News sentiment
- Social media analysis
- Fear & Greed index
- Whale tracking
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

__all__ = [
    'SentimentService',
    'get_sentiment_service'
]


class SentimentService:
    """
    Unified sentiment service that consolidates:
    - ai_news_sentiment
    - social_sentiment
    - social_sentiment_pipeline
    - fear_greed_service
    - whale_tracking
    - whale_alert_service
    - cryptopanic_service
    """
    
    def __init__(self, db=None):
        self.db = db
        self._news = None
        self._social = None
        self._fear_greed = None
        self._whale = None
        logger.info("📰 Sentiment Service initialized")
    
    @property
    def news(self):
        """Lazy load news sentiment"""
        if self._news is None:
            try:
                from services.ai_news_sentiment import AINewsSentiment
                self._news = AINewsSentiment(self.db)
            except Exception as e:
                logger.warning(f"Could not load news sentiment: {e}")
        return self._news
    
    @property
    def social(self):
        """Lazy load social sentiment"""
        if self._social is None:
            try:
                from services.social_sentiment import SocialSentiment
                self._social = SocialSentiment(self.db)
            except Exception as e:
                logger.warning(f"Could not load social sentiment: {e}")
        return self._social
    
    @property
    def fear_greed(self):
        """Lazy load fear & greed"""
        if self._fear_greed is None:
            try:
                from services.fear_greed_service import FearGreedService
                self._fear_greed = FearGreedService()
            except Exception as e:
                logger.warning(f"Could not load fear & greed: {e}")
        return self._fear_greed
    
    # === News Sentiment ===
    async def get_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get news sentiment for a symbol"""
        if not self.news:
            return {"sentiment": 0.5, "articles": 0, "error": "News service not available"}
        
        try:
            return await self.news.analyze(symbol)
        except Exception as e:
            logger.error(f"News sentiment error: {e}")
            return {"sentiment": 0.5, "error": str(e)}
    
    async def get_latest_news(self, symbol: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest news articles"""
        if not self.news:
            return []
        
        try:
            return await self.news.get_latest(symbol, limit)
        except Exception as e:
            logger.error(f"Get news error: {e}")
            return []
    
    # === Social Sentiment ===
    async def get_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get social media sentiment"""
        if not self.social:
            return {"sentiment": 0.5, "volume": 0, "error": "Social service not available"}
        
        try:
            return await self.social.analyze(symbol)
        except Exception as e:
            logger.error(f"Social sentiment error: {e}")
            return {"sentiment": 0.5, "error": str(e)}
    
    # === Fear & Greed ===
    async def get_fear_greed(self) -> Dict[str, Any]:
        """Get current Fear & Greed index"""
        if not self.fear_greed:
            return {"value": 50, "classification": "neutral", "error": "Service not available"}
        
        try:
            return await self.fear_greed.get_index()
        except Exception as e:
            logger.error(f"Fear & Greed error: {e}")
            return {"value": 50, "classification": "neutral", "error": str(e)}
    
    # === Whale Tracking ===
    async def get_whale_activity(self, symbol: str = None) -> Dict[str, Any]:
        """Get whale transaction activity"""
        if self._whale is None:
            try:
                from services.whale_tracking import WhaleTracking
                self._whale = WhaleTracking(self.db)
            except Exception as e:
                logger.warning(f"Could not load whale tracking: {e}")
                return {"activity": [], "error": "Whale tracking not available"}
        
        try:
            return await self._whale.get_activity(symbol)
        except Exception as e:
            return {"activity": [], "error": str(e)}
    
    # === Combined Sentiment ===
    async def get_combined_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get combined sentiment from all sources"""
        news = await self.get_news_sentiment(symbol)
        social = await self.get_social_sentiment(symbol)
        fear_greed = await self.get_fear_greed()
        
        # Calculate weighted average
        news_score = news.get("sentiment", 0.5)
        social_score = social.get("sentiment", 0.5)
        fg_score = fear_greed.get("value", 50) / 100
        
        # Weights: news 40%, social 30%, fear&greed 30%
        combined = (news_score * 0.4) + (social_score * 0.3) + (fg_score * 0.3)
        
        return {
            "symbol": symbol,
            "combined_score": round(combined, 3),
            "classification": self._classify_sentiment(combined),
            "components": {
                "news": {
                    "score": news_score,
                    "weight": 0.4,
                    "articles": news.get("articles", 0)
                },
                "social": {
                    "score": social_score,
                    "weight": 0.3,
                    "volume": social.get("volume", 0)
                },
                "fear_greed": {
                    "score": fg_score,
                    "weight": 0.3,
                    "value": fear_greed.get("value", 50),
                    "classification": fear_greed.get("classification", "neutral")
                }
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _classify_sentiment(self, score: float) -> str:
        """Classify sentiment score"""
        if score >= 0.7:
            return "very_bullish"
        elif score >= 0.55:
            return "bullish"
        elif score >= 0.45:
            return "neutral"
        elif score >= 0.3:
            return "bearish"
        else:
            return "very_bearish"
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service": "sentiment",
            "news": self._news is not None,
            "social": self._social is not None,
            "fear_greed": self._fear_greed is not None,
            "whale": self._whale is not None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Singleton
_sentiment_service = None

def get_sentiment_service(db=None) -> SentimentService:
    """Get or create sentiment service singleton"""
    global _sentiment_service
    if _sentiment_service is None:
        _sentiment_service = SentimentService(db)
    return _sentiment_service

"""
Fear & Greed Index Service
===========================
Free API for crypto market sentiment from alternative.me
No authentication required.
"""

import logging
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class FearGreedService:
    """
    Fetches the Crypto Fear & Greed Index from alternative.me
    
    Index Values:
    - 0-24: Extreme Fear (good time to buy)
    - 25-49: Fear
    - 50: Neutral
    - 51-74: Greed
    - 75-100: Extreme Greed (good time to sell)
    """
    
    BASE_URL = "https://api.alternative.me/fng/"
    
    def __init__(self):
        self._cache = None
        self._cache_time = None
        self._cache_ttl = timedelta(minutes=10)
        logger.info("📊 Fear & Greed Index service initialized")
    
    async def get_current_index(self) -> Dict[str, Any]:
        """Get the current Fear & Greed Index value"""
        data = await self._fetch_data(limit=1)
        if not data:
            return self._default_response()
        
        current = data[0]
        return {
            "value": int(current.get("value", 50)),
            "classification": current.get("value_classification", "Neutral"),
            "timestamp": self._parse_timestamp(current.get("timestamp")),
            "signal": self._get_signal(int(current.get("value", 50))),
            "recommendation": self._get_recommendation(int(current.get("value", 50)))
        }
    
    async def get_historical(self, days: int = 7) -> Dict[str, Any]:
        """Get historical Fear & Greed data"""
        data = await self._fetch_data(limit=days)
        if not data:
            return {"history": [], "trend": "neutral"}
        
        history = []
        for item in data:
            history.append({
                "value": int(item.get("value", 50)),
                "classification": item.get("value_classification", "Neutral"),
                "date": self._parse_timestamp(item.get("timestamp"))
            })
        
        # Calculate trend
        if len(history) >= 2:
            recent_avg = sum(h["value"] for h in history[:3]) / min(3, len(history))
            older_avg = sum(h["value"] for h in history[-3:]) / min(3, len(history))
            
            if recent_avg > older_avg + 5:
                trend = "improving"  # Moving towards greed
            elif recent_avg < older_avg - 5:
                trend = "declining"  # Moving towards fear
            else:
                trend = "stable"
        else:
            trend = "neutral"
        
        return {
            "history": history,
            "trend": trend,
            "current": history[0] if history else None
        }
    
    async def _fetch_data(self, limit: int = 1) -> Optional[List[Dict]]:
        """Fetch data from the API with caching"""
        # Check cache
        if (self._cache and self._cache_time and 
            datetime.now() - self._cache_time < self._cache_ttl and
            len(self._cache) >= limit):
            return self._cache[:limit]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}?limit={max(limit, 10)}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        data = result.get("data", [])
                        
                        # Update cache
                        self._cache = data
                        self._cache_time = datetime.now()
                        
                        return data[:limit]
                    else:
                        logger.warning(f"Fear & Greed API returned {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Fear & Greed API error: {e}")
            return None
    
    def _parse_timestamp(self, ts: str) -> str:
        """Parse Unix timestamp to ISO format"""
        try:
            return datetime.fromtimestamp(int(ts)).isoformat()
        except:
            return datetime.now().isoformat()
    
    def _get_signal(self, value: int) -> str:
        """Convert index value to trading signal"""
        if value <= 24:
            return "EXTREME_FEAR"
        elif value <= 44:
            return "FEAR"
        elif value <= 55:
            return "NEUTRAL"
        elif value <= 74:
            return "GREED"
        else:
            return "EXTREME_GREED"
    
    def _get_recommendation(self, value: int) -> Dict[str, Any]:
        """Get trading recommendation based on index"""
        if value <= 20:
            return {
                "action": "STRONG_BUY",
                "reason": "Extreme fear - historically good buying opportunity",
                "confidence": 0.8
            }
        elif value <= 35:
            return {
                "action": "BUY",
                "reason": "Fear in market - potential accumulation zone",
                "confidence": 0.7
            }
        elif value <= 55:
            return {
                "action": "HOLD",
                "reason": "Neutral sentiment - no clear direction",
                "confidence": 0.5
            }
        elif value <= 75:
            return {
                "action": "REDUCE",
                "reason": "Greed in market - consider taking profits",
                "confidence": 0.7
            }
        else:
            return {
                "action": "SELL",
                "reason": "Extreme greed - historically good selling opportunity",
                "confidence": 0.8
            }
    
    def _default_response(self) -> Dict[str, Any]:
        """Return default response when API fails"""
        return {
            "value": 50,
            "classification": "Neutral",
            "timestamp": datetime.now().isoformat(),
            "signal": "NEUTRAL",
            "recommendation": {
                "action": "HOLD",
                "reason": "Unable to fetch sentiment data",
                "confidence": 0.3
            }
        }


# Singleton instance
_fear_greed_service = None


def get_fear_greed_service() -> FearGreedService:
    global _fear_greed_service
    if _fear_greed_service is None:
        _fear_greed_service = FearGreedService()
    return _fear_greed_service

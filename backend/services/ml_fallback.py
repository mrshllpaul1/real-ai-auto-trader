"""
ML Fallback Service
===================
Provides simple predictions when heavy ML libraries aren't installed.
The app keeps working - just with simpler analysis.
"""

import logging
import random
from datetime import datetime, timezone
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SimplePredictionService:
    """
    Fallback prediction service using simple technical analysis
    when TensorFlow/PyTorch aren't available.
    """
    
    def __init__(self):
        logger.info("📊 Using simple prediction service (ML libraries not installed)")
    
    def predict_direction(self, prices: List[float], symbol: str = "BTC") -> Dict[str, Any]:
        """
        Simple trend-based prediction.
        Uses moving averages and momentum.
        """
        if len(prices) < 20:
            return {
                "signal": "HOLD",
                "confidence": 0.5,
                "reason": "Insufficient data"
            }
        
        # Simple moving averages
        sma_short = sum(prices[-7:]) / 7
        sma_long = sum(prices[-20:]) / 20
        
        # Current vs averages
        current = prices[-1]
        
        # Momentum (rate of change)
        momentum = (prices[-1] - prices[-5]) / prices[-5] if prices[-5] != 0 else 0
        
        # Generate signal
        if sma_short > sma_long and momentum > 0.01:
            signal = "BUY"
            confidence = min(0.5 + abs(momentum) * 5, 0.85)
        elif sma_short < sma_long and momentum < -0.01:
            signal = "SELL"
            confidence = min(0.5 + abs(momentum) * 5, 0.85)
        else:
            signal = "HOLD"
            confidence = 0.5
        
        return {
            "signal": signal,
            "confidence": round(confidence, 2),
            "sma_short": round(sma_short, 2),
            "sma_long": round(sma_long, 2),
            "momentum": round(momentum * 100, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": "simple_technical"
        }
    
    def get_market_regime(self, prices: List[float]) -> Dict[str, Any]:
        """
        Simple market regime detection.
        """
        if len(prices) < 30:
            return {"regime": "unknown", "confidence": 0.3}
        
        # Calculate volatility
        returns = [(prices[i] - prices[i-1]) / prices[i-1] 
                   for i in range(1, len(prices)) if prices[i-1] != 0]
        
        if not returns:
            return {"regime": "unknown", "confidence": 0.3}
        
        volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5
        
        # Trend
        trend = (prices[-1] - prices[0]) / prices[0] if prices[0] != 0 else 0
        
        # Determine regime
        if volatility > 0.03:
            regime = "high_volatility"
        elif trend > 0.05:
            regime = "bull"
        elif trend < -0.05:
            regime = "bear"
        else:
            regime = "sideways"
        
        return {
            "regime": regime,
            "confidence": 0.6,
            "volatility": round(volatility * 100, 2),
            "trend": round(trend * 100, 2),
            "method": "simple_analysis"
        }


# Singleton
_fallback_service = None

def get_fallback_predictor() -> SimplePredictionService:
    global _fallback_service
    if _fallback_service is None:
        _fallback_service = SimplePredictionService()
    return _fallback_service


def check_ml_available() -> Dict[str, bool]:
    """Check which ML libraries are available"""
    results = {}
    
    try:
        import tensorflow
        results["tensorflow"] = True
    except ImportError:
        results["tensorflow"] = False
    
    try:
        import torch
        results["torch"] = True
    except ImportError:
        results["torch"] = False
    
    try:
        import sklearn
        results["sklearn"] = True
    except ImportError:
        results["sklearn"] = False
    
    try:
        import xgboost
        results["xgboost"] = True
    except ImportError:
        results["xgboost"] = False
    
    try:
        import lightgbm
        results["lightgbm"] = True
    except ImportError:
        results["lightgbm"] = False
    
    return results

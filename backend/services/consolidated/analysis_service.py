"""
Consolidated Analysis Service
=============================
Combines all technical and market analysis:
- Technical indicators (RSI, MACD, Bollinger, etc.)
- Pattern recognition
- Multi-timeframe analysis
- Cross-asset correlation
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

__all__ = [
    'AnalysisService',
    'get_analysis_service'
]


class AnalysisService:
    """
    Unified analysis service that consolidates:
    - advanced_technical_analysis
    - cross_asset_correlation
    - regime_predictor
    - causal_feature_selection
    - multitimeframe analysis
    """
    
    def __init__(self, db=None):
        self.db = db
        self._technical = None
        self._correlation = None
        self._regime = None
        logger.info("📈 Analysis Service initialized")
    
    @property
    def technical(self):
        """Lazy load technical analysis"""
        if self._technical is None:
            try:
                from services.advanced_technical_analysis import AdvancedTechnicalAnalysis
                self._technical = AdvancedTechnicalAnalysis()
            except Exception as e:
                logger.warning(f"Could not load technical analysis: {e}")
        return self._technical
    
    @property
    def correlation(self):
        """Lazy load correlation analysis"""
        if self._correlation is None:
            try:
                from services.cross_asset_correlation import CrossAssetCorrelation
                self._correlation = CrossAssetCorrelation(self.db)
            except Exception as e:
                logger.warning(f"Could not load correlation analysis: {e}")
        return self._correlation
    
    # === Technical Analysis ===
    async def get_technical_indicators(self, symbol: str, ohlcv: List[Dict]) -> Dict[str, Any]:
        """Get all technical indicators for a symbol"""
        if not self.technical:
            return {"error": "Technical analysis not available"}
        
        try:
            return await self.technical.analyze(symbol, ohlcv)
        except Exception as e:
            logger.error(f"Technical analysis error: {e}")
            return {"error": str(e)}
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def calculate_macd(self, prices: List[float]) -> Dict[str, float]:
        """Calculate MACD"""
        if len(prices) < 26:
            return {"macd": 0, "signal": 0, "histogram": 0}
        
        def ema(data, period):
            multiplier = 2 / (period + 1)
            result = [data[0]]
            for i in range(1, len(data)):
                result.append((data[i] * multiplier) + (result[-1] * (1 - multiplier)))
            return result
        
        ema12 = ema(prices, 12)
        ema26 = ema(prices, 26)
        macd_line = [ema12[i] - ema26[i] for i in range(len(prices))]
        signal_line = ema(macd_line, 9)
        
        return {
            "macd": macd_line[-1],
            "signal": signal_line[-1],
            "histogram": macd_line[-1] - signal_line[-1]
        }
    
    def calculate_bollinger(self, prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            price = prices[-1] if prices else 0
            return {"upper": price * 1.02, "middle": price, "lower": price * 0.98}
        
        recent = prices[-period:]
        middle = sum(recent) / period
        variance = sum((p - middle) ** 2 for p in recent) / period
        std = variance ** 0.5
        
        return {
            "upper": middle + (std_dev * std),
            "middle": middle,
            "lower": middle - (std_dev * std)
        }
    
    # === Correlation Analysis ===
    async def get_correlations(self, symbols: List[str]) -> Dict[str, Any]:
        """Get correlation matrix for symbols"""
        if not self.correlation:
            return {"error": "Correlation analysis not available"}
        
        try:
            return await self.correlation.calculate(symbols)
        except Exception as e:
            logger.error(f"Correlation error: {e}")
            return {"error": str(e)}
    
    # === Market Regime ===
    async def detect_regime(self, symbol: str) -> Dict[str, Any]:
        """Detect current market regime"""
        if self._regime is None:
            try:
                from services.regime_predictor import RegimePredictor
                self._regime = RegimePredictor(self.db)
            except Exception as e:
                logger.warning(f"Could not load regime predictor: {e}")
                return {"regime": "unknown", "confidence": 0}
        
        try:
            return await self._regime.predict(symbol)
        except Exception as e:
            return {"regime": "unknown", "error": str(e)}
    
    # === Quick Analysis ===
    async def quick_analysis(self, symbol: str, prices: List[float]) -> Dict[str, Any]:
        """Get quick technical analysis summary"""
        rsi = self.calculate_rsi(prices)
        macd = self.calculate_macd(prices)
        bb = self.calculate_bollinger(prices)
        
        # Determine trend
        price = prices[-1] if prices else 0
        sma20 = sum(prices[-20:]) / min(20, len(prices)) if prices else 0
        sma50 = sum(prices[-50:]) / min(50, len(prices)) if prices else 0
        
        trend = "bullish" if price > sma20 > sma50 else (
            "bearish" if price < sma20 < sma50 else "neutral"
        )
        
        # Generate signal
        signals = []
        if rsi < 30:
            signals.append("oversold")
        elif rsi > 70:
            signals.append("overbought")
        
        if macd["histogram"] > 0:
            signals.append("macd_bullish")
        else:
            signals.append("macd_bearish")
        
        if price < bb["lower"]:
            signals.append("below_lower_bb")
        elif price > bb["upper"]:
            signals.append("above_upper_bb")
        
        return {
            "symbol": symbol,
            "price": price,
            "rsi": round(rsi, 2),
            "macd": {k: round(v, 4) for k, v in macd.items()},
            "bollinger": {k: round(v, 2) for k, v in bb.items()},
            "trend": trend,
            "signals": signals,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service": "analysis",
            "technical": self._technical is not None,
            "correlation": self._correlation is not None,
            "regime": self._regime is not None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Singleton
_analysis_service = None

def get_analysis_service(db=None) -> AnalysisService:
    """Get or create analysis service singleton"""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService(db)
    return _analysis_service

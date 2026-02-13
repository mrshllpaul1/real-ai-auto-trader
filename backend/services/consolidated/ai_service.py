"""
Consolidated AI Service
=======================
Combines all AI/ML prediction and analysis functionality:
- Signal aggregation
- ML predictions
- Ensemble models
- Learning loops
- Model training
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

__all__ = [
    'AIService',
    'get_ai_service'
]


class AIService:
    """
    Unified AI service that consolidates:
    - ai_signal_aggregator
    - ensemble_ai
    - enhanced_ai_engine
    - ai_learning_loop
    - self_improving_ai
    - ai_portfolio_manager
    - confidence_explainer
    """
    
    def __init__(self, db=None):
        self.db = db
        self._signal_aggregator = None
        self._ensemble = None
        self._learning_loop = None
        self._portfolio_manager = None
        self._confidence_explainer = None
        logger.info("🧠 AI Service initialized")
    
    @property
    def signal_aggregator(self):
        """Lazy load signal aggregator"""
        if self._signal_aggregator is None:
            try:
                from services.ai_signal_aggregator import AISignalAggregator
                self._signal_aggregator = AISignalAggregator(self.db)
            except Exception as e:
                logger.warning(f"Could not load signal aggregator: {e}")
        return self._signal_aggregator
    
    @property
    def ensemble(self):
        """Lazy load ensemble AI"""
        if self._ensemble is None:
            try:
                from services.ensemble_ai import EnsembleAI
                self._ensemble = EnsembleAI(self.db)
            except Exception as e:
                logger.warning(f"Could not load ensemble AI: {e}")
        return self._ensemble
    
    @property
    def confidence_explainer(self):
        """Lazy load confidence explainer"""
        if self._confidence_explainer is None:
            try:
                from services.confidence_explainer import get_confidence_explainer
                self._confidence_explainer = get_confidence_explainer(self.db)
            except Exception as e:
                logger.warning(f"Could not load confidence explainer: {e}")
        return self._confidence_explainer
    
    # === Prediction Methods ===
    async def get_prediction(self, symbol: str) -> Dict[str, Any]:
        """Get AI prediction for a symbol"""
        if self.signal_aggregator:
            try:
                return await self.signal_aggregator.get_aggregated_signal(symbol)
            except Exception as e:
                logger.error(f"Prediction error for {symbol}: {e}")
        
        return {
            "symbol": symbol,
            "signal": "hold",
            "confidence": 0.5,
            "error": "Signal aggregator not available"
        }
    
    async def get_batch_predictions(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Get predictions for multiple symbols"""
        results = []
        for symbol in symbols:
            prediction = await self.get_prediction(symbol)
            results.append(prediction)
        return results
    
    async def explain_prediction(self, symbol: str) -> Dict[str, Any]:
        """Get explanation for prediction confidence"""
        if self.confidence_explainer:
            prediction = await self.get_prediction(symbol)
            return self.confidence_explainer.explain_confidence(
                symbol=symbol,
                confidence=prediction.get("confidence", 0.5),
                signal=prediction.get("signal", "hold"),
                features=prediction.get("features", {})
            )
        return {"error": "Confidence explainer not available"}
    
    # === Ensemble Methods ===
    async def get_ensemble_prediction(self, symbol: str) -> Dict[str, Any]:
        """Get ensemble model prediction"""
        if self.ensemble:
            try:
                return await self.ensemble.predict(symbol)
            except Exception as e:
                logger.error(f"Ensemble prediction error: {e}")
        return {"error": "Ensemble not available"}
    
    # === Portfolio AI ===
    async def get_portfolio_recommendation(self, budget: float) -> Dict[str, Any]:
        """Get AI portfolio allocation recommendation"""
        if self._portfolio_manager is None:
            try:
                from services.ai_portfolio_manager import AIPortfolioManager
                self._portfolio_manager = AIPortfolioManager(self.db)
            except Exception as e:
                logger.warning(f"Could not load portfolio manager: {e}")
                return {"error": "Portfolio manager not available"}
        
        return await self._portfolio_manager.get_recommendation(budget)
    
    # === Status ===
    def get_status(self) -> Dict[str, Any]:
        """Get AI service status"""
        return {
            "service": "ai",
            "signal_aggregator": self._signal_aggregator is not None,
            "ensemble": self._ensemble is not None,
            "confidence_explainer": self._confidence_explainer is not None,
            "portfolio_manager": self._portfolio_manager is not None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Singleton
_ai_service = None

def get_ai_service(db=None) -> AIService:
    """Get or create AI service singleton"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService(db)
    return _ai_service

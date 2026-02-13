"""
ML Confidence Explanation API Routes
====================================
Provides endpoints for AI model confidence explanations.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/confidence-explain", tags=["AI Confidence Explanation"])

# Global references
_db = None
_explainer = None
_prediction_services = None


def set_dependencies(database, explainer=None, prediction_services=None):
    """Set dependencies from main app"""
    global _db, _explainer, _prediction_services
    _db = database
    _explainer = explainer
    _prediction_services = prediction_services


@router.get("/")
async def get_explanation_status():
    """Get status of the confidence explanation service"""
    return {
        "status": "active" if _explainer else "not_initialized",
        "features": [
            "feature_attribution",
            "natural_language_explanation",
            "key_drivers",
            "risk_assessment",
            "actionable_insights"
        ],
        "supported_categories": [
            "technical",
            "sentiment", 
            "on_chain",
            "market_structure"
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/{symbol}")
async def explain_symbol_confidence(
    symbol: str,
    include_features: bool = Query(True, description="Include raw feature values"),
    include_risks: bool = Query(True, description="Include risk assessment")
):
    """
    Get AI confidence explanation for a specific symbol.
    
    This endpoint provides:
    - Natural language explanation of the AI's prediction
    - Key factors driving the confidence level
    - Feature-by-feature contribution breakdown
    - Risk factors and actionable insights
    """
    if _explainer is None:
        raise HTTPException(status_code=503, detail="Explanation service not initialized")
    
    symbol = symbol.upper()
    
    # Get current AI prediction for the symbol
    prediction = await _get_prediction_for_symbol(symbol)
    
    if not prediction:
        raise HTTPException(
            status_code=404, 
            detail=f"No AI prediction available for {symbol}"
        )
    
    # Extract relevant data
    confidence = prediction.get("confidence", 0.5)
    signal = prediction.get("signal", "hold")
    features = prediction.get("features", {})
    
    # Generate explanation
    explanation = _explainer.explain_confidence(
        symbol=symbol,
        confidence=confidence,
        signal=signal,
        features=features
    )
    
    # Optionally filter response
    if not include_features:
        explanation.pop("contributions", None)
    
    if not include_risks:
        explanation.pop("risk_factors", None)
    
    return explanation


@router.post("/custom")
async def explain_custom_prediction(
    symbol: str,
    confidence: float = Query(..., ge=0, le=1, description="Confidence score (0-1)"),
    signal: str = Query(..., description="Prediction signal (buy/sell/hold)"),
    features: Optional[Dict[str, Any]] = None
):
    """
    Generate explanation for a custom prediction with provided features.
    
    Useful for:
    - Explaining hypothetical scenarios
    - Testing different feature combinations
    - Understanding model behavior
    """
    if _explainer is None:
        raise HTTPException(status_code=503, detail="Explanation service not initialized")
    
    # Use provided features or defaults
    if features is None:
        features = _get_default_features()
    
    explanation = _explainer.explain_confidence(
        symbol=symbol.upper(),
        confidence=confidence,
        signal=signal.lower(),
        features=features
    )
    
    return explanation


@router.get("/batch")
async def explain_multiple_symbols(
    symbols: str = Query(..., description="Comma-separated list of symbols"),
    top_n: int = Query(3, ge=1, le=10, description="Number of key drivers per symbol")
):
    """
    Get brief explanations for multiple symbols at once.
    Returns summary-level data optimized for dashboard display.
    """
    if _explainer is None:
        raise HTTPException(status_code=503, detail="Explanation service not initialized")
    
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    results = []
    
    for symbol in symbol_list[:10]:  # Limit to 10 symbols
        try:
            prediction = await _get_prediction_for_symbol(symbol)
            
            if prediction:
                explanation = _explainer.explain_confidence(
                    symbol=symbol,
                    confidence=prediction.get("confidence", 0.5),
                    signal=prediction.get("signal", "hold"),
                    features=prediction.get("features", {})
                )
                
                results.append({
                    "symbol": symbol,
                    "confidence": explanation["confidence"],
                    "signal": explanation["signal"],
                    "summary": explanation["summary"],
                    "key_drivers": explanation["key_drivers"][:top_n],
                    "confidence_level": explanation["confidence_level"],
                    "agreement_score": explanation["agreement_score"]
                })
            else:
                results.append({
                    "symbol": symbol,
                    "error": "No prediction available"
                })
        except Exception as e:
            logger.error(f"Error explaining {symbol}: {e}")
            results.append({
                "symbol": symbol,
                "error": str(e)
            })
    
    return {
        "explanations": results,
        "count": len(results),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/feature-importance")
async def get_feature_importance():
    """
    Get the feature importance weights used by the explanation model.
    Useful for understanding which factors matter most in predictions.
    """
    if _explainer is None:
        raise HTTPException(status_code=503, detail="Explanation service not initialized")
    
    weights = _explainer.FEATURE_WEIGHTS
    
    # Flatten and sort by importance
    all_features = []
    for category, features in weights.items():
        for feature, importance in features.items():
            all_features.append({
                "category": category,
                "feature": feature,
                "importance": importance,
                "importance_pct": f"{importance * 100:.1f}%"
            })
    
    all_features.sort(key=lambda x: x["importance"], reverse=True)
    
    return {
        "by_category": weights,
        "ranked": all_features,
        "total_features": len(all_features),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/thresholds")
async def get_interpretation_thresholds():
    """
    Get the thresholds used for interpreting feature values.
    Helps understand what values are considered significant.
    """
    if _explainer is None:
        raise HTTPException(status_code=503, detail="Explanation service not initialized")
    
    return {
        "thresholds": _explainer.THRESHOLDS,
        "interpretation_guide": {
            "rsi": {
                "description": "Relative Strength Index",
                "oversold": "Below threshold indicates oversold (bullish signal)",
                "overbought": "Above threshold indicates overbought (bearish signal)"
            },
            "fear_greed": {
                "description": "Market Fear & Greed Index",
                "extreme_fear": "Below threshold indicates extreme fear (contrarian bullish)",
                "extreme_greed": "Above threshold indicates extreme greed (contrarian bearish)"
            },
            "volume_change": {
                "description": "Volume relative to average",
                "significant": "Above threshold indicates above-average activity",
                "extreme": "Above threshold indicates major volume surge"
            },
            "volatility": {
                "description": "Price volatility measure",
                "low": "Below threshold indicates calm market",
                "high": "Above threshold indicates high volatility"
            }
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


async def _get_prediction_for_symbol(symbol: str) -> Optional[Dict[str, Any]]:
    """Get current AI prediction for a symbol"""
    # Try to get from prediction services
    if _prediction_services:
        try:
            # Try automated trader signals
            if hasattr(_prediction_services, 'get_prediction_signals'):
                signals = await _prediction_services.get_prediction_signals(symbol)
                if signals:
                    composite = signals.get('composite', {})
                    return {
                        "confidence": composite.get('confidence', 0.5),
                        "signal": composite.get('signal', 'hold'),
                        "features": _extract_features_from_signals(signals)
                    }
        except Exception as e:
            logger.warning(f"Could not get prediction for {symbol}: {e}")
    
    # Try database for cached predictions
    if _db:
        try:
            cached = await _db.ai_predictions.find_one(
                {"symbol": symbol},
                sort=[("timestamp", -1)]
            )
            if cached:
                return {
                    "confidence": cached.get("confidence", 0.5),
                    "signal": cached.get("signal", "hold"),
                    "features": cached.get("features", _get_default_features())
                }
        except Exception as e:
            logger.warning(f"Could not fetch cached prediction: {e}")
    
    # Return sample prediction with default features for demo
    return {
        "confidence": 0.65,
        "signal": "hold",
        "features": _get_default_features()
    }


def _extract_features_from_signals(signals: Dict[str, Any]) -> Dict[str, Any]:
    """Extract feature values from AI signals"""
    features = {}
    
    components = signals.get('components', {})
    
    # Technical
    tech = components.get('advanced_ta', {})
    features['rsi'] = tech.get('rsi', 50)
    features['macd'] = tech.get('macd', {})
    features['bollinger'] = tech.get('bollinger', {})
    features['momentum'] = tech.get('momentum', 0)
    features['volume_change'] = tech.get('volume_change', 1.0)
    
    # Sentiment
    sentiment = components.get('social', {})
    features['news_sentiment'] = sentiment.get('score', 50) / 100
    features['social_volume_change'] = sentiment.get('volume_change', 1.0)
    features['fear_greed'] = signals.get('fear_greed', 50)
    
    # On-chain
    onchain = components.get('on_chain', {})
    features['exchange_flow'] = onchain.get('exchange_flow', 0)
    features['active_addresses_change'] = onchain.get('active_addresses_change', 0)
    
    # Market structure
    orderbook = components.get('order_book', {})
    features['order_book_imbalance'] = orderbook.get('imbalance', 0)
    features['spread'] = orderbook.get('spread', 0.001)
    
    # Derived
    features['volatility'] = tech.get('volatility', 0.03)
    features['price'] = signals.get('price', 0)
    
    return features


def _get_default_features() -> Dict[str, Any]:
    """Return default feature values for demo/testing"""
    return {
        "rsi": 50,
        "macd": {"macd": 0, "signal": 0, "histogram": 0},
        "bollinger": {"upper": 100, "middle": 95, "lower": 90},
        "momentum": 0.02,
        "volume_change": 1.2,
        "news_sentiment": 0.55,
        "fear_greed": 45,
        "social_volume_change": 1.1,
        "exchange_flow": -0.01,
        "active_addresses_change": 0.05,
        "order_book_imbalance": 0.1,
        "spread": 0.002,
        "volatility": 0.03,
        "price": 50000
    }

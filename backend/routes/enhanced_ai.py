"""
Enhanced AI API Routes
Exposes all AI enhancement features.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/enhanced-ai", tags=["Enhanced AI"])

_db = None
_enhanced_ai = None
_regime_predictor = None


def set_dependencies(database, enhanced_ai, regime_predictor=None):
    global _db, _enhanced_ai, _regime_predictor
    _db = database
    _enhanced_ai = enhanced_ai
    _regime_predictor = regime_predictor


@router.get("/signal/{symbol}")
async def get_enhanced_signal(symbol: str):
    """
    Get enhanced AI trading signal for a symbol.
    
    Combines:
    - Ensemble model voting
    - Multi-timeframe analysis
    - Sentiment integration
    - Whale tracking
    - Dynamic position sizing
    """
    if not _enhanced_ai:
        raise HTTPException(status_code=503, detail="Enhanced AI not initialized")
    
    # Get model predictions if regime predictor available
    model_predictions = None
    if _regime_predictor and _regime_predictor.is_trained:
        try:
            pred = await _regime_predictor.predict_regime(symbol)
            if pred and 'all_predictions' in pred:
                model_predictions = pred['all_predictions']
        except:
            pass
    
    result = await _enhanced_ai.get_enhanced_signal(symbol, model_predictions)
    return result


@router.get("/multi-timeframe/{symbol}")
async def get_multi_timeframe_analysis(symbol: str):
    """
    Get multi-timeframe technical analysis.
    
    Analyzes 1H, 4H, 1D, 1W timeframes for signal confirmation.
    """
    if not _enhanced_ai:
        raise HTTPException(status_code=503, detail="Enhanced AI not initialized")
    
    result = await _enhanced_ai.mtf_analyzer.analyze(symbol)
    return result


@router.get("/sentiment")
async def get_market_sentiment():
    """
    Get aggregated market sentiment.
    
    Combines Fear & Greed, news, and social sentiment.
    """
    if not _enhanced_ai:
        raise HTTPException(status_code=503, detail="Enhanced AI not initialized")
    
    result = await _enhanced_ai.sentiment.get_market_sentiment()
    return result


@router.get("/whale-activity")
async def get_whale_activity(symbol: Optional[str] = None):
    """
    Get whale activity and large wallet movements.
    """
    if not _enhanced_ai:
        raise HTTPException(status_code=503, detail="Enhanced AI not initialized")
    
    result = await _enhanced_ai.whale_tracker.get_whale_activity(symbol)
    return result


@router.post("/position-size")
async def calculate_position_size(
    confidence: float = Query(70, ge=0, le=100),
    consensus: float = Query(80, ge=0, le=100),
    volatility: float = Query(3.0, ge=0, le=20),
    current_exposure: float = Query(0, ge=0, le=100)
):
    """
    Calculate dynamic position size based on multiple factors.
    """
    if not _enhanced_ai:
        raise HTTPException(status_code=503, detail="Enhanced AI not initialized")
    
    result = _enhanced_ai.risk_manager.calculate_position_size(
        confidence=confidence,
        consensus=consensus,
        volatility=volatility,
        current_exposure=current_exposure
    )
    return result


@router.get("/features/{symbol}")
async def get_technical_features(symbol: str):
    """
    Get all 25+ calculated technical features for a symbol.
    """
    if not _enhanced_ai or not _db:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    # Get OHLCV data
    ohlcv = await _db.historical_ohlcv.find(
        {'symbol': symbol},
        {'_id': 0}
    ).sort('timestamp', -1).limit(100).to_list(100)
    
    if not ohlcv:
        raise HTTPException(status_code=404, detail=f"No data for {symbol}")
    
    ohlcv.reverse()
    features = await _enhanced_ai.calculate_features(ohlcv)
    
    return {
        'symbol': symbol,
        'features': features,
        'feature_count': len(features),
        'timestamp': datetime.utcnow().isoformat()
    }


@router.get("/ensemble/status")
async def get_ensemble_status():
    """Get current ensemble voting system status"""
    if not _enhanced_ai:
        raise HTTPException(status_code=503, detail="Enhanced AI not initialized")
    
    return {
        'model_weights': _enhanced_ai.ensemble.model_weights,
        'last_predictions': _enhanced_ai.ensemble.predictions,
        'models_count': len(_enhanced_ai.ensemble.model_weights)
    }


@router.get("/retrain-status")
async def get_retrain_status():
    """Check if models need retraining"""
    if not _enhanced_ai:
        raise HTTPException(status_code=503, detail="Enhanced AI not initialized")
    
    should_retrain = await _enhanced_ai.should_retrain()
    
    return {
        'should_retrain': should_retrain,
        'last_retrain': _enhanced_ai.last_retrain.isoformat() if _enhanced_ai.last_retrain else None,
        'retrain_interval_hours': 24
    }


@router.get("/scan-top-coins")
async def scan_top_coins(limit: int = Query(10, ge=1, le=50)):
    """
    Scan top coins with enhanced AI analysis.
    """
    if not _enhanced_ai:
        raise HTTPException(status_code=503, detail="Enhanced AI not initialized")
    
    coins = ['BTC', 'ETH', 'SOL', 'DOT', 'ADA', 'XRP', 'AVAX', 'LINK', 'MATIC', 'ATOM',
             'UNI', 'AAVE', 'INJ', 'SUI', 'APT', 'ARB', 'OP', 'NEAR', 'FTM', 'DOGE'][:limit]
    
    results = []
    for coin in coins:
        try:
            signal = await _enhanced_ai.get_enhanced_signal(coin)
            results.append({
                'symbol': coin,
                'action': signal.get('recommendation', {}).get('action', 'unknown'),
                'confidence': signal.get('recommendation', {}).get('confidence', 0),
                'score': signal.get('recommendation', {}).get('total_score', 0),
                'position_size': signal.get('position_sizing', {}).get('position_pct', 0),
                'mtf_alignment': signal.get('multi_timeframe', {}).get('alignment', 'unknown')
            })
        except Exception as e:
            results.append({'symbol': coin, 'error': str(e)})
    
    # Sort by score
    results.sort(key=lambda x: x.get('score', -99), reverse=True)
    
    return {
        'coins_scanned': len(results),
        'results': results,
        'timestamp': datetime.utcnow().isoformat()
    }

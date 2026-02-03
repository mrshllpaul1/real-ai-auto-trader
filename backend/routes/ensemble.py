"""
Ensemble AI & Universe Optimizer API Routes
Combines all ML/DL models for optimal predictions.
Analyzes top 1000 coins and rebuilds optimal trading universe.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import asyncio

router = APIRouter(prefix="/ensemble", tags=["Ensemble AI"])

# Dependencies
_db = None
_market_service = None
_ensemble = None
_optimizer = None
_deep_learning_ai = None

def set_dependencies(db, market_service, ensemble, optimizer, deep_learning_ai=None):
    global _db, _market_service, _ensemble, _optimizer, _deep_learning_ai
    _db = db
    _market_service = market_service
    _ensemble = ensemble
    _optimizer = optimizer
    _deep_learning_ai = deep_learning_ai


class PredictionRequest(BaseModel):
    coin_id: str
    optimize_weights: Optional[bool] = True


class BatchPredictionRequest(BaseModel):
    coin_ids: List[str]
    optimize_weights: Optional[bool] = True


class UniverseBuildRequest(BaseModel):
    target_size: Optional[int] = 50
    analyze_count: Optional[int] = 500


# Background task tracking
_build_status = {
    "running": False,
    "started_at": None,
    "progress": 0,
    "result": None
}


@router.get("/status")
async def get_ensemble_status():
    """Get status of Ensemble AI system"""
    from services.ensemble_ai import get_rebuild_status
    
    rebuild_status = get_rebuild_status()
    
    return {
        "ensemble_initialized": _ensemble is not None,
        "optimizer_initialized": _optimizer is not None,
        "deep_learning_available": _deep_learning_ai is not None,
        "model_weights": _ensemble.model_weights if _ensemble else None,
        "universe_rebuild_status": rebuild_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/predict/{coin_id}")
async def get_ensemble_prediction(coin_id: str, optimize_weights: bool = True):
    """
    Get ensemble prediction for a coin using all ML/DL models.
    
    Combines:
    - LSTM Neural Network
    - Technical Analysis (RSI, MACD, SMA)
    - Pattern Recognition
    - Momentum Analysis
    - Trend Analysis
    - Volatility Analysis
    - Sentiment Analysis
    
    Returns weighted consensus signal with accuracy estimate.
    """
    if not _ensemble or not _market_service:
        raise HTTPException(status_code=503, detail="Ensemble AI not initialized")
    
    # Get price data
    hist_data = await _market_service.get_historical_data(coin_id, days=90)
    if not hist_data or not hist_data.get('prices'):
        raise HTTPException(status_code=404, detail=f"No price data for {coin_id}")
    
    prices = [p[1] for p in hist_data['prices']]
    current_price = prices[-1] if prices else 0
    
    result = await _ensemble.get_ensemble_prediction(
        coin_id=coin_id,
        prices=prices,
        current_price=current_price,
        optimize_weights=optimize_weights
    )
    
    return result


@router.post("/predict-batch")
async def get_batch_predictions(request: BatchPredictionRequest):
    """Get ensemble predictions for multiple coins"""
    if not _ensemble or not _market_service:
        raise HTTPException(status_code=503, detail="Ensemble AI not initialized")
    
    if len(request.coin_ids) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 coins per batch")
    
    results = []
    for coin_id in request.coin_ids:
        try:
            hist_data = await _market_service.get_historical_data(coin_id, days=90)
            if hist_data and hist_data.get('prices'):
                prices = [p[1] for p in hist_data['prices']]
                result = await _ensemble.get_ensemble_prediction(
                    coin_id=coin_id,
                    prices=prices,
                    current_price=prices[-1],
                    optimize_weights=request.optimize_weights
                )
                results.append(result)
        except Exception as e:
            results.append({"coin_id": coin_id, "error": str(e)})
    
    # Sort by confidence
    results.sort(key=lambda x: x.get('confidence', 0), reverse=True)
    
    return {
        "count": len(results),
        "predictions": results,
        "top_buys": [r for r in results if 'BUY' in r.get('final_signal', '')][:5],
        "top_sells": [r for r in results if 'SELL' in r.get('final_signal', '')][:5]
    }


@router.get("/weights")
async def get_model_weights():
    """Get current model weights"""
    if not _ensemble:
        raise HTTPException(status_code=503, detail="Ensemble AI not initialized")
    
    return {
        "weights": _ensemble.model_weights,
        "description": {
            "lstm": "LSTM Neural Network - price prediction",
            "technical": "Technical Analysis - RSI, MACD, SMA",
            "pattern": "Pattern Recognition - chart patterns",
            "momentum": "Momentum Analysis - ROC, MACD",
            "trend": "Trend Analysis - slope, higher highs",
            "volatility": "Volatility Analysis - Bollinger, stddev",
            "sentiment": "Sentiment Analysis - news sentiment"
        }
    }


@router.post("/optimize-weights")
async def optimize_model_weights():
    """Optimize model weights based on historical performance"""
    if not _ensemble:
        raise HTTPException(status_code=503, detail="Ensemble AI not initialized")
    
    old_weights = dict(_ensemble.model_weights)
    _ensemble._optimize_weights()
    new_weights = _ensemble.model_weights
    
    return {
        "status": "optimized",
        "old_weights": old_weights,
        "new_weights": new_weights
    }


async def run_universe_build(target_size: int, analyze_count: int = 500):
    """Background task to build optimal universe"""
    from services.ensemble_ai import run_universe_rebuild_background
    
    if _optimizer:
        await run_universe_rebuild_background(_optimizer, target_size, analyze_count)


@router.post("/rebuild-universe")
async def rebuild_universe(request: UniverseBuildRequest, background_tasks: BackgroundTasks):
    """
    Rebuild optimal trading universe from top 1000 coins.
    
    This is the main Ensemble AI feature that:
    1. Analyzes up to 1000 coins using all ML/DL models
    2. Scores each coin using ensemble of: LSTM, Technical, Pattern, Momentum, Trend, Volatility
    3. Builds optimal portfolio based on scores
    4. Compares with existing recommendations
    5. Identifies hidden gems (high score + low market cap)
    
    Runs as background task - check /build-status for progress.
    """
    from services.ensemble_ai import get_rebuild_status
    
    if not _optimizer:
        raise HTTPException(status_code=503, detail="Universe optimizer not initialized")
    
    status = get_rebuild_status()
    if status.get("running"):
        return {
            "status": "already_running",
            "started_at": status.get("started_at"),
            "progress": status.get("progress"),
            "progress_message": status.get("progress_message")
        }
    
    background_tasks.add_task(run_universe_build, request.target_size, request.analyze_count)
    
    return {
        "status": "started",
        "target_size": request.target_size,
        "analyze_count": request.analyze_count,
        "message": f"Universe rebuild started. Analyzing up to {request.analyze_count} coins. Check /build-status for progress."
    }


@router.get("/build-status")
async def get_build_status():
    """Get detailed status of universe build including progress percentage"""
    from services.ensemble_ai import get_rebuild_status
    
    status = get_rebuild_status()
    return {
        **status,
        "endpoints": {
            "rebuild": "POST /api/ensemble/rebuild-universe",
            "results": "GET /api/ensemble/optimal-universe",
            "comparison": "GET /api/ensemble/comparison",
            "hidden_gems": "GET /api/ensemble/hidden-gems"
        }
    }


@router.get("/optimal-universe")
async def get_optimal_universe():
    """Get the current optimal universe"""
    if _db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    cursor = _db.optimal_universe.find().sort("universe_score", -1)
    coins = await cursor.to_list(length=100)
    
    for coin in coins:
        coin.pop('_id', None)
    
    return {
        "count": len(coins),
        "coins": coins,
        "top_10": [c['symbol'] for c in coins[:10]]
    }


@router.get("/hidden-gems")
async def get_hidden_gems_from_universe():
    """Get hidden gems from the optimal universe"""
    if _db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    # High score, low market cap
    cursor = _db.optimal_universe.find({
        "universe_score": {"$gte": 65},
        "market_cap": {"$lt": 500_000_000}
    }).sort("universe_score", -1).limit(20)
    
    gems = await cursor.to_list(length=20)
    
    for gem in gems:
        gem.pop('_id', None)
    
    return {
        "count": len(gems),
        "hidden_gems": gems
    }


@router.get("/top-predictions")
async def get_top_predictions():
    """Get ensemble predictions for top universe coins"""
    if not _ensemble or not _db:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    # Get top coins from universe
    cursor = _db.optimal_universe.find().sort("universe_score", -1).limit(10)
    top_coins = await cursor.to_list(length=10)
    
    predictions = []
    for coin in top_coins:
        try:
            coin_id = coin['coin_id']
            hist_data = await _market_service.get_historical_data(coin_id, days=90)
            if hist_data and hist_data.get('prices'):
                prices = [p[1] for p in hist_data['prices']]
                result = await _ensemble.get_ensemble_prediction(
                    coin_id=coin_id,
                    prices=prices,
                    current_price=prices[-1],
                    optimize_weights=True
                )
                result['universe_score'] = coin.get('universe_score', 0)
                predictions.append(result)
        except:
            continue
    
    # Sort by combined score
    predictions.sort(
        key=lambda x: x.get('confidence', 0) + x.get('universe_score', 0),
        reverse=True
    )
    
    return {
        "count": len(predictions),
        "predictions": predictions,
        "best_opportunities": [p for p in predictions if 'BUY' in p.get('final_signal', '')][:5]
    }

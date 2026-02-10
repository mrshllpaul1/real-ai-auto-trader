"""
Multi-Timeframe (MTF) Training API Routes

Endpoints for training and using multi-timeframe ML models.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mtf-training", tags=["MTF Training"])

# Global reference
_mtf_service = None
_db = None


def set_dependencies(db, mtf_service=None):
    """Set service dependencies"""
    global _mtf_service, _db
    _db = db
    _mtf_service = mtf_service


def get_service():
    """Get MTF training service with lazy initialization"""
    global _mtf_service, _db
    if _mtf_service is None and _db is not None:
        from services.mtf_training_service import get_mtf_training_service
        _mtf_service = get_mtf_training_service(_db)
    return _mtf_service


class MTFTrainingRequest(BaseModel):
    """Request model for MTF training"""
    symbols: Optional[List[str]] = Field(
        default=None,
        description="List of coin symbols to train on. If None, uses all available."
    )
    timeframes: Optional[List[str]] = Field(
        default=["1h", "4h", "1D"],
        description="Timeframes to use for training"
    )
    epochs: Optional[int] = Field(
        default=50,
        ge=10,
        le=500,
        description="Number of training epochs"
    )
    learning_rate: Optional[float] = Field(
        default=0.001,
        ge=0.0001,
        le=0.1,
        description="Learning rate for optimization"
    )


class PredictionRequest(BaseModel):
    """Request model for predictions"""
    symbol: str = Field(..., description="Coin symbol to predict")
    timeframes: Optional[List[str]] = Field(
        default=["1h", "4h", "1D"],
        description="Timeframes to analyze"
    )


class BatchPredictionRequest(BaseModel):
    """Request model for batch predictions"""
    symbols: Optional[List[str]] = Field(
        default=None,
        description="List of symbols to predict. If None, uses all available."
    )
    timeframes: Optional[List[str]] = Field(
        default=["1h", "4h", "1D"],
        description="Timeframes to analyze"
    )


@router.get("/status")
async def get_training_status():
    """
    Get current MTF training status.
    
    Returns the status of any ongoing or completed training.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="MTF Training service not initialized")
    
    status = await service.get_training_status()
    return status


@router.post("/train-now")
async def train_now(
    request: MTFTrainingRequest = None,
    background_tasks: BackgroundTasks = None
):
    """
    Start multi-timeframe model training immediately.
    
    This endpoint trains ML models using multi-timeframe OHLCV data.
    The training considers signals from multiple timeframes (1h, 4h, 1D)
    to capture both short-term momentum and long-term trends.
    
    Features extracted:
    - Price & Volume metrics across timeframes
    - Technical indicators (SMA, RSI, Volatility)
    - Trend alignment scores
    - Cross-timeframe divergences
    
    Returns:
        Training results with accuracy metrics
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="MTF Training service not initialized")
    
    if request is None:
        request = MTFTrainingRequest()
    
    logger.info(f"🚀 Starting MTF training with {request.epochs} epochs...")
    
    # Run training (can be background or sync based on request)
    result = await service.train_mtf_model(
        symbols=request.symbols,
        timeframes=request.timeframes,
        epochs=request.epochs,
        learning_rate=request.learning_rate
    )
    
    return result


@router.post("/train-background")
async def train_background(
    request: MTFTrainingRequest,
    background_tasks: BackgroundTasks
):
    """
    Start MTF training in the background.
    
    Use this for large training jobs that may take longer.
    Check status at /api/mtf-training/status
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="MTF Training service not initialized")
    
    background_tasks.add_task(
        service.train_mtf_model,
        request.symbols,
        request.timeframes,
        request.epochs,
        request.learning_rate
    )
    
    return {
        "message": "MTF training started in background",
        "status": "processing",
        "check_status_at": "/api/mtf-training/status",
        "config": {
            "symbols": request.symbols or "all available",
            "timeframes": request.timeframes,
            "epochs": request.epochs
        }
    }


@router.get("/history")
async def get_training_history(limit: int = 10):
    """
    Get MTF training history.
    
    Returns past training runs with their results and accuracy metrics.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="MTF Training service not initialized")
    
    history = await service.get_training_history(limit)
    
    return {
        "history": history,
        "count": len(history)
    }


@router.post("/predict")
async def predict_symbol(request: PredictionRequest):
    """
    Get MTF prediction for a single symbol.
    
    Uses the trained multi-timeframe model to generate:
    - Buy/Sell/Hold signal
    - Confidence score
    - Multi-timeframe alignment analysis
    
    Requires a trained model. Run /train-now first if no model exists.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="MTF Training service not initialized")
    
    prediction = await service.predict(
        symbol=request.symbol,
        timeframes=request.timeframes
    )
    
    if "error" in prediction:
        raise HTTPException(status_code=400, detail=prediction["error"])
    
    return prediction


@router.get("/predict/{symbol}")
async def predict_symbol_get(symbol: str):
    """
    Get MTF prediction for a symbol (GET version).
    
    Simple endpoint to get prediction for a specific coin.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="MTF Training service not initialized")
    
    prediction = await service.predict(symbol=symbol.upper())
    
    if "error" in prediction:
        raise HTTPException(status_code=400, detail=prediction["error"])
    
    return prediction


@router.post("/predict-batch")
async def predict_batch(request: BatchPredictionRequest = None):
    """
    Get MTF predictions for multiple symbols.
    
    Returns predictions for all symbols, sorted by confidence.
    Separates Buy, Sell, and Hold signals.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="MTF Training service not initialized")
    
    if request is None:
        request = BatchPredictionRequest()
    
    predictions = await service.predict_batch(
        symbols=request.symbols,
        timeframes=request.timeframes
    )
    
    return predictions


@router.get("/predict-all")
async def predict_all():
    """
    Get predictions for all available symbols.
    
    Convenience endpoint that predicts on all symbols with MTF data.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="MTF Training service not initialized")
    
    predictions = await service.predict_batch()
    
    return predictions


@router.get("/alignment/{symbol}")
async def get_timeframe_alignment(symbol: str):
    """
    Get multi-timeframe alignment analysis for a symbol.
    
    Shows whether all timeframes agree on trend direction:
    - Strong bullish: All timeframes bullish
    - Strong bearish: All timeframes bearish
    - Mixed: Timeframes disagree (caution)
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="MTF Training service not initialized")
    
    mtf_service = await service.get_mtf_service()
    if not mtf_service:
        raise HTTPException(status_code=500, detail="MTF data service not initialized")
    
    # Get features
    features = await mtf_service.get_training_features(symbol.upper())
    
    if not features.get("timeframes"):
        raise HTTPException(
            status_code=404,
            detail=f"No MTF data available for {symbol}. Download data first."
        )
    
    # Calculate alignment
    alignment = await service.calculate_mtf_alignment(features)
    
    return {
        "symbol": symbol.upper(),
        "alignment": alignment,
        "features": features,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/available-symbols")
async def get_available_symbols():
    """
    Get list of symbols with MTF data available for training/prediction.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="MTF Training service not initialized")
    
    symbols = await service._get_default_training_symbols()
    
    return {
        "symbols": symbols,
        "count": len(symbols),
        "note": "These symbols have multi-timeframe data available"
    }


@router.get("/model-info")
async def get_model_info():
    """
    Get information about the trained MTF model.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="MTF Training service not initialized")
    
    model_doc = await service.model_collection.find_one(
        {"type": "mtf_ensemble"},
        {"_id": 0, "weights": 0, "normalization": 0}  # Exclude large fields
    )
    
    if not model_doc:
        return {
            "status": "no_model",
            "message": "No trained model found. Run POST /api/mtf-training/train-now first."
        }
    
    return {
        "status": "ready",
        "model": model_doc
    }

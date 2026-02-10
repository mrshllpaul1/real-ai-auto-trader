"""
Enhanced Multi-Timeframe (MTF) Training API Routes

Endpoints for training and using enhanced MTF models with media/sentiment integration.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enhanced-mtf-training", tags=["Enhanced MTF Training"])

# Global reference
_enhanced_mtf_service = None
_db = None


def set_dependencies(db, service=None):
    """Set service dependencies"""
    global _enhanced_mtf_service, _db
    _db = db
    _enhanced_mtf_service = service


def get_service():
    """Get Enhanced MTF training service with lazy initialization"""
    global _enhanced_mtf_service, _db
    if _enhanced_mtf_service is None and _db is not None:
        from services.enhanced_mtf_training_service import get_enhanced_mtf_service
        _enhanced_mtf_service = get_enhanced_mtf_service(_db)
    return _enhanced_mtf_service


class EnhancedTrainingRequest(BaseModel):
    """Request model for enhanced MTF training"""
    symbols: Optional[List[str]] = Field(
        default=None,
        description="List of coin symbols to train on. Use ['all'] for full Kraken universe (600+ coins). If None, uses default list."
    )
    use_all_kraken: Optional[bool] = Field(
        default=False,
        description="Set to true to train on all Kraken coins (600+)"
    )
    timeframes: Optional[List[str]] = Field(
        default=["1h", "4h", "1D"],
        description="Timeframes to use for training"
    )
    epochs: Optional[int] = Field(
        default=100,
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
    download_data: Optional[bool] = Field(
        default=True,
        description="Whether to download OHLCV data before training"
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
        description="List of symbols to predict. If None, uses default list."
    )
    timeframes: Optional[List[str]] = Field(
        default=["1h", "4h", "1D"],
        description="Timeframes to analyze"
    )


@router.get("/status")
async def get_training_status():
    """
    Get current enhanced MTF training status.
    
    Returns the status of any ongoing or completed training.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Enhanced MTF Training service not initialized")
    
    status = await service.get_training_status()
    return status


@router.post("/train")
async def train_enhanced_model(
    request: EnhancedTrainingRequest = None
):
    """
    Train enhanced MTF model with technical + sentiment features.
    
    This endpoint trains ML models using:
    - Multi-timeframe OHLCV data (1h, 4h, 1D)
    - Social sentiment (Twitter, Reddit analysis)
    - Fear & Greed Index
    - News sentiment
    - FOMO/Fear indicators
    
    Features extracted:
    - Technical: SMA, RSI, Volatility, Volume, Returns
    - Sentiment: Twitter/Reddit scores, Fear & Greed, Hype cycle
    
    Returns:
        Training results with accuracy metrics
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Enhanced MTF Training service not initialized")
    
    if request is None:
        request = EnhancedTrainingRequest()
    
    # Handle use_all_kraken flag
    symbols = request.symbols
    if request.use_all_kraken:
        symbols = ["all"]
        logger.info("🌐 Training on full Kraken universe (600+ coins)...")
    
    logger.info(f"🚀 Starting Enhanced MTF training with {request.epochs} epochs...")
    
    result = await service.train_enhanced_model(
        symbols=symbols,
        timeframes=request.timeframes,
        epochs=request.epochs,
        learning_rate=request.learning_rate,
        download_data=request.download_data
    )
    
    return result


@router.post("/train-background")
async def train_background(
    request: EnhancedTrainingRequest,
    background_tasks: BackgroundTasks
):
    """
    Start enhanced MTF training in the background.
    
    Use this for large training jobs that may take longer.
    Check status at /api/enhanced-mtf-training/status
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Enhanced MTF Training service not initialized")
    
    background_tasks.add_task(
        service.train_enhanced_model,
        request.symbols,
        request.timeframes,
        request.epochs,
        request.learning_rate,
        request.download_data
    )
    
    return {
        "message": "Enhanced MTF training started in background",
        "status": "processing",
        "check_status_at": "/api/enhanced-mtf-training/status",
        "config": {
            "symbols": request.symbols or "default list (15 coins)",
            "timeframes": request.timeframes,
            "epochs": request.epochs,
            "features": "technical + sentiment"
        }
    }


@router.get("/history")
async def get_training_history(limit: int = 10):
    """
    Get enhanced MTF training history.
    
    Returns past training runs with their results and accuracy metrics.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Enhanced MTF Training service not initialized")
    
    history = await service.get_training_history(limit)
    
    return {
        "history": history,
        "count": len(history)
    }


@router.post("/predict")
async def predict_symbol(request: PredictionRequest):
    """
    Get enhanced MTF prediction for a single symbol.
    
    Uses the trained model combining technical + sentiment features to generate:
    - Buy/Sell/Hold signal
    - Confidence score
    - Technical analysis summary
    - Sentiment breakdown (Twitter, Reddit, Fear & Greed)
    
    Requires a trained model. Run /train first if no model exists.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Enhanced MTF Training service not initialized")
    
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
    Get enhanced MTF prediction for a symbol (GET version).
    
    Simple endpoint to get prediction for a specific coin.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Enhanced MTF Training service not initialized")
    
    prediction = await service.predict(symbol=symbol.upper())
    
    if "error" in prediction:
        raise HTTPException(status_code=400, detail=prediction["error"])
    
    return prediction


@router.post("/predict-all")
async def predict_all(request: BatchPredictionRequest = None):
    """
    Get enhanced MTF predictions for all symbols.
    
    Returns predictions for all symbols, sorted by confidence.
    Separates Buy, Sell, and Hold signals.
    Includes sentiment breakdown for each prediction.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Enhanced MTF Training service not initialized")
    
    if request is None:
        request = BatchPredictionRequest()
    
    predictions = await service.predict_all(
        symbols=request.symbols,
        timeframes=request.timeframes
    )
    
    return predictions


@router.get("/predict-all")
async def predict_all_get():
    """
    Get predictions for all default symbols.
    
    Convenience endpoint that predicts on all default coins.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Enhanced MTF Training service not initialized")
    
    predictions = await service.predict_all()
    
    return predictions


@router.get("/model-info")
async def get_model_info():
    """
    Get information about the trained enhanced MTF model.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Enhanced MTF Training service not initialized")
    
    model_info = await service.get_model_info()
    
    return model_info


@router.get("/kraken-universe")
async def get_kraken_universe():
    """
    Get all available coins from Kraken exchange.
    
    Returns the full list of 600+ coins available for training.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Enhanced MTF Training service not initialized")
    
    coins = await service.fetch_all_kraken_coins()
    stats = await service.get_kraken_universe_stats()
    
    return {
        "total_coins": len(coins),
        "coins": coins,
        "stats": stats,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post("/train-all-kraken")
async def train_all_kraken(
    epochs: int = 100,
    download_data: bool = True,
    background_tasks: BackgroundTasks = None
):
    """
    Train on ALL Kraken coins (600+).
    
    This is a long-running operation that trains the model on the entire
    Kraken coin universe with technical + sentiment features.
    
    Note: This operation may take several minutes to complete.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Enhanced MTF Training service not initialized")
    
    # Get all Kraken coins
    all_coins = await service.fetch_all_kraken_coins()
    
    logger.info(f"🌐 Starting training on {len(all_coins)} Kraken coins...")
    
    # Run training
    result = await service.train_enhanced_model(
        symbols=all_coins,
        epochs=epochs,
        download_data=download_data
    )
    
    return result


@router.post("/train-fast")
async def train_fast(
    epochs: int = 100,
    batch_size: int = 50
):
    """
    Fast training on ALL Kraken coins using sentiment features only.
    
    This is much faster as it doesn't require downloading OHLCV data.
    Uses only sentiment signals: Twitter, Reddit, Fear & Greed, FOMO/Fear.
    
    Typically completes in under 2 minutes for 600+ coins.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Enhanced MTF Training service not initialized")
    
    logger.info(f"⚡ Starting fast sentiment training...")
    
    result = await service.train_sentiment_only(
        symbols=["all"],
        epochs=epochs,
        batch_size=batch_size
    )
    
    return result


@router.post("/download-data")
async def download_data(
    symbols: Optional[List[str]] = None,
    timeframes: Optional[List[str]] = None,
    force: bool = False
):
    """
    Download OHLCV data from Kraken for training.
    
    Args:
        symbols: List of coin symbols (default: all default coins)
        timeframes: List of timeframes (default: 1h, 4h, 1D)
        force: Force re-download even if data exists
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Enhanced MTF Training service not initialized")
    
    result = await service.download_ohlcv_data(
        symbols=symbols,
        timeframes=timeframes,
        force=force
    )
    
    return result


@router.get("/sentiment/{symbol}")
async def get_sentiment(symbol: str):
    """
    Get current sentiment analysis for a symbol.
    
    Returns combined sentiment from:
    - Twitter/X analysis
    - Reddit analysis
    - Fear & Greed Index
    - FOMO/Fear detection
    - Hype cycle analysis
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Enhanced MTF Training service not initialized")
    
    sentiment = await service.fetch_social_sentiment(symbol.upper())
    fear_greed = await service.fetch_fear_greed_index()
    
    return {
        "symbol": symbol.upper(),
        "sentiment": sentiment,
        "fear_greed": fear_greed,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/fear-greed")
async def get_fear_greed():
    """
    Get current Fear & Greed Index.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Enhanced MTF Training service not initialized")
    
    fear_greed = await service.fetch_fear_greed_index()
    
    return fear_greed

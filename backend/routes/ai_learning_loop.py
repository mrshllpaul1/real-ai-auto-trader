"""
AI Learning Loop API Routes
Endpoints for storing predictions, recording outcomes, and getting performance metrics.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/ai-learning", tags=["AI Learning Loop"])

# Dependencies
_db = None
_learning_service = None


def set_dependencies(db, learning_service):
    """Set dependencies from server.py"""
    global _db, _learning_service
    _db = db
    _learning_service = learning_service


class StorePredictionRequest(BaseModel):
    prediction_type: str  # price_direction, price_target, gem_potential, signal
    coin_symbol: str
    prediction: Dict[str, Any]  # The actual prediction data
    confidence: float  # 0-100
    source_model: str  # lstm, ensemble, gem_predictor, etc.
    metadata: Optional[Dict] = None


class RecordOutcomeRequest(BaseModel):
    prediction_id: Optional[str] = None
    coin_symbol: Optional[str] = None
    prediction_type: Optional[str] = None
    actual_outcome: Dict[str, Any]


@router.get("/status")
async def get_service_status():
    """Get learning loop service status"""
    if not _learning_service:
        return {"status": "not_initialized"}
    
    # Get counts
    predictions_count = await _db.ai_predictions.count_documents({})
    verified_count = await _db.ai_predictions.count_documents({"verified": True})
    outcomes_count = await _db.ai_outcomes.count_documents({})
    
    return {
        "status": "operational",
        "total_predictions": predictions_count,
        "verified_predictions": verified_count,
        "total_outcomes": outcomes_count,
        "verification_rate": round(verified_count / predictions_count * 100, 1) if predictions_count > 0 else 0
    }


@router.post("/store-prediction")
async def store_prediction(request: StorePredictionRequest):
    """
    Store an AI prediction for later verification.
    
    Example:
    {
        "prediction_type": "price_direction",
        "coin_symbol": "BTC",
        "prediction": {"direction": "up", "target_price": 95000},
        "confidence": 75,
        "source_model": "lstm"
    }
    """
    if not _learning_service:
        raise HTTPException(status_code=503, detail="Learning service not initialized")
    
    prediction_id = await _learning_service.store_prediction(
        prediction_type=request.prediction_type,
        coin_symbol=request.coin_symbol,
        prediction=request.prediction,
        confidence=request.confidence,
        source_model=request.source_model,
        metadata=request.metadata
    )
    
    return {
        "success": True,
        "prediction_id": prediction_id,
        "message": f"Prediction stored for {request.coin_symbol}"
    }


@router.post("/record-outcome")
async def record_outcome(request: RecordOutcomeRequest):
    """
    Record the actual outcome for a prediction.
    
    Example:
    {
        "prediction_id": "abc123",
        "actual_outcome": {"direction": "up", "actual_price": 94500}
    }
    
    Or match by coin + type:
    {
        "coin_symbol": "BTC",
        "prediction_type": "price_direction",
        "actual_outcome": {"direction": "up"}
    }
    """
    if not _learning_service:
        raise HTTPException(status_code=503, detail="Learning service not initialized")
    
    result = await _learning_service.record_outcome(
        prediction_id=request.prediction_id,
        coin_symbol=request.coin_symbol,
        prediction_type=request.prediction_type,
        actual_outcome=request.actual_outcome
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/model-performance")
async def get_model_performance(model: Optional[str] = None, days: int = 30):
    """
    Get performance metrics for AI models.
    
    Args:
        model: Specific model name (optional, returns all if not specified)
        days: Number of days to look back (default: 30)
    """
    if not _learning_service:
        raise HTTPException(status_code=503, detail="Learning service not initialized")
    
    performance = await _learning_service.get_model_performance(
        source_model=model,
        days=days
    )
    
    return {
        "model": model or "all",
        "days": days,
        "performance": performance
    }


@router.get("/insights")
async def get_learning_insights():
    """
    Get AI learning insights for model improvement.
    
    Returns:
    - Model rankings by accuracy
    - Weak areas that need improvement
    - Strong areas performing well
    - Recommended weight adjustments
    """
    if not _learning_service:
        raise HTTPException(status_code=503, detail="Learning service not initialized")
    
    insights = await _learning_service.get_learning_insights()
    return insights


@router.get("/training-feedback")
async def get_training_feedback(model: Optional[str] = None):
    """
    Get feedback data formatted for retraining.
    
    Returns successful and failed patterns to guide model updates.
    """
    if not _learning_service:
        raise HTTPException(status_code=503, detail="Learning service not initialized")
    
    feedback = await _learning_service.get_training_feedback(model_name=model)
    return feedback


@router.get("/predictions/unverified")
async def get_unverified_predictions(limit: int = 50):
    """Get predictions that haven't been verified yet"""
    if _db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    predictions = await _db.ai_predictions.find(
        {"verified": False},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Convert ObjectId to string
    for pred in predictions:
        if "_id" in pred:
            pred["prediction_id"] = str(pred["_id"])
    
    return {
        "count": len(predictions),
        "predictions": predictions
    }


@router.get("/predictions/recent")
async def get_recent_predictions(limit: int = 50, verified_only: bool = False):
    """Get recent predictions"""
    if _db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    query = {"verified": True} if verified_only else {}
    
    predictions = await _db.ai_predictions.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {
        "count": len(predictions),
        "predictions": predictions
    }

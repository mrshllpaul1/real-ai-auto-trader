"""
Hidden Gem Predictor API Routes
Endpoints for finding and predicting hidden gem cryptocurrencies.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/gems", tags=["Hidden Gems"])

# Dependencies
_db = None
_gem_predictor = None

def set_dependencies(db, gem_predictor):
    """Set dependencies from server.py"""
    global _db, _gem_predictor
    _db = db
    _gem_predictor = gem_predictor


class ScanRequest(BaseModel):
    limit: Optional[int] = 30


class PredictRequest(BaseModel):
    days_ahead: Optional[int] = 7


# Background task status
_training_status = {
    "running": False,
    "last_run": None,
    "result": None
}


@router.post("/scan")
async def scan_for_gems(request: ScanRequest):
    """
    Scan the market for hidden gem opportunities.
    
    Returns coins ranked by gem potential based on:
    - Volume surge
    - Price momentum
    - Market cap potential
    - Technical setup
    """
    if not _gem_predictor:
        raise HTTPException(status_code=503, detail="Gem predictor not initialized")
    
    gems = await _gem_predictor.scan_for_gems(limit=request.limit)
    
    return {
        "count": len(gems),
        "gems": gems,
        "scan_time": datetime.utcnow().isoformat()
    }


@router.post("/predict")
async def predict_next_gems(request: PredictRequest):
    """
    Predict which coins are likely to pump in the next X days.
    
    Uses AI analysis of current gems to predict potential movers.
    """
    if not _gem_predictor:
        raise HTTPException(status_code=503, detail="Gem predictor not initialized")
    
    result = await _gem_predictor.predict_next_gems(days_ahead=request.days_ahead)
    
    return result


@router.get("/top")
async def get_top_gems():
    """Get the top hidden gems right now"""
    if not _gem_predictor:
        raise HTTPException(status_code=503, detail="Gem predictor not initialized")
    
    gems = await _gem_predictor.scan_for_gems(limit=10)
    
    return {
        "top_gems": gems[:5],
        "potential_gems": gems[5:10] if len(gems) > 5 else [],
        "generated_at": datetime.utcnow().isoformat()
    }


async def run_training_task():
    """Background task to train the gem predictor"""
    global _training_status
    _training_status["running"] = True
    _training_status["started_at"] = datetime.utcnow().isoformat()
    
    try:
        result = await _gem_predictor.train_on_historical()
        _training_status["result"] = result
        _training_status["last_run"] = datetime.utcnow().isoformat()
    except Exception as e:
        _training_status["result"] = {"error": str(e)}
    finally:
        _training_status["running"] = False


async def run_deep_training_task():
    """Background task for deep historical training"""
    try:
        await _gem_predictor.train_on_historical_deep()
    except Exception as e:
        from services.hidden_gem_predictor import _gem_training_status
        _gem_training_status["error"] = str(e)
        _gem_training_status["running"] = False


@router.post("/train")
async def train_gem_predictor(background_tasks: BackgroundTasks):
    """
    Train the gem predictor on historical data.
    
    Analyzes past successful gem picks to improve future predictions.
    Runs in background.
    """
    if not _gem_predictor:
        raise HTTPException(status_code=503, detail="Gem predictor not initialized")
    
    if _training_status["running"]:
        return {
            "status": "already_running",
            "started_at": _training_status.get("started_at")
        }
    
    background_tasks.add_task(run_training_task)
    
    return {
        "status": "started",
        "message": "Training started in background"
    }


@router.post("/train-deep")
async def train_gem_predictor_deep(background_tasks: BackgroundTasks):
    """
    Deep historical training on 2009-2026 gem data.
    
    Analyzes all historical gems (BTC, ETH, DOGE, SHIB, etc.) to learn:
    - Optimal volume thresholds
    - Best market cap ranges
    - Category performance patterns
    - Technical indicators that predicted success
    
    Updates model weights for better future predictions.
    """
    if not _gem_predictor:
        raise HTTPException(status_code=503, detail="Gem predictor not initialized")
    
    from services.hidden_gem_predictor import get_gem_training_status
    status = get_gem_training_status()
    
    if status.get("running"):
        return {
            "status": "already_running",
            "started_at": status.get("started_at"),
            "progress": status.get("progress"),
            "message": status.get("message")
        }
    
    background_tasks.add_task(run_deep_training_task)
    
    return {
        "status": "started",
        "message": "Deep historical training started. Analyzing 15+ years of gem data.",
        "check_status": "/api/gems/deep-training-status"
    }


@router.get("/deep-training-status")
async def get_deep_training_status():
    """Get detailed status of deep historical training"""
    from services.hidden_gem_predictor import get_gem_training_status
    return get_gem_training_status()


@router.get("/training-status")
async def get_training_status():
    """Get the status of gem predictor training"""
    return _training_status


@router.get("/history")
async def get_gem_history(limit: int = 10):
    """Get history of gem predictions"""
    if _db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    cursor = _db.gem_predictions.find().sort("predicted_at", -1).limit(limit)
    predictions = await cursor.to_list(length=limit)
    
    for p in predictions:
        p.pop('_id', None)
    
    return {
        "count": len(predictions),
        "predictions": predictions
    }


@router.post("/verify/{prediction_id}")
async def verify_prediction(prediction_id: str, actual_gains: dict):
    """
    Verify a past prediction with actual results.
    
    This helps train the model for better future predictions.
    """
    if _db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    from bson import ObjectId
    
    try:
        result = await _db.gem_predictions.update_one(
            {"_id": ObjectId(prediction_id)},
            {
                "$set": {
                    "verified": True,
                    "actual_performance": actual_gains,
                    "verified_at": datetime.utcnow()
                }
            }
        )
        
        return {"status": "verified", "updated": result.modified_count > 0}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

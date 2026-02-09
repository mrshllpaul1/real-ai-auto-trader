"""
Gem ML/DL Prediction API Routes
Endpoints for ML vs DL gem prediction comparison.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/gems/ml-dl", tags=["Gem ML/DL Prediction"])

# Dependencies
_db = None
_gem_engine = None

def set_dependencies(db, gem_engine):
    """Set dependencies from server.py"""
    global _db, _gem_engine
    _db = db
    _gem_engine = gem_engine


def get_gem_engine():
    """Get or lazy-load the gem prediction engine"""
    global _gem_engine, _db
    if _gem_engine is None and _db is not None:
        try:
            from services.gem_ml_dl_predictor import get_gem_prediction_engine
            _gem_engine = get_gem_prediction_engine(_db)
        except Exception as e:
            print(f"Failed to initialize gem engine: {e}")
    return _gem_engine


class TrainRequest(BaseModel):
    symbols: Optional[List[str]] = None


class PredictRequest(BaseModel):
    coin_id: str
    symbol: Optional[str] = None


class ScanRequest(BaseModel):
    coins: Optional[List[str]] = None


# Training status
_training_status = {
    "running": False,
    "started_at": None,
    "progress": 0,
    "message": "",
    "result": None
}


async def _run_training(symbols: List[str] = None):
    """Background training task"""
    global _training_status
    _training_status["running"] = True
    _training_status["message"] = "Training ML and DL models..."
    
    try:
        engine = get_gem_engine()
        if engine is None:
            raise Exception("Gem prediction engine not available")
        result = await engine.train_models(symbols)
        _training_status["result"] = result
        _training_status["message"] = "Training complete"
    except Exception as e:
        _training_status["result"] = {"error": str(e)}
        _training_status["message"] = f"Training failed: {str(e)}"
    finally:
        _training_status["running"] = False


@router.post("/train")
async def train_models(request: TrainRequest, background_tasks: BackgroundTasks):
    """
    Train all ML and DL models for gem prediction.
    
    Models trained:
    - ML: RandomForest, GradientBoosting, SVM
    - DL: LSTM, GRU, BiLSTM, CNN-LSTM, Attention
    
    Training runs in background. Check /status for progress.
    """
    global _training_status
    
    if not _gem_engine:
        raise HTTPException(status_code=503, detail="Gem prediction engine not initialized")
    
    if _training_status["running"]:
        return {
            "status": "already_running",
            "started_at": _training_status["started_at"],
            "message": _training_status["message"]
        }
    
    _training_status = {
        "running": True,
        "started_at": datetime.utcnow().isoformat(),
        "progress": 0,
        "message": "Starting training...",
        "result": None
    }
    
    background_tasks.add_task(_run_training, request.symbols)
    
    return {
        "status": "started",
        "message": "Training ML and DL models in background",
        "check_status": "/api/gems/ml-dl/status"
    }


@router.get("/status")
async def get_training_status():
    """Get current training status and results"""
    return {
        **_training_status,
        "is_trained": _gem_engine.is_trained if _gem_engine else False,
        "models_available": list(_gem_engine.models.keys()) if _gem_engine else []
    }


@router.post("/predict")
async def predict_gem(request: PredictRequest):
    """
    Predict gem potential for a specific coin.
    
    Returns predictions from all ML and DL models for comparison.
    """
    if not _gem_engine:
        raise HTTPException(status_code=503, detail="Gem prediction engine not initialized")
    
    if not _gem_engine.is_trained:
        raise HTTPException(status_code=400, detail="Models not trained. Call /train first")
    
    result = await _gem_engine.predict_gem(request.coin_id, request.symbol)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/compare")
async def compare_models():
    """
    Get detailed ML vs DL model comparison.
    
    Shows accuracy rankings for all models and determines
    which approach (ML or DL) performs better for gem prediction.
    """
    if not _gem_engine:
        raise HTTPException(status_code=503, detail="Gem prediction engine not initialized")
    
    result = await _gem_engine.compare_models()
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/scan")
async def scan_for_gems(request: ScanRequest):
    """
    Scan multiple coins and rank by gem potential.
    
    Uses the best performing model to score each coin.
    """
    if not _gem_engine:
        raise HTTPException(status_code=503, detail="Gem prediction engine not initialized")
    
    if not _gem_engine.is_trained:
        raise HTTPException(status_code=400, detail="Models not trained. Call /train first")
    
    results = await _gem_engine.scan_for_gems(request.coins)
    
    return {
        "count": len(results),
        "gems": results,
        "best_model": _gem_engine.best_model,
        "scanned_at": datetime.utcnow().isoformat()
    }


@router.get("/model-info")
async def get_model_info():
    """Get information about all available models"""
    if not _gem_engine:
        raise HTTPException(status_code=503, detail="Gem prediction engine not initialized")
    
    return {
        "models": [
            {
                "name": name,
                "type": meta.get("type"),
                "category": meta.get("category"),
                "description": meta.get("description"),
                "accuracy": round(_gem_engine.model_accuracy.get(name, 0), 1),
                "is_best": name == _gem_engine.best_model
            }
            for name, meta in _gem_engine.model_metadata.items()
        ],
        "best_overall": _gem_engine.best_model,
        "best_ml": _gem_engine.best_ml_model,
        "best_dl": _gem_engine.best_dl_model,
        "is_trained": _gem_engine.is_trained
    }


@router.get("/training-history")
async def get_training_history(limit: int = 10):
    """Get history of model training runs"""
    if not _db:
        raise HTTPException(status_code=503, detail="Database not available")
    
    history = await _db.gem_model_training.find(
        {}, {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return {
        "count": len(history),
        "history": history
    }

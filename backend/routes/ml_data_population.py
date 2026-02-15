"""ML Data Population API

Endpoints to populate ML analytics with real prediction data.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from services.ml_data_populator import (
    get_ml_data_populator,
    run_population,
    STRATEGY_VARIANTS,
    MODEL_NAMES,
    COINS
)
from services.ml_analytics import (
    get_confidence_calibrator,
    get_drift_detector,
    get_ab_manager
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ml-data", tags=["ML Data Population"])

_db = None
_population_status = {"status": "idle", "last_run": None, "results": None}


def set_dependencies(db):
    """Set database dependency."""
    global _db
    _db = db


class PopulationConfig(BaseModel):
    """Configuration for data population."""
    calibration_predictions: int = Field(default=500, ge=100, le=5000)
    drift_samples: int = Field(default=200, ge=50, le=1000)
    ab_trades_per_variant: int = Field(default=50, ge=20, le=500)


@router.get("/status")
async def get_population_status():
    """Get current status of ML data population."""
    return _population_status


@router.post("/populate")
async def populate_ml_data(background_tasks: BackgroundTasks, config: Optional[PopulationConfig] = None):
    """Trigger ML data population (runs in background)."""
    global _population_status
    
    if _population_status["status"] == "running":
        return {"status": "already_running", "message": "Population is already in progress"}
    
    _population_status["status"] = "running"
    _population_status["started_at"] = datetime.utcnow().isoformat()
    
    async def run_in_background():
        global _population_status
        try:
            populator = get_ml_data_populator(_db)
            results = await populator.populate_all()
            _population_status = {
                "status": "complete",
                "last_run": datetime.utcnow().isoformat(),
                "results": results
            }
        except Exception as e:
            _population_status = {
                "status": "error",
                "last_run": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    background_tasks.add_task(run_in_background)
    
    return {
        "status": "started",
        "message": "ML data population started in background",
        "config": config.dict() if config else "default"
    }


@router.post("/populate-sync")
async def populate_ml_data_sync():
    """Trigger ML data population (synchronous - waits for completion)."""
    global _population_status
    
    _population_status["status"] = "running"
    
    try:
        populator = get_ml_data_populator(_db)
        results = await populator.populate_all()
        _population_status = {
            "status": "complete",
            "last_run": datetime.utcnow().isoformat(),
            "results": results
        }
        return _population_status
    except Exception as e:
        _population_status = {
            "status": "error",
            "last_run": datetime.utcnow().isoformat(),
            "error": str(e)
        }
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy-variants")
async def get_strategy_variants():
    """Get all available strategy variants for A/B testing."""
    return {
        "variants": STRATEGY_VARIANTS,
        "total": len(STRATEGY_VARIANTS),
        "categories": [
            {"name": "RSI-based", "variants": ["Conservative RSI", "Aggressive RSI"]},
            {"name": "Momentum", "variants": ["MACD Momentum", "Volume Surge", "Golden Cross Hunter"]},
            {"name": "Mean Reversion", "variants": ["Bollinger Breakout"]},
            {"name": "Sentiment", "variants": ["Fear & Greed Contrarian", "News Sentiment Rider"]},
            {"name": "On-Chain", "variants": ["Whale Following"]},
            {"name": "Multi-Signal", "variants": ["Multi-Timeframe Confluence"]}
        ]
    }


@router.get("/models")
async def get_available_models():
    """Get all ML models tracked in analytics."""
    calibrator = get_confidence_calibrator()
    drift_detector = get_drift_detector()
    
    # Get current status for each model
    drift_status = drift_detector.get_drift_status()
    
    models_info = []
    for model in MODEL_NAMES:
        model_data = {
            "name": model,
            "display_name": model.replace("_", " ").title(),
            "drift_status": drift_status.get("models", {}).get(model, {}).get("status", "unknown"),
            "current_accuracy": drift_status.get("models", {}).get(model, {}).get("current_accuracy")
        }
        models_info.append(model_data)
    
    return {
        "models": models_info,
        "total": len(MODEL_NAMES)
    }


@router.get("/coins")
async def get_tracked_coins():
    """Get all coins tracked in predictions."""
    return {
        "coins": COINS,
        "total": len(COINS)
    }


@router.post("/reset")
async def reset_ml_data():
    """Reset all ML analytics data (use with caution)."""
    global _population_status
    
    # Reset calibrator
    calibrator = get_confidence_calibrator()
    calibrator._predictions = []
    
    # Reset drift detector
    drift_detector = get_drift_detector()
    drift_detector._predictions = []
    drift_detector._alerts = []
    drift_detector._baseline_accuracy = {}
    
    # Reset A/B manager
    ab_manager = get_ab_manager()
    ab_manager._tests = {}
    ab_manager._results = {}
    
    _population_status = {"status": "reset", "last_run": datetime.utcnow().isoformat()}
    
    return {
        "status": "reset_complete",
        "message": "All ML analytics data has been reset",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/summary")
async def get_ml_data_summary():
    """Get summary of all ML analytics data."""
    calibrator = get_confidence_calibrator()
    drift_detector = get_drift_detector()
    ab_manager = get_ab_manager()
    
    calibration = calibrator.get_accuracy_by_confidence_level()
    drift_status = drift_detector.get_drift_status()
    ab_tests = ab_manager.list_tests()
    
    return {
        "calibration": {
            "total_predictions": calibration.get("total_predictions", 0),
            "overall_accuracy": calibration.get("overall_accuracy"),
            "levels": calibration.get("levels", {})
        },
        "drift_detection": {
            "models_tracked": len(drift_status.get("models", {})),
            "alerts_active": len(drift_detector.get_alerts(acknowledged=False)),
            "window_size": drift_status.get("window_size")
        },
        "ab_testing": {
            "active_tests": len([t for t in ab_tests if t.get("status") == "running"]),
            "total_tests": len(ab_tests),
            "total_samples": sum(t.get("total_samples", 0) for t in ab_tests)
        },
        "population_status": _population_status,
        "timestamp": datetime.utcnow().isoformat()
    }

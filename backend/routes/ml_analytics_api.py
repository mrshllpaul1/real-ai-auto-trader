"""ML Analytics API

Provides endpoints for:
- Confidence calibration
- Model drift detection
- A/B testing management
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from services.ml_analytics import (
    get_confidence_calibrator,
    get_drift_detector,
    get_ab_manager
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ml-analytics", tags=["ML Analytics"])


# ==================== Confidence Calibration ====================

class PredictionRecord(BaseModel):
    """Record a prediction for calibration."""
    prediction_id: str
    coin_id: str
    predicted_action: str = Field(..., description="BUY, SELL, or HOLD")
    confidence: float = Field(..., ge=0, le=1)
    model_name: str


class OutcomeRecord(BaseModel):
    """Record actual outcome."""
    prediction_id: str
    actual_correct: bool


@router.post("/calibration/record-prediction")
async def record_prediction(record: PredictionRecord):
    """Record a prediction for calibration analysis."""
    calibrator = get_confidence_calibrator()
    calibrator.record_prediction(
        prediction_id=record.prediction_id,
        coin_id=record.coin_id,
        predicted_action=record.predicted_action,
        confidence=record.confidence,
        model_name=record.model_name
    )
    return {"status": "recorded", "prediction_id": record.prediction_id}


@router.post("/calibration/record-outcome")
async def record_outcome(record: OutcomeRecord):
    """Record the actual outcome of a prediction."""
    calibrator = get_confidence_calibrator()
    calibrator.record_outcome(
        prediction_id=record.prediction_id,
        actual_correct=record.actual_correct
    )
    return {"status": "recorded", "prediction_id": record.prediction_id}


@router.get("/calibration/curve")
async def get_calibration_curve(model_name: Optional[str] = None):
    """Get calibration curve showing confidence vs actual accuracy."""
    calibrator = get_confidence_calibrator()
    return calibrator.get_calibration_curve(model_name)


@router.get("/calibration/accuracy-by-level")
async def get_accuracy_by_confidence_level():
    """Get accuracy breakdown by confidence level (HIGH/MEDIUM/LOW/VERY_LOW)."""
    calibrator = get_confidence_calibrator()
    return calibrator.get_accuracy_by_confidence_level()


# ==================== Model Drift Detection ====================

class DriftRecord(BaseModel):
    """Record prediction outcome for drift detection."""
    model_name: str
    is_correct: bool


class BaselineConfig(BaseModel):
    """Set baseline accuracy for a model."""
    model_name: str
    accuracy: float = Field(..., ge=0, le=1)


@router.post("/drift/record")
async def record_drift_data(record: DriftRecord):
    """Record prediction outcome for drift detection."""
    detector = get_drift_detector()
    detector.record_prediction_outcome(
        model_name=record.model_name,
        is_correct=record.is_correct
    )
    return {"status": "recorded"}


@router.post("/drift/set-baseline")
async def set_drift_baseline(config: BaselineConfig):
    """Set baseline accuracy for drift comparison."""
    detector = get_drift_detector()
    detector.set_baseline(config.model_name, config.accuracy)
    return {"status": "baseline_set", "model_name": config.model_name, "accuracy": config.accuracy}


@router.get("/drift/status")
async def get_drift_status(model_name: Optional[str] = None):
    """Get current drift status for models."""
    detector = get_drift_detector()
    return detector.get_drift_status(model_name)


@router.get("/drift/alerts")
async def get_drift_alerts(acknowledged: bool = False):
    """Get drift alerts."""
    detector = get_drift_detector()
    alerts = detector.get_alerts(acknowledged)
    return {
        "alerts": alerts,
        "total": len(alerts),
        "unacknowledged": len([a for a in alerts if not a.get("acknowledged")])
    }


@router.post("/drift/alerts/{alert_id}/acknowledge")
async def acknowledge_drift_alert(alert_id: str):
    """Acknowledge a drift alert."""
    detector = get_drift_detector()
    detector.acknowledge_alert(alert_id)
    return {"status": "acknowledged", "alert_id": alert_id}


# ==================== A/B Testing ====================

class ABTestCreate(BaseModel):
    """Create a new A/B test."""
    test_id: str
    test_name: str
    variants: List[Dict[str, Any]]
    traffic_split: Optional[List[float]] = None
    metric: str = "win_rate"


class ABTestResult(BaseModel):
    """Record A/B test result."""
    test_id: str
    variant_id: str
    outcome: float
    metadata: Optional[Dict] = None


@router.post("/ab-test/create")
async def create_ab_test(config: ABTestCreate):
    """Create a new A/B test."""
    manager = get_ab_manager()
    result = manager.create_test(
        test_id=config.test_id,
        test_name=config.test_name,
        variants=config.variants,
        traffic_split=config.traffic_split,
        metric=config.metric
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/ab-test/record-result")
async def record_ab_test_result(result: ABTestResult):
    """Record a result for an A/B test."""
    manager = get_ab_manager()
    manager.record_result(
        test_id=result.test_id,
        variant_id=result.variant_id,
        outcome=result.outcome,
        metadata=result.metadata
    )
    return {"status": "recorded"}


@router.get("/ab-test/{test_id}/results")
async def get_ab_test_results(test_id: str):
    """Get results for an A/B test."""
    manager = get_ab_manager()
    result = manager.get_test_results(test_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/ab-test/list")
async def list_ab_tests(status: Optional[str] = None):
    """List all A/B tests."""
    manager = get_ab_manager()
    tests = manager.list_tests(status)
    return {"tests": tests, "total": len(tests)}


@router.post("/ab-test/{test_id}/stop")
async def stop_ab_test(test_id: str):
    """Stop an A/B test."""
    manager = get_ab_manager()
    result = manager.stop_test(test_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ==================== Cache & Deduplication Stats ====================

@router.get("/cache/stats")
async def get_cache_stats():
    """Get smart cache statistics."""
    from services.smart_cache import get_smart_cache, get_deduplicator
    
    cache = get_smart_cache()
    dedup = get_deduplicator()
    
    return {
        "cache": cache.get_stats(),
        "deduplication": dedup.get_stats(),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/cache/clear")
async def clear_cache(pattern: Optional[str] = "*"):
    """Clear cache entries."""
    from services.smart_cache import get_smart_cache
    
    cache = get_smart_cache()
    count = await cache.clear_pattern(pattern)
    
    return {
        "status": "cleared",
        "pattern": pattern,
        "cleared_count": count
    }


# ==================== Combined Dashboard ====================

@router.get("/dashboard")
async def get_ml_analytics_dashboard():
    """Get combined ML analytics dashboard data."""
    from services.smart_cache import get_smart_cache, get_deduplicator
    
    calibrator = get_confidence_calibrator()
    detector = get_drift_detector()
    ab_manager = get_ab_manager()
    cache = get_smart_cache()
    dedup = get_deduplicator()
    
    return {
        "calibration": {
            "accuracy_by_level": calibrator.get_accuracy_by_confidence_level(),
            "curve": calibrator.get_calibration_curve()
        },
        "drift": {
            "status": detector.get_drift_status(),
            "active_alerts": len(detector.get_alerts(acknowledged=False))
        },
        "ab_testing": {
            "active_tests": len(ab_manager.list_tests(status="running")),
            "total_tests": len(ab_manager.list_tests())
        },
        "infrastructure": {
            "cache": cache.get_stats(),
            "deduplication": dedup.get_stats()
        },
        "generated_at": datetime.utcnow().isoformat()
    }

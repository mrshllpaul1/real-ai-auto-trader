"""
Whale Alerts & Event Backtesting API Routes
============================================
Real-time alerts and prediction accuracy tracking.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any


router = APIRouter(prefix="/alerts", tags=["Whale Alerts & Backtesting"])

_db = None


def set_db(db):
    global _db
    _db = db


async def get_database():
    global _db
    if _db is None:
        from server import db
        _db = db
    return _db


# =============================================================================
# WHALE ALERTS
# =============================================================================

class UpdateThresholdRequest(BaseModel):
    metric: str
    warning: Optional[float] = None
    critical: Optional[float] = None
    urgent: Optional[float] = None


@router.get("/whale/active")
async def get_active_alerts(severity: Optional[str] = None, db=Depends(get_database)):
    """Get all active whale alerts"""
    from services.whale_alert_service import get_whale_alert_service
    service = get_whale_alert_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Whale alert service not available")
    
    alerts = await service.get_active_alerts(severity_filter=severity)
    return {"alerts": alerts, "count": len(alerts)}


@router.get("/whale/summary")
async def get_alert_summary(db=Depends(get_database)):
    """Get summary of current alerts"""
    from services.whale_alert_service import get_whale_alert_service
    service = get_whale_alert_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Whale alert service not available")
    
    return await service.get_alert_summary()


@router.post("/whale/check")
async def check_for_alerts(db=Depends(get_database)):
    """Manually trigger alert check against current on-chain data"""
    from services.whale_alert_service import get_whale_alert_service
    from services.onchain_data_service import get_onchain_service
    
    alert_service = get_whale_alert_service(db)
    onchain_service = get_onchain_service(db)
    
    if not alert_service or not onchain_service:
        raise HTTPException(status_code=500, detail="Required services not available")
    
    # Get latest on-chain data
    onchain_data = await onchain_service.get_whale_activity()
    
    # Check for alerts
    new_alerts = await alert_service.check_for_alerts(onchain_data)
    
    return {
        "status": "checked",
        "new_alerts": len(new_alerts),
        "alerts": [
            {
                "alert_id": a.alert_id,
                "title": a.title,
                "severity": a.severity.value,
                "price_impact": a.price_impact_expected
            }
            for a in new_alerts
        ]
    }


@router.post("/whale/dismiss/{alert_id}")
async def dismiss_alert(alert_id: str, db=Depends(get_database)):
    """Dismiss an alert"""
    from services.whale_alert_service import get_whale_alert_service
    service = get_whale_alert_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Whale alert service not available")
    
    success = await service.dismiss_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"status": "dismissed", "alert_id": alert_id}


@router.post("/whale/read/{alert_id}")
async def mark_alert_read(alert_id: str, db=Depends(get_database)):
    """Mark an alert as read"""
    from services.whale_alert_service import get_whale_alert_service
    service = get_whale_alert_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Whale alert service not available")
    
    success = await service.mark_alert_read(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"status": "marked_read", "alert_id": alert_id}


@router.post("/whale/threshold")
async def update_threshold(request: UpdateThresholdRequest, db=Depends(get_database)):
    """Update alert thresholds"""
    from services.whale_alert_service import get_whale_alert_service
    service = get_whale_alert_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Whale alert service not available")
    
    return await service.update_threshold(
        request.metric,
        warning=request.warning,
        critical=request.critical,
        urgent=request.urgent
    )


@router.get("/whale/thresholds")
async def get_thresholds(db=Depends(get_database)):
    """Get current alert thresholds"""
    from services.whale_alert_service import get_whale_alert_service
    service = get_whale_alert_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Whale alert service not available")
    
    thresholds = {}
    for metric, threshold in service.thresholds.items():
        thresholds[metric] = {
            "name": threshold.name,
            "warning": threshold.warning_threshold,
            "critical": threshold.critical_threshold,
            "urgent": threshold.urgent_threshold,
            "cooldown_minutes": threshold.cooldown_minutes
        }
    
    return {"thresholds": thresholds}


@router.post("/whale/monitoring/start")
async def start_alert_monitoring(db=Depends(get_database)):
    """Start real-time whale alert monitoring"""
    from services.whale_alert_service import get_whale_alert_service
    service = get_whale_alert_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Whale alert service not available")
    
    return await service.start_monitoring()


@router.post("/whale/monitoring/stop")
async def stop_alert_monitoring(db=Depends(get_database)):
    """Stop whale alert monitoring"""
    from services.whale_alert_service import get_whale_alert_service
    service = get_whale_alert_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Whale alert service not available")
    
    return await service.stop_monitoring()


# =============================================================================
# EVENT BACKTESTING
# =============================================================================

class BacktestRequest(BaseModel):
    predictions: List[Dict[str, Any]]
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class SimulateRequest(BaseModel):
    n_predictions: int = 50


@router.post("/backtest/run")
async def run_backtest(request: BacktestRequest, db=Depends(get_database)):
    """Run backtest on a list of predictions"""
    from services.event_backtest_service import get_event_backtest_service
    service = get_event_backtest_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Event backtest service not available")
    
    return await service.backtest_predictions(
        predictions=request.predictions,
        start_date=request.start_date,
        end_date=request.end_date
    )


@router.post("/backtest/simulate")
async def simulate_backtest(request: SimulateRequest = None, db=Depends(get_database)):
    """Simulate predictions and run backtest"""
    from services.event_backtest_service import get_event_backtest_service
    service = get_event_backtest_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Event backtest service not available")
    
    n = request.n_predictions if request else 50
    return await service.simulate_predictions(n_predictions=n)


@router.get("/backtest/accuracy")
async def get_prediction_accuracy(event_type: Optional[str] = None, db=Depends(get_database)):
    """Get historical prediction accuracy metrics"""
    from services.event_backtest_service import get_event_backtest_service
    service = get_event_backtest_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Event backtest service not available")
    
    return await service.get_historical_accuracy(event_type=event_type)


@router.get("/backtest/event-types")
async def get_event_type_performance(db=Depends(get_database)):
    """Get performance breakdown by event type"""
    from services.event_backtest_service import get_event_backtest_service
    service = get_event_backtest_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Event backtest service not available")
    
    return await service.get_event_type_performance()


@router.get("/backtest/historical-events")
async def get_historical_events(event_type: Optional[str] = None, db=Depends(get_database)):
    """Get historical events used for backtesting"""
    from services.event_backtest_service import get_event_backtest_service
    service = get_event_backtest_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Event backtest service not available")
    
    events = service.historical_events
    if event_type:
        events = [e for e in events if e.event_type == event_type]
    
    from dataclasses import asdict
    return {
        "events": [asdict(e) for e in events],
        "count": len(events),
        "event_types": list(set(e.event_type for e in service.historical_events))
    }


@router.post("/backtest/adaptive-predictions")
async def backtest_adaptive_predictions(db=Depends(get_database)):
    """Backtest current adaptive strategy predictions"""
    from services.event_backtest_service import get_event_backtest_service
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    
    backtest_service = get_event_backtest_service(db)
    adaptive_service = get_adaptive_strategy_service(db)
    
    if not backtest_service or not adaptive_service:
        raise HTTPException(status_code=500, detail="Required services not available")
    
    # Get current predictions from adaptive service
    events = await adaptive_service.predict_future_events(days_ahead=365)
    
    # Convert to backtest format
    predictions = []
    for event in events:
        predictions.append({
            "event_id": event.event_id,
            "event_type": event.event_type,
            "predicted_date": event.predicted_date,
            "probability": event.probability,
            "expected_impact": event.expected_impact
        })
    
    # Run backtest
    return await backtest_service.backtest_predictions(predictions)

"""
Adaptive Strategy & Event Prediction API Routes
================================================
Auto-adjust parameters, regime detection, and event prediction.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any


router = APIRouter(prefix="/adaptive-strategy", tags=["Adaptive Strategy"])

_db = None


def set_db(db):
    global _db
    _db = db


def set_dependencies(db, adaptive_strategy_service=None):
    """Set dependencies from service initialization"""
    global _db
    _db = db


async def get_database():
    global _db
    if _db is None:
        from server import db
        _db = db
    return _db


class PredictEventsRequest(BaseModel):
    days_ahead: int = 30


class RecordPerformanceRequest(BaseModel):
    variant_id: str
    regime: str
    win_rate: float
    sharpe_ratio: float
    total_trades: int


# =============================================================================
# MARKET REGIME DETECTION
# =============================================================================

@router.get("/regime/current")
async def get_current_regime(db=Depends(get_database)):
    """Get current market regime detection"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    service = get_adaptive_strategy_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Adaptive strategy service not available")
    
    regime = await service.detect_market_regime()
    
    from dataclasses import asdict
    return {
        "status": "detected",
        "regime": asdict(regime)
    }


@router.get("/regime/history")
async def get_regime_history(limit: int = 50, db=Depends(get_database)):
    """Get historical regime detections"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    service = get_adaptive_strategy_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Adaptive strategy service not available")
    
    return {
        "history": service.regime_history[-limit:],
        "total": len(service.regime_history)
    }


# =============================================================================
# REGIME-SPECIFIC VARIANTS
# =============================================================================

@router.post("/variants/initialize")
async def initialize_regime_variants(db=Depends(get_database)):
    """Initialize all regime-specific strategy variants"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    service = get_adaptive_strategy_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Adaptive strategy service not available")
    
    return await service.initialize_regime_variants()


@router.get("/variants")
async def get_regime_variants(db=Depends(get_database)):
    """Get all regime-specific variants"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    service = get_adaptive_strategy_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Adaptive strategy service not available")
    
    from dataclasses import asdict
    variants_by_regime = {}
    
    for vid, variant in service.regime_variants.items():
        regime = variant.target_regime
        if regime not in variants_by_regime:
            variants_by_regime[regime] = []
        variants_by_regime[regime].append(asdict(variant))
    
    return {
        "total_variants": len(service.regime_variants),
        "variants_by_regime": variants_by_regime
    }


@router.get("/variants/{regime}")
async def get_variants_for_regime(regime: str, db=Depends(get_database)):
    """Get variants optimized for a specific regime"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    service = get_adaptive_strategy_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Adaptive strategy service not available")
    
    from dataclasses import asdict
    variants = [
        asdict(v) for v in service.regime_variants.values()
        if v.target_regime == regime
    ]
    
    if not variants:
        raise HTTPException(status_code=404, detail=f"No variants found for regime: {regime}")
    
    return {
        "regime": regime,
        "variants": variants,
        "count": len(variants)
    }


# =============================================================================
# AUTO-ADJUSTMENT
# =============================================================================

@router.post("/auto-adjust")
async def auto_adjust_parameters(db=Depends(get_database)):
    """Auto-adjust strategy parameters based on current market conditions"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    service = get_adaptive_strategy_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Adaptive strategy service not available")
    
    return await service.auto_adjust_parameters()


@router.get("/optimal-strategy")
async def get_optimal_strategy(db=Depends(get_database)):
    """Get the optimal strategy for current market conditions"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    service = get_adaptive_strategy_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Adaptive strategy service not available")
    
    return await service.get_optimal_strategy()


# =============================================================================
# EVENT PREDICTION
# =============================================================================

@router.post("/predict-events")
async def predict_future_events(request: PredictEventsRequest, db=Depends(get_database)):
    """Predict future market events"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    service = get_adaptive_strategy_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Adaptive strategy service not available")
    
    events = await service.predict_future_events(days_ahead=request.days_ahead)
    
    from dataclasses import asdict
    return {
        "status": "predicted",
        "days_ahead": request.days_ahead,
        "events": [asdict(e) for e in events],
        "total_events": len(events),
        "high_probability_events": len([e for e in events if e.probability > 0.7])
    }


@router.get("/predicted-events")
async def get_predicted_events(min_probability: float = 0.5, db=Depends(get_database)):
    """Get currently predicted events"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    service = get_adaptive_strategy_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Adaptive strategy service not available")
    
    from dataclasses import asdict
    filtered_events = [
        asdict(e) for e in service.predicted_events
        if e.probability >= min_probability
    ]
    
    return {
        "events": filtered_events,
        "total": len(filtered_events),
        "min_probability_filter": min_probability
    }


@router.get("/predicted-events/{event_type}")
async def get_events_by_type(event_type: str, db=Depends(get_database)):
    """Get predicted events of a specific type"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    service = get_adaptive_strategy_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Adaptive strategy service not available")
    
    from dataclasses import asdict
    events = [
        asdict(e) for e in service.predicted_events
        if e.event_type == event_type
    ]
    
    return {
        "event_type": event_type,
        "events": events,
        "count": len(events)
    }


@router.get("/event-calendar")
async def get_event_calendar(days_ahead: int = 60, db=Depends(get_database)):
    """Get organized calendar of all predicted and scheduled events"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    service = get_adaptive_strategy_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Adaptive strategy service not available")
    
    return await service.get_event_calendar(days_ahead=days_ahead)


@router.get("/event-coverage-stats")
async def get_event_coverage_stats(db=Depends(get_database)):
    """Get statistics on event prediction coverage across all event types"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    service = get_adaptive_strategy_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Adaptive strategy service not available")
    
    return await service.get_event_coverage_stats()


@router.get("/event-types")
async def get_all_event_types(db=Depends(get_database)):
    """Get all defined event types with their metadata"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    service = get_adaptive_strategy_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Adaptive strategy service not available")
    
    event_types = []
    for event_config in service.PREDICTABLE_EVENTS:
        active_predictions = [e for e in service.predicted_events if e.event_type == event_config["type"]]
        event_types.append({
            "type": event_config["type"],
            "description": event_config["description"],
            "impact": event_config.get("impact", "mixed"),
            "confidence": event_config.get("confidence", 0.5),
            "lead_indicators": event_config.get("lead_indicators", []),
            "recurrence": event_config.get("recurrence", "varies"),
            "active_predictions": len(active_predictions),
        })
    
    return {
        "event_types": event_types,
        "total_types": len(event_types),
        "types_with_predictions": len([et for et in event_types if et["active_predictions"] > 0])
    }


@router.get("/scheduled-events")
async def get_scheduled_events_calendar(days_ahead: int = 90, db=Depends(get_database)):
    """Get raw scheduled events from the 2025 calendar"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    from datetime import datetime, timezone
    
    service = get_adaptive_strategy_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Adaptive strategy service not available")
    
    now = datetime.now(timezone.utc)
    scheduled = []
    
    for calendar_key, events in service.SCHEDULED_EVENTS_2025.items():
        for ev in events:
            ev_date = datetime.strptime(ev["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_until = (ev_date - now).days
            if 0 <= days_until <= days_ahead:
                scheduled.append({
                    "date": ev["date"],
                    "days_until": days_until,
                    "description": ev["description"],
                    "calendar_category": calendar_key,
                    "coins": ev.get("coins", []),
                    "impact_pct": ev.get("impact_pct", None),
                })
    
    scheduled.sort(key=lambda x: x["date"])
    
    return {
        "scheduled_events": scheduled,
        "total": len(scheduled),
        "days_ahead": days_ahead,
        "calendars": list(service.SCHEDULED_EVENTS_2025.keys())
    }


# =============================================================================
# ADAPTIVE MONITORING
# =============================================================================

@router.post("/monitoring/start")
async def start_adaptive_monitoring(db=Depends(get_database)):
    """Start continuous adaptive monitoring"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    service = get_adaptive_strategy_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Adaptive strategy service not available")
    
    return await service.start_adaptive_monitoring()


@router.post("/monitoring/stop")
async def stop_adaptive_monitoring(db=Depends(get_database)):
    """Stop adaptive monitoring"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    service = get_adaptive_strategy_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Adaptive strategy service not available")
    
    return await service.stop_adaptive_monitoring()


@router.get("/status")
async def get_adaptation_status(db=Depends(get_database)):
    """Get current adaptation status"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    service = get_adaptive_strategy_service(db)
    
    if not service:
        return {"status": "not_initialized", "message": "Initialize service first"}
    
    return await service.get_adaptation_status()


# =============================================================================
# PERFORMANCE TRACKING
# =============================================================================

@router.post("/performance/record")
async def record_variant_performance(request: RecordPerformanceRequest, db=Depends(get_database)):
    """Record performance of a variant in a specific regime"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    service = get_adaptive_strategy_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Adaptive strategy service not available")
    
    variant = service.regime_variants.get(request.variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    
    # Update performance
    variant.performance_in_regime = request.win_rate * 0.4 + request.sharpe_ratio * 10 * 0.6
    
    # Update regime performance stats
    perf = service.regime_performance[request.regime]
    perf["total_trades"] += request.total_trades
    perf["winning_trades"] += int(request.total_trades * request.win_rate / 100)
    perf["sharpe_sum"] += request.sharpe_ratio
    
    return {
        "status": "recorded",
        "variant_id": request.variant_id,
        "regime": request.regime,
        "performance_score": variant.performance_in_regime
    }


@router.get("/performance/{regime}")
async def get_regime_performance(regime: str, db=Depends(get_database)):
    """Get performance statistics for a regime"""
    from services.adaptive_strategy_service import get_adaptive_strategy_service
    service = get_adaptive_strategy_service(db)
    
    if not service:
        raise HTTPException(status_code=500, detail="Adaptive strategy service not available")
    
    perf = service.regime_performance.get(regime, {})
    total_trades = perf.get("total_trades", 0)
    
    return {
        "regime": regime,
        "total_trades": total_trades,
        "win_rate": (perf.get("winning_trades", 0) / total_trades * 100) if total_trades > 0 else 0,
        "avg_sharpe": perf.get("sharpe_sum", 0) / max(1, total_trades // 100)
    }

"""
Upgrades API Routes
===================
Routes for all upgraded features: P0, P1, PWA, P3
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

router = APIRouter(prefix="/api/upgrades", tags=["upgrades"])


# ============================================================================
# Push Notifications Routes
# ============================================================================

class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: Dict[str, str]
    device_info: Optional[str] = None


class NotificationPreferencesRequest(BaseModel):
    preferences: Dict[str, bool]


@router.post("/notifications/subscribe")
async def subscribe_push(request: PushSubscriptionRequest):
    """Subscribe to push notifications"""
    from services.push_notifications import get_push_service
    service = get_push_service()
    if not service:
        raise HTTPException(500, "Push service not available")
    
    user_id = "demo_user"  # Would come from auth in production
    return await service.subscribe(user_id, request.dict(), request.device_info)


@router.post("/notifications/unsubscribe")
async def unsubscribe_push(endpoint: str):
    """Unsubscribe from push notifications"""
    from services.push_notifications import get_push_service
    service = get_push_service()
    if not service:
        raise HTTPException(500, "Push service not available")
    
    return await service.unsubscribe("demo_user", endpoint)


@router.get("/notifications/pending")
async def get_pending_notifications():
    """Get pending notifications for polling"""
    from services.push_notifications import get_push_service
    service = get_push_service()
    if not service:
        return []
    
    return await service.get_pending_notifications("demo_user")


@router.get("/notifications/history")
async def get_notification_history(limit: int = 50, unread_only: bool = False):
    """Get notification history"""
    from services.push_notifications import get_push_service
    service = get_push_service()
    if not service:
        return []
    
    return await service.get_notification_history("demo_user", limit, unread_only)


@router.post("/notifications/preferences")
async def set_notification_preferences(request: NotificationPreferencesRequest):
    """Set notification preferences"""
    from services.push_notifications import get_push_service
    service = get_push_service()
    if not service:
        raise HTTPException(500, "Push service not available")
    
    return await service.set_preferences("demo_user", request.preferences)


@router.get("/notifications/status")
async def get_notifications_status():
    """Get push notification service status"""
    from services.push_notifications import get_push_service
    service = get_push_service()
    if not service:
        return {"active": False}
    
    return await service.get_status()


# ============================================================================
# Arbitrage Routes
# ============================================================================

class ArbitrageSettingsRequest(BaseModel):
    min_spread_pct: Optional[float] = None
    min_profit_usd: Optional[float] = None
    max_trade_size_usd: Optional[float] = None
    auto_execute: Optional[bool] = None
    enabled_exchanges: Optional[List[str]] = None


@router.get("/arbitrage/status")
async def get_arbitrage_status():
    """Get arbitrage service status"""
    from services.arbitrage_service import get_arbitrage_service
    service = get_arbitrage_service()
    if not service:
        return {"is_monitoring": False, "message": "Service not initialized"}
    
    return await service.get_status()


@router.post("/arbitrage/start")
async def start_arbitrage_monitoring():
    """Start arbitrage monitoring"""
    from services.arbitrage_service import get_arbitrage_service
    service = get_arbitrage_service()
    if not service:
        raise HTTPException(500, "Arbitrage service not available")
    
    return await service.start_monitoring()


@router.post("/arbitrage/stop")
async def stop_arbitrage_monitoring():
    """Stop arbitrage monitoring"""
    from services.arbitrage_service import get_arbitrage_service
    service = get_arbitrage_service()
    if not service:
        raise HTTPException(500, "Arbitrage service not available")
    
    return await service.stop_monitoring()


@router.get("/arbitrage/prices")
async def get_exchange_prices():
    """Get current prices from all exchanges"""
    from services.arbitrage_service import get_arbitrage_service
    service = get_arbitrage_service()
    if not service:
        return {}
    
    return await service.get_prices()


@router.get("/arbitrage/opportunities")
async def get_arbitrage_opportunities():
    """Get current arbitrage opportunities"""
    from services.arbitrage_service import get_arbitrage_service
    service = get_arbitrage_service()
    if not service:
        return []
    
    return await service.get_opportunities()


@router.post("/arbitrage/execute/{opportunity_id}")
async def execute_arbitrage(opportunity_id: str):
    """Execute an arbitrage trade"""
    from services.arbitrage_service import get_arbitrage_service
    service = get_arbitrage_service()
    if not service:
        raise HTTPException(500, "Arbitrage service not available")
    
    return await service.execute_arbitrage(opportunity_id)


@router.post("/arbitrage/settings")
async def update_arbitrage_settings(request: ArbitrageSettingsRequest):
    """Update arbitrage settings"""
    from services.arbitrage_service import get_arbitrage_service
    service = get_arbitrage_service()
    if not service:
        raise HTTPException(500, "Arbitrage service not available")
    
    return await service.update_settings(request.dict(exclude_none=True))


@router.get("/arbitrage/history")
async def get_arbitrage_history(limit: int = 50):
    """Get arbitrage opportunity history"""
    from services.arbitrage_service import get_arbitrage_service
    service = get_arbitrage_service()
    if not service:
        return []
    
    return await service.get_history(limit)


# ============================================================================
# Rebalancer Routes
# ============================================================================

class AllocationRequest(BaseModel):
    allocations: Dict[str, float]
    tolerance_pct: Optional[float] = 5.0


class RebalancerSettingsRequest(BaseModel):
    rebalance_threshold_pct: Optional[float] = None
    min_trade_usd: Optional[float] = None
    max_trade_pct: Optional[float] = None
    check_interval_hours: Optional[int] = None
    auto_execute: Optional[bool] = None


@router.get("/rebalancer/status")
async def get_rebalancer_status():
    """Get rebalancer service status"""
    from services.portfolio_rebalancer import get_rebalancer
    service = get_rebalancer()
    if not service:
        return {"enabled": False, "message": "Service not initialized"}
    
    return await service.get_status()


@router.get("/rebalancer/allocations")
async def get_current_allocations():
    """Get current portfolio allocations"""
    from services.portfolio_rebalancer import get_rebalancer
    service = get_rebalancer()
    if not service:
        raise HTTPException(500, "Rebalancer service not available")
    
    return await service.get_current_allocations()


@router.post("/rebalancer/allocations")
async def set_target_allocations(request: AllocationRequest):
    """Set target allocations"""
    from services.portfolio_rebalancer import get_rebalancer
    service = get_rebalancer()
    if not service:
        raise HTTPException(500, "Rebalancer service not available")
    
    return await service.set_target_allocations(request.allocations, request.tolerance_pct)


@router.post("/rebalancer/template/{template_name}")
async def apply_allocation_template(template_name: str):
    """Apply a predefined allocation template"""
    from services.portfolio_rebalancer import get_rebalancer
    service = get_rebalancer()
    if not service:
        raise HTTPException(500, "Rebalancer service not available")
    
    return await service.apply_template(template_name)


@router.get("/rebalancer/analyze")
async def analyze_rebalance():
    """Analyze portfolio and get rebalance recommendations"""
    from services.portfolio_rebalancer import get_rebalancer
    service = get_rebalancer()
    if not service:
        raise HTTPException(500, "Rebalancer service not available")
    
    return await service.analyze_rebalance()


@router.post("/rebalancer/execute")
async def execute_rebalance(dry_run: bool = True):
    """Execute rebalancing trades"""
    from services.portfolio_rebalancer import get_rebalancer
    service = get_rebalancer()
    if not service:
        raise HTTPException(500, "Rebalancer service not available")
    
    return await service.execute_rebalance(dry_run)


@router.post("/rebalancer/start")
async def start_auto_rebalance():
    """Start automatic rebalancing"""
    from services.portfolio_rebalancer import get_rebalancer
    service = get_rebalancer()
    if not service:
        raise HTTPException(500, "Rebalancer service not available")
    
    return await service.start_auto_rebalance()


@router.post("/rebalancer/stop")
async def stop_auto_rebalance():
    """Stop automatic rebalancing"""
    from services.portfolio_rebalancer import get_rebalancer
    service = get_rebalancer()
    if not service:
        raise HTTPException(500, "Rebalancer service not available")
    
    return await service.stop_auto_rebalance()


@router.get("/rebalancer/history")
async def get_rebalance_history(limit: int = 20):
    """Get rebalancing history"""
    from services.portfolio_rebalancer import get_rebalancer
    service = get_rebalancer()
    if not service:
        return []
    
    return await service.get_history(limit)


# ============================================================================
# Trailing Stop Routes
# ============================================================================

class TrailingStopRequest(BaseModel):
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    quantity: float
    trail_pct: Optional[float] = None


class TrailingStopUpdateRequest(BaseModel):
    trail_pct: Optional[float] = None
    quantity: Optional[float] = None


@router.get("/trailing-stops/status")
async def get_trailing_stops_status():
    """Get trailing stop service status"""
    from services.trailing_stop_service import get_trailing_stop_service
    service = get_trailing_stop_service()
    if not service:
        return {"is_monitoring": False, "message": "Service not initialized"}
    
    return await service.get_status()


@router.post("/trailing-stops/create")
async def create_trailing_stop(request: TrailingStopRequest):
    """Create a new trailing stop"""
    from services.trailing_stop_service import get_trailing_stop_service
    service = get_trailing_stop_service()
    if not service:
        raise HTTPException(500, "Trailing stop service not available")
    
    return await service.create_trailing_stop(
        user_id="demo_user",
        symbol=request.symbol,
        side=request.side,
        entry_price=request.entry_price,
        quantity=request.quantity,
        trail_pct=request.trail_pct
    )


@router.put("/trailing-stops/{stop_id}")
async def update_trailing_stop(stop_id: str, request: TrailingStopUpdateRequest):
    """Update a trailing stop"""
    from services.trailing_stop_service import get_trailing_stop_service
    service = get_trailing_stop_service()
    if not service:
        raise HTTPException(500, "Trailing stop service not available")
    
    return await service.update_trailing_stop(stop_id, request.trail_pct, request.quantity)


@router.delete("/trailing-stops/{stop_id}")
async def cancel_trailing_stop(stop_id: str):
    """Cancel a trailing stop"""
    from services.trailing_stop_service import get_trailing_stop_service
    service = get_trailing_stop_service()
    if not service:
        raise HTTPException(500, "Trailing stop service not available")
    
    return await service.cancel_trailing_stop(stop_id)


@router.get("/trailing-stops/active")
async def get_active_trailing_stops():
    """Get all active trailing stops"""
    from services.trailing_stop_service import get_trailing_stop_service
    service = get_trailing_stop_service()
    if not service:
        return []
    
    return await service.get_active_stops("demo_user")


@router.post("/trailing-stops/start")
async def start_trailing_stop_monitoring():
    """Start trailing stop monitoring"""
    from services.trailing_stop_service import get_trailing_stop_service
    service = get_trailing_stop_service()
    if not service:
        raise HTTPException(500, "Trailing stop service not available")
    
    return await service.start_monitoring()


@router.post("/trailing-stops/stop")
async def stop_trailing_stop_monitoring():
    """Stop trailing stop monitoring"""
    from services.trailing_stop_service import get_trailing_stop_service
    service = get_trailing_stop_service()
    if not service:
        raise HTTPException(500, "Trailing stop service not available")
    
    return await service.stop_monitoring()


@router.get("/trailing-stops/history")
async def get_trailing_stop_history(limit: int = 50):
    """Get trailing stop history"""
    from services.trailing_stop_service import get_trailing_stop_service
    service = get_trailing_stop_service()
    if not service:
        return []
    
    return await service.get_history("demo_user", limit)


# ============================================================================
# Combined Status Endpoint
# ============================================================================

@router.get("/status")
async def get_all_upgrades_status():
    """Get status of all upgraded features"""
    from services.push_notifications import get_push_service
    from services.arbitrage_service import get_arbitrage_service
    from services.portfolio_rebalancer import get_rebalancer
    from services.trailing_stop_service import get_trailing_stop_service
    
    status = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": {}
    }
    
    # Push notifications
    push = get_push_service()
    status["features"]["push_notifications"] = await push.get_status() if push else {"active": False}
    
    # Arbitrage
    arb = get_arbitrage_service()
    status["features"]["arbitrage"] = await arb.get_status() if arb else {"is_monitoring": False}
    
    # Rebalancer
    reb = get_rebalancer()
    status["features"]["rebalancer"] = await reb.get_status() if reb else {"enabled": False}
    
    # Trailing stops
    trail = get_trailing_stop_service()
    status["features"]["trailing_stops"] = await trail.get_status() if trail else {"is_monitoring": False}
    
    return status

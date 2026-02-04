"""
Stop-Loss Automation Routes
API endpoints for managing automated stop-loss and take-profit monitoring.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/automation", tags=["Stop-Loss Automation"])

# Dependencies (set by server.py)
db = None
stop_loss_service = None


def set_dependencies(database, service):
    """Set dependencies from server.py"""
    global db, stop_loss_service
    db = database
    stop_loss_service = service


class UpdateLevelsRequest(BaseModel):
    position_id: str
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None


@router.get("/status")
async def get_automation_status():
    """Get stop-loss automation status and statistics"""
    if not stop_loss_service:
        raise HTTPException(status_code=503, detail="Automation service not initialized")
    
    stats = stop_loss_service.get_stats()
    
    return {
        "enabled": True,
        "check_interval_minutes": stats['config']['check_interval_minutes'],
        "statistics": {
            "total_checks": stats['total_checks'],
            "positions_closed_stop_loss": stats['positions_closed_stop_loss'],
            "positions_closed_take_profit": stats['positions_closed_take_profit'],
            "total_pnl_from_automation": round(stats['total_pnl_from_automation'], 2),
            "last_check": stats['last_check']
        },
        "config": stats['config']
    }


@router.post("/check-now")
async def trigger_check():
    """Manually trigger a stop-loss check (for testing)"""
    if not stop_loss_service:
        raise HTTPException(status_code=503, detail="Automation service not initialized")
    
    result = await stop_loss_service.check_all_positions()
    
    return result


@router.get("/history")
async def get_automation_history(limit: int = 20):
    """Get history of automation executions"""
    if not stop_loss_service:
        raise HTTPException(status_code=503, detail="Automation service not initialized")
    
    history = await stop_loss_service.get_automation_history(limit=limit)
    
    return {
        "history": history,
        "count": len(history)
    }


@router.post("/update-levels")
async def update_position_levels(request: UpdateLevelsRequest):
    """Update stop-loss or take-profit levels for a position"""
    if not stop_loss_service:
        raise HTTPException(status_code=503, detail="Automation service not initialized")
    
    result = await stop_loss_service.update_position_levels(
        position_id=request.position_id,
        stop_loss_price=request.stop_loss_price,
        take_profit_price=request.take_profit_price
    )
    
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('error'))
    
    return result


@router.get("/positions-at-risk")
async def get_positions_at_risk():
    """Get positions that are close to their stop-loss or take-profit"""
    if not stop_loss_service:
        raise HTTPException(status_code=503, detail="Automation service not initialized")
    
    positions = await stop_loss_service._get_open_positions()
    
    at_risk = []
    near_profit = []
    
    for pos in positions:
        symbol = pos.get('symbol')
        if not symbol:
            continue
        
        current_price = await stop_loss_service._get_current_price(symbol)
        if not current_price:
            continue
        
        entry_price = pos.get('entry_price', 0)
        stop_loss_price = pos.get('stop_loss_price', 0)
        take_profit_price = pos.get('take_profit_price', float('inf'))
        
        if entry_price <= 0:
            continue
        
        pnl_pct = (current_price - entry_price) / entry_price * 100
        
        # Calculate distance to stop-loss and take-profit
        if stop_loss_price > 0:
            distance_to_stop = (current_price - stop_loss_price) / stop_loss_price * 100
            if distance_to_stop < 5:  # Within 5% of stop-loss
                at_risk.append({
                    'coin_id': pos.get('coin_id'),
                    'current_price': current_price,
                    'stop_loss_price': stop_loss_price,
                    'distance_pct': round(distance_to_stop, 2),
                    'pnl_pct': round(pnl_pct, 2),
                    'risk_level': 'HIGH' if distance_to_stop < 2 else 'MEDIUM'
                })
        
        if take_profit_price < float('inf'):
            distance_to_tp = (take_profit_price - current_price) / current_price * 100
            if distance_to_tp < 10:  # Within 10% of take-profit
                near_profit.append({
                    'coin_id': pos.get('coin_id'),
                    'current_price': current_price,
                    'take_profit_price': take_profit_price,
                    'distance_pct': round(distance_to_tp, 2),
                    'pnl_pct': round(pnl_pct, 2)
                })
    
    return {
        "positions_at_risk": at_risk,
        "positions_near_profit": near_profit,
        "total_at_risk": len(at_risk),
        "total_near_profit": len(near_profit)
    }

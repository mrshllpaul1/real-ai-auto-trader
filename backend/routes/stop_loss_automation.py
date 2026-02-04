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


class TrailingStopConfigRequest(BaseModel):
    enabled: Optional[bool] = None
    trailing_stop_pct: Optional[float] = None
    activation_pct: Optional[float] = None


@router.get("/trailing-stop/config")
async def get_trailing_stop_config():
    """Get current trailing stop-loss configuration"""
    if not stop_loss_service:
        raise HTTPException(status_code=503, detail="Automation service not initialized")
    
    config = stop_loss_service.config
    stats = stop_loss_service.stats
    
    return {
        "trailing_stop": {
            "enabled": config.get('trailing_stop_enabled', False),
            "trail_percentage": config.get('trailing_stop_pct', 10.0),
            "activation_percentage": config.get('trailing_stop_activation_pct', 5.0),
            "description": "Trailing stop activates after position is in profit by activation_pct, then trails at trail_percentage below highest price"
        },
        "statistics": {
            "trailing_stops_updated": stats.get('trailing_stops_updated', 0),
            "positions_closed_trailing_stop": stats.get('positions_closed_trailing_stop', 0)
        },
        "example": {
            "scenario": "Entry $100, trail 10%, activation 5%",
            "step_1": "Price rises to $105 (5% profit) → Trailing stop activates at $94.50",
            "step_2": "Price rises to $120 → Trailing stop moves to $108",
            "step_3": "Price drops to $115 → Trailing stop stays at $108 (never moves down)",
            "step_4": "Price drops to $108 → TRAILING STOP TRIGGERED, position closed at $108 (8% profit locked)"
        }
    }


@router.post("/trailing-stop/config")
async def update_trailing_stop_config(request: TrailingStopConfigRequest):
    """Update trailing stop-loss configuration"""
    if not stop_loss_service:
        raise HTTPException(status_code=503, detail="Automation service not initialized")
    
    updated = {}
    
    if request.enabled is not None:
        stop_loss_service.config['trailing_stop_enabled'] = request.enabled
        updated['trailing_stop_enabled'] = request.enabled
    
    if request.trailing_stop_pct is not None:
        if request.trailing_stop_pct < 1 or request.trailing_stop_pct > 50:
            raise HTTPException(status_code=400, detail="trailing_stop_pct must be between 1% and 50%")
        stop_loss_service.config['trailing_stop_pct'] = request.trailing_stop_pct
        updated['trailing_stop_pct'] = request.trailing_stop_pct
    
    if request.activation_pct is not None:
        if request.activation_pct < 0 or request.activation_pct > 20:
            raise HTTPException(status_code=400, detail="activation_pct must be between 0% and 20%")
        stop_loss_service.config['trailing_stop_activation_pct'] = request.activation_pct
        updated['trailing_stop_activation_pct'] = request.activation_pct
    
    return {
        "success": True,
        "updated": updated,
        "current_config": {
            "enabled": stop_loss_service.config['trailing_stop_enabled'],
            "trail_percentage": stop_loss_service.config['trailing_stop_pct'],
            "activation_percentage": stop_loss_service.config['trailing_stop_activation_pct']
        }
    }


class PartialTpConfigRequest(BaseModel):
    enabled: Optional[bool] = None
    move_stop_to_breakeven: Optional[bool] = None
    levels: Optional[list] = None


@router.get("/partial-tp/config")
async def get_partial_take_profit_config():
    """Get current partial take-profit configuration"""
    if not stop_loss_service:
        raise HTTPException(status_code=503, detail="Automation service not initialized")
    
    config = stop_loss_service.config
    stats = stop_loss_service.stats
    
    return {
        "partial_take_profit": {
            "enabled": config.get('partial_take_profit_enabled', False),
            "move_stop_to_breakeven": config.get('move_stop_to_breakeven', True),
            "levels": config.get('partial_tp_levels', []),
            "description": "Partial TP closes portions of position at multiple profit levels, locking in gains while letting the rest ride"
        },
        "statistics": {
            "partial_take_profits": stats.get('partial_take_profits', 0)
        },
        "example": {
            "scenario": "Entry $100, position $1000",
            "level_1": "At 30% profit ($130): Close 50% ($500) → Lock $150 profit, $500 remains",
            "level_2": "At 50% profit ($150): Close 25% ($250) → Lock additional $125 profit, $250 remains",
            "level_3": "At 100% profit ($200): Close final 25% ($250) → Lock final $250 profit",
            "total_outcome": "If all levels hit: $525 total profit vs $300 if closed all at 30%",
            "bonus": "After first partial TP, stop-loss moves to breakeven - zero risk on remaining!"
        }
    }


@router.post("/partial-tp/config")
async def update_partial_take_profit_config(request: PartialTpConfigRequest):
    """Update partial take-profit configuration"""
    if not stop_loss_service:
        raise HTTPException(status_code=503, detail="Automation service not initialized")
    
    updated = {}
    
    if request.enabled is not None:
        stop_loss_service.config['partial_take_profit_enabled'] = request.enabled
        updated['partial_take_profit_enabled'] = request.enabled
    
    if request.move_stop_to_breakeven is not None:
        stop_loss_service.config['move_stop_to_breakeven'] = request.move_stop_to_breakeven
        updated['move_stop_to_breakeven'] = request.move_stop_to_breakeven
    
    if request.levels is not None:
        # Validate levels
        total_pct = sum(level.get('pct_of_position', 0) for level in request.levels)
        if total_pct > 100:
            raise HTTPException(status_code=400, detail="Total percentage across levels cannot exceed 100%")
        
        stop_loss_service.config['partial_tp_levels'] = request.levels
        updated['partial_tp_levels'] = request.levels
    
    return {
        "success": True,
        "updated": updated,
        "current_config": {
            "enabled": stop_loss_service.config['partial_take_profit_enabled'],
            "move_stop_to_breakeven": stop_loss_service.config['move_stop_to_breakeven'],
            "levels": stop_loss_service.config['partial_tp_levels']
        }
    }


@router.get("/partial-tp/positions")
async def get_positions_with_partial_tp():
    """Get all positions with their partial take-profit status"""
    if not stop_loss_service:
        raise HTTPException(status_code=503, detail="Automation service not initialized")
    
    positions = await stop_loss_service._get_open_positions()
    
    result = []
    for pos in positions:
        entry_price = pos.get('entry_price', 0)
        current_price = await stop_loss_service._get_current_price(pos.get('symbol')) if pos.get('symbol') else None
        pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 and current_price else 0
        
        partial_tp_taken = pos.get('partial_tp_taken', [])
        levels = stop_loss_service.config['partial_tp_levels']
        
        # Determine next TP level
        next_level = None
        for i, level in enumerate(levels):
            level_id = f"level_{i}"
            if level_id not in partial_tp_taken:
                next_level = {
                    'level_id': level_id,
                    'at_profit_pct': level['at_profit_pct'],
                    'close_pct': level['pct_of_position'],
                    'distance_pct': round(level['at_profit_pct'] - pnl_pct, 2)
                }
                break
        
        result.append({
            "coin_id": pos.get('coin_id'),
            "position_id": pos.get('position_id'),
            "entry_price": entry_price,
            "current_price": current_price,
            "pnl_pct": round(pnl_pct, 2),
            "partial_tp_taken": partial_tp_taken,
            "levels_taken": len(partial_tp_taken),
            "levels_remaining": len(levels) - len(partial_tp_taken),
            "next_level": next_level,
            "stop_at_breakeven": pos.get('stop_moved_to_breakeven', False),
            "original_amount_usd": pos.get('original_amount_usd', pos.get('amount_usd', 0)),
            "remaining_amount_usd": pos.get('amount_usd', 0)
        })
    
    return {
        "positions": result,
        "total": len(result),
        "with_partial_tp_taken": len([p for p in result if p['levels_taken'] > 0]),
        "config": {
            "enabled": stop_loss_service.config['partial_take_profit_enabled'],
            "levels": stop_loss_service.config['partial_tp_levels']
        }
    }


@router.get("/trailing-stop/positions")
async def get_positions_with_trailing_stop():
    """Get all positions with their trailing stop status"""
    if not stop_loss_service:
        raise HTTPException(status_code=503, detail="Automation service not initialized")
    
    positions = await stop_loss_service._get_open_positions()
    
    result = []
    for pos in positions:
        symbol = pos.get('symbol')
        current_price = await stop_loss_service._get_current_price(symbol) if symbol else None
        
        entry_price = pos.get('entry_price', 0)
        highest_price = pos.get('highest_price', entry_price)
        trailing_stop_price = pos.get('trailing_stop_price', 0)
        
        pnl_pct = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 and current_price else 0
        
        activation_pct = stop_loss_service.config['trailing_stop_activation_pct']
        is_active = pnl_pct >= activation_pct
        
        result.append({
            "coin_id": pos.get('coin_id'),
            "position_id": pos.get('position_id'),
            "entry_price": entry_price,
            "current_price": current_price,
            "highest_price": highest_price,
            "trailing_stop_price": trailing_stop_price,
            "original_stop_loss": pos.get('stop_loss_price', 0),
            "pnl_pct": round(pnl_pct, 2),
            "trailing_stop_active": is_active,
            "trailing_stop_activated_at": pos.get('trailing_stop_updated_at'),
            "distance_to_trailing_stop": round((current_price - trailing_stop_price) / current_price * 100, 2) if current_price and trailing_stop_price > 0 else None
        })
    
    return {
        "positions": result,
        "total": len(result),
        "with_active_trailing": len([p for p in result if p['trailing_stop_active']]),
        "config": {
            "enabled": stop_loss_service.config['trailing_stop_enabled'],
            "trail_pct": stop_loss_service.config['trailing_stop_pct'],
            "activation_pct": stop_loss_service.config['trailing_stop_activation_pct']
        }
    }


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

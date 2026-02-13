from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class AutoTradeConfig(BaseModel):
    user_id: str
    enabled: bool
    paper_trading_enabled: bool = True
    real_trading_enabled: bool = False
    amount_per_trade: float = 100  # USD
    min_confidence: float = 70  # Minimum confidence to execute
    max_daily_trades: int = 10

async def get_database():
    from server import db
    return db

# Global scheduler instance
scheduler = None

@router.post("/configure")
async def configure_auto_trading(
    config: AutoTradeConfig,
    db = Depends(get_database)
):
    """Configure auto-trading settings for a user"""
    try:
        await db.auto_trade_config.replace_one(
            {'user_id': config.user_id},
            config.model_dump(),
            upsert=True
        )
        
        return {
            'message': 'Auto-trading configured successfully',
            'config': config.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/{user_id}")
async def get_auto_trading_config(
    user_id: str,
    db = Depends(get_database)
):
    """Get auto-trading configuration for a user"""
    try:
        config = await db.auto_trade_config.find_one(
            {'user_id': user_id},
            {'_id': 0}
        )
        
        if not config:
            return {
                'configured': False,
                'message': 'No configuration found'
            }
        
        return {
            'configured': True,
            'config': config
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start")
async def start_auto_trading(
    background_tasks: BackgroundTasks,
    db = Depends(get_database)
):
    """Start the auto-trading scheduler"""
    try:
        global scheduler
        
        if scheduler and scheduler.is_running:
            return {
                'message': 'Auto-trading is already running',
                'status': 'running'
            }
        
        from services.auto_trading_scheduler import AutoTradingScheduler
        scheduler = AutoTradingScheduler(db)
        
        # Start in background
        background_tasks.add_task(scheduler.start)
        
        # Persist state
        try:
            from services.state_persistence import get_state_persistence
            persistence = get_state_persistence(db)
            if persistence:
                await persistence.set_state("auto_trading", True, metadata={"started_via": "api"})
        except Exception as e:
            pass
        
        return {
            'message': 'Auto-trading started successfully',
            'status': 'starting',
            'background_mode': True,
            'mobile_compatible': True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_auto_trading(db = Depends(get_database)):
    """Stop the auto-trading scheduler"""
    try:
        global scheduler
        
        # Always persist state as stopped
        try:
            from services.state_persistence import get_state_persistence
            persistence = get_state_persistence(db)
            if persistence:
                await persistence.set_state("auto_trading", False)
        except Exception as e:
            pass
        
        if not scheduler or not scheduler.is_running:
            return {
                'message': 'Auto-trading is not running',
                'status': 'stopped'
            }
        
        await scheduler.stop()
        
        return {
            'message': 'Auto-trading stopped successfully',
            'status': 'stopped'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_auto_trading_status(db = Depends(get_database)):
    """Get current auto-trading status"""
    try:
        global scheduler
        
        # Check persisted state
        is_persisted_running = False
        try:
            from services.state_persistence import get_state_persistence
            persistence = get_state_persistence(db)
            if persistence:
                state = await persistence.get_state("auto_trading")
                is_persisted_running = state.get("is_running", False) if state else False
        except Exception as e:
            pass
        
        if not scheduler:
            return {
                'initialized': False,
                'running': is_persisted_running,
                'persisted_running': is_persisted_running,
                'message': 'Auto-trading not initialized'
            }
        
        status = await scheduler.get_status()
        
        return {
            'initialized': True,
            'persisted_running': is_persisted_running,
            **status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

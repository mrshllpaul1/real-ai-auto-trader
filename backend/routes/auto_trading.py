from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any

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
        
        return {
            'message': 'Auto-trading started successfully',
            'status': 'starting',
            'background_mode': True,
            'mobile_compatible': True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_auto_trading():
    """Stop the auto-trading scheduler"""
    try:
        global scheduler
        
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
async def get_auto_trading_status():
    """Get current auto-trading status"""
    try:
        global scheduler
        
        if not scheduler:
            return {
                'initialized': False,
                'running': False,
                'message': 'Auto-trading not initialized'
            }
        
        status = await scheduler.get_status()
        
        return {
            'initialized': True,
            **status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk-status")
async def get_risk_status(db = Depends(get_database)):
    """Get comprehensive risk management status"""
    try:
        from services.risk_manager import RiskManager
        risk_manager = RiskManager(db)
        
        status = risk_manager.get_comprehensive_status()
        
        return {
            'success': True,
            'risk_status': status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emergency-stop")
async def trigger_emergency_stop(
    reason: str,
    db = Depends(get_database)
):
    """Trigger emergency stop - immediately halts all trading"""
    try:
        from services.risk_manager import RiskManager
        risk_manager = RiskManager(db)
        
        risk_manager.trigger_emergency_stop(reason)
        
        # Also stop the scheduler if running
        global scheduler
        if scheduler and scheduler.is_running:
            await scheduler.stop()
        
        return {
            'success': True,
            'message': 'Emergency stop activated',
            'reason': reason
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-emergency-stop")
async def reset_emergency_stop(db = Depends(get_database)):
    """Reset emergency stop (requires manual confirmation)"""
    try:
        from services.risk_manager import RiskManager
        risk_manager = RiskManager(db)
        
        risk_manager.reset_emergency_stop()
        
        return {
            'success': True,
            'message': 'Emergency stop reset - trading can resume'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/assess-trade-risk")
async def assess_trade_risk(
    trade_info: Dict[str, Any],
    db = Depends(get_database)
):
    """Assess risk for a potential trade"""
    try:
        from services.risk_manager import RiskManager
        risk_manager = RiskManager(db)
        
        assessment = await risk_manager.assess_trade_risk(trade_info)
        
        return {
            'success': True,
            'assessment': assessment
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

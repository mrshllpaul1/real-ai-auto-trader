"""
Model Retrain Scheduler API Routes
Provides endpoints for managing the automatic model retraining schedule.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/model-retrain-scheduler", tags=["Model Retrain Scheduler"])

_scheduler = None
_db = None


def set_dependencies(db, scheduler=None):
    """Set dependencies for the routes"""
    global _db, _scheduler
    _db = db
    _scheduler = scheduler


def get_scheduler():
    """Get or create the scheduler instance"""
    global _scheduler
    if _scheduler is None and _db is not None:
        from services.model_retrain_scheduler import get_retrain_scheduler
        _scheduler = get_retrain_scheduler(_db)
    return _scheduler


class ScheduleConfig(BaseModel):
    enabled: Optional[bool] = None
    run_day: Optional[int] = None  # 0=Monday, 6=Sunday
    run_hour: Optional[int] = None  # 0-23
    run_minute: Optional[int] = None  # 0-59
    retrain_historical: Optional[bool] = None
    retrain_gem_ml_dl: Optional[bool] = None
    retrain_mtf: Optional[bool] = None
    max_coins: Optional[int] = None


@router.get("/status")
async def get_scheduler_status():
    """Get current scheduler status and next run time"""
    scheduler = get_scheduler()
    if not scheduler:
        return {
            "running": False,
            "enabled": True,
            "schedule": {
                "day": "Sunday",
                "time": "03:00 UTC"
            },
            "last_run": None,
            "next_run": None,
            "message": "Scheduler not initialized yet"
        }
    return scheduler.get_status()


@router.post("/start")
async def start_scheduler():
    """Start the retrain scheduler"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    await scheduler.start()
    return {"status": "started", **scheduler.get_status()}


@router.post("/stop")
async def stop_scheduler():
    """Stop the retrain scheduler"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    await scheduler.stop()
    return {"status": "stopped"}


@router.post("/run-now")
async def run_retrain_now(background_tasks: BackgroundTasks):
    """Manually trigger a model retrain right now"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    # Run in background
    background_tasks.add_task(scheduler.run_retrain, True)
    
    return {
        "status": "started",
        "message": "Model retrain started in background",
        "check_progress": "/api/training-progress/active"
    }


@router.put("/config")
async def update_scheduler_config(config: ScheduleConfig):
    """Update scheduler configuration"""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    updates = {k: v for k, v in config.dict().items() if v is not None}
    result = await scheduler.update_config(updates)
    return result


@router.get("/history")
async def get_retrain_history(limit: int = 10):
    """Get history of scheduled retrains"""
    if not _db:
        return {"history": [], "total": 0}
    
    history = await _db.scheduled_retrain_history.find(
        {},
        {"_id": 0}
    ).sort("started_at", -1).limit(limit).to_list(limit)
    
    return {
        "history": history,
        "total": len(history)
    }

"""
Weekly Selection Scheduler API Routes
Manage and monitor the automatic weekly coin selection scheduler.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

router = APIRouter(prefix="/weekly-scheduler", tags=["Weekly Scheduler"])

# Global references (set during app startup)
_scheduler = None
_db = None


def set_dependencies(scheduler, db):
    """Set dependencies from main app"""
    global _scheduler, _db
    _scheduler = scheduler
    _db = db


class SchedulerConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    run_day: Optional[int] = None  # 0=Monday, 6=Sunday
    run_hour: Optional[int] = None
    run_minute: Optional[int] = None
    main_coins_count: Optional[int] = None
    gem_coins_count: Optional[int] = None
    auto_execute: Optional[bool] = None
    paper_trade: Optional[bool] = None
    position_size_pct: Optional[float] = None
    use_isolated_budget: Optional[bool] = None


class ExecuteRequest(BaseModel):
    selection_id: Optional[str] = None
    paper_trade: Optional[bool] = None


@router.get("/status")
async def get_scheduler_status():
    """Get current scheduler status and configuration"""
    if _scheduler is None:
        return {
            "running": False,
            "enabled": False,
            "message": "Scheduler not initialized"
        }
    
    return await _scheduler.get_status()


@router.post("/start")
async def start_scheduler():
    """Start the weekly selection scheduler"""
    if _scheduler is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    await _scheduler.start()
    return {
        "success": True,
        "message": "Scheduler started",
        "status": await _scheduler.get_status()
    }


@router.post("/stop")
async def stop_scheduler():
    """Stop the weekly selection scheduler"""
    if _scheduler is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    await _scheduler.stop()
    return {
        "success": True,
        "message": "Scheduler stopped"
    }


@router.post("/run-now")
async def run_selection_now(background_tasks: BackgroundTasks):
    """Manually trigger coin selection immediately"""
    if _scheduler is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    # Run in background to avoid timeout
    async def run_async():
        return await _scheduler.run_selection(force=True)
    
    result = await _scheduler.run_selection(force=True)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.put("/config")
async def update_config(config: SchedulerConfigUpdate):
    """Update scheduler configuration"""
    if _scheduler is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    updates = config.model_dump(exclude_none=True)
    result = await _scheduler.update_config(updates)
    
    return result


@router.post("/execute")
async def execute_selection(request: ExecuteRequest = None):
    """
    Execute trades for an existing coin selection.
    If no selection_id provided, executes the latest selection.
    """
    if _scheduler is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    selection_id = request.selection_id if request else None
    paper_trade = request.paper_trade if request else None
    
    result = await _scheduler.execute_selection(selection_id, paper_trade)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Execution failed"))
    
    return result


@router.get("/last-execution")
async def get_last_execution():
    """Get the result of the last trade execution"""
    if _scheduler is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    execution = await _scheduler.get_last_execution()
    
    if execution is None:
        return {"message": "No execution yet"}
    
    return execution


@router.get("/latest-selection")
async def get_latest_selection():
    """Get the most recent weekly coin selection"""
    if _scheduler is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    selection = await _scheduler.get_latest_selection()
    
    if selection is None:
        return {"message": "No selection available yet"}
    
    return selection


@router.get("/history")
async def get_selection_history(limit: int = 10):
    """Get history of weekly selections"""
    if _db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    selections = await _db.weekly_selections.find(
        {},
        projection={"_id": 0}
    ).sort([("selection_date", -1)]).limit(limit).to_list(limit)
    
    return {
        "count": len(selections),
        "selections": selections
    }


@router.get("/upcoming")
async def get_upcoming_selection():
    """Get information about the next scheduled selection"""
    if _scheduler is None:
        return {
            "scheduled": False,
            "message": "Scheduler not initialized"
        }
    
    status = await _scheduler.get_status()
    
    return {
        "scheduled": status.get("running", False) and status.get("enabled", False),
        "next_run": status.get("next_run"),
        "config": status.get("config")
    }

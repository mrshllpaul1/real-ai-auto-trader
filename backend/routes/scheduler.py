"""
Scheduler API Routes
Control automated trading schedules.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])

# Global reference
scheduler_service = None


def set_dependencies(service):
    global scheduler_service
    scheduler_service = service


class GrowthExecuteSchedule(BaseModel):
    capital: Optional[float] = 500
    paper_trade: Optional[bool] = True
    interval_hours: Optional[int] = 24


class WeeklyTradeSchedule(BaseModel):
    day_of_week: Optional[str] = 'mon'
    hour: Optional[int] = 8
    paper_trade: Optional[bool] = True


class MonitorSchedule(BaseModel):
    interval_hours: Optional[int] = 1


class CompoundSchedule(BaseModel):
    hour: Optional[int] = 0


class RetrainSchedule(BaseModel):
    day_of_week: Optional[str] = 'mon'
    hour: Optional[int] = 6
    coins: Optional[list] = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot']


@router.get("/status")
async def get_scheduler_status():
    """Get current scheduler status and active jobs"""
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    return scheduler_service.get_status()


@router.post("/start")
async def start_scheduler():
    """Start the scheduler"""
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    await scheduler_service.start()
    return {"success": True, "message": "Scheduler started"}


@router.post("/stop")
async def stop_scheduler():
    """Stop the scheduler"""
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    await scheduler_service.stop()
    return {"success": True, "message": "Scheduler stopped"}


@router.post("/setup-default")
async def setup_default_schedule(paper_trade: bool = True):
    """
    Set up the default passive income schedule:
    - Monitor positions every hour
    - Compound profits daily
    - Weekly trading on Mondays
    """
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    result = await scheduler_service.setup_default_schedule(paper_trade=paper_trade)
    return result


@router.post("/jobs/growth-monitor")
async def add_growth_monitor(schedule: MonitorSchedule):
    """Add job to monitor growth positions periodically"""
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    return await scheduler_service.add_growth_monitor_job(
        interval_hours=schedule.interval_hours
    )


@router.post("/jobs/growth-execute")
async def add_growth_execution(schedule: GrowthExecuteSchedule):
    """Add job to execute growth strategy periodically"""
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    return await scheduler_service.add_growth_execution_job(
        capital=schedule.capital,
        paper_trade=schedule.paper_trade,
        interval_hours=schedule.interval_hours
    )


@router.post("/jobs/weekly-trader")
async def add_weekly_trader(schedule: WeeklyTradeSchedule):
    """Add weekly automated trading job"""
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    return await scheduler_service.add_weekly_trader_job(
        day_of_week=schedule.day_of_week,
        hour=schedule.hour,
        paper_trade=schedule.paper_trade
    )


@router.post("/jobs/compound")
async def add_compound_job(schedule: CompoundSchedule):
    """Add daily profit compounding job"""
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    return await scheduler_service.add_compound_job(hour=schedule.hour)


@router.delete("/jobs/{job_id}")
async def remove_job(job_id: str):
    """Remove a scheduled job"""
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    return await scheduler_service.remove_job(job_id)


@router.post("/jobs/{job_id}/run")
async def run_job_now(job_id: str):
    """Manually trigger a job immediately"""
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    return await scheduler_service.run_job_now(job_id)


@router.get("/history")
async def get_execution_history(limit: int = 50):
    """Get scheduler execution history"""
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    history = await scheduler_service.get_execution_history(limit=limit)
    return {"history": history, "count": len(history)}

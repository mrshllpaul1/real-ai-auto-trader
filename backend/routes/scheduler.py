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
    coins: Optional[list] = None  # None = use all coins from universe


class GemRetrainSchedule(BaseModel):
    day_of_week: Optional[str] = 'sun'
    hour: Optional[int] = 9  # 9 AM UTC = 2 AM MST


class OHLCVUpdateSchedule(BaseModel):
    hour: Optional[int] = 4  # 4 AM UTC
    coins: Optional[list] = None  # None = update all stored coins


class OHLCVExpansionSchedule(BaseModel):
    day_of_week: Optional[str] = 'sun'
    hour: Optional[int] = 4  # 4 AM UTC
    batch_size: Optional[int] = 50


class EventTriggerCheckSchedule(BaseModel):
    interval_minutes: Optional[int] = 15


@router.get("/status")
async def get_scheduler_status():
    """Get current scheduler status and active jobs"""
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    status = scheduler_service.get_status()
    status["scheduled_jobs"] = scheduler_service.get_scheduled_jobs()
    return status


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
    - Compound profits daily at midnight
    - Weekly AI retraining on Mondays at 6 AM UTC
    - Weekly trading on Mondays at 8 AM UTC
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


@router.post("/jobs/weekly-retrain")
async def add_weekly_retrain(schedule: RetrainSchedule):
    """
    Add weekly AI retraining job.
    
    - Runs on Mondays at 6 AM UTC by default (before trading at 8 AM)
    - Trains on ALL 107 coins in the universe by default
    - Uses REAL market data only from Twelve Data API
    - Updates pattern recognition and hidden gem detection
    """
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    return await scheduler_service.add_weekly_retrain_job(
        day_of_week=schedule.day_of_week,
        hour=schedule.hour,
        coins=schedule.coins  # None = all coins
    )


@router.post("/jobs/retrain-now")
async def retrain_now(coins: list = None):
    """
    Trigger AI retraining immediately.
    
    - If coins is None, trains on ALL 107 coins in the universe
    - Runs Historical Trainer (patterns + hidden gems)
    - Runs Enhanced Trainer (technical indicators)
    - Uses REAL market data only
    """
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    result = await scheduler_service._run_weekly_retrain(coins=coins)
    return result


@router.get("/coin-universe")
async def get_coin_universe():
    """Get the full coin universe used for training"""
    from services.dynamic_coin_universe import get_training_coins, get_gem_candidates, CATEGORIES
    
    all_coins = await get_training_coins()
    gems = await get_gem_candidates()
    
    return {
        "total_coins": len(all_coins),
        "gem_candidates": len(gems),
        "coins": all_coins,
        "categories": CATEGORIES
    }


@router.delete("/jobs/{job_id}")
async def remove_job(job_id: str):
    """Remove a scheduled job"""
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    return await scheduler_service.remove_job(job_id)


@router.post("/jobs/gem-predictor-retrain")
async def add_gem_predictor_retrain(schedule: GemRetrainSchedule):
    """
    Add weekly gem predictor retraining job.
    
    Default: Every Sunday at 2 AM MST (9 AM UTC) - while you're sleeping!
    
    - Trains on 15+ years of historical gem data (2009-2026)
    - Updates model weights based on successful gem patterns
    - Improves hidden gem prediction accuracy
    """
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    return await scheduler_service.add_gem_predictor_retrain_job(
        day_of_week=schedule.day_of_week,
        hour=schedule.hour
    )


@router.post("/jobs/gem-predictor-retrain-now")
async def retrain_gem_predictor_now():
    """
    Manually trigger gem predictor retraining immediately.
    
    Runs deep historical training on gem data from 2009-2026.
    """
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    return await scheduler_service.run_job_now('gem_predictor_retrain')


@router.post("/jobs/{job_id}/run")
async def run_job_now(job_id: str):
    """Manually trigger a job immediately"""
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    return await scheduler_service.run_job_now(job_id)


@router.post("/jobs/daily-ohlcv-update")
async def add_daily_ohlcv_update(schedule: OHLCVUpdateSchedule):
    """
    Add daily OHLCV data update job.
    
    Keeps historical data fresh by downloading latest market data daily.
    
    Default: Every day at 4 AM UTC
    
    - Updates all coins currently stored in the database
    - Downloads latest 30 days to capture recent changes
    - Essential for keeping AI training data current
    """
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    return await scheduler_service.add_daily_ohlcv_update_job(
        hour=schedule.hour,
        coins=schedule.coins
    )


@router.post("/jobs/ohlcv-update-now")
async def run_ohlcv_update_now(coins: list = None):
    """
    Manually trigger OHLCV data update immediately.
    
    Updates historical data for all stored coins (or specified list).
    """
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    return await scheduler_service._run_daily_ohlcv_update(coins=coins)


@router.post("/jobs/weekly-ohlcv-expansion")
async def add_weekly_ohlcv_expansion(schedule: OHLCVExpansionSchedule):
    """
    Add weekly OHLCV expansion job to download 50 more coins every Sunday.
    
    Continues until all AI favorite coins (200+) are completed.
    
    Default: Every Sunday at 4 AM UTC
    
    - Downloads next batch of coins not yet in database
    - Automatically stops when all coins are complete
    - Tracks progress and sends alerts
    """
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    return await scheduler_service.add_weekly_ohlcv_expansion_job(
        day_of_week=schedule.day_of_week,
        hour=schedule.hour,
        batch_size=schedule.batch_size
    )


@router.post("/jobs/ohlcv-expansion-now")
async def run_ohlcv_expansion_now(batch_size: int = 50):
    """
    Manually trigger OHLCV expansion immediately.
    
    Downloads the next batch of coins not yet in the database.
    """
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    return await scheduler_service._run_weekly_ohlcv_expansion(batch_size=batch_size)


@router.get("/ohlcv-expansion-status")
async def get_ohlcv_expansion_status():
    """
    Get status of OHLCV expansion progress.
    
    Shows how many AI coins have been downloaded and how many remain.
    """
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    from services.historical_data_downloader import get_historical_downloader
    downloader = get_historical_downloader(scheduler_service.db)
    
    if not downloader:
        raise HTTPException(status_code=500, detail="Downloader not initialized")
    
    return await downloader.get_next_batch_to_download(50)


@router.get("/history")
async def get_execution_history(limit: int = 50):
    """Get scheduler execution history"""
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler not initialized")
    
    history = await scheduler_service.get_execution_history(limit=limit)
    return {"history": history, "count": len(history)}

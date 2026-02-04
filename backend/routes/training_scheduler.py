"""
Training Scheduler API Routes
Endpoints for managing automatic model training schedules
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter(prefix="/training-scheduler", tags=["Training Scheduler"])

# Service reference
_scheduler = None


def set_dependencies(scheduler):
    """Set the training scheduler service dependency"""
    global _scheduler
    _scheduler = scheduler


class CreateScheduleRequest(BaseModel):
    """Request model for creating a training schedule"""
    schedule_id: str
    model_type: str
    schedule_type: str = "cron"  # "cron" or "interval"
    cron_expression: Optional[str] = None  # e.g., "0 2 * * *" for 2 AM daily
    interval_hours: Optional[int] = None
    config: Optional[Dict[str, Any]] = None  # Training config (episodes, etc.)
    enabled: bool = True


class ToggleScheduleRequest(BaseModel):
    """Request model for toggling a schedule"""
    enabled: bool


@router.get("/")
async def get_all_schedules():
    """
    Get all training schedules
    
    Returns list of all configured training schedules with their status
    """
    if not _scheduler:
        raise HTTPException(status_code=503, detail="Training scheduler not initialized")
    
    schedules = await _scheduler.get_schedules()
    
    return {
        "count": len(schedules),
        "schedules": schedules
    }


@router.post("/")
async def create_schedule(request: CreateScheduleRequest):
    """
    Create a new training schedule
    
    Schedule types:
    - cron: Use cron_expression (e.g., "0 2 * * *" for daily at 2 AM)
    - interval: Use interval_hours (e.g., 24 for every 24 hours)
    
    Config options vary by model type:
    - rl_agent: {"episodes": 100}
    - transformer: {"epochs": 10}
    - regime: {}
    """
    if not _scheduler:
        raise HTTPException(status_code=503, detail="Training scheduler not initialized")
    
    # Validate schedule type
    if request.schedule_type == "cron" and not request.cron_expression:
        raise HTTPException(status_code=400, detail="cron_expression required for cron schedule")
    if request.schedule_type == "interval" and not request.interval_hours:
        raise HTTPException(status_code=400, detail="interval_hours required for interval schedule")
    
    result = await _scheduler.add_schedule(
        schedule_id=request.schedule_id,
        model_type=request.model_type,
        schedule_type=request.schedule_type,
        cron_expression=request.cron_expression,
        interval_hours=request.interval_hours,
        config=request.config,
        enabled=request.enabled
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


# ===========================================
# AUTO-SPOT SCAN SCHEDULING ENDPOINTS
# (Must be before /{schedule_id} routes to avoid path conflicts)
# ===========================================

class AutoSpotScanScheduleRequest(BaseModel):
    """Request model for creating auto-spot scan schedule"""
    interval_minutes: int = 60  # How often to scan
    paper_trade: bool = True    # Use paper trading
    enabled: bool = True        # Whether schedule is active


@router.post("/auto-spot-scan")
async def create_auto_spot_scan_schedule(request: AutoSpotScanScheduleRequest):
    """
    Create a scheduled auto-spot scan that runs periodically.
    
    The AI will automatically:
    1. Scan top trading pairs for opportunities
    2. Analyze each with AI signals
    3. Execute trades for strong buy/sell signals
    
    Args:
        interval_minutes: How often to scan (default: 60)
        paper_trade: Whether to simulate trades (default: True)
        enabled: Whether schedule is active (default: True)
    """
    if not _scheduler:
        raise HTTPException(status_code=503, detail="Training scheduler not initialized")
    
    result = await _scheduler.add_auto_spot_scan_schedule(
        interval_minutes=request.interval_minutes,
        paper_trade=request.paper_trade,
        enabled=request.enabled
    )
    
    return result


@router.get("/auto-spot-scan/status")
async def get_auto_spot_scan_status():
    """
    Get status of auto-spot scan schedule.
    
    Returns:
        Schedule status including last run, next run, and results
    """
    if not _scheduler:
        raise HTTPException(status_code=503, detail="Training scheduler not initialized")
    
    return await _scheduler.get_auto_spot_scan_status()


@router.delete("/auto-spot-scan")
async def remove_auto_spot_scan_schedule():
    """Remove the auto-spot scan schedule"""
    if not _scheduler:
        raise HTTPException(status_code=503, detail="Training scheduler not initialized")
    
    # Find and remove the auto-spot scan schedule
    status = await _scheduler.get_auto_spot_scan_status()
    
    if not status.get("schedule_id"):
        return {"status": "not_found", "message": "No auto-spot scan schedule exists"}
    
    result = await _scheduler.remove_schedule(status["schedule_id"])
    return result


@router.post("/auto-spot-scan/toggle")
async def toggle_auto_spot_scan(enabled: bool):
    """Enable or disable the auto-spot scan schedule"""
    if not _scheduler:
        raise HTTPException(status_code=503, detail="Training scheduler not initialized")
    
    status = await _scheduler.get_auto_spot_scan_status()
    
    if not status.get("schedule_id"):
        return {"error": "No auto-spot scan schedule exists. Create one first."}
    
    result = await _scheduler.toggle_schedule(status["schedule_id"], enabled)
    return result


@router.post("/auto-spot-scan/run-now")
async def run_auto_spot_scan_now(paper_trade: bool = True):
    """
    Manually trigger an auto-spot scan right now.
    
    Args:
        paper_trade: Whether to simulate trades (default: True)
    """
    if not _scheduler:
        raise HTTPException(status_code=503, detail="Training scheduler not initialized")
    
    # Import and run directly
    from routes.kraken import _automated_trader
    
    if _automated_trader is None:
        raise HTTPException(status_code=503, detail="Auto trader not initialized")
    
    result = await _automated_trader.auto_spot_scan(paper_trade=paper_trade)
    
    return result


# ===========================================
# INDIVIDUAL SCHEDULE MANAGEMENT
# ===========================================

@router.get("/{schedule_id}")
async def get_schedule(schedule_id: str):
    """Get details of a specific schedule"""
    if not _scheduler:
        raise HTTPException(status_code=503, detail="Training scheduler not initialized")
    
    schedule = await _scheduler.get_schedule(schedule_id)
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    return schedule


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: str):
    """Delete a training schedule"""
    if not _scheduler:
        raise HTTPException(status_code=503, detail="Training scheduler not initialized")
    
    result = await _scheduler.remove_schedule(schedule_id)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: str, request: ToggleScheduleRequest):
    """Enable or disable a schedule"""
    if not _scheduler:
        raise HTTPException(status_code=503, detail="Training scheduler not initialized")
    
    result = await _scheduler.toggle_schedule(schedule_id, request.enabled)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/{schedule_id}/run-now")
async def run_schedule_now(schedule_id: str):
    """Manually trigger a scheduled training immediately"""
    if not _scheduler:
        raise HTTPException(status_code=503, detail="Training scheduler not initialized")
    
    result = await _scheduler.run_now(schedule_id)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/presets/list")
async def get_schedule_presets():
    """Get predefined schedule presets"""
    return {
        "presets": [
            {
                "name": "Daily RL Agent (2 AM)",
                "description": "Train RL agent daily at 2 AM UTC",
                "config": {
                    "schedule_type": "cron",
                    "cron_expression": "0 2 * * *",
                    "model_type": "rl_agent",
                    "config": {"episodes": 100}
                }
            },
            {
                "name": "Daily Transformer (3 AM)",
                "description": "Train Transformer model daily at 3 AM UTC",
                "config": {
                    "schedule_type": "cron",
                    "cron_expression": "0 3 * * *",
                    "model_type": "transformer",
                    "config": {}
                }
            },
            {
                "name": "Weekly Full Training (Sunday 1 AM)",
                "description": "Comprehensive training every Sunday at 1 AM UTC",
                "config": {
                    "schedule_type": "cron",
                    "cron_expression": "0 1 * * 0",
                    "model_type": "rl_agent",
                    "config": {"episodes": 200}
                }
            },
            {
                "name": "Every 6 Hours",
                "description": "Train every 6 hours",
                "config": {
                    "schedule_type": "interval",
                    "interval_hours": 6,
                    "model_type": "rl_agent",
                    "config": {"episodes": 50}
                }
            },
            {
                "name": "Every 12 Hours",
                "description": "Train twice daily",
                "config": {
                    "schedule_type": "interval",
                    "interval_hours": 12,
                    "model_type": "transformer",
                    "config": {}
                }
            }
        ]
    }


@router.get("/model-types/available")
async def get_available_model_types():
    """Get list of model types that can be scheduled"""
    if not _scheduler:
        raise HTTPException(status_code=503, detail="Training scheduler not initialized")
    
    return {
        "model_types": list(_scheduler.training_callbacks.keys()),
        "descriptions": {
            "rl_agent": "Reinforcement Learning Trading Agent - learns optimal trading actions",
            "transformer": "Transformer Predictor - attention-based price prediction",
            "regime": "Market Regime Predictor - detects market conditions"
        }
    }

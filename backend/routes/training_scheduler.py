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

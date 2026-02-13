"""
Background Task API Routes
Monitor and manage long-running operations.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/tasks", tags=["Background Tasks"])

# Global references
_db = None
_task_manager = None


def set_dependencies(database, task_manager):
    """Set dependencies from main app"""
    global _db, _task_manager
    _db = database
    _task_manager = task_manager


class CancelTaskRequest(BaseModel):
    task_id: str


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get status of a specific background task.
    
    Returns:
    - task_id: Unique identifier
    - status: pending/running/completed/failed/cancelled
    - progress: 0-100%
    - message: Current status message
    - result: Task result (if completed)
    - error: Error message (if failed)
    """
    if not _task_manager:
        raise HTTPException(status_code=503, detail="Task manager not initialized")
    
    status = await _task_manager.get_task_status(task_id)
    
    if not status:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return status


@router.get("/active")
async def get_active_tasks():
    """
    Get all currently active (pending or running) tasks.
    """
    if not _task_manager:
        raise HTTPException(status_code=503, detail="Task manager not initialized")
    
    tasks = await _task_manager.get_active_tasks()
    
    return {
        "count": len(tasks),
        "tasks": tasks
    }


@router.get("/history")
async def get_task_history(
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get history of background task executions.
    
    Task types:
    - model_training
    - backtesting
    - data_download
    - universe_expansion
    - gem_scan
    - regime_prediction
    """
    if not _task_manager:
        raise HTTPException(status_code=503, detail="Task manager not initialized")
    
    from services.background_tasks import TaskType
    
    task_type_enum = None
    if task_type:
        try:
            task_type_enum = TaskType(task_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid task type: {task_type}")
    
    history = await _task_manager.get_task_history(task_type_enum, limit)
    
    return {
        "count": len(history),
        "history": history
    }


@router.post("/cancel")
async def cancel_task(request: CancelTaskRequest):
    """
    Cancel a running task.
    
    Note: Only running tasks can be cancelled. Completed/failed tasks cannot be cancelled.
    """
    if not _task_manager:
        raise HTTPException(status_code=503, detail="Task manager not initialized")
    
    success = await _task_manager.cancel_task(request.task_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Task not found or already completed")
    
    return {
        "success": True,
        "message": f"Task {request.task_id} cancellation requested"
    }


@router.delete("/cleanup")
async def cleanup_old_tasks(days: int = Query(7, ge=1, le=90)):
    """
    Clean up old task records from database.
    
    Args:
        days: Remove tasks older than this many days (default: 7)
    """
    if not _task_manager:
        raise HTTPException(status_code=503, detail="Task manager not initialized")
    
    result = await _task_manager.cleanup_old_tasks(days)
    
    return {
        "success": True,
        "deleted_count": result["deleted"],
        "message": f"Removed task records older than {days} days"
    }


@router.get("/timeout-config")
async def get_timeout_config():
    """
    Get default timeout configuration for different task types.
    """
    from services.background_tasks import DEFAULT_TIMEOUTS, TaskType
    
    return {
        "timeouts": {
            task_type.value: timeout 
            for task_type, timeout in DEFAULT_TIMEOUTS.items()
        },
        "note": "Timeouts are in seconds. Custom timeouts can be specified per-task."
    }


# Integration endpoints for triggering long-running tasks with background execution

@router.post("/train/regime-models")
async def trigger_regime_training():
    """
    Trigger regime prediction model training as a background task.
    
    This trains all 8 ML/DL models for market regime prediction.
    Returns immediately with a task_id for tracking progress.
    """
    if not _task_manager or not _db:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    from services.regime_predictor import get_regime_predictor
    from services.background_tasks import TaskType, wrap_with_progress
    
    regime_predictor = get_regime_predictor(_db)
    
    async def train_wrapper(progress_callback=None, **kwargs):
        if progress_callback:
            progress_callback(10, "Loading historical data...")
        result = await regime_predictor.train_models()
        return result
    
    task_id = await _task_manager.submit_task(
        task_type=TaskType.MODEL_TRAINING,
        task_func=train_wrapper,
        task_name="Regime Model Training (8 models)",
        timeout=600  # 10 minutes
    )
    
    return {
        "message": "Training started in background",
        "task_id": task_id,
        "check_status": f"/api/tasks/status/{task_id}"
    }


@router.post("/train/gem-models")
async def trigger_gem_training():
    """
    Trigger gem prediction model training as a background task.
    
    This trains all ML/DL models for hidden gem detection.
    """
    if not _task_manager or not _db:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    from services.gem_ml_dl_predictor import get_gem_prediction_engine
    from services.background_tasks import TaskType
    
    gem_engine = get_gem_prediction_engine(_db)
    
    async def train_wrapper(progress_callback=None, **kwargs):
        if progress_callback:
            progress_callback(10, "Preparing training data...")
        result = await gem_engine.train_models()
        return result
    
    task_id = await _task_manager.submit_task(
        task_type=TaskType.MODEL_TRAINING,
        task_func=train_wrapper,
        task_name="Gem Prediction Model Training (8 models)",
        timeout=600
    )
    
    return {
        "message": "Training started in background",
        "task_id": task_id,
        "check_status": f"/api/tasks/status/{task_id}"
    }


@router.post("/scan/gems")
async def trigger_gem_scan():
    """
    Trigger a full gem scan as a background task.
    """
    if not _task_manager or not _db:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    from services.gem_ml_dl_predictor import get_gem_prediction_engine
    from services.background_tasks import TaskType
    
    gem_engine = get_gem_prediction_engine(_db)
    
    if not gem_engine.is_trained:
        raise HTTPException(status_code=400, detail="Gem models not trained. Train first using /tasks/train/gem-models")
    
    async def scan_wrapper(progress_callback=None, **kwargs):
        if progress_callback:
            progress_callback(10, "Starting gem scan...")
        results = await gem_engine.scan_for_gems()
        return {"gems": results, "count": len(results)}
    
    task_id = await _task_manager.submit_task(
        task_type=TaskType.GEM_SCAN,
        task_func=scan_wrapper,
        task_name="Full Gem Scan (20 coins)",
        timeout=180
    )
    
    return {
        "message": "Gem scan started in background",
        "task_id": task_id,
        "check_status": f"/api/tasks/status/{task_id}"
    }

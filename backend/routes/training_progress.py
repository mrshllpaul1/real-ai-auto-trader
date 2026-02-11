"""
Training Progress API Routes
Provides endpoints for monitoring training progress across all systems.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

from services.training_progress_manager import get_progress_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/training-progress", tags=["Training Progress"])


@router.get("/active")
async def get_active_tasks():
    """Get all currently running training tasks"""
    manager = get_progress_manager()
    tasks = manager.get_active_tasks()
    return {
        "active_count": len(tasks),
        "tasks": tasks
    }


@router.get("/all")
async def get_all_tasks(limit: int = 20):
    """Get all training tasks (recent first)"""
    manager = get_progress_manager()
    tasks = manager.get_all_tasks(limit=limit)
    return {
        "total": len(tasks),
        "tasks": tasks
    }


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a specific training task"""
    manager = get_progress_manager()
    task = manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.post("/cleanup")
async def cleanup_old_tasks(max_age_hours: int = 24):
    """Remove old completed/failed tasks"""
    manager = get_progress_manager()
    manager.cleanup_old_tasks(max_age_hours=max_age_hours)
    return {"message": f"Cleaned up tasks older than {max_age_hours} hours"}

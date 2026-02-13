"""
Training Progress API Routes
Provides endpoints for monitoring training progress across all systems.
Includes WebSocket support for real-time updates.
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Optional
import logging

from services.training_progress_manager import get_progress_manager
from services.websocket_manager import get_ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/training-progress", tags=["Training Progress"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time training progress updates.
    
    Connect to receive live updates for all training tasks.
    Messages are JSON objects with format:
    {
        "type": "progress_update",
        "task_id": "...",
        "task_type": "...",
        "status": "running|completed|failed",
        "progress": 0-100,
        "message": "...",
        "current_item": "...",
        "items_processed": N,
        "total_items": M,
        "timestamp": "ISO datetime"
    }
    """
    ws_manager = get_ws_manager()
    await ws_manager.connect(websocket)
    
    try:
        # Send current active tasks on connect
        progress_manager = get_progress_manager()
        active_tasks = progress_manager.get_active_tasks()
        for task in active_tasks:
            await websocket.send_json({
                "type": "initial_state",
                **task
            })
        
        # Keep connection alive and listen for any messages
        while True:
            try:
                # Wait for any message (ping/pong handling)
                data = await websocket.receive_text()
                # Echo back for ping/pong
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_manager.disconnect(websocket)


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


@router.post("/stop/{task_id}")
async def stop_task(task_id: str, reason: str = "Stopped by user"):
    """Stop a specific training task gracefully"""
    manager = get_progress_manager()
    task = manager.get_task(task_id)
    
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    if task["status"] not in ["running", "pending"]:
        raise HTTPException(status_code=400, detail=f"Task is already {task['status']}")
    
    await manager.stop_task(task_id, reason)
    return {
        "message": f"Task {task_id} stopped",
        "reason": reason,
        "task": manager.get_task(task_id)
    }


@router.post("/stop-all")
async def stop_all_tasks(reason: str = "Stopped all by user"):
    """Stop all running training tasks"""
    manager = get_progress_manager()
    active_tasks = manager.get_active_tasks()
    
    stopped = []
    for task in active_tasks:
        await manager.stop_task(task["task_id"], reason)
        stopped.append(task["task_id"])
    
    return {
        "message": f"Stopped {len(stopped)} tasks",
        "stopped_tasks": stopped
    }


@router.post("/cancel/{task_id}")
async def request_cancel(task_id: str):
    """Request graceful cancellation of a task (will stop at next checkpoint)"""
    manager = get_progress_manager()
    success = await manager.request_cancel(task_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Could not cancel task (may not be running)")
    
    return {
        "message": f"Cancellation requested for {task_id}",
        "note": "Task will stop at the next checkpoint"
    }


@router.get("/check-stuck")
async def check_stuck_tasks():
    """Check for stuck tasks and optionally stop them"""
    manager = get_progress_manager()
    active_tasks = manager.get_active_tasks()
    
    stuck_tasks = []
    for task in active_tasks:
        if manager.is_task_stuck(task["task_id"]):
            stuck_tasks.append({
                "task_id": task["task_id"],
                "task_type": task["task_type"],
                "message": task["message"],
                "last_progress": task.get("current_item", "unknown")
            })
    
    return {
        "stuck_count": len(stuck_tasks),
        "stuck_tasks": stuck_tasks,
        "note": "Use POST /stop/{task_id} to stop stuck tasks"
    }


@router.post("/stop-stuck")
async def stop_stuck_tasks():
    """Automatically stop all stuck tasks"""
    manager = get_progress_manager()
    active_tasks = manager.get_active_tasks()
    
    stopped = []
    for task in active_tasks:
        if manager.is_task_stuck(task["task_id"]):
            await manager.stop_task(task["task_id"], "Automatically stopped - task was stuck")
            stopped.append(task["task_id"])
    
    return {
        "message": f"Stopped {len(stopped)} stuck tasks",
        "stopped_tasks": stopped
    }

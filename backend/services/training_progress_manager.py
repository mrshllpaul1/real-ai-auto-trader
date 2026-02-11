"""
Training Progress Manager
Centralized service for tracking and reporting progress of long-running training tasks.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class TrainingTask:
    """Represents a training task with progress tracking"""
    task_id: str
    task_type: str
    status: str = "pending"  # pending, running, completed, failed, cancelled, stopped
    progress: int = 0  # 0-100
    message: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    steps_completed: int = 0
    total_steps: int = 0
    current_item: str = ""
    items_processed: int = 0
    total_items: int = 0
    cancel_requested: bool = False
    last_progress_time: Optional[datetime] = None
    stuck_threshold_seconds: int = 120  # Consider stuck if no progress for 2 minutes


class TrainingProgressManager:
    """
    Singleton manager for tracking training progress across all systems.
    Provides real-time progress updates via polling or WebSocket.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._tasks: Dict[str, TrainingTask] = {}
        self._callbacks: Dict[str, Callable] = {}
        logger.info("TrainingProgressManager initialized")
    
    def create_task(self, task_id: str, task_type: str, total_items: int = 0, total_steps: int = 0) -> TrainingTask:
        """Create a new training task"""
        task = TrainingTask(
            task_id=task_id,
            task_type=task_type,
            status="pending",
            total_items=total_items,
            total_steps=total_steps
        )
        self._tasks[task_id] = task
        logger.info(f"Created training task: {task_id} ({task_type})")
        return task
    
    async def start_task(self, task_id: str, message: str = "Starting..."):
        """Mark a task as started and broadcast via WebSocket"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.status = "running"
            task.started_at = datetime.now(timezone.utc)
            task.message = message
            task.progress = 0
            logger.info(f"Started task: {task_id}")
            
            # Broadcast via WebSocket
            await self._broadcast_update(task)
    
    async def update_progress(
        self, 
        task_id: str, 
        progress: int = None, 
        message: str = None,
        current_item: str = None,
        items_processed: int = None,
        steps_completed: int = None
    ):
        """Update task progress and broadcast via WebSocket"""
        if task_id not in self._tasks:
            return
        
        task = self._tasks[task_id]
        
        # Update last progress time
        task.last_progress_time = datetime.now(timezone.utc)
        
        if progress is not None:
            task.progress = min(100, max(0, progress))
        if message is not None:
            task.message = message
        if current_item is not None:
            task.current_item = current_item
        if items_processed is not None:
            task.items_processed = items_processed
            # Auto-calculate progress based on items
            if task.total_items > 0:
                task.progress = int((items_processed / task.total_items) * 100)
        if steps_completed is not None:
            task.steps_completed = steps_completed
            # Auto-calculate progress based on steps
            if task.total_steps > 0:
                task.progress = int((steps_completed / task.total_steps) * 100)
        
        # Broadcast via WebSocket
        await self._broadcast_update(task)
    
    async def request_cancel(self, task_id: str) -> bool:
        """Request cancellation of a task"""
        if task_id not in self._tasks:
            return False
        
        task = self._tasks[task_id]
        if task.status != "running":
            return False
        
        task.cancel_requested = True
        task.message = "Cancellation requested..."
        logger.info(f"Cancel requested for task: {task_id}")
        await self._broadcast_update(task)
        return True
    
    def is_cancel_requested(self, task_id: str) -> bool:
        """Check if cancellation was requested for a task"""
        if task_id not in self._tasks:
            return False
        return self._tasks[task_id].cancel_requested
    
    def is_task_stuck(self, task_id: str) -> bool:
        """Check if a task is stuck (no progress for threshold time)"""
        if task_id not in self._tasks:
            return False
        
        task = self._tasks[task_id]
        if task.status != "running" or task.last_progress_time is None:
            return False
        
        elapsed = (datetime.now(timezone.utc) - task.last_progress_time).total_seconds()
        return elapsed > task.stuck_threshold_seconds
    
    async def stop_task(self, task_id: str, reason: str = "Stopped by user"):
        """Stop a task gracefully"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.status = "stopped"
            task.completed_at = datetime.now(timezone.utc)
            task.message = reason
            task.cancel_requested = True
            logger.info(f"Stopped task: {task_id} - {reason}")
            
            # Broadcast via WebSocket
            await self._broadcast_update(task)
    
    async def complete_task(self, task_id: str, result: Dict = None, message: str = "Completed"):
        """Mark a task as completed and broadcast via WebSocket"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.now(timezone.utc)
            task.message = message
            task.result = result
            logger.info(f"Completed task: {task_id}")
            
            # Broadcast via WebSocket
            await self._broadcast_update(task)
    
    async def fail_task(self, task_id: str, error: str):
        """Mark a task as failed and broadcast via WebSocket"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.status = "failed"
            task.completed_at = datetime.now(timezone.utc)
            task.error = error
            task.message = f"Failed: {error}"
            logger.error(f"Failed task: {task_id} - {error}")
            
            # Broadcast via WebSocket
            await self._broadcast_update(task)
    
    async def _broadcast_update(self, task: TrainingTask):
        """Broadcast task update via WebSocket"""
        try:
            from services.websocket_manager import get_ws_manager
            ws_manager = get_ws_manager()
            await ws_manager.send_progress_update(
                task_id=task.task_id,
                task_type=task.task_type,
                progress=task.progress,
                message=task.message,
                current_item=task.current_item,
                items_processed=task.items_processed,
                total_items=task.total_items,
                status=task.status,
                result=task.result
            )
        except Exception as e:
            logger.debug(f"WebSocket broadcast failed (no clients?): {e}")
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task status"""
        if task_id not in self._tasks:
            return None
        
        task = self._tasks[task_id]
        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "status": task.status,
            "progress": task.progress,
            "message": task.message,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "current_item": task.current_item,
            "items_processed": task.items_processed,
            "total_items": task.total_items,
            "steps_completed": task.steps_completed,
            "total_steps": task.total_steps,
            "result": task.result,
            "error": task.error,
            "duration_seconds": (
                (task.completed_at or datetime.now(timezone.utc)) - task.started_at
            ).total_seconds() if task.started_at else 0
        }
    
    def get_active_tasks(self) -> list:
        """Get all active (running) tasks"""
        return [
            self.get_task(task_id) 
            for task_id, task in self._tasks.items() 
            if task.status == "running"
        ]
    
    def get_all_tasks(self, limit: int = 20) -> list:
        """Get all tasks (most recent first)"""
        sorted_tasks = sorted(
            self._tasks.values(),
            key=lambda t: t.started_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True
        )
        return [self.get_task(t.task_id) for t in sorted_tasks[:limit]]
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Remove old completed/failed tasks"""
        cutoff = datetime.now(timezone.utc)
        to_remove = []
        for task_id, task in self._tasks.items():
            if task.status in ("completed", "failed") and task.completed_at:
                age = (cutoff - task.completed_at).total_seconds() / 3600
                if age > max_age_hours:
                    to_remove.append(task_id)
        
        for task_id in to_remove:
            del self._tasks[task_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old training tasks")


# Singleton instance
_progress_manager = None

def get_progress_manager() -> TrainingProgressManager:
    """Get the singleton progress manager"""
    global _progress_manager
    if _progress_manager is None:
        _progress_manager = TrainingProgressManager()
    return _progress_manager

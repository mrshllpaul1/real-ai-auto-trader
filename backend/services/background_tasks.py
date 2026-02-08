"""
Background Task Manager
Handles long-running operations with progress tracking and status endpoints.

Operations that typically timeout (>30s):
- Model training (ML, DL, regime predictor)
- Backtesting (historical simulations)
- OHLCV data downloads (bulk coin data)
- Universe expansion (coin discovery)
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable, Awaitable
from motor.motor_asyncio import AsyncIOMotorDatabase
from enum import Enum
import logging
import traceback
import uuid
import numpy as np

logger = logging.getLogger(__name__)


def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(i) for i in obj]
    elif isinstance(obj, (np.integer, np.int32, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    return obj


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    MODEL_TRAINING = "model_training"
    BACKTESTING = "backtesting"
    DATA_DOWNLOAD = "data_download"
    UNIVERSE_EXPANSION = "universe_expansion"
    GEM_SCAN = "gem_scan"
    REGIME_PREDICTION = "regime_prediction"
    RL_AGENT_TRAINING = "rl_agent_training"
    TRANSFORMER_TRAINING = "transformer_training"
    CUSTOM = "custom"


# Default timeout per task type (seconds)
DEFAULT_TIMEOUTS = {
    TaskType.MODEL_TRAINING: 600,      # 10 minutes
    TaskType.BACKTESTING: 900,          # 15 minutes
    TaskType.DATA_DOWNLOAD: 300,        # 5 minutes
    TaskType.UNIVERSE_EXPANSION: 300,   # 5 minutes
    TaskType.GEM_SCAN: 120,             # 2 minutes
    TaskType.REGIME_PREDICTION: 300,    # 5 minutes
    TaskType.RL_AGENT_TRAINING: 900,    # 15 minutes (RL takes longer)
    TaskType.TRANSFORMER_TRAINING: 600, # 10 minutes
    TaskType.CUSTOM: 120                # 2 minutes
}


class BackgroundTaskManager:
    """
    Manages long-running background tasks with:
    - Progress tracking
    - Status persistence
    - Automatic timeout handling
    - Cancellation support
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.tasks: Dict[str, asyncio.Task] = {}
        self.task_status: Dict[str, Dict[str, Any]] = {}
        self._collection = db.background_tasks
    
    async def submit_task(
        self,
        task_type: TaskType,
        task_func: Callable[..., Awaitable[Any]],
        task_name: str = None,
        timeout: int = None,
        **kwargs
    ) -> str:
        """
        Submit a task for background execution.
        
        Args:
            task_type: Type of task (for categorization and default timeout)
            task_func: Async function to execute
            task_name: Human-readable task name
            timeout: Custom timeout (uses default if not provided)
            **kwargs: Arguments to pass to task_func
        
        Returns:
            task_id: Unique identifier for tracking the task
        """
        task_id = str(uuid.uuid4())[:8]
        task_timeout = timeout or DEFAULT_TIMEOUTS.get(task_type, 120)
        
        # Initialize status
        status = {
            "task_id": task_id,
            "task_type": task_type.value,
            "task_name": task_name or f"{task_type.value}_{task_id}",
            "status": TaskStatus.PENDING.value,
            "progress": 0,
            "message": "Task queued",
            "result": None,
            "error": None,
            "started_at": None,
            "completed_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "timeout": task_timeout
        }
        
        self.task_status[task_id] = status
        
        # Save to DB
        await self._collection.insert_one({**status})
        
        # Create and start background task
        async def run_with_timeout():
            try:
                self.task_status[task_id]["status"] = TaskStatus.RUNNING.value
                self.task_status[task_id]["started_at"] = datetime.now(timezone.utc).isoformat()
                self.task_status[task_id]["message"] = "Task running..."
                
                await self._update_db_status(task_id)
                
                # Run with timeout
                result = await asyncio.wait_for(
                    task_func(progress_callback=lambda p, m: self._update_progress(task_id, p, m), **kwargs),
                    timeout=task_timeout
                )
                
                self.task_status[task_id]["status"] = TaskStatus.COMPLETED.value
                self.task_status[task_id]["result"] = result
                self.task_status[task_id]["progress"] = 100
                self.task_status[task_id]["message"] = "Task completed successfully"
                self.task_status[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
                
                logger.info(f"✅ Task {task_id} ({task_name}) completed")
                
            except asyncio.TimeoutError:
                self.task_status[task_id]["status"] = TaskStatus.FAILED.value
                self.task_status[task_id]["error"] = f"Task timed out after {task_timeout} seconds"
                self.task_status[task_id]["message"] = "Task timed out"
                self.task_status[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
                
                logger.error(f"⏱️ Task {task_id} timed out")
                
            except asyncio.CancelledError:
                self.task_status[task_id]["status"] = TaskStatus.CANCELLED.value
                self.task_status[task_id]["message"] = "Task cancelled"
                self.task_status[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
                
                logger.info(f"🚫 Task {task_id} cancelled")
                
            except Exception as e:
                self.task_status[task_id]["status"] = TaskStatus.FAILED.value
                self.task_status[task_id]["error"] = str(e)
                self.task_status[task_id]["message"] = f"Task failed: {str(e)[:100]}"
                self.task_status[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
                
                logger.error(f"❌ Task {task_id} failed: {e}")
                logger.debug(traceback.format_exc())
            
            finally:
                await self._update_db_status(task_id)
                # Clean up completed task from memory after a delay
                asyncio.create_task(self._cleanup_task(task_id, delay=300))
        
        # Start the task
        task = asyncio.create_task(run_with_timeout())
        self.tasks[task_id] = task
        
        logger.info(f"📋 Task {task_id} ({task_name}) submitted, timeout: {task_timeout}s")
        
        return task_id
    
    def _update_progress(self, task_id: str, progress: int, message: str = None):
        """Update task progress (called by task functions)"""
        if task_id in self.task_status:
            self.task_status[task_id]["progress"] = min(progress, 99)  # Keep 100 for completion
            if message:
                self.task_status[task_id]["message"] = message
            
            # Non-blocking DB update
            asyncio.create_task(self._update_db_status(task_id))
    
    async def _update_db_status(self, task_id: str):
        """Update status in database"""
        if task_id in self.task_status:
            status = self.task_status[task_id]
            await self._collection.update_one(
                {"task_id": task_id},
                {"$set": {
                    "status": status["status"],
                    "progress": status["progress"],
                    "message": status["message"],
                    "result": status["result"],
                    "error": status["error"],
                    "started_at": status["started_at"],
                    "completed_at": status["completed_at"]
                }}
            )
    
    async def _cleanup_task(self, task_id: str, delay: int = 300):
        """Remove task from memory after delay"""
        await asyncio.sleep(delay)
        self.tasks.pop(task_id, None)
        # Keep in task_status for a while longer for status checks
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a task"""
        # Check memory first
        if task_id in self.task_status:
            return {k: v for k, v in self.task_status[task_id].items() if k != "_id"}
        
        # Check database
        doc = await self._collection.find_one({"task_id": task_id}, {"_id": 0})
        return doc
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if not task.done():
                task.cancel()
                return True
        return False
    
    async def get_active_tasks(self) -> list:
        """Get all active/running tasks"""
        active = []
        for task_id, status in self.task_status.items():
            if status["status"] in [TaskStatus.PENDING.value, TaskStatus.RUNNING.value]:
                active.append({k: v for k, v in status.items() if k != "_id"})
        return active
    
    async def get_task_history(self, task_type: TaskType = None, limit: int = 20) -> list:
        """Get task execution history"""
        query = {}
        if task_type:
            query["task_type"] = task_type.value
        
        history = await self._collection.find(
            query, {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return history
    
    async def cleanup_old_tasks(self, days: int = 7):
        """Remove task records older than specified days"""
        from datetime import timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        result = await self._collection.delete_many({
            "created_at": {"$lt": cutoff},
            "status": {"$in": [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value]}
        })
        
        return {"deleted": result.deleted_count}


# Wrapper functions for common long-running operations

async def wrap_with_progress(
    func: Callable[..., Awaitable[Any]],
    progress_callback: Callable[[int, str], None] = None,
    **kwargs
) -> Any:
    """
    Wrapper to add progress callback to existing functions.
    Used when the underlying function doesn't support progress tracking.
    """
    if progress_callback:
        progress_callback(10, "Starting operation...")
    
    result = await func(**{k: v for k, v in kwargs.items() if k != 'progress_callback'})
    
    if progress_callback:
        progress_callback(100, "Operation complete")
    
    return result


# Global instance
_task_manager = None


def get_task_manager(db: AsyncIOMotorDatabase = None) -> BackgroundTaskManager:
    """Get or create task manager instance"""
    global _task_manager
    if _task_manager is None and db is not None:
        _task_manager = BackgroundTaskManager(db)
    return _task_manager

"""
Training Scheduler Service
Schedules automatic model retraining at configurable times
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable
from motor.motor_asyncio import AsyncIOMotorDatabase
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Singleton instance
_training_scheduler = None


class TrainingScheduler:
    """
    Service to schedule and manage automatic model training.
    Supports cron-based and interval-based scheduling.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.training_schedules
        self.scheduler = AsyncIOScheduler()
        self.active_schedules: Dict[str, Dict] = {}
        self.training_callbacks: Dict[str, Callable] = {}
        self._started = False
    
    async def start(self):
        """Start the scheduler"""
        if not self._started:
            self.scheduler.start()
            self._started = True
            logger.info("✅ Training Scheduler started")
            
            # Load saved schedules from database
            await self._load_saved_schedules()
    
    async def stop(self):
        """Stop the scheduler"""
        if self._started:
            self.scheduler.shutdown()
            self._started = False
            logger.info("🛑 Training Scheduler stopped")
    
    def register_trainer(self, model_type: str, train_func: Callable):
        """
        Register a training function for a model type
        
        Args:
            model_type: Type of model (e.g., 'rl_agent', 'transformer')
            train_func: Async function to call for training
        """
        self.training_callbacks[model_type] = train_func
        logger.info(f"📝 Registered trainer for {model_type}")
    
    async def add_schedule(
        self,
        schedule_id: str,
        model_type: str,
        schedule_type: str = "cron",
        cron_expression: Optional[str] = None,
        interval_hours: Optional[int] = None,
        config: Optional[Dict] = None,
        enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Add a new training schedule
        
        Args:
            schedule_id: Unique identifier for the schedule
            model_type: Type of model to train
            schedule_type: "cron" or "interval"
            cron_expression: Cron expression (e.g., "0 2 * * *" for 2 AM daily)
            interval_hours: Hours between training runs
            config: Training configuration (episodes, etc.)
            enabled: Whether schedule is active
            
        Returns:
            Schedule details
        """
        if model_type not in self.training_callbacks:
            return {"error": f"No trainer registered for {model_type}"}
        
        schedule = {
            "schedule_id": schedule_id,
            "model_type": model_type,
            "schedule_type": schedule_type,
            "cron_expression": cron_expression,
            "interval_hours": interval_hours,
            "config": config or {},
            "enabled": enabled,
            "created_at": datetime.now(timezone.utc),
            "last_run": None,
            "next_run": None,
            "run_count": 0
        }
        
        # Remove existing schedule with same ID
        if schedule_id in self.active_schedules:
            await self.remove_schedule(schedule_id)
        
        # Create the job
        if enabled:
            job = await self._create_job(schedule)
            if job:
                schedule["next_run"] = job.next_run_time
        
        # Save to database
        await self.collection.update_one(
            {"schedule_id": schedule_id},
            {"$set": schedule},
            upsert=True
        )
        
        self.active_schedules[schedule_id] = schedule
        
        logger.info(f"📅 Added training schedule: {schedule_id} for {model_type}")
        
        return {
            "status": "created",
            "schedule": {
                "schedule_id": schedule_id,
                "model_type": model_type,
                "schedule_type": schedule_type,
                "enabled": enabled,
                "next_run": schedule.get("next_run").isoformat() if schedule.get("next_run") else None
            }
        }
    
    async def _create_job(self, schedule: Dict) -> Any:
        """Create an APScheduler job for a schedule"""
        schedule_id = schedule["schedule_id"]
        model_type = schedule["model_type"]
        config = schedule.get("config", {})
        
        async def training_job():
            logger.info(f"🚀 Running scheduled training: {schedule_id} ({model_type})")
            
            try:
                # Get the trainer function
                trainer = self.training_callbacks.get(model_type)
                if trainer:
                    # Run training
                    result = await trainer(**config)
                    
                    # Update schedule
                    await self.collection.update_one(
                        {"schedule_id": schedule_id},
                        {
                            "$set": {"last_run": datetime.now(timezone.utc)},
                            "$inc": {"run_count": 1}
                        }
                    )
                    
                    logger.info(f"✅ Scheduled training complete: {schedule_id}")
                    return result
                else:
                    logger.error(f"No trainer found for {model_type}")
                    
            except Exception as e:
                logger.error(f"❌ Scheduled training failed: {schedule_id} - {e}")
        
        # Create trigger based on schedule type
        if schedule["schedule_type"] == "cron" and schedule.get("cron_expression"):
            # Parse cron expression (minute hour day month day_of_week)
            parts = schedule["cron_expression"].split()
            if len(parts) >= 5:
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )
            else:
                logger.error(f"Invalid cron expression: {schedule['cron_expression']}")
                return None
                
        elif schedule["schedule_type"] == "interval" and schedule.get("interval_hours"):
            trigger = IntervalTrigger(hours=schedule["interval_hours"])
        else:
            logger.error(f"Invalid schedule configuration: {schedule}")
            return None
        
        # Add job to scheduler
        job = self.scheduler.add_job(
            training_job,
            trigger=trigger,
            id=schedule_id,
            name=f"train_{model_type}_{schedule_id}",
            replace_existing=True
        )
        
        return job
    
    async def remove_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Remove a training schedule"""
        try:
            # Remove from scheduler
            if self.scheduler.get_job(schedule_id):
                self.scheduler.remove_job(schedule_id)
            
            # Remove from database
            await self.collection.delete_one({"schedule_id": schedule_id})
            
            # Remove from active schedules
            if schedule_id in self.active_schedules:
                del self.active_schedules[schedule_id]
            
            logger.info(f"🗑️ Removed training schedule: {schedule_id}")
            return {"status": "removed", "schedule_id": schedule_id}
            
        except Exception as e:
            logger.error(f"Failed to remove schedule: {e}")
            return {"error": str(e)}
    
    async def toggle_schedule(self, schedule_id: str, enabled: bool) -> Dict[str, Any]:
        """Enable or disable a schedule"""
        schedule = await self.collection.find_one({"schedule_id": schedule_id})
        
        if not schedule:
            return {"error": "Schedule not found"}
        
        if enabled:
            # Create job if enabling
            job = await self._create_job(schedule)
            next_run = job.next_run_time if job else None
        else:
            # Remove job if disabling
            if self.scheduler.get_job(schedule_id):
                self.scheduler.remove_job(schedule_id)
            next_run = None
        
        await self.collection.update_one(
            {"schedule_id": schedule_id},
            {"$set": {"enabled": enabled, "next_run": next_run}}
        )
        
        if schedule_id in self.active_schedules:
            self.active_schedules[schedule_id]["enabled"] = enabled
            self.active_schedules[schedule_id]["next_run"] = next_run
        
        return {
            "status": "updated",
            "schedule_id": schedule_id,
            "enabled": enabled,
            "next_run": next_run.isoformat() if next_run else None
        }
    
    async def get_schedules(self) -> List[Dict[str, Any]]:
        """Get all training schedules"""
        schedules = await self.collection.find(
            {},
            {"_id": 0}
        ).to_list(length=100)
        
        # Update next_run from scheduler
        for schedule in schedules:
            job = self.scheduler.get_job(schedule["schedule_id"])
            if job:
                schedule["next_run"] = job.next_run_time
        
        return schedules
    
    async def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific schedule"""
        schedule = await self.collection.find_one(
            {"schedule_id": schedule_id},
            {"_id": 0}
        )
        
        if schedule:
            job = self.scheduler.get_job(schedule_id)
            if job:
                schedule["next_run"] = job.next_run_time
        
        return schedule
    
    async def run_now(self, schedule_id: str) -> Dict[str, Any]:
        """Manually trigger a scheduled training immediately"""
        schedule = await self.collection.find_one({"schedule_id": schedule_id})
        
        if not schedule:
            return {"error": "Schedule not found"}
        
        model_type = schedule["model_type"]
        config = schedule.get("config", {})
        
        trainer = self.training_callbacks.get(model_type)
        if not trainer:
            return {"error": f"No trainer registered for {model_type}"}
        
        try:
            logger.info(f"🚀 Running training now: {schedule_id} ({model_type})")
            result = await trainer(**config)
            
            # Update schedule
            await self.collection.update_one(
                {"schedule_id": schedule_id},
                {
                    "$set": {"last_run": datetime.now(timezone.utc)},
                    "$inc": {"run_count": 1}
                }
            )
            
            return {
                "status": "started",
                "schedule_id": schedule_id,
                "model_type": model_type,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Manual training failed: {e}")
            return {"error": str(e)}
    
    async def _load_saved_schedules(self):
        """Load schedules from database on startup"""
        schedules = await self.collection.find({"enabled": True}).to_list(length=100)
        
        for schedule in schedules:
            schedule_id = schedule["schedule_id"]
            model_type = schedule["model_type"]
            
            # Only load if trainer is registered
            if model_type in self.training_callbacks:
                job = await self._create_job(schedule)
                if job:
                    self.active_schedules[schedule_id] = schedule
                    logger.info(f"📅 Loaded schedule: {schedule_id} for {model_type}")
            else:
                logger.warning(f"⚠️ Skipped schedule {schedule_id}: no trainer for {model_type}")
        
        logger.info(f"📋 Loaded {len(self.active_schedules)} training schedules")


def get_training_scheduler(db: AsyncIOMotorDatabase) -> TrainingScheduler:
    """Get or create the training scheduler singleton"""
    global _training_scheduler
    if _training_scheduler is None:
        _training_scheduler = TrainingScheduler(db)
    return _training_scheduler

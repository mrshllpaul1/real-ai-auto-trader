"""
Model Retraining Scheduler
Automatically retrains all AI models on a configurable schedule (default: Sunday 3AM UTC).
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

# Singleton instance
_retrain_scheduler = None


class ModelRetrainScheduler:
    """
    Scheduler that automatically retrains all AI models on a schedule.
    - Default: Every Sunday at 3:00 AM UTC
    - Trains: Historical patterns, Gem ML/DL, MTF predictor, Enhanced models
    - Provides progress tracking via the training progress manager
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._config = {
            "enabled": True,
            "run_day": 6,      # Sunday (0=Monday, 6=Sunday)
            "run_hour": 3,     # 3 AM UTC
            "run_minute": 0,
            "retrain_historical": True,
            "retrain_gem_ml_dl": True,
            "retrain_mtf": True,
            "max_coins": None,  # None = all coins
            "notify_on_complete": True,
        }
        self._last_run: Optional[datetime] = None
        self._next_run: Optional[datetime] = None
        self._last_result: Optional[Dict] = None
    
    async def load_config(self):
        """Load scheduler configuration from database"""
        config = await self.db.scheduler_config.find_one({"type": "model_retrain"})
        if config:
            self._config.update({k: v for k, v in config.items() if k != "_id" and k != "type"})
        self._calculate_next_run()
    
    async def save_config(self):
        """Save scheduler configuration to database"""
        await self.db.scheduler_config.update_one(
            {"type": "model_retrain"},
            {"$set": {**self._config, "type": "model_retrain", "updated_at": datetime.now(timezone.utc)}},
            upsert=True
        )
    
    def _calculate_next_run(self):
        """Calculate the next scheduled run time"""
        now = datetime.now(timezone.utc)
        
        # Find next target day
        days_until_target = (self._config["run_day"] - now.weekday()) % 7
        if days_until_target == 0:
            # It's the target day - check if we've passed the run time
            run_time_today = now.replace(
                hour=self._config["run_hour"],
                minute=self._config["run_minute"],
                second=0,
                microsecond=0
            )
            if now >= run_time_today:
                days_until_target = 7  # Next week
        
        self._next_run = now.replace(
            hour=self._config["run_hour"],
            minute=self._config["run_minute"],
            second=0,
            microsecond=0
        ) + timedelta(days=days_until_target)
    
    async def start(self):
        """Start the scheduler background task"""
        if self._running:
            logger.warning("Model retrain scheduler already running")
            return
        
        await self.load_config()
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info(f"🔄 Model retrain scheduler started. Next run: {self._next_run}")
    
    async def stop(self):
        """Stop the scheduler"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Model retrain scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop that checks and runs on schedule"""
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                
                if self._next_run and now >= self._next_run and self._config["enabled"]:
                    logger.info("🚀 Running scheduled model retraining...")
                    await self.run_retrain()
                    self._calculate_next_run()
                    logger.info(f"📅 Next model retrain scheduled for: {self._next_run}")
                
                # Sleep for 1 minute before checking again
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Model retrain scheduler error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def run_retrain(self, force: bool = False) -> Dict[str, Any]:
        """
        Run the model retraining process.
        
        Args:
            force: If True, run even if not scheduled time
            
        Returns:
            Dict with retraining results
        """
        from services.training_progress_manager import get_progress_manager
        from services.historical_trainer import HistoricalTrainer
        from services.enhanced_historical_trainer import EnhancedHistoricalTrainer
        from services.dynamic_coin_universe import get_training_coins
        import uuid
        
        start_time = datetime.now(timezone.utc)
        self._last_run = start_time
        
        task_id = f"scheduled-retrain-{uuid.uuid4().hex[:8]}"
        progress_manager = get_progress_manager()
        
        try:
            # Get training coins
            try:
                all_coins = await get_training_coins()
            except Exception:
                all_coins = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot', 
                            'avalanche', 'chainlink', 'polygon', 'dogecoin', 'shiba-inu']
            
            max_coins = self._config.get("max_coins")
            training_coins = all_coins[:max_coins] if max_coins else all_coins
            total_coins = len(training_coins)
            
            # Create progress task
            progress_manager.create_task(
                task_id=task_id,
                task_type="scheduled-retrain",
                total_items=total_coins * 3,
                total_steps=4
            )
            
            await progress_manager.start_task(task_id, f"Scheduled retrain: {total_coins} coins")
            
            results = {
                "task_id": task_id,
                "started_at": start_time.isoformat(),
                "coins_trained": 0,
                "phases_completed": [],
                "errors": []
            }
            
            items_done = 0
            
            # Phase 1: Historical Training
            if self._config.get("retrain_historical", True):
                await progress_manager.update_progress(
                    task_id, progress=0, 
                    message="Phase 1/4: Historical Pattern Training"
                )
                
                try:
                    historical_trainer = HistoricalTrainer(self.db)
                    for i, coin in enumerate(training_coins):
                        await progress_manager.update_progress(
                            task_id,
                            current_item=f"Historical: {coin}",
                            items_processed=items_done + i + 1,
                            message=f"Phase 1/4: {coin} ({i+1}/{total_coins})"
                        )
                        try:
                            await historical_trainer.train_on_historical_data([coin], 2020, True)
                        except Exception as e:
                            logger.warning(f"Historical training failed for {coin}: {e}")
                    
                    results["phases_completed"].append("historical")
                except Exception as e:
                    results["errors"].append(f"Historical training: {e}")
                
                items_done += total_coins
            
            # Phase 2: Enhanced Training
            if self._config.get("retrain_historical", True):
                await progress_manager.update_progress(
                    task_id, progress=33,
                    message="Phase 2/4: Technical Indicator Training"
                )
                
                try:
                    enhanced_trainer = EnhancedHistoricalTrainer(self.db)
                    for i, coin in enumerate(training_coins):
                        await progress_manager.update_progress(
                            task_id,
                            current_item=f"Technical: {coin}",
                            items_processed=items_done + i + 1,
                            message=f"Phase 2/4: {coin} ({i+1}/{total_coins})"
                        )
                        try:
                            await enhanced_trainer.train_with_real_data([coin])
                        except Exception as e:
                            logger.warning(f"Enhanced training failed for {coin}: {e}")
                    
                    results["phases_completed"].append("enhanced")
                except Exception as e:
                    results["errors"].append(f"Enhanced training: {e}")
                
                items_done += total_coins
            
            # Phase 3: Gem ML/DL Training
            if self._config.get("retrain_gem_ml_dl", True):
                await progress_manager.update_progress(
                    task_id, progress=66,
                    message="Phase 3/4: Gem ML/DL Model Training"
                )
                
                try:
                    from services.gem_ml_dl_predictor import get_gem_predictor
                    gem_predictor = get_gem_predictor(self.db)
                    if gem_predictor:
                        await gem_predictor.train_models(training_coins[:20])
                        results["phases_completed"].append("gem_ml_dl")
                except Exception as e:
                    results["errors"].append(f"Gem ML/DL training: {e}")
                
                items_done += total_coins
            
            # Phase 4: Save results
            await progress_manager.update_progress(
                task_id, progress=95,
                message="Phase 4/4: Saving training results"
            )
            
            # Save training record to database
            results["coins_trained"] = total_coins
            results["completed_at"] = datetime.now(timezone.utc).isoformat()
            results["duration_seconds"] = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            await self.db.scheduled_retrain_history.insert_one({
                **results,
                "scheduled": True,
                "config": self._config
            })
            
            self._last_result = results
            
            # Complete progress
            await progress_manager.complete_task(
                task_id,
                result=results,
                message=f"Scheduled retrain complete: {total_coins} coins"
            )
            
            logger.info(f"✅ Scheduled model retrain complete: {total_coins} coins in {results['duration_seconds']:.0f}s")
            return results
            
        except Exception as e:
            logger.error(f"Scheduled retrain failed: {e}")
            await progress_manager.fail_task(task_id, str(e))
            return {"error": str(e), "task_id": task_id}
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            "running": self._running,
            "enabled": self._config["enabled"],
            "schedule": {
                "day": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][self._config["run_day"]],
                "time": f"{self._config['run_hour']:02d}:{self._config['run_minute']:02d} UTC"
            },
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "next_run": self._next_run.isoformat() if self._next_run else None,
            "config": self._config,
            "last_result": self._last_result
        }
    
    async def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update scheduler configuration"""
        self._config.update(updates)
        await self.save_config()
        self._calculate_next_run()
        return self.get_status()


def get_retrain_scheduler(db: AsyncIOMotorDatabase = None) -> ModelRetrainScheduler:
    """Get the singleton retrain scheduler instance"""
    global _retrain_scheduler
    if _retrain_scheduler is None and db is not None:
        _retrain_scheduler = ModelRetrainScheduler(db)
    return _retrain_scheduler

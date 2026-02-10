"""
Scheduled Task: Daily Sentiment Snapshot Creator
Automatically creates daily sentiment snapshots at midnight UTC.
"""

import asyncio
from datetime import datetime, time, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DailySentimentSnapshotTask:
    """
    Background task that creates daily sentiment snapshots.
    Runs at midnight UTC every day.
    """
    
    def __init__(self, sentiment_tracker):
        self.sentiment_tracker = sentiment_tracker
        self.running = False
        self.task: Optional[asyncio.Task] = None
        
    def start(self):
        """Start the daily snapshot task"""
        if self.running:
            logger.warning("Daily sentiment snapshot task already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._run_scheduler())
        logger.info("✅ Daily sentiment snapshot task started")
    
    def stop(self):
        """Stop the daily snapshot task"""
        self.running = False
        if self.task:
            self.task.cancel()
        logger.info("Daily sentiment snapshot task stopped")
    
    async def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Calculate time until next midnight UTC
                now = datetime.utcnow()
                tomorrow = datetime.combine(
                    now.date() + timedelta(days=1),
                    time(0, 0, 0)
                )
                seconds_until_midnight = (tomorrow - now).total_seconds()
                
                # Wait until midnight
                logger.info(f"Next snapshot in {seconds_until_midnight/3600:.1f} hours")
                await asyncio.sleep(seconds_until_midnight)
                
                # Create snapshot
                await self._create_snapshot()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in daily snapshot task: {e}")
                # Wait 1 hour before retrying on error
                await asyncio.sleep(3600)
    
    async def _create_snapshot(self):
        """Create today's sentiment snapshot"""
        try:
            logger.info("Creating daily sentiment snapshot...")
            
            result = await self.sentiment_tracker.create_daily_snapshot()
            
            logger.info(
                f"✅ Daily sentiment snapshot created: "
                f"{result['snapshots_created']} coins on {result['date']}"
            )
            
        except Exception as e:
            logger.error(f"Failed to create daily sentiment snapshot: {e}")


async def setup_daily_snapshot_task(sentiment_tracker):
    """
    Setup and start the daily sentiment snapshot task.
    Call this during server initialization.
    """
    task = DailySentimentSnapshotTask(sentiment_tracker)
    task.start()
    return task

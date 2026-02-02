"""
Scheduler Service
Runs automated trading strategies on a schedule.
Enables truly passive income generation.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Manages scheduled execution of trading strategies.
    Supports both growth engine and regular AI trading.
    """
    
    def __init__(self, db, growth_engine, automated_trader, alert_service=None):
        self.db = db
        self.growth_engine = growth_engine
        self.automated_trader = automated_trader
        self.alert_service = alert_service
        
        # Initialize scheduler
        self.scheduler = AsyncIOScheduler(timezone='UTC')
        
        # Job tracking
        self.active_jobs = {}
        self.execution_history = []
        
        # Default schedules
        self.default_schedules = {
            'growth_monitor': {
                'trigger': 'interval',
                'hours': 1,
                'description': 'Monitor growth positions hourly'
            },
            'growth_scan': {
                'trigger': 'interval',
                'hours': 4,
                'description': 'Scan for new growth opportunities every 4 hours'
            },
            'weekly_rebalance': {
                'trigger': 'cron',
                'day_of_week': 'mon',
                'hour': 8,
                'description': 'Weekly portfolio rebalance on Mondays at 8 AM UTC'
            },
            'daily_compound': {
                'trigger': 'cron',
                'hour': 0,
                'description': 'Compound profits daily at midnight UTC'
            }
        }
    
    async def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Scheduler started")
            
            # Log to DB
            await self.db.scheduler_events.insert_one({
                'event': 'SCHEDULER_STARTED',
                'timestamp': datetime.utcnow().isoformat()
            })
    
    async def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("⏹️ Scheduler stopped")
            
            await self.db.scheduler_events.insert_one({
                'event': 'SCHEDULER_STOPPED',
                'timestamp': datetime.utcnow().isoformat()
            })
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        jobs = []
        try:
            for job in self.scheduler.get_jobs():
                try:
                    next_run = getattr(job, 'next_run_time', None)
                    jobs.append({
                        'id': job.id,
                        'name': getattr(job, 'name', job.id),
                        'next_run': next_run.isoformat() if next_run else None,
                        'trigger': str(job.trigger) if hasattr(job, 'trigger') else 'unknown'
                    })
                except Exception as e:
                    logger.warning(f"Error getting job info: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error getting scheduler jobs: {e}")
        
        return {
            'running': self.scheduler.running,
            'jobs': jobs,
            'job_count': len(jobs)
        }
    
    async def add_growth_monitor_job(self, interval_hours: int = 1) -> Dict[str, Any]:
        """Add job to monitor growth positions"""
        job_id = 'growth_monitor'
        
        # Remove existing job if present
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        # Add new job
        self.scheduler.add_job(
            self._run_growth_monitor,
            trigger=IntervalTrigger(hours=interval_hours),
            id=job_id,
            name='Growth Position Monitor',
            replace_existing=True
        )
        
        self.active_jobs[job_id] = {
            'type': 'growth_monitor',
            'interval_hours': interval_hours,
            'created_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"📊 Growth monitor job added (every {interval_hours}h)")
        return {'success': True, 'job_id': job_id, 'interval_hours': interval_hours}
    
    async def add_growth_execution_job(
        self,
        capital: float = 500,
        paper_trade: bool = True,
        interval_hours: int = 24
    ) -> Dict[str, Any]:
        """Add job to execute growth strategy periodically"""
        job_id = 'growth_execute'
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        self.scheduler.add_job(
            self._run_growth_execution,
            trigger=IntervalTrigger(hours=interval_hours),
            id=job_id,
            name='Growth Strategy Execution',
            kwargs={'capital': capital, 'paper_trade': paper_trade},
            replace_existing=True
        )
        
        self.active_jobs[job_id] = {
            'type': 'growth_execute',
            'capital': capital,
            'paper_trade': paper_trade,
            'interval_hours': interval_hours,
            'created_at': datetime.utcnow().isoformat()
        }
        
        mode = 'PAPER' if paper_trade else 'REAL'
        logger.info(f"🚀 Growth execution job added (${capital} {mode} every {interval_hours}h)")
        return {'success': True, 'job_id': job_id, 'capital': capital, 'mode': mode}
    
    async def add_compound_job(self, hour: int = 0) -> Dict[str, Any]:
        """Add daily profit compounding job"""
        job_id = 'daily_compound'
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        self.scheduler.add_job(
            self._run_compound,
            trigger=CronTrigger(hour=hour),
            id=job_id,
            name='Daily Profit Compounding',
            replace_existing=True
        )
        
        self.active_jobs[job_id] = {
            'type': 'compound',
            'hour': hour,
            'created_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"💰 Compound job added (daily at {hour}:00 UTC)")
        return {'success': True, 'job_id': job_id, 'hour': hour}
    
    async def add_weekly_trader_job(
        self,
        day_of_week: str = 'mon',
        hour: int = 8,
        paper_trade: bool = True
    ) -> Dict[str, Any]:
        """Add weekly automated trading job"""
        job_id = 'weekly_trader'
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        self.scheduler.add_job(
            self._run_weekly_trade,
            trigger=CronTrigger(day_of_week=day_of_week, hour=hour),
            id=job_id,
            name='Weekly Automated Trading',
            kwargs={'paper_trade': paper_trade},
            replace_existing=True
        )
        
        self.active_jobs[job_id] = {
            'type': 'weekly_trader',
            'day_of_week': day_of_week,
            'hour': hour,
            'paper_trade': paper_trade,
            'created_at': datetime.utcnow().isoformat()
        }
        
        mode = 'PAPER' if paper_trade else 'REAL'
        logger.info(f"📅 Weekly trader job added ({day_of_week} at {hour}:00 UTC, {mode})")
        return {'success': True, 'job_id': job_id, 'schedule': f'{day_of_week} at {hour}:00 UTC'}
    
    async def remove_job(self, job_id: str) -> Dict[str, Any]:
        """Remove a scheduled job"""
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            self.active_jobs.pop(job_id, None)
            logger.info(f"❌ Job removed: {job_id}")
            return {'success': True, 'removed': job_id}
        return {'success': False, 'error': f'Job {job_id} not found'}
    
    async def run_job_now(self, job_id: str) -> Dict[str, Any]:
        """Manually trigger a job immediately"""
        job = self.scheduler.get_job(job_id)
        if job:
            # Run the job function directly
            if job_id == 'growth_monitor':
                result = await self._run_growth_monitor()
            elif job_id == 'growth_execute':
                result = await self._run_growth_execution()
            elif job_id == 'daily_compound':
                result = await self._run_compound()
            elif job_id == 'weekly_trader':
                result = await self._run_weekly_trade()
            else:
                return {'success': False, 'error': 'Unknown job type'}
            
            return {'success': True, 'job_id': job_id, 'result': result}
        return {'success': False, 'error': f'Job {job_id} not found'}
    
    # ========== Job Execution Functions ==========
    
    async def _run_growth_monitor(self) -> Dict[str, Any]:
        """Execute growth position monitoring"""
        timestamp = datetime.utcnow()
        logger.info(f"⏰ [{timestamp.strftime('%H:%M')}] Running growth monitor...")
        
        try:
            result = await self.growth_engine.monitor_positions()
            
            # Record execution
            execution = {
                'job_id': 'growth_monitor',
                'timestamp': timestamp.isoformat(),
                'success': True,
                'result': {
                    'checked': result.get('checked', 0),
                    'stop_losses': len(result.get('stop_losses_hit', [])),
                    'take_profits': len(result.get('take_profits_hit', [])),
                    'trailing_updated': result.get('trailing_stops_updated', 0)
                }
            }
            await self.db.scheduler_executions.insert_one(execution)
            
            # Send alerts if positions closed
            sl_count = len(result.get('stop_losses_hit', []))
            tp_count = len(result.get('take_profits_hit', []))
            
            if (sl_count > 0 or tp_count > 0) and self.alert_service:
                await self.alert_service.send_alert(
                    title="📊 Position Update",
                    message=f"Stop Losses: {sl_count} | Take Profits: {tp_count}",
                    alert_type="position_update",
                    priority="normal"
                )
            
            logger.info(f"  ✅ Monitor complete: {result.get('checked', 0)} checked, SL:{sl_count}, TP:{tp_count}")
            return result
            
        except Exception as e:
            logger.error(f"  ❌ Growth monitor error: {e}")
            await self.db.scheduler_executions.insert_one({
                'job_id': 'growth_monitor',
                'timestamp': timestamp.isoformat(),
                'success': False,
                'error': str(e)
            })
            return {'error': str(e)}
    
    async def _run_growth_execution(
        self,
        capital: float = 500,
        paper_trade: bool = True
    ) -> Dict[str, Any]:
        """Execute growth strategy"""
        timestamp = datetime.utcnow()
        mode = 'PAPER' if paper_trade else 'REAL'
        logger.info(f"🚀 [{timestamp.strftime('%H:%M')}] Running growth execution (${capital} {mode})...")
        
        try:
            result = await self.growth_engine.execute_growth_strategy(
                capital=capital,
                paper_trade=paper_trade
            )
            
            execution = {
                'job_id': 'growth_execute',
                'timestamp': timestamp.isoformat(),
                'success': result.get('success', False),
                'capital': capital,
                'paper_trade': paper_trade,
                'trades': result.get('execution', {}).get('total_trades', 0)
            }
            await self.db.scheduler_executions.insert_one(execution)
            
            if result.get('success') and self.alert_service:
                trades = result.get('execution', {}).get('total_trades', 0)
                await self.alert_service.send_alert(
                    title="🚀 Growth Strategy Executed",
                    message=f"Deployed ${capital} in {mode} mode\n{trades} trades opened",
                    alert_type="execution",
                    priority="normal"
                )
            
            logger.info(f"  ✅ Execution complete: {result.get('execution', {}).get('total_trades', 0)} trades")
            return result
            
        except Exception as e:
            logger.error(f"  ❌ Growth execution error: {e}")
            await self.db.scheduler_executions.insert_one({
                'job_id': 'growth_execute',
                'timestamp': timestamp.isoformat(),
                'success': False,
                'error': str(e)
            })
            return {'error': str(e)}
    
    async def _run_compound(self) -> Dict[str, Any]:
        """Execute profit compounding"""
        timestamp = datetime.utcnow()
        logger.info(f"💰 [{timestamp.strftime('%H:%M')}] Running profit compounding...")
        
        try:
            result = await self.growth_engine.compound_profits()
            
            execution = {
                'job_id': 'daily_compound',
                'timestamp': timestamp.isoformat(),
                'success': True,
                'compounded': result.get('compounded', False),
                'amount': result.get('amount', 0)
            }
            await self.db.scheduler_executions.insert_one(execution)
            
            if result.get('compounded') and self.alert_service:
                await self.alert_service.send_alert(
                    title="💰 Profits Compounded",
                    message=f"Reinvested ${result.get('amount', 0):.2f}\n{result.get('trades', 0)} new trades",
                    alert_type="compound",
                    priority="normal"
                )
            
            logger.info(f"  ✅ Compound complete: {'Compounded' if result.get('compounded') else 'No profits to compound'}")
            return result
            
        except Exception as e:
            logger.error(f"  ❌ Compound error: {e}")
            return {'error': str(e)}
    
    async def _run_weekly_trade(self, paper_trade: bool = True) -> Dict[str, Any]:
        """Execute weekly automated trading"""
        timestamp = datetime.utcnow()
        mode = 'PAPER' if paper_trade else 'REAL'
        logger.info(f"📅 [{timestamp.strftime('%H:%M')}] Running weekly trade ({mode})...")
        
        try:
            result = await self.automated_trader.execute_weekly_trades(paper_trade=paper_trade)
            
            execution = {
                'job_id': 'weekly_trader',
                'timestamp': timestamp.isoformat(),
                'success': result.get('success', False),
                'paper_trade': paper_trade,
                'trades': len(result.get('trades', []))
            }
            await self.db.scheduler_executions.insert_one(execution)
            
            if result.get('success') and self.alert_service:
                await self.alert_service.send_alert(
                    title="📅 Weekly Trades Executed",
                    message=f"{mode}: {len(result.get('trades', []))} trades",
                    alert_type="weekly_trade",
                    priority="normal"
                )
            
            logger.info(f"  ✅ Weekly trade complete: {len(result.get('trades', []))} trades")
            return result
            
        except Exception as e:
            logger.error(f"  ❌ Weekly trade error: {e}")
            return {'error': str(e)}
    
    async def get_execution_history(self, limit: int = 50) -> list:
        """Get recent scheduler execution history"""
        history = await self.db.scheduler_executions.find(
            {}, {'_id': 0}
        ).sort('timestamp', -1).limit(limit).to_list(limit)
        return history
    
    async def setup_default_schedule(self, paper_trade: bool = True) -> Dict[str, Any]:
        """Set up the default passive income schedule"""
        results = {}
        
        # 1. Monitor positions every hour
        results['monitor'] = await self.add_growth_monitor_job(interval_hours=1)
        
        # 2. Compound profits daily at midnight
        results['compound'] = await self.add_compound_job(hour=0)
        
        # 3. Weekly trading on Mondays
        results['weekly'] = await self.add_weekly_trader_job(
            day_of_week='mon',
            hour=8,
            paper_trade=paper_trade
        )
        
        logger.info("📋 Default schedule configured")
        
        return {
            'success': True,
            'jobs_configured': len(results),
            'details': results,
            'message': 'Passive income schedule active!'
        }

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
        
        # AI trainers (set later via set_trainers)
        self.historical_trainer = None
        self.enhanced_trainer = None
        
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
            },
            'weekly_retrain': {
                'trigger': 'cron',
                'day_of_week': 'mon',
                'hour': 6,
                'description': 'Retrain AI models on Mondays at 6 AM UTC'
            }
        }
    
    def set_trainers(self, historical_trainer, enhanced_trainer):
        """Set AI trainers for retraining jobs"""
        self.historical_trainer = historical_trainer
        self.enhanced_trainer = enhanced_trainer
        logger.info("✅ AI trainers configured for scheduler")
    
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
    
    async def add_discovery_job(self, hour: int = 10) -> Dict[str, Any]:
        """Add daily AI discovery job to find new coins"""
        job_id = 'daily_discovery'
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        self.scheduler.add_job(
            self._run_discovery,
            trigger=CronTrigger(hour=hour),
            id=job_id,
            name='Daily AI Discovery',
            replace_existing=True
        )
        
        self.active_jobs[job_id] = {
            'type': 'discovery',
            'hour': hour,
            'created_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"🔍 Discovery job added (daily at {hour}:00 UTC)")
        return {'success': True, 'job_id': job_id, 'hour': hour}
    
    async def add_weekly_retrain_job(
        self,
        day_of_week: str = 'mon',
        hour: int = 6,
        coins: list = None
    ) -> Dict[str, Any]:
        """
        Add weekly AI retraining job.
        Runs every Monday at 6 AM UTC by default (before trading at 8 AM).
        Uses ALL coins from the coin universe for comprehensive training.
        """
        job_id = 'weekly_retrain'
        
        # Use all coins from universe if not specified
        if coins is None:
            from services.dynamic_coin_universe import get_training_coins
            coins = await get_training_coins()
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        self.scheduler.add_job(
            self._run_weekly_retrain,
            trigger=CronTrigger(day_of_week=day_of_week, hour=hour),
            id=job_id,
            name='Weekly AI Retraining',
            kwargs={'coins': coins},
            replace_existing=True
        )
        
        self.active_jobs[job_id] = {
            'type': 'weekly_retrain',
            'day_of_week': day_of_week,
            'hour': hour,
            'coins': coins,
            'coin_count': len(coins),
            'created_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"🧠 Weekly retrain job added ({day_of_week} at {hour}:00 UTC) - {len(coins)} coins")
        return {
            'success': True, 
            'job_id': job_id, 
            'schedule': f'{day_of_week} at {hour}:00 UTC',
            'coin_count': len(coins),
            'coins': coins[:10] if len(coins) > 10 else coins,  # Show first 10 for brevity
            'note': f'Training on {len(coins)} coins from universe' if len(coins) > 10 else None
        }
    
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
            elif job_id == 'weekly_retrain':
                result = await self._run_weekly_retrain()
            elif job_id == 'gem_predictor_retrain':
                result = await self._run_gem_predictor_retrain()
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
    
    async def _run_discovery(self) -> Dict[str, Any]:
        """Execute AI coin discovery scan"""
        timestamp = datetime.utcnow()
        logger.info(f"🔍 [{timestamp.strftime('%H:%M')}] Running AI discovery scan...")
        
        try:
            from services.ai_coin_discovery import get_discovery_service
            discovery_service = get_discovery_service()
            
            if not discovery_service:
                logger.warning("  ⚠️ Discovery service not available")
                return {'error': 'Discovery service not initialized'}
            
            result = await discovery_service.run_discovery_scan()
            
            execution = {
                'job_id': 'daily_discovery',
                'timestamp': timestamp.isoformat(),
                'success': True,
                'candidates_found': result.get('candidates_found', 0),
                'coins_added': result.get('coins_added', []),
                'coins_pending': result.get('coins_pending', [])
            }
            await self.db.scheduler_executions.insert_one(execution)
            
            added = result.get('coins_added', [])
            pending = result.get('coins_pending', [])
            
            if added and self.alert_service:
                await self.alert_service.send_alert(
                    title="🔍 AI Discovery Complete",
                    message=f"Found {result.get('candidates_found', 0)} candidates\nAdded: {', '.join(added) if added else 'None'}",
                    alert_type="discovery",
                    priority="high" if added else "normal"
                )
            
            logger.info(f"  ✅ Discovery complete: {len(added)} added, {len(pending)} pending")
            return result
            
        except Exception as e:
            logger.error(f"  ❌ Discovery error: {e}")
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
    
    async def _run_weekly_retrain(
        self,
        coins: list = None
    ) -> Dict[str, Any]:
        """
        Execute weekly AI retraining with real market data.
        This updates the AI's pattern recognition and hidden gem detection.
        Trains on ALL coins in the universe for comprehensive learning.
        """
        timestamp = datetime.utcnow()
        logger.info(f"🧠 [{timestamp.strftime('%H:%M')}] Running weekly AI retraining...")
        
        # Use all coins from universe if not specified
        if coins is None:
            from services.dynamic_coin_universe import get_training_coins
            coins = await get_training_coins()
        
        logger.info(f"  📊 Training on {len(coins)} coins from universe")
        
        results = {
            'timestamp': timestamp.isoformat(),
            'coins': coins,
            'coin_count': len(coins),
            'historical_trainer': None,
            'enhanced_trainer': None,
            'total_patterns': 0,
            'hidden_gems_found': 0,
            'coins_trained': 0,
            'coins_skipped': 0,
            'success': False
        }
        
        try:
            # Run Historical Trainer
            if self.historical_trainer:
                logger.info(f"  📊 Training Historical Trainer on {len(coins)} coins...")
                hist_result = await self.historical_trainer.train_on_historical_data(
                    coins=coins,
                    start_year=2020,
                    include_hidden_gems=True
                )
                results['historical_trainer'] = {
                    'success': True,
                    'patterns': hist_result.get('total_patterns', 0),
                    'gems': hist_result.get('hidden_gems_found', 0),
                    'accuracy': hist_result.get('training_accuracy', 0)
                }
                results['total_patterns'] += hist_result.get('total_patterns', 0)
                results['hidden_gems_found'] += hist_result.get('hidden_gems_found', 0)
                logger.info(f"    ✅ Historical: {hist_result.get('total_patterns', 0)} patterns, {hist_result.get('hidden_gems_found', 0)} gems")
            
            # Run Enhanced Trainer
            if self.enhanced_trainer:
                logger.info(f"  🎯 Training Enhanced Trainer on {len(coins)} coins...")
                enh_result = await self.enhanced_trainer.train_with_real_data(coins=coins)
                results['enhanced_trainer'] = {
                    'success': True,
                    'patterns': enh_result.get('total_patterns', 0),
                    'gems': enh_result.get('hidden_gems_found', 0),
                    'accuracy': enh_result.get('training_accuracy', 0)
                }
                results['total_patterns'] += enh_result.get('total_patterns', 0)
                results['hidden_gems_found'] += enh_result.get('hidden_gems_found', 0)
                logger.info(f"    ✅ Enhanced: {enh_result.get('total_patterns', 0)} patterns, {enh_result.get('hidden_gems_found', 0)} gems")
            
            results['success'] = True
            
            # Store execution record
            execution = {
                'job_id': 'weekly_retrain',
                'timestamp': timestamp.isoformat(),
                'success': True,
                'coins': coins,
                'total_patterns': results['total_patterns'],
                'hidden_gems_found': results['hidden_gems_found']
            }
            await self.db.scheduler_executions.insert_one(execution)
            
            # Send alert
            if self.alert_service:
                await self.alert_service.send_alert(
                    title="🧠 Weekly AI Retraining Complete",
                    message=f"Trained on {len(coins)} coins\nPatterns: {results['total_patterns']}\nGems Found: {results['hidden_gems_found']}",
                    alert_type="retraining",
                    priority="normal"
                )
            
            logger.info(f"  ✅ Weekly retrain complete: {results['total_patterns']} patterns, {results['hidden_gems_found']} gems")
            return results
            
        except Exception as e:
            logger.error(f"  ❌ Weekly retrain error: {e}")
            
            await self.db.scheduler_executions.insert_one({
                'job_id': 'weekly_retrain',
                'timestamp': timestamp.isoformat(),
                'success': False,
                'error': str(e)
            })
            
            return {'success': False, 'error': str(e)}
    
    async def _run_gem_predictor_retrain(self) -> Dict[str, Any]:
        """
        Execute gem predictor deep historical retraining.
        Uses historical gem data (2009-2026) to update prediction model.
        Scheduled weekly at 2 AM MST (9 AM UTC).
        """
        timestamp = datetime.utcnow()
        logger.info(f"💎 [{timestamp.strftime('%H:%M')}] Running gem predictor deep retraining...")
        
        try:
            # Import and run gem predictor training
            from services.hidden_gem_predictor import get_hidden_gem_predictor
            
            gem_predictor = get_hidden_gem_predictor(self.db, None, None)
            
            if gem_predictor:
                result = await gem_predictor.train_on_historical_deep()
                
                execution = {
                    'job_id': 'gem_predictor_retrain',
                    'timestamp': timestamp.isoformat(),
                    'success': result.get('status') == 'completed',
                    'patterns_discovered': len(result.get('patterns_discovered', [])),
                    'model_accuracy': result.get('model_metrics', {}).get('final_accuracy', 0),
                    'historical_gems': len(result.get('historical_gems', []))
                }
                await self.db.scheduler_executions.insert_one(execution)
                
                # Send alert
                if self.alert_service:
                    await self.alert_service.send_alert(
                        title="💎 Gem Predictor Retrained",
                        message=f"Analyzed {len(result.get('historical_gems', []))} historical gems\nPatterns: {len(result.get('patterns_discovered', []))}\nAccuracy: {result.get('model_metrics', {}).get('final_accuracy', 0):.1f}%",
                        alert_type="gem_retrain",
                        priority="normal"
                    )
                
                logger.info(f"  ✅ Gem predictor retrain complete: {result.get('model_metrics', {}).get('final_accuracy', 0):.1f}% accuracy")
                return result
            else:
                return {'success': False, 'error': 'Gem predictor not available'}
                
        except Exception as e:
            logger.error(f"  ❌ Gem predictor retrain error: {e}")
            
            await self.db.scheduler_executions.insert_one({
                'job_id': 'gem_predictor_retrain',
                'timestamp': timestamp.isoformat(),
                'success': False,
                'error': str(e)
            })
            
            return {'success': False, 'error': str(e)}
    
    async def add_gem_predictor_retrain_job(
        self,
        day_of_week: str = 'sun',
        hour: int = 9  # 9 AM UTC = 2 AM MST
    ) -> Dict[str, Any]:
        """
        Add weekly gem predictor retraining job.
        Default: Every Sunday at 2 AM MST (9 AM UTC)
        """
        job_id = 'gem_predictor_retrain'
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        self.scheduler.add_job(
            self._run_gem_predictor_retrain,
            trigger=CronTrigger(day_of_week=day_of_week, hour=hour),
            id=job_id,
            name='Weekly Gem Predictor Retraining',
            replace_existing=True
        )
        
        self.active_jobs[job_id] = {
            'type': 'gem_predictor_retrain',
            'day_of_week': day_of_week,
            'hour': hour,
            'hour_mst': (hour - 7) % 24,  # Convert UTC to MST
            'created_at': datetime.utcnow().isoformat()
        }
        
        mst_hour = (hour - 7) % 24
        logger.info(f"💎 Gem predictor retrain job added ({day_of_week} at {hour}:00 UTC / {mst_hour}:00 MST)")
        return {
            'success': True, 
            'job_id': job_id, 
            'schedule': f'{day_of_week} at {hour}:00 UTC ({mst_hour}:00 MST)',
            'next_run_utc': f'{day_of_week.capitalize()} at {hour}:00 UTC',
            'next_run_mst': f'{day_of_week.capitalize()} at {mst_hour}:00 MST'
        }
    
    async def add_weekly_ohlcv_expansion_job(
        self,
        day_of_week: str = 'sun',
        hour: int = 4,  # 4 AM UTC
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Add weekly OHLCV expansion job to download 50 more coins every Sunday.
        Continues until all AI favorite coins are completed.
        
        Default: Every Sunday at 4 AM UTC
        """
        job_id = 'weekly_ohlcv_expansion'
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        self.scheduler.add_job(
            self._run_weekly_ohlcv_expansion,
            trigger=CronTrigger(day_of_week=day_of_week, hour=hour),
            id=job_id,
            name='Weekly OHLCV Expansion (50 coins)',
            kwargs={'batch_size': batch_size},
            replace_existing=True
        )
        
        self.active_jobs[job_id] = {
            'type': 'weekly_ohlcv_expansion',
            'day_of_week': day_of_week,
            'hour': hour,
            'batch_size': batch_size,
            'created_at': datetime.utcnow().isoformat()
        }
        
        mst_hour = (hour - 7) % 24
        logger.info(f"📊 Weekly OHLCV expansion job added ({day_of_week} at {hour}:00 UTC / {mst_hour}:00 MST)")
        return {
            'success': True, 
            'job_id': job_id, 
            'schedule': f'{day_of_week} at {hour}:00 UTC ({mst_hour}:00 MST)',
            'batch_size': batch_size,
            'message': f'Will download {batch_size} new coins every {day_of_week.capitalize()} until all AI coins are complete'
        }
    
    async def _run_weekly_ohlcv_expansion(self, batch_size: int = 50) -> Dict[str, Any]:
        """
        Execute weekly OHLCV expansion to download next batch of coins.
        """
        timestamp = datetime.utcnow()
        logger.info(f"📊 [{timestamp.strftime('%H:%M')}] Running weekly OHLCV expansion ({batch_size} coins)...")
        
        try:
            from services.historical_data_downloader import get_historical_downloader
            
            downloader = get_historical_downloader(self.db)
            
            if not downloader:
                logger.warning("  ⚠️ Historical data downloader not available")
                return {'error': 'Downloader not initialized'}
            
            # Download next batch
            result = await downloader.download_next_batch(batch_size=batch_size, max_days=3000)
            
            # Store execution record
            execution = {
                'job_id': 'weekly_ohlcv_expansion',
                'timestamp': timestamp.isoformat(),
                'success': True,
                'batch_size': batch_size,
                'result': {
                    'coins_downloaded': result.get('coins_completed', 0),
                    'records_added': result.get('total_records', 0),
                    'expansion_progress': result.get('expansion_progress', {})
                }
            }
            await self.db.scheduler_executions.insert_one(execution)
            
            progress = result.get('expansion_progress', {})
            
            # Send alert
            if self.alert_service:
                if progress.get('is_complete'):
                    await self.alert_service.send_alert(
                        title="🎉 OHLCV Expansion Complete!",
                        message=f"All {progress.get('coins_downloaded', 0)} AI coins have been downloaded!",
                        alert_type="ohlcv_expansion",
                        priority="high"
                    )
                else:
                    await self.alert_service.send_alert(
                        title="📊 Weekly OHLCV Expansion Complete",
                        message=f"Downloaded {result.get('coins_completed', 0)} coins\nProgress: {progress.get('progress_pct', 0)}%\nRemaining: {progress.get('coins_remaining', 0)} coins",
                        alert_type="ohlcv_expansion",
                        priority="low"
                    )
            
            logger.info(f"  ✅ OHLCV expansion complete: {result.get('coins_completed', 0)} coins, {progress.get('progress_pct', 0)}% total progress")
            
            return result
            
        except Exception as e:
            logger.error(f"  ❌ OHLCV expansion error: {e}")
            
            await self.db.scheduler_executions.insert_one({
                'job_id': 'weekly_ohlcv_expansion',
                'timestamp': timestamp.isoformat(),
                'success': False,
                'error': str(e)
            })
            
            return {'error': str(e)}
    
    async def add_daily_ohlcv_update_job(
        self,
        hour: int = 4,  # 4 AM UTC
        coins: list = None
    ) -> Dict[str, Any]:
        """
        Add daily OHLCV data update job.
        Updates historical data for AI training with latest market data.
        Default: Every day at 4 AM UTC
        """
        job_id = 'daily_ohlcv_update'
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        self.scheduler.add_job(
            self._run_daily_ohlcv_update,
            trigger=CronTrigger(hour=hour),
            id=job_id,
            name='Daily OHLCV Data Update',
            kwargs={'coins': coins},
            replace_existing=True
        )
        
        self.active_jobs[job_id] = {
            'type': 'daily_ohlcv_update',
            'hour': hour,
            'coins': coins,
            'created_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"📊 Daily OHLCV update job added (daily at {hour}:00 UTC)")
        return {
            'success': True, 
            'job_id': job_id, 
            'schedule': f'Daily at {hour}:00 UTC',
            'coins': 'all stored' if not coins else coins
        }
    
    async def _run_daily_ohlcv_update(self, coins: list = None, batch_size: int = 100) -> Dict[str, Any]:
        """
        Execute daily OHLCV data update for ALL coins in database.
        Processes coins in batches to handle the full 500+ coin universe.
        
        Args:
            coins: Optional list of specific coins to update
            batch_size: Number of coins to process per batch (default 100)
        """
        timestamp = datetime.utcnow()
        logger.info(f"📊 [{timestamp.strftime('%H:%M')}] Running daily OHLCV update...")
        
        try:
            from services.coindesk_service import get_cryptocompare_service
            
            crypto_service = get_cryptocompare_service()
            
            if not crypto_service:
                logger.warning("  ⚠️ CryptoCompare service not available")
                return {'error': 'Services not initialized'}
            
            # Get coins to update (from DB or specified)
            if coins:
                coins_to_update = coins
            else:
                # Get all coins currently in the database
                existing_symbols = await self.db.historical_ohlcv.distinct("symbol")
                coins_to_update = existing_symbols if existing_symbols else []
            
            if not coins_to_update:
                logger.info("  ℹ️ No coins to update")
                return {'message': 'No coins to update'}
            
            total_coins = len(coins_to_update)
            logger.info(f"  📊 Updating {total_coins} coins in batches of {batch_size}...")
            
            results = {
                'total_coins': total_coins,
                'coins_updated': 0,
                'coins_failed': 0,
                'new_records': 0,
                'batches_completed': 0,
                'errors': []
            }
            
            # Process ALL coins in batches
            for batch_start in range(0, total_coins, batch_size):
                batch_end = min(batch_start + batch_size, total_coins)
                batch = coins_to_update[batch_start:batch_end]
                batch_num = (batch_start // batch_size) + 1
                total_batches = (total_coins + batch_size - 1) // batch_size
                
                logger.info(f"  📦 Processing batch {batch_num}/{total_batches} ({len(batch)} coins)...")
                
                for coin in batch:
                    try:
                        # Get latest 7 days to update recent data (reduced from 30 to speed up)
                        data = await crypto_service.get_historical_daily(coin, limit=7)
                        
                        if "error" not in data and data.get("data"):
                            # Update/insert new records
                            for candle in data["data"]:
                                await self.db.historical_ohlcv.update_one(
                                    {"symbol": coin.upper(), "date": candle["date"]},
                                    {"$set": {
                                        "symbol": coin.upper(),
                                        "timestamp": candle["timestamp"],
                                        "date": candle["date"],
                                        "open": candle["open"],
                                        "high": candle["high"],
                                        "low": candle["low"],
                                        "close": candle["close"],
                                        "volume_from": candle["volume_from"],
                                        "volume_to": candle["volume_to"],
                                        "source": "cryptocompare",
                                        "updated_at": datetime.utcnow()
                                    }},
                                    upsert=True
                                )
                            results['coins_updated'] += 1
                            results['new_records'] += len(data["data"])
                        else:
                            results['coins_failed'] += 1
                            if len(results['errors']) < 20:  # Limit error list size
                                results['errors'].append({'coin': coin, 'error': data.get('error', 'No data')})
                        
                        # Brief delay to respect rate limits
                        await asyncio.sleep(0.2)
                        
                    except Exception as e:
                        results['coins_failed'] += 1
                        if len(results['errors']) < 20:
                            results['errors'].append({'coin': coin, 'error': str(e)})
                
                results['batches_completed'] += 1
                logger.info(f"    ✓ Batch {batch_num} complete: {results['coins_updated']} updated so far")
                
                # Small pause between batches
                await asyncio.sleep(1)
            
            # Store execution record
            execution = {
                'job_id': 'daily_ohlcv_update',
                'timestamp': timestamp.isoformat(),
                'success': True,
                'total_coins': total_coins,
                'coins_updated': results['coins_updated'],
                'coins_failed': results['coins_failed'],
                'new_records': results['new_records'],
                'batches_completed': results['batches_completed']
            }
            await self.db.scheduler_executions.insert_one(execution)
            
            success_rate = (results['coins_updated'] / total_coins * 100) if total_coins > 0 else 0
            logger.info(f"  ✅ OHLCV update complete: {results['coins_updated']}/{total_coins} coins ({success_rate:.1f}%), {results['new_records']} records")
            
            # Send alert
            if self.alert_service and results['coins_updated'] > 0:
                await self.alert_service.send_alert(
                    title="📊 Daily OHLCV Update Complete",
                    message=f"Updated {results['coins_updated']}/{total_coins} coins ({success_rate:.1f}%)\n{results['new_records']} records added",
                    alert_type="ohlcv_update",
                    priority="low"
                )
            
            return results
            
        except Exception as e:
            logger.error(f"  ❌ OHLCV update error: {e}")
            
            await self.db.scheduler_executions.insert_one({
                'job_id': 'daily_ohlcv_update',
                'timestamp': timestamp.isoformat(),
                'success': False,
                'error': str(e)
            })
            
            return {'error': str(e)}
    
    def get_scheduled_jobs(self) -> Dict[str, Any]:
        """Get all scheduled jobs from APScheduler"""
        jobs = {}
        for job in self.scheduler.get_jobs():
            trigger_info = str(job.trigger)
            jobs[job.id] = {
                'name': job.name,
                'trigger': trigger_info,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            }
        return jobs
    
    async def get_execution_history(self, limit: int = 50) -> list:
        """Get recent scheduler execution history"""
        history = await self.db.scheduler_executions.find(
            {}, {'_id': 0}
        ).sort('timestamp', -1).limit(limit).to_list(limit)
        return history
    
    async def setup_default_schedule(self, paper_trade: bool = True) -> Dict[str, Any]:
        """Set up the default passive income schedule with full universe training"""
        from services.dynamic_coin_universe import get_training_coins
        
        results = {}
        all_coins = await get_training_coins()
        
        # 1. Monitor positions every hour
        results['monitor'] = await self.add_growth_monitor_job(interval_hours=1)
        
        # 2. Compound profits daily at midnight
        results['compound'] = await self.add_compound_job(hour=0)
        
        # 3. Weekly AI retraining on Mondays at 6 AM (before trading) - ALL COINS
        results['retrain'] = await self.add_weekly_retrain_job(
            day_of_week='mon',
            hour=6,
            coins=all_coins
        )
        
        # 4. Weekly trading on Mondays at 8 AM (after retraining)
        results['weekly'] = await self.add_weekly_trader_job(
            day_of_week='mon',
            hour=8,
            paper_trade=paper_trade
        )
        
        # 5. AI Discovery scan daily at 10 AM
        results['discovery'] = await self.add_discovery_job(hour=10)
        
        # 6. Gem Predictor retraining every Sunday at 2 AM MST (9 AM UTC)
        results['gem_retrain'] = await self.add_gem_predictor_retrain_job(
            day_of_week='sun',
            hour=9  # 9 AM UTC = 2 AM MST
        )
        
        # 7. Daily OHLCV data update at 4 AM UTC - keeps all 500+ coins fresh
        results['ohlcv_update'] = await self.add_daily_ohlcv_update_job(hour=4)
        
        # 8. Event trigger checking every 15 minutes
        results['event_triggers'] = await self.add_event_trigger_check_job(interval_minutes=15)
        
        logger.info(f"📋 Default schedule configured (training on {len(all_coins)} coins)")
        
        return {
            'success': True,
            'jobs_configured': len(results),
            'details': results,
            'coin_universe_size': len(all_coins),
            'message': f'Passive income schedule active! AI will retrain on {len(all_coins)} coins every Monday, Gem Predictor retrains Sundays at 2 AM MST, OHLCV updated daily at 4 AM UTC.'
        }


    # ========== Event Trigger Jobs ==========
    
    async def add_event_trigger_check_job(
        self,
        interval_minutes: int = 15
    ) -> Dict[str, Any]:
        """
        Add periodic event trigger checking job.
        Checks news events against all enabled triggers and executes matching actions.
        
        Default: Every 15 minutes
        """
        job_id = 'event_trigger_check'
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        self.scheduler.add_job(
            self._run_event_trigger_check,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=job_id,
            name='Event Trigger Checker',
            replace_existing=True
        )
        
        self.active_jobs[job_id] = {
            'type': 'event_trigger_check',
            'interval_minutes': interval_minutes,
            'created_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"🎯 Event trigger check job added (every {interval_minutes} minutes)")
        return {
            'success': True, 
            'job_id': job_id, 
            'interval_minutes': interval_minutes,
            'message': f'Will check news events every {interval_minutes} minutes against all enabled triggers'
        }
    
    async def _run_event_trigger_check(self) -> Dict[str, Any]:
        """
        Execute event trigger checking.
        Fetches recent news and matches against all enabled triggers.
        """
        timestamp = datetime.utcnow()
        logger.info(f"🎯 [{timestamp.strftime('%H:%M')}] Running event trigger check...")
        
        try:
            from services.event_triggers import get_event_trigger_service
            
            trigger_service = get_event_trigger_service()
            
            if not trigger_service:
                logger.warning("  ⚠️ Event trigger service not available")
                return {'error': 'Trigger service not initialized'}
            
            # Check recent events against triggers
            executions = await trigger_service.check_recent_events()
            
            # Store execution record
            execution = {
                'job_id': 'event_trigger_check',
                'timestamp': timestamp.isoformat(),
                'success': True,
                'triggers_matched': len(executions),
                'executions': [
                    {
                        'trigger_id': e.get('trigger_id'),
                        'action': e.get('action'),
                        'success': e.get('success')
                    } for e in executions
                ]
            }
            await self.db.scheduler_executions.insert_one(execution)
            
            # Send alert if triggers executed
            if executions and self.alert_service:
                successful = sum(1 for e in executions if e.get('success'))
                await self.alert_service.send_alert(
                    title="🎯 Event Triggers Executed",
                    message=f"{len(executions)} trigger(s) matched news events\n{successful} executed successfully",
                    alert_type="event_trigger",
                    priority="high" if any(e.get('action') in ['buy', 'sell'] for e in executions) else "normal"
                )
            
            logger.info(f"  ✅ Trigger check complete: {len(executions)} triggers matched")
            
            return {
                'status': 'checked',
                'triggers_matched': len(executions),
                'executions': executions
            }
            
        except Exception as e:
            logger.error(f"  ❌ Event trigger check error: {e}")
            
            await self.db.scheduler_executions.insert_one({
                'job_id': 'event_trigger_check',
                'timestamp': timestamp.isoformat(),
                'success': False,
                'error': str(e)
            })
            
            return {'error': str(e)}

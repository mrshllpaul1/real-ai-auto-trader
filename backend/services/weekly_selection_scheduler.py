"""
Weekly Coin Selection Scheduler
Automatically runs coin selection every Sunday to pick the best 10 coins + 1 gem
for the upcoming trading week. Can optionally auto-execute trades.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

# Singleton instance
_scheduler_instance = None


class WeeklySelectionScheduler:
    """
    Scheduler that automatically runs coin selection every Sunday.
    - Runs at a configurable time (default: Sunday 00:00 UTC)
    - Selects 10 main coins + 1 gem coin
    - Stores results in database for auto-trading to use
    - Sends notifications/alerts when selection is ready
    - NEW: Can auto-execute trades based on selections
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, coin_selector=None, auto_trader=None):
        self.db = db
        self.coin_selector = coin_selector
        self.auto_trader = auto_trader  # AutomatedWeeklyTrader instance
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._config = {
            "enabled": True,
            "run_day": 6,  # Sunday (0=Monday, 6=Sunday)
            "run_hour": 0,  # UTC hour
            "run_minute": 0,
            "main_coins_count": 10,
            "gem_coins_count": 1,
            "auto_execute": False,  # If True, automatically place trades after selection
            "paper_trade": True,    # If True, use paper trading; False for real trades
            "position_size_pct": 9, # Position size per coin (percentage of budget)
            "use_isolated_budget": True,  # Use isolated budget for trades
        }
        self._last_run: Optional[datetime] = None
        self._next_run: Optional[datetime] = None
        self._last_execution: Optional[Dict] = None
    
    def set_auto_trader(self, auto_trader):
        """Set the auto trader instance (can be set after initialization)"""
        self.auto_trader = auto_trader
        logger.info("✅ Auto trader connected to weekly scheduler")
    
    async def load_config(self):
        """Load scheduler configuration from database"""
        config = await self.db.scheduler_config.find_one({"type": "weekly_selection"})
        if config:
            self._config.update({k: v for k, v in config.items() if k != "_id" and k != "type"})
        self._calculate_next_run()
    
    async def save_config(self):
        """Save scheduler configuration to database"""
        await self.db.scheduler_config.update_one(
            {"type": "weekly_selection"},
            {"$set": {**self._config, "type": "weekly_selection", "updated_at": datetime.now(timezone.utc)}},
            upsert=True
        )
    
    def _calculate_next_run(self):
        """Calculate the next scheduled run time"""
        now = datetime.now(timezone.utc)
        
        # Find next Sunday
        days_until_sunday = (self._config["run_day"] - now.weekday()) % 7
        if days_until_sunday == 0:
            # It's Sunday - check if we've passed the run time
            run_time_today = now.replace(
                hour=self._config["run_hour"],
                minute=self._config["run_minute"],
                second=0,
                microsecond=0
            )
            if now >= run_time_today:
                days_until_sunday = 7  # Next Sunday
        
        self._next_run = now.replace(
            hour=self._config["run_hour"],
            minute=self._config["run_minute"],
            second=0,
            microsecond=0
        ) + timedelta(days=days_until_sunday)
    
    async def start(self):
        """Start the scheduler background task"""
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        await self.load_config()
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info(f"📅 Weekly selection scheduler started. Next run: {self._next_run}")
    
    async def stop(self):
        """Stop the scheduler"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Weekly selection scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop that checks and runs on schedule"""
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                
                if self._next_run and now >= self._next_run and self._config["enabled"]:
                    logger.info("🚀 Running scheduled weekly coin selection...")
                    await self.run_selection()
                    self._calculate_next_run()
                
                # Sleep for 1 minute before checking again
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def run_selection(self, force: bool = False) -> Dict[str, Any]:
        """
        Run the coin selection process.
        
        Args:
            force: If True, run even if not scheduled time
            
        Returns:
            Dict with selection results
        """
        if not self.coin_selector:
            return {"error": "Coin selector not initialized"}
        
        start_time = datetime.now(timezone.utc)
        week_start = start_time + timedelta(days=(7 - start_time.weekday()) % 7)  # Next Monday
        
        try:
            # Load latest Kraken pairs
            await self.coin_selector.load_kraken_pairs()
            
            # Determine market condition
            market_condition = await self._determine_market_condition()
            
            # Select main coins (10)
            main_coins = await self.coin_selector.select_best_coins(
                week_start=week_start,
                market_condition=market_condition,
                max_coins=self._config["main_coins_count"]
            )
            
            # Select gem coins (high risk/reward)
            gem_coins = await self._select_gem_coins(
                week_start=week_start,
                market_condition=market_condition,
                count=self._config["gem_coins_count"],
                exclude=[c["coin_id"] for c in main_coins]
            )
            
            # Store selection results
            selection_record = {
                "week_start": week_start.isoformat(),
                "selection_date": start_time.isoformat(),
                "market_condition": market_condition,
                "main_coins": main_coins,
                "gem_coins": gem_coins,
                "total_coins": len(main_coins) + len(gem_coins),
                "coin_universe_size": len(self.coin_selector.coin_universe),
                "status": "ready",
                "auto_executed": False
            }
            
            await self.db.weekly_selections.insert_one(selection_record)
            
            # Create alert
            await self._create_selection_alert(main_coins, gem_coins, market_condition)
            
            self._last_run = start_time
            
            logger.info(f"✅ Weekly selection complete: {len(main_coins)} main + {len(gem_coins)} gems")
            
            result = {
                "success": True,
                "week_start": week_start.isoformat(),
                "market_condition": market_condition,
                "main_coins": main_coins,
                "gem_coins": gem_coins,
                "total_selected": len(main_coins) + len(gem_coins),
                "universe_size": len(self.coin_selector.coin_universe),
                "auto_executed": False,
                "execution_result": None
            }
            
            # Auto-execute trades if enabled
            if self._config.get("auto_execute", False):
                logger.info("🚀 Auto-execute enabled - executing trades...")
                execution_result = await self._execute_trades(main_coins, gem_coins, market_condition)
                result["auto_executed"] = True
                result["execution_result"] = execution_result
                self._last_execution = execution_result
                
                # Update selection record with execution status
                await self.db.weekly_selections.update_one(
                    {"selection_date": start_time.isoformat()},
                    {"$set": {
                        "auto_executed": True,
                        "execution_result": execution_result,
                        "executed_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Selection error: {e}")
            return {"error": str(e)}
    
    async def _execute_trades(
        self, 
        main_coins: List[Dict], 
        gem_coins: List[Dict],
        market_condition: str
    ) -> Dict[str, Any]:
        """
        Execute trades based on the coin selection.
        Uses the AutomatedWeeklyTrader to place orders.
        """
        if not self.auto_trader:
            return {
                "success": False,
                "error": "Auto trader not connected",
                "trades": []
            }
        
        paper_trade = self._config.get("paper_trade", True)
        trades_executed = []
        errors = []
        
        logger.info(f"📈 Executing {'PAPER' if paper_trade else 'REAL'} trades for {len(main_coins)} main + {len(gem_coins)} gem coins")
        
        try:
            # Store selections in the format the auto_trader expects
            await self.db.ai_weekly_selection.delete_many({})  # Clear old selection
            
            selection_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "market_condition": market_condition,
                "main_coins": [
                    {
                        "coin_id": c.get("coin_id"),
                        "symbol": c.get("symbol", c.get("coin_id", "").upper()[:4]),
                        "score": c.get("total_score", 50),
                        "reasoning": c.get("reasoning", "")
                    }
                    for c in main_coins
                ],
                "gem_coins": [
                    {
                        "coin_id": c.get("coin_id"),
                        "symbol": c.get("symbol", c.get("coin_id", "").upper()[:4]),
                        "score": c.get("total_score", c.get("gem_score", 50)),
                        "is_gem": True
                    }
                    for c in gem_coins
                ]
            }
            await self.db.ai_weekly_selection.insert_one(selection_data)
            
            # Execute the weekly rebalance using the auto trader
            execution_result = await self.auto_trader.execute_weekly_rebalance(paper_trade=paper_trade)
            
            if execution_result.get("success"):
                trades_executed = execution_result.get("trades", [])
                logger.info(f"✅ Successfully executed {len(trades_executed)} trades")
                
                # Create success alert
                await self._create_execution_alert(
                    trades_executed, 
                    paper_trade, 
                    execution_result.get("total_invested", 0)
                )
            else:
                errors.append(execution_result.get("error", "Unknown error"))
                logger.error(f"❌ Trade execution failed: {errors}")
            
            return {
                "success": len(errors) == 0,
                "paper_trade": paper_trade,
                "trades_count": len(trades_executed),
                "trades": trades_executed,
                "total_invested": execution_result.get("total_invested", 0),
                "errors": errors,
                "execution_time": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "trades": []
            }
    
    async def _create_execution_alert(
        self,
        trades: List[Dict],
        paper_trade: bool,
        total_invested: float
    ):
        """Create an alert for trade execution"""
        trade_count = len(trades)
        mode = "PAPER" if paper_trade else "REAL"
        
        alert = {
            "title": f"💰 Weekly Trades Executed ({mode})",
            "message": f"Executed {trade_count} trades\n"
                      f"Total invested: ${total_invested:,.2f}\n"
                      f"Mode: {mode} Trading",
            "priority": "high" if not paper_trade else "medium",
            "type": "trade_execution",
            "created_at": datetime.now(timezone.utc),
            "read": False,
            "data": {
                "trades_count": trade_count,
                "paper_trade": paper_trade,
                "total_invested": total_invested
            }
        }
        await self.db.alerts.insert_one(alert)
    
    async def _determine_market_condition(self) -> str:
        """Determine current market condition based on BTC trend"""
        try:
            # Check Fear & Greed index from database
            fg = await self.db.fear_greed_cache.find_one(
                {}, sort=[("timestamp", -1)]
            )
            if fg:
                value = fg.get("value", 50)
                if value >= 70:
                    return "bullish"
                elif value <= 30:
                    return "bearish"
            
            # Fallback: Check BTC 7-day trend
            btc_prices = await self.db.historical_prices.find(
                {"coin_id": "bitcoin"}
            ).sort([("timestamp", -1)]).limit(7).to_list(7)
            
            if btc_prices and len(btc_prices) >= 2:
                current = btc_prices[0].get("price", 0)
                week_ago = btc_prices[-1].get("price", 0)
                if week_ago > 0:
                    change = (current - week_ago) / week_ago * 100
                    if change > 10:
                        return "bullish"
                    elif change < -10:
                        return "bearish"
            
            return "neutral"
        except:
            return "neutral"
    
    async def _select_gem_coins(
        self,
        week_start: datetime,
        market_condition: str,
        count: int,
        exclude: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Select gem coins (high risk/reward potential).
        Looks for:
        - Low market cap coins
        - High volatility
        - Recent momentum
        - Social buzz
        """
        gems = []
        
        # Get all coins and filter out main selections
        all_scores = []
        for coin_id in self.coin_selector.coin_universe:
            if coin_id in exclude:
                continue
            
            # Skip major coins
            if coin_id in ['bitcoin', 'ethereum', 'solana', 'cardano', 'ripple']:
                continue
            
            try:
                score_data = await self.coin_selector._calculate_coin_score(
                    coin_id, week_start, market_condition
                )
                if score_data:
                    # Boost score for high volatility (gem potential)
                    volatility = score_data['scores'].get('volatility', 50)
                    if volatility > 60:
                        score_data['gem_score'] = score_data['total_score'] * 1.2
                    else:
                        score_data['gem_score'] = score_data['total_score']
                    
                    score_data['is_gem'] = True
                    all_scores.append(score_data)
            except:
                continue
        
        # Sort by gem score and take top gems
        all_scores.sort(key=lambda x: x.get('gem_score', 0), reverse=True)
        gems = all_scores[:count]
        
        return gems
    
    async def _create_selection_alert(
        self,
        main_coins: List[Dict],
        gem_coins: List[Dict],
        market_condition: str
    ):
        """Create an alert for the new selection"""
        main_symbols = [c.get('symbol', c.get('coin_id', '')[:4].upper()) for c in main_coins[:5]]
        gem_symbols = [c.get('symbol', c.get('coin_id', '')[:4].upper()) for c in gem_coins]
        
        alert = {
            "title": "🎯 Weekly Coin Selection Ready",
            "message": f"Market: {market_condition.upper()}\n"
                      f"Main: {', '.join(main_symbols)}...\n"
                      f"Gems: {', '.join(gem_symbols)}\n"
                      f"Review in Auto Trading tab.",
            "priority": "high",
            "type": "weekly_selection",
            "created_at": datetime.now(timezone.utc),
            "read": False
        }
        await self.db.alerts.insert_one(alert)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        await self.load_config()
        
        # Get latest selection
        latest = await self.db.weekly_selections.find_one(
            {}, sort=[("selection_date", -1)],
            projection={"_id": 0, "main_coins": 0, "gem_coins": 0}
        )
        
        return {
            "running": self._running,
            "enabled": self._config.get("enabled", True),
            "config": self._config,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "next_run": self._next_run.isoformat() if self._next_run else None,
            "latest_selection": latest
        }
    
    async def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update scheduler configuration"""
        valid_keys = ["enabled", "run_day", "run_hour", "run_minute", 
                      "main_coins_count", "gem_coins_count", "auto_execute",
                      "paper_trade", "position_size_pct", "use_isolated_budget"]
        
        for key, value in updates.items():
            if key in valid_keys:
                self._config[key] = value
        
        await self.save_config()
        self._calculate_next_run()
        
        return {"success": True, "config": self._config}
    
    async def get_latest_selection(self) -> Optional[Dict[str, Any]]:
        """Get the most recent weekly selection"""
        selection = await self.db.weekly_selections.find_one(
            {}, sort=[("selection_date", -1)],
            projection={"_id": 0}
        )
        return selection
    
    async def get_last_execution(self) -> Optional[Dict[str, Any]]:
        """Get the last trade execution result"""
        return self._last_execution
    
    async def execute_selection(self, selection_id: str = None, paper_trade: bool = None) -> Dict[str, Any]:
        """
        Manually execute trades for an existing selection.
        
        Args:
            selection_id: Optional ID of selection to execute. If None, uses latest.
            paper_trade: Override paper_trade setting. If None, uses config.
        """
        if not self.auto_trader:
            return {"success": False, "error": "Auto trader not connected"}
        
        # Get the selection
        if selection_id:
            selection = await self.db.weekly_selections.find_one({"_id": selection_id})
        else:
            selection = await self.db.weekly_selections.find_one(
                {}, sort=[("selection_date", -1)]
            )
        
        if not selection:
            return {"success": False, "error": "No selection found"}
        
        if selection.get("auto_executed"):
            return {"success": False, "error": "Selection already executed", "executed_at": selection.get("executed_at")}
        
        # Execute trades
        use_paper = paper_trade if paper_trade is not None else self._config.get("paper_trade", True)
        
        result = await self._execute_trades(
            selection.get("main_coins", []),
            selection.get("gem_coins", []),
            selection.get("market_condition", "neutral")
        )
        
        # Update selection with execution
        if result.get("success"):
            await self.db.weekly_selections.update_one(
                {"_id": selection.get("_id")},
                {"$set": {
                    "auto_executed": True,
                    "execution_result": result,
                    "executed_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        return result


def get_weekly_scheduler() -> Optional[WeeklySelectionScheduler]:
    """Get the singleton scheduler instance"""
    return _scheduler_instance


async def initialize_weekly_scheduler(db: AsyncIOMotorDatabase, coin_selector=None, auto_trader=None) -> WeeklySelectionScheduler:
    """Initialize the weekly scheduler"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = WeeklySelectionScheduler(db, coin_selector, auto_trader)
        await _scheduler_instance.load_config()
    
    return _scheduler_instance

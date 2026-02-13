"""
Kraken Data Expansion Service
Handles bulk downloading of historical data for ALL Kraken coins.

Features:
- Batch download of all 631+ Kraken coins
- Background processing with progress tracking
- Auto-detection of new coin listings
- Scheduled updates for new coins
- Rate limiting to avoid API throttling
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
import os

logger = logging.getLogger(__name__)

# Rate limiting settings
BATCH_SIZE = 10  # Coins per batch
DELAY_BETWEEN_COINS = 1.0  # Seconds between coin downloads
DELAY_BETWEEN_BATCHES = 5.0  # Seconds between batches


class KrakenDataExpansionService:
    """
    Service for expanding the training data universe to all Kraken coins.
    
    Provides:
    - Bulk historical data download for all coins
    - Progress tracking for long-running downloads
    - New coin detection and auto-addition
    - Scheduled background updates
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.progress_collection = db["data_expansion_progress"]
        self.coin_universe_collection = db["training_coin_universe"]
        self._current_job: Dict[str, Any] = {}
        self._is_running = False
        
    async def get_kraken_universe_manager(self):
        """Get the Kraken Universe Manager service"""
        from services.kraken_universe_manager import get_kraken_universe_manager
        return get_kraken_universe_manager(self.db)
    
    async def get_mtf_service(self):
        """Get the Multi-Timeframe Historical service"""
        from services.multitimeframe_historical_service import get_multitimeframe_service
        return get_multitimeframe_service(self.db)
    
    async def get_all_kraken_coins(self) -> List[str]:
        """
        Get all unique crypto coins from Kraken.
        
        Returns:
            List of coin symbols (e.g., ['BTC', 'ETH', 'SOL', ...])
        """
        universe_mgr = await self.get_kraken_universe_manager()
        if not universe_mgr:
            logger.warning("Kraken Universe Manager not available")
            return []
        
        # Get stats which includes all coins
        stats = await universe_mgr.get_universe_stats()
        
        if stats.get("status") != "synced":
            # Sync if not synced
            await universe_mgr.sync_universe()
            stats = await universe_mgr.get_universe_stats()
        
        return stats.get("crypto_coins", [])
    
    async def get_coins_with_data(self) -> Set[str]:
        """
        Get list of coins that already have MTF data downloaded.
        
        Returns:
            Set of coin symbols with existing data
        """
        mtf_service = await self.get_mtf_service()
        if not mtf_service:
            return set()
        
        stats = await mtf_service.get_storage_stats()
        
        # Collect all symbols across timeframes
        all_symbols = set()
        for tf_data in stats.get("timeframes", {}).values():
            all_symbols.update(tf_data.get("symbols", []))
        
        return all_symbols
    
    async def get_coins_needing_download(self) -> List[str]:
        """
        Get list of coins that need data downloaded.
        
        Returns:
            List of coin symbols without MTF data
        """
        all_coins = await self.get_all_kraken_coins()
        coins_with_data = await self.get_coins_with_data()
        
        # Filter out coins that already have data
        needs_download = [c for c in all_coins if c not in coins_with_data]
        
        return needs_download
    
    async def download_all_coins(
        self,
        timeframes: List[str] = None,
        batch_size: int = BATCH_SIZE,
        priority_coins: List[str] = None
    ) -> Dict[str, Any]:
        """
        Download historical data for ALL Kraken coins.
        
        This is a long-running operation that downloads MTF data for all coins.
        Progress is tracked and can be monitored.
        
        Args:
            timeframes: List of timeframes to download (default: 1h, 4h, 1D)
            batch_size: Number of coins to process per batch
            priority_coins: Coins to download first (e.g., top market cap)
        
        Returns:
            Job status with progress tracking
        """
        if self._is_running:
            return {
                "status": "already_running",
                "message": "A download job is already in progress",
                "current_job": self._current_job
            }
        
        if timeframes is None:
            timeframes = ["1h", "4h", "1D"]
        
        # Get coins needing download
        coins_to_download = await self.get_coins_needing_download()
        
        if not coins_to_download:
            return {
                "status": "complete",
                "message": "All coins already have data downloaded",
                "total_coins": len(await self.get_all_kraken_coins())
            }
        
        # Prioritize certain coins if specified
        if priority_coins:
            priority_set = set(priority_coins)
            priority_list = [c for c in coins_to_download if c in priority_set]
            other_list = [c for c in coins_to_download if c not in priority_set]
            coins_to_download = priority_list + other_list
        
        # Initialize job tracking
        job_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self._current_job = {
            "job_id": job_id,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "total_coins": len(coins_to_download),
            "completed_coins": 0,
            "failed_coins": 0,
            "current_coin": None,
            "timeframes": timeframes,
            "batch_size": batch_size,
            "progress_pct": 0,
            "successful": [],
            "failed": [],
            "eta_minutes": None
        }
        
        self._is_running = True
        
        # Start background download
        asyncio.create_task(self._download_coins_background(
            coins_to_download, timeframes, batch_size, job_id
        ))
        
        return {
            "status": "started",
            "job_id": job_id,
            "message": f"Started downloading {len(coins_to_download)} coins",
            "total_coins": len(coins_to_download),
            "timeframes": timeframes,
            "check_progress_at": "/api/kraken-expansion/progress"
        }
    
    async def _download_coins_background(
        self,
        coins: List[str],
        timeframes: List[str],
        batch_size: int,
        job_id: str
    ):
        """Background task to download all coins"""
        mtf_service = await self.get_mtf_service()
        
        if not mtf_service:
            self._current_job["status"] = "failed"
            self._current_job["error"] = "MTF service not available"
            self._is_running = False
            return
        
        start_time = datetime.now(timezone.utc)
        total = len(coins)
        
        try:
            for idx, coin in enumerate(coins):
                self._current_job["current_coin"] = coin
                self._current_job["progress_pct"] = int((idx / total) * 100)
                
                # Calculate ETA
                if idx > 0:
                    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                    avg_time_per_coin = elapsed / idx
                    remaining = total - idx
                    eta_seconds = avg_time_per_coin * remaining
                    self._current_job["eta_minutes"] = round(eta_seconds / 60, 1)
                
                try:
                    logger.info(f"📊 [{idx+1}/{total}] Downloading {coin}...")
                    
                    result = await mtf_service.download_all_timeframes(
                        symbol=coin,
                        timeframes=timeframes
                    )
                    
                    if result.get("success_count", 0) > 0:
                        self._current_job["completed_coins"] += 1
                        self._current_job["successful"].append({
                            "symbol": coin,
                            "timeframes_downloaded": result.get("success_count", 0)
                        })
                    else:
                        self._current_job["failed_coins"] += 1
                        self._current_job["failed"].append({
                            "symbol": coin,
                            "error": result.get("errors", ["Unknown error"])
                        })
                    
                except Exception as e:
                    logger.warning(f"Failed to download {coin}: {e}")
                    self._current_job["failed_coins"] += 1
                    self._current_job["failed"].append({
                        "symbol": coin,
                        "error": str(e)
                    })
                
                # Rate limiting
                await asyncio.sleep(DELAY_BETWEEN_COINS)
                
                # Longer pause between batches
                if (idx + 1) % batch_size == 0:
                    logger.info(f"⏳ Batch complete, pausing {DELAY_BETWEEN_BATCHES}s...")
                    await asyncio.sleep(DELAY_BETWEEN_BATCHES)
            
            # Job complete
            self._current_job["status"] = "completed"
            self._current_job["completed_at"] = datetime.now(timezone.utc).isoformat()
            self._current_job["progress_pct"] = 100
            self._current_job["current_coin"] = None
            
            # Save final results
            await self.progress_collection.insert_one({
                **self._current_job,
                "timestamp": datetime.now(timezone.utc)
            })
            
            logger.info(f"✅ Download job {job_id} completed: {self._current_job['completed_coins']}/{total} successful")
            
        except Exception as e:
            logger.error(f"Download job failed: {e}")
            self._current_job["status"] = "failed"
            self._current_job["error"] = str(e)
        
        finally:
            self._is_running = False
    
    async def get_progress(self) -> Dict[str, Any]:
        """Get current download progress"""
        if self._is_running:
            return self._current_job
        
        # Get last completed job
        last_job = await self.progress_collection.find_one(
            {},
            sort=[("timestamp", -1)]
        )
        
        if last_job:
            last_job["_id"] = str(last_job["_id"])
            return {
                "status": "idle",
                "last_job": last_job,
                "message": "No download in progress"
            }
        
        return {
            "status": "idle",
            "message": "No download jobs found. Start one with POST /download-all"
        }
    
    async def stop_download(self) -> Dict[str, Any]:
        """Stop current download job"""
        if not self._is_running:
            return {
                "status": "not_running",
                "message": "No download job is currently running"
            }
        
        self._is_running = False
        self._current_job["status"] = "stopped"
        self._current_job["stopped_at"] = datetime.now(timezone.utc).isoformat()
        
        return {
            "status": "stopped",
            "message": "Download job stopped",
            "completed_coins": self._current_job["completed_coins"],
            "total_coins": self._current_job["total_coins"]
        }
    
    async def check_for_new_coins(self) -> Dict[str, Any]:
        """
        Check for newly listed coins on Kraken that don't have data yet.
        
        Returns:
            Dict with new coins found
        """
        # Sync universe to get latest
        universe_mgr = await self.get_kraken_universe_manager()
        if universe_mgr:
            await universe_mgr.sync_universe()
        
        # Get coins without data
        new_coins = await self.get_coins_needing_download()
        
        if new_coins:
            # Add to training universe
            await self._add_to_training_universe(new_coins)
        
        return {
            "new_coins_found": len(new_coins),
            "coins": new_coins[:50],  # Show first 50
            "total_pending": len(new_coins),
            "message": f"Found {len(new_coins)} coins without historical data"
        }
    
    async def _add_to_training_universe(self, coins: List[str]):
        """Add new coins to the training universe collection"""
        for coin in coins:
            await self.coin_universe_collection.update_one(
                {"symbol": coin},
                {
                    "$set": {
                        "symbol": coin,
                        "source": "kraken",
                        "added_at": datetime.now(timezone.utc),
                        "has_mtf_data": False,
                        "training_enabled": True
                    }
                },
                upsert=True
            )
    
    async def get_expansion_stats(self) -> Dict[str, Any]:
        """Get statistics about data expansion progress"""
        all_coins = await self.get_all_kraken_coins()
        coins_with_data = await self.get_coins_with_data()
        coins_needing_download = await self.get_coins_needing_download()
        
        mtf_service = await self.get_mtf_service()
        storage_stats = await mtf_service.get_storage_stats() if mtf_service else {}
        
        return {
            "kraken_universe": {
                "total_coins": len(all_coins),
                "coins_with_data": len(coins_with_data),
                "coins_pending": len(coins_needing_download),
                "coverage_pct": round(len(coins_with_data) / max(len(all_coins), 1) * 100, 1)
            },
            "storage": {
                "total_records": storage_stats.get("total_records", 0),
                "timeframes": list(storage_stats.get("timeframes", {}).keys())
            },
            "download_status": "running" if self._is_running else "idle",
            "current_job": self._current_job if self._is_running else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def download_priority_coins(
        self,
        count: int = 50,
        timeframes: List[str] = None
    ) -> Dict[str, Any]:
        """
        Download data for top priority coins first (major coins).
        
        Args:
            count: Number of top coins to download
            timeframes: Timeframes to download
        
        Returns:
            Job status
        """
        # Priority order - major coins first
        PRIORITY_COINS = [
            "BTC", "ETH", "SOL", "XRP", "ADA", "AVAX", "DOT", "LINK", "MATIC", "UNI",
            "LTC", "BCH", "ATOM", "XLM", "ALGO", "NEAR", "APT", "ARB", "OP", "INJ",
            "FIL", "AAVE", "MKR", "CRV", "SNX", "COMP", "SUSHI", "YFI", "BAL", "1INCH",
            "DYDX", "GMX", "RUNE", "ENS", "LDO", "RPL", "FXS", "CVX", "LQTY", "PENDLE",
            "TIA", "SEI", "SUI", "MINA", "FLOW", "IMX", "SAND", "MANA", "AXS", "GALA"
        ]
        
        coins_needing = await self.get_coins_needing_download()
        
        # Filter to priority coins that need downloading
        priority_to_download = [c for c in PRIORITY_COINS if c in coins_needing][:count]
        
        if not priority_to_download:
            # If all priority coins done, just download next batch
            priority_to_download = coins_needing[:count]
        
        if not priority_to_download:
            return {
                "status": "complete",
                "message": "All coins already have data"
            }
        
        return await self.download_all_coins(
            timeframes=timeframes,
            priority_coins=priority_to_download
        )


# Global instance
_expansion_service: Optional[KrakenDataExpansionService] = None


def get_expansion_service(db: AsyncIOMotorDatabase = None) -> Optional[KrakenDataExpansionService]:
    """Get or create Kraken Data Expansion Service instance"""
    global _expansion_service
    if _expansion_service is None and db is not None:
        _expansion_service = KrakenDataExpansionService(db)
    return _expansion_service

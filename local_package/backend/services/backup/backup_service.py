"""
Data Backup Service
====================
Comprehensive backup system for all critical data:
- MongoDB collections
- Market data
- ML models
- Configuration
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path
import gzip
import shutil

logger = logging.getLogger(__name__)

class DataBackupService:
    """
    Complete data backup service for Tethys Trading Platform
    """
    
    def __init__(self, db, backup_dir: str = "/app/backups"):
        self.db = db
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Collections to backup (prioritized)
        self.critical_collections = [
            # Trading & Portfolio
            "trades", "orders", "positions", "portfolio_snapshots",
            "trade_history", "execution_logs",
            
            # Market Data (YOUR PRIORITY)
            "market_data", "price_history", "ticker_data",
            "ohlcv_data", "order_book_snapshots",
            
            # Media & News Data (YOUR PRIORITY)
            "news_articles", "sentiment_data", "social_media_data",
            "crypto_news", "market_sentiment",
            
            # AI & ML
            "ml_models", "model_performance", "predictions",
            "training_history", "feature_store",
            
            # Configuration & State
            "user_settings", "api_keys", "system_state",
            "risk_settings", "strategy_configs",
            
            # Analytics
            "performance_metrics", "backtest_results",
            "signal_history", "alert_history"
        ]
        
        logger.info(f"📦 Backup Service initialized - Dir: {self.backup_dir}")
    
    async def backup_collection(self, collection_name: str, compress: bool = True) -> Dict[str, Any]:
        """Backup a single MongoDB collection"""
        try:
            collection = self.db[collection_name]
            
            # Get all documents
            cursor = collection.find({})
            documents = []
            async for doc in cursor:
                # Convert ObjectId to string for JSON serialization
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
                # Convert datetime objects
                for key, value in doc.items():
                    if isinstance(value, datetime):
                        doc[key] = value.isoformat()
                documents.append(doc)
            
            if not documents:
                return {"collection": collection_name, "count": 0, "status": "empty"}
            
            # Create backup file
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"{collection_name}_{timestamp}.json"
            filepath = self.backup_dir / filename
            
            # Write to file
            with open(filepath, 'w') as f:
                json.dump(documents, f, indent=2, default=str)
            
            # Compress if requested
            if compress:
                compressed_path = filepath.with_suffix('.json.gz')
                with open(filepath, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(filepath)
                filepath = compressed_path
            
            file_size = os.path.getsize(filepath)
            
            logger.info(f"✅ Backed up {collection_name}: {len(documents)} docs, {file_size/1024:.1f}KB")
            
            return {
                "collection": collection_name,
                "count": len(documents),
                "file": str(filepath),
                "size_bytes": file_size,
                "compressed": compress,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"❌ Backup failed for {collection_name}: {e}")
            return {
                "collection": collection_name,
                "status": "error",
                "error": str(e)
            }
    
    async def full_backup(self, compress: bool = True) -> Dict[str, Any]:
        """Perform full backup of all critical collections"""
        logger.info("🚀 Starting full database backup...")
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_subdir = self.backup_dir / f"full_backup_{timestamp}"
        backup_subdir.mkdir(parents=True, exist_ok=True)
        
        # Temporarily change backup dir
        original_dir = self.backup_dir
        self.backup_dir = backup_subdir
        
        results = {
            "timestamp": timestamp,
            "backup_dir": str(backup_subdir),
            "collections": [],
            "total_documents": 0,
            "total_size_bytes": 0,
            "success_count": 0,
            "error_count": 0
        }
        
        # Get all collections in database
        all_collections = await self.db.list_collection_names()
        collections_to_backup = list(set(self.critical_collections) & set(all_collections))
        
        # Add any collections not in our list
        for col in all_collections:
            if col not in collections_to_backup and not col.startswith('system.'):
                collections_to_backup.append(col)
        
        for collection_name in collections_to_backup:
            result = await self.backup_collection(collection_name, compress)
            results["collections"].append(result)
            
            if result["status"] == "success":
                results["success_count"] += 1
                results["total_documents"] += result.get("count", 0)
                results["total_size_bytes"] += result.get("size_bytes", 0)
            elif result["status"] == "error":
                results["error_count"] += 1
        
        # Restore original backup dir
        self.backup_dir = original_dir
        
        # Create manifest
        manifest_path = backup_subdir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"✅ Full backup complete: {results['success_count']} collections, "
                   f"{results['total_documents']} docs, {results['total_size_bytes']/1024/1024:.2f}MB")
        
        return results
    
    async def backup_market_data(self) -> Dict[str, Any]:
        """Specifically backup all market-related data (YOUR PRIORITY)"""
        logger.info("📊 Backing up market data...")
        
        market_collections = [
            "market_data", "price_history", "ticker_data",
            "ohlcv_data", "order_book_snapshots", "candles",
            "historical_prices", "market_indicators"
        ]
        
        results = {"type": "market_data", "collections": []}
        
        all_collections = await self.db.list_collection_names()
        
        for col in market_collections:
            if col in all_collections:
                result = await self.backup_collection(col, compress=True)
                results["collections"].append(result)
        
        return results
    
    async def backup_news_media(self) -> Dict[str, Any]:
        """Specifically backup all news/media data (YOUR PRIORITY)"""
        logger.info("📰 Backing up news and media data...")
        
        news_collections = [
            "news_articles", "sentiment_data", "social_media_data",
            "crypto_news", "market_sentiment", "news_sentiment",
            "twitter_data", "reddit_data", "media_mentions"
        ]
        
        results = {"type": "news_media", "collections": []}
        
        all_collections = await self.db.list_collection_names()
        
        for col in news_collections:
            if col in all_collections:
                result = await self.backup_collection(col, compress=True)
                results["collections"].append(result)
        
        return results
    
    async def backup_ml_models(self) -> Dict[str, Any]:
        """Backup ML model data and training history"""
        logger.info("🤖 Backing up ML models and training data...")
        
        ml_collections = [
            "ml_models", "model_performance", "predictions",
            "training_history", "feature_store", "model_weights",
            "hyperparameters", "experiment_results"
        ]
        
        results = {"type": "ml_models", "collections": []}
        
        all_collections = await self.db.list_collection_names()
        
        for col in ml_collections:
            if col in all_collections:
                result = await self.backup_collection(col, compress=True)
                results["collections"].append(result)
        
        return results
    
    async def restore_collection(self, filepath: str, collection_name: str = None) -> Dict[str, Any]:
        """Restore a collection from backup file"""
        try:
            path = Path(filepath)
            
            # Determine collection name from filename if not provided
            if not collection_name:
                collection_name = path.stem.split('_')[0]
            
            # Read file (handle compressed)
            if path.suffix == '.gz':
                with gzip.open(path, 'rt') as f:
                    documents = json.load(f)
            else:
                with open(path, 'r') as f:
                    documents = json.load(f)
            
            if not documents:
                return {"status": "empty", "collection": collection_name}
            
            # Remove _id fields to let MongoDB generate new ones
            for doc in documents:
                if '_id' in doc:
                    del doc['_id']
            
            collection = self.db[collection_name]
            result = await collection.insert_many(documents)
            
            logger.info(f"✅ Restored {len(result.inserted_ids)} docs to {collection_name}")
            
            return {
                "status": "success",
                "collection": collection_name,
                "restored_count": len(result.inserted_ids)
            }
            
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        backups = []
        
        for item in self.backup_dir.iterdir():
            if item.is_dir() and item.name.startswith('full_backup_'):
                manifest_path = item / "manifest.json"
                if manifest_path.exists():
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                    backups.append({
                        "type": "full",
                        "path": str(item),
                        "timestamp": manifest.get("timestamp"),
                        "collections": manifest.get("success_count"),
                        "size_mb": manifest.get("total_size_bytes", 0) / 1024 / 1024
                    })
            elif item.is_file() and (item.suffix == '.json' or item.name.endswith('.json.gz')):
                backups.append({
                    "type": "single",
                    "path": str(item),
                    "name": item.name,
                    "size_mb": item.stat().st_size / 1024 / 1024
                })
        
        return sorted(backups, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    async def get_backup_stats(self) -> Dict[str, Any]:
        """Get backup statistics"""
        backups = self.list_backups()
        total_size = sum(b.get("size_mb", 0) for b in backups)
        
        return {
            "backup_count": len(backups),
            "total_size_mb": round(total_size, 2),
            "backup_dir": str(self.backup_dir),
            "latest_backup": backups[0] if backups else None,
            "backups": backups[:10]  # Last 10 backups
        }


# Singleton instance
_backup_service = None

def get_backup_service(db) -> DataBackupService:
    global _backup_service
    if _backup_service is None:
        _backup_service = DataBackupService(db)
    return _backup_service

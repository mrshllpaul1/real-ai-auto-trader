"""
Backup API Routes
"""

from fastapi import APIRouter, Depends, BackgroundTasks
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backup", tags=["Data Backup"])

# Database dependency
async def get_database():
    from motor.motor_asyncio import AsyncIOMotorClient
    import os
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL', 'mongodb://localhost:27017'))
    return client[os.environ.get('DB_NAME', 'tethys_trading')]


@router.post("/full")
async def trigger_full_backup(
    background_tasks: BackgroundTasks,
    db = Depends(get_database)
):
    """Trigger a full database backup"""
    from services.backup.backup_service import get_backup_service
    
    backup_service = get_backup_service(db)
    
    # Run in background
    async def do_backup():
        result = await backup_service.full_backup(compress=True)
        logger.info(f"Full backup completed: {result}")
    
    background_tasks.add_task(do_backup)
    
    return {
        "status": "started",
        "message": "Full backup started in background"
    }


@router.post("/market-data")
async def backup_market_data(db = Depends(get_database)):
    """Backup all market data (prices, OHLCV, etc.)"""
    from services.backup.backup_service import get_backup_service
    
    backup_service = get_backup_service(db)
    result = await backup_service.backup_market_data()
    
    return result


@router.post("/news-media")
async def backup_news_media(db = Depends(get_database)):
    """Backup all news and media data"""
    from services.backup.backup_service import get_backup_service
    
    backup_service = get_backup_service(db)
    result = await backup_service.backup_news_media()
    
    return result


@router.post("/ml-models")
async def backup_ml_models(db = Depends(get_database)):
    """Backup ML models and training data"""
    from services.backup.backup_service import get_backup_service
    
    backup_service = get_backup_service(db)
    result = await backup_service.backup_ml_models()
    
    return result


@router.get("/list")
async def list_backups(db = Depends(get_database)):
    """List all available backups"""
    from services.backup.backup_service import get_backup_service
    
    backup_service = get_backup_service(db)
    return backup_service.list_backups()


@router.get("/stats")
async def get_backup_stats(db = Depends(get_database)):
    """Get backup statistics"""
    from services.backup.backup_service import get_backup_service
    
    backup_service = get_backup_service(db)
    return await backup_service.get_backup_stats()


@router.post("/collection/{collection_name}")
async def backup_single_collection(
    collection_name: str,
    db = Depends(get_database)
):
    """Backup a single collection"""
    from services.backup.backup_service import get_backup_service
    
    backup_service = get_backup_service(db)
    result = await backup_service.backup_collection(collection_name, compress=True)
    
    return result

"""
Kraken Data Expansion API Routes

Endpoints for downloading historical data for all Kraken coins
and managing the training data universe.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kraken-expansion", tags=["Kraken Data Expansion"])

# Global reference
_expansion_service = None
_db = None


def set_dependencies(db, expansion_service=None):
    """Set service dependencies"""
    global _expansion_service, _db
    _db = db
    _expansion_service = expansion_service


def get_service():
    """Get expansion service with lazy initialization"""
    global _expansion_service, _db
    if _expansion_service is None and _db is not None:
        from services.kraken_data_expansion_service import get_expansion_service
        _expansion_service = get_expansion_service(_db)
    return _expansion_service


class DownloadRequest(BaseModel):
    """Request model for download operations"""
    timeframes: Optional[List[str]] = Field(
        default=["1h", "4h", "1D"],
        description="Timeframes to download"
    )
    batch_size: Optional[int] = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of coins to process per batch"
    )
    priority_coins: Optional[List[str]] = Field(
        default=None,
        description="Coins to download first"
    )


class PriorityDownloadRequest(BaseModel):
    """Request model for priority coin download"""
    count: Optional[int] = Field(
        default=50,
        ge=10,
        le=200,
        description="Number of priority coins to download"
    )
    timeframes: Optional[List[str]] = Field(
        default=["1h", "4h", "1D"],
        description="Timeframes to download"
    )


@router.get("/stats")
async def get_expansion_stats():
    """
    Get statistics about data expansion progress.
    
    Shows:
    - Total Kraken coins available
    - Coins with historical data
    - Coins pending download
    - Coverage percentage
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Expansion service not initialized")
    
    return await service.get_expansion_stats()


@router.get("/progress")
async def get_download_progress():
    """
    Get current download job progress.
    
    Shows progress of ongoing download or last completed job.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Expansion service not initialized")
    
    return await service.get_progress()


@router.post("/download-all")
async def download_all_coins(request: DownloadRequest = None):
    """
    Start downloading historical data for ALL Kraken coins.
    
    This is a long-running background operation that will:
    1. Get all 631+ unique coins from Kraken
    2. Download multi-timeframe OHLCV data for each
    3. Store data in MongoDB for training
    
    Monitor progress at /api/kraken-expansion/progress
    
    Note: This may take several hours for all coins.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Expansion service not initialized")
    
    if request is None:
        request = DownloadRequest()
    
    result = await service.download_all_coins(
        timeframes=request.timeframes,
        batch_size=request.batch_size,
        priority_coins=request.priority_coins
    )
    
    return result


@router.post("/download-priority")
async def download_priority_coins(request: PriorityDownloadRequest = None):
    """
    Download data for top priority coins first.
    
    Downloads major coins (BTC, ETH, SOL, etc.) before smaller coins.
    Useful for getting started quickly with major trading pairs.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Expansion service not initialized")
    
    if request is None:
        request = PriorityDownloadRequest()
    
    result = await service.download_priority_coins(
        count=request.count,
        timeframes=request.timeframes
    )
    
    return result


@router.post("/stop")
async def stop_download():
    """
    Stop the current download job.
    
    Already downloaded data is preserved.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Expansion service not initialized")
    
    return await service.stop_download()


@router.get("/check-new")
async def check_for_new_coins():
    """
    Check for newly listed coins on Kraken.
    
    Syncs with Kraken and identifies coins without historical data.
    New coins are automatically added to the training universe.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Expansion service not initialized")
    
    return await service.check_for_new_coins()


@router.get("/pending-coins")
async def get_pending_coins():
    """
    Get list of coins that need data downloaded.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Expansion service not initialized")
    
    pending = await service.get_coins_needing_download()
    
    return {
        "pending_count": len(pending),
        "coins": pending,
        "message": f"{len(pending)} coins need historical data download"
    }


@router.get("/coins-with-data")
async def get_coins_with_data():
    """
    Get list of coins that already have MTF data.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Expansion service not initialized")
    
    coins = await service.get_coins_with_data()
    
    return {
        "count": len(coins),
        "coins": sorted(list(coins)),
        "message": f"{len(coins)} coins have historical data"
    }


@router.get("/all-kraken-coins")
async def get_all_kraken_coins():
    """
    Get list of all unique coins available on Kraken.
    """
    service = get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Expansion service not initialized")
    
    coins = await service.get_all_kraken_coins()
    
    return {
        "count": len(coins),
        "coins": coins,
        "message": f"{len(coins)} unique coins available on Kraken"
    }

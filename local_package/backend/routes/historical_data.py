"""
Historical Data API Routes
Endpoints for downloading, managing, and retrieving historical OHLCV data for AI training.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncio

router = APIRouter(prefix="/historical-data", tags=["Historical Data"])

# Service dependencies (set during initialization)
_db = None
_downloader = None
_cryptocompare_service = None


def set_dependencies(db, downloader, cryptocompare_service):
    """Set service dependencies"""
    global _db, _downloader, _cryptocompare_service
    _db = db
    _downloader = downloader
    _cryptocompare_service = cryptocompare_service


# Request models
class DownloadRequest(BaseModel):
    coins: Optional[List[str]] = None
    max_days: int = 3000


class CoinDataRequest(BaseModel):
    coin_symbol: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: Optional[int] = None


@router.get("/status")
async def get_service_status():
    """Get historical data service status"""
    if not _downloader:
        return {
            "status": "not_initialized",
            "message": "Historical data service not initialized"
        }
    
    stats = await _downloader.get_storage_stats()
    
    return {
        "status": "operational",
        "storage": stats,
        "api_configured": bool(_cryptocompare_service and _cryptocompare_service.api_key)
    }


@router.get("/download-status")
async def get_download_status():
    """Get current download progress"""
    from services.historical_data_downloader import get_download_status
    return get_download_status()


@router.post("/download/start")
async def start_download(
    request: DownloadRequest,
    background_tasks: BackgroundTasks
):
    """
    Start downloading historical data for specified coins.
    Runs as a background task.
    """
    if not _downloader:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    from services.historical_data_downloader import get_download_status
    status = get_download_status()
    
    if status.get("running"):
        return {
            "status": "already_running",
            "current_coin": status.get("current_coin"),
            "progress": status.get("progress"),
            "message": "Download already in progress. Check /download-status for updates."
        }
    
    # Start download in background using proper async handling
    async def run_download():
        await _downloader.download_all_coins(
            coins=request.coins,
            max_days=request.max_days
        )
    
    # Use asyncio.create_task within the event loop context
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(run_download())
    
    return {
        "status": "started",
        "coins": request.coins or _downloader.TOP_COINS,
        "max_days": request.max_days,
        "message": "Download started. Check /download-status for progress."
    }


@router.post("/download/single/{coin_symbol}")
async def download_single_coin(coin_symbol: str, max_days: int = 3000):
    """Download historical data for a single coin (synchronous)"""
    if not _downloader:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    result = await _downloader.download_coin_history(coin_symbol, max_days)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/coin/{coin_symbol}")
async def get_coin_history(
    coin_symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None
):
    """Get stored historical data for a coin"""
    if not _downloader:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    result = await _downloader.get_coin_data(coin_symbol, start, end, limit)
    
    if not result.get("data"):
        raise HTTPException(
            status_code=404,
            detail=f"No data found for {coin_symbol}. Try downloading first."
        )
    
    return result


@router.get("/training-data")
async def get_training_data(
    coins: Optional[str] = None,
    min_records: int = 365
):
    """
    Get historical data formatted for AI training.
    
    Args:
        coins: Comma-separated list of coin symbols (optional)
        min_records: Minimum records required per coin
    """
    if not _downloader:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    coin_list = coins.split(",") if coins else None
    
    result = await _downloader.get_training_data(coin_list, min_records)
    
    return result


@router.get("/stats")
async def get_storage_stats():
    """Get statistics about stored historical data"""
    if not _downloader:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    return await _downloader.get_storage_stats()


@router.get("/api/daily/{coin_symbol}")
async def fetch_daily_ohlcv(coin_symbol: str, limit: int = 365):
    """
    Fetch daily OHLCV data directly from CryptoCompare API.
    Does not store - use for quick lookups.
    """
    if not _cryptocompare_service:
        raise HTTPException(status_code=500, detail="CryptoCompare service not initialized")
    
    result = await _cryptocompare_service.get_historical_daily(coin_symbol, limit=limit)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/api/hourly/{coin_symbol}")
async def fetch_hourly_ohlcv(coin_symbol: str, limit: int = 168):
    """
    Fetch hourly OHLCV data directly from CryptoCompare API.
    Does not store - use for quick lookups.
    """
    if not _cryptocompare_service:
        raise HTTPException(status_code=500, detail="CryptoCompare service not initialized")
    
    result = await _cryptocompare_service.get_historical_hourly(coin_symbol, limit=limit)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.delete("/coin/{coin_symbol}")
async def delete_coin_data(coin_symbol: str):
    """Delete stored historical data for a coin"""
    if not _db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    result = await _db.historical_ohlcv.delete_many({"symbol": coin_symbol.upper()})
    
    return {
        "symbol": coin_symbol.upper(),
        "deleted_records": result.deleted_count,
        "status": "success"
    }


@router.delete("/all")
async def delete_all_data():
    """Delete all stored historical data"""
    if not _db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    result = await _db.historical_ohlcv.delete_many({})
    
    return {
        "deleted_records": result.deleted_count,
        "status": "success"
    }

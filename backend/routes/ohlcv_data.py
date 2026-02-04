"""
OHLCV Data API Routes
Endpoints for managing historical OHLCV data
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

router = APIRouter(prefix="/data", tags=["OHLCV Data"])
logger = logging.getLogger(__name__)

# Service instance
_ohlcv_manager = None


def set_dependencies(ohlcv_manager):
    """Set dependencies"""
    global _ohlcv_manager
    _ohlcv_manager = ohlcv_manager


class DownloadRequest(BaseModel):
    symbols: Optional[List[str]] = None
    days: int = 365
    timeframe: str = "daily"


class TrainingDataRequest(BaseModel):
    symbols: Optional[List[str]] = None
    min_records: int = 100
    timeframe: str = "daily"


@router.get("/ohlcv/stats")
async def get_ohlcv_stats():
    """
    Get statistics about stored OHLCV data
    Returns record counts, date ranges, and symbol coverage
    """
    if not _ohlcv_manager:
        raise HTTPException(status_code=503, detail="OHLCV manager not initialized")
    
    return await _ohlcv_manager.get_stats()


@router.post("/ohlcv/download")
async def download_ohlcv_data(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Start downloading historical OHLCV data
    
    Args:
        symbols: List of coin symbols (default: top 32 coins)
        days: Number of days of history (default: 365)
        timeframe: 'daily' or 'hourly'
    
    Note: Downloads run in background. Check progress with /ohlcv/download/progress
    """
    if not _ohlcv_manager:
        raise HTTPException(status_code=503, detail="OHLCV manager not initialized")
    
    # Check if already running
    progress = _ohlcv_manager.get_download_progress()
    if progress['running']:
        return {
            'status': 'already_running',
            'progress': progress
        }
    
    # Start download in background
    background_tasks.add_task(
        _ohlcv_manager.download_historical_data,
        request.symbols,
        request.days,
        request.timeframe
    )
    
    return {
        'status': 'started',
        'message': f'Downloading {len(request.symbols or _ohlcv_manager.training_coins)} coins, {request.days} days each',
        'check_progress': '/api/data/ohlcv/download/progress'
    }


@router.get("/ohlcv/download/progress")
async def get_download_progress():
    """Get current download progress"""
    if not _ohlcv_manager:
        raise HTTPException(status_code=503, detail="OHLCV manager not initialized")
    
    return _ohlcv_manager.get_download_progress()


@router.get("/ohlcv/training-data")
async def get_training_data(
    symbols: Optional[str] = None,
    min_records: int = 100,
    timeframe: str = "daily"
):
    """
    Get OHLCV data formatted for ML/DL training
    
    Args:
        symbols: Comma-separated list of symbols (default: top 10 coins)
        min_records: Minimum records per symbol
        timeframe: 'daily' or 'hourly'
    """
    if not _ohlcv_manager:
        raise HTTPException(status_code=503, detail="OHLCV manager not initialized")
    
    symbol_list = symbols.split(',') if symbols else None
    
    return await _ohlcv_manager.get_training_data(
        symbols=symbol_list,
        min_records=min_records,
        timeframe=timeframe
    )


@router.post("/ohlcv/download-sync")
async def download_ohlcv_sync(request: DownloadRequest):
    """
    Download OHLCV data synchronously (blocks until complete)
    Use for smaller downloads only
    """
    if not _ohlcv_manager:
        raise HTTPException(status_code=503, detail="OHLCV manager not initialized")
    
    # Limit sync download to 5 coins
    symbols = (request.symbols or _ohlcv_manager.training_coins)[:5]
    
    return await _ohlcv_manager.download_historical_data(
        symbols=symbols,
        days=request.days,
        timeframe=request.timeframe
    )


@router.get("/ohlcv/{symbol}")
async def get_symbol_data(
    symbol: str,
    limit: int = 100,
    timeframe: str = "daily"
):
    """
    Get OHLCV data for a specific symbol
    
    Args:
        symbol: Coin symbol (BTC, ETH, etc.)
        limit: Number of records to return
        timeframe: 'daily' or 'hourly'
    """
    if not _ohlcv_manager:
        raise HTTPException(status_code=503, detail="OHLCV manager not initialized")
    
    cursor = _ohlcv_manager.db.ohlcv_data.find(
        {'symbol': symbol.upper(), 'timeframe': timeframe},
        {'_id': 0}
    ).sort('timestamp', -1).limit(limit)
    
    data = await cursor.to_list(length=limit)
    
    return {
        'symbol': symbol.upper(),
        'count': len(data),
        'timeframe': timeframe,
        'data': data
    }


@router.get("/status")
async def get_data_service_status():
    """Get OHLCV data service status"""
    if not _ohlcv_manager:
        return {'initialized': False}
    
    stats = await _ohlcv_manager.get_stats()
    
    return {
        'initialized': True,
        'stats': stats,
        'training_coins': _ohlcv_manager.training_coins[:10],
        'download_progress': _ohlcv_manager.get_download_progress()
    }

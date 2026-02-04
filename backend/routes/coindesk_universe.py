"""
CoinDesk Universe API Routes
Endpoints for syncing CoinDesk data and downloading OHLCV.
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional
from datetime import datetime, timezone
import asyncio

router = APIRouter(prefix="/coindesk-universe", tags=["CoinDesk Universe"])

# Dependencies
_coindesk_universe = None
_sync_status = {
    "coins_sync": {"running": False, "progress": 0, "total": 0},
    "cross_ref": {"running": False},
    "ohlcv_download": {"running": False, "progress": 0, "total": 0, "current_coin": ""}
}

def set_dependencies(coindesk_universe):
    global _coindesk_universe
    _coindesk_universe = coindesk_universe


@router.get("/status")
async def get_universe_status():
    """
    Get status of CoinDesk universe sync and OHLCV data.
    """
    if not _coindesk_universe:
        raise HTTPException(status_code=503, detail="CoinDesk Universe service not initialized")
    
    stats = await _coindesk_universe.get_universe_stats()
    stats["sync_status"] = _sync_status
    
    return stats


@router.post("/sync-coins")
async def sync_all_coindesk_coins(background_tasks: BackgroundTasks):
    """
    Sync all 3,000+ coins from CoinDesk API.
    Runs in background - check /status for progress.
    """
    if not _coindesk_universe:
        raise HTTPException(status_code=503, detail="CoinDesk Universe service not initialized")
    
    if _sync_status["coins_sync"]["running"]:
        return {"status": "already_running", "progress": _sync_status["coins_sync"]}
    
    async def run_sync():
        _sync_status["coins_sync"]["running"] = True
        _sync_status["coins_sync"]["progress"] = 0
        
        def progress_cb(page, total):
            _sync_status["coins_sync"]["progress"] = page
            _sync_status["coins_sync"]["total"] = total
        
        try:
            result = await _coindesk_universe.sync_all_coins(progress_callback=progress_cb)
            _sync_status["coins_sync"]["result"] = result
        finally:
            _sync_status["coins_sync"]["running"] = False
    
    background_tasks.add_task(run_sync)
    
    return {
        "status": "started",
        "message": "Syncing all CoinDesk coins in background. Check /status for progress.",
        "estimated_time": "2-3 minutes"
    }


@router.post("/sync-coins-blocking")
async def sync_all_coindesk_coins_blocking():
    """
    Sync all CoinDesk coins (blocking - waits for completion).
    Use this for immediate results.
    """
    if not _coindesk_universe:
        raise HTTPException(status_code=503, detail="CoinDesk Universe service not initialized")
    
    return await _coindesk_universe.sync_all_coins()


@router.post("/cross-reference")
async def cross_reference_with_kraken():
    """
    Cross-reference CoinDesk coins with Kraken tradeable coins.
    Identifies which coins can be traded on Kraken.
    """
    if not _coindesk_universe:
        raise HTTPException(status_code=503, detail="CoinDesk Universe service not initialized")
    
    return await _coindesk_universe.cross_reference_with_kraken()


@router.post("/download-ohlcv")
async def download_ohlcv_for_tradeable(
    background_tasks: BackgroundTasks,
    days: int = Query(365, description="Number of days of history"),
    limit: Optional[int] = Query(None, description="Limit number of coins")
):
    """
    Download OHLCV historical data for all tradeable coins.
    Runs in background - check /status for progress.
    """
    if not _coindesk_universe:
        raise HTTPException(status_code=503, detail="CoinDesk Universe service not initialized")
    
    if _sync_status["ohlcv_download"]["running"]:
        return {"status": "already_running", "progress": _sync_status["ohlcv_download"]}
    
    async def run_download():
        _sync_status["ohlcv_download"]["running"] = True
        _sync_status["ohlcv_download"]["progress"] = 0
        
        def progress_cb(current, total, symbol, records):
            _sync_status["ohlcv_download"]["progress"] = current
            _sync_status["ohlcv_download"]["total"] = total
            _sync_status["ohlcv_download"]["current_coin"] = symbol
            _sync_status["ohlcv_download"]["last_records"] = records
        
        try:
            result = await _coindesk_universe.download_ohlcv_for_tradeable(
                days=days,
                limit=limit,
                progress_callback=progress_cb
            )
            _sync_status["ohlcv_download"]["result"] = {
                "coins_processed": result["coins_processed"],
                "total_records": result["total_records"],
                "errors_count": len(result["errors"])
            }
        finally:
            _sync_status["ohlcv_download"]["running"] = False
    
    background_tasks.add_task(run_download)
    
    return {
        "status": "started",
        "message": f"Downloading {days} days of OHLCV data for tradeable coins. Check /status for progress.",
        "estimated_time": f"~{limit or 500} coins × 0.3s = ~{(limit or 500) * 0.3 / 60:.0f} minutes"
    }


@router.post("/download-ohlcv-blocking")
async def download_ohlcv_blocking(
    days: int = Query(365, description="Number of days of history"),
    limit: Optional[int] = Query(50, description="Limit number of coins")
):
    """
    Download OHLCV data (blocking - waits for completion).
    Use limit parameter for faster results.
    """
    if not _coindesk_universe:
        raise HTTPException(status_code=503, detail="CoinDesk Universe service not initialized")
    
    return await _coindesk_universe.download_ohlcv_for_tradeable(days=days, limit=limit)


@router.get("/matched-coins")
async def get_matched_coins(
    limit: int = Query(100, description="Max results")
):
    """
    Get coins that exist on both CoinDesk and Kraken (tradeable).
    """
    if not _coindesk_universe:
        raise HTTPException(status_code=503, detail="CoinDesk Universe service not initialized")
    
    coins = await _coindesk_universe.db["coin_cross_reference"].find(
        {"tradeable_on_kraken": True},
        {"_id": 0}
    ).sort("market_cap_rank", 1).limit(limit).to_list(limit)
    
    return {
        "count": len(coins),
        "coins": coins
    }


@router.get("/ohlcv/{symbol}")
async def get_coin_ohlcv(
    symbol: str,
    limit: int = Query(30, description="Number of days")
):
    """
    Get OHLCV data for a specific coin.
    """
    if not _coindesk_universe:
        raise HTTPException(status_code=503, detail="CoinDesk Universe service not initialized")
    
    data = await _coindesk_universe.db["historical_ohlcv"].find(
        {"symbol": symbol.upper()},
        {"_id": 0}
    ).sort("date", -1).limit(limit).to_list(limit)
    
    return {
        "symbol": symbol.upper(),
        "count": len(data),
        "data": data
    }

"""
Enhanced Data API Routes
Routes for:
- Kraken Universe Management
- On-Chain Metrics
- Multi-Timeframe Historical Data
- Data Provider API Key Management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import os

router = APIRouter(prefix="/enhanced-data", tags=["Enhanced Data"])

# Service dependencies (set during initialization)
_db = None
_kraken_universe_mgr = None
_onchain_service = None
_mtf_service = None


def set_dependencies(db, kraken_universe_mgr=None, onchain_service=None, mtf_service=None):
    """Set service dependencies"""
    global _db, _kraken_universe_mgr, _onchain_service, _mtf_service
    _db = db
    _kraken_universe_mgr = kraken_universe_mgr
    _onchain_service = onchain_service
    _mtf_service = mtf_service


# ============ REQUEST MODELS ============

class SyncUniverseRequest(BaseModel):
    force: bool = False


class DownloadHistoryRequest(BaseModel):
    symbols: Optional[List[str]] = None
    timeframes: Optional[List[str]] = None
    max_days: int = 365


class OnChainRequest(BaseModel):
    symbols: List[str] = ["BTC", "ETH"]


class DataProviderKeysRequest(BaseModel):
    blockchair_api_key: Optional[str] = None
    glassnode_api_key: Optional[str] = None
    cryptoquant_api_key: Optional[str] = None
    coinglass_api_key: Optional[str] = None
    santiment_api_key: Optional[str] = None


# ============ KRAKEN UNIVERSE ROUTES ============

@router.get("/kraken-universe/stats")
async def get_universe_stats():
    """Get Kraken trading universe statistics"""
    if not _kraken_universe_mgr:
        raise HTTPException(status_code=500, detail="Kraken Universe Manager not initialized")
    
    return await _kraken_universe_mgr.get_universe_stats()


@router.post("/kraken-universe/sync")
async def sync_kraken_universe(background_tasks: BackgroundTasks):
    """
    Sync all tradeable coins from Kraken.
    Discovers new coins automatically.
    """
    if not _kraken_universe_mgr:
        raise HTTPException(status_code=500, detail="Kraken Universe Manager not initialized")
    
    # Run sync in background
    background_tasks.add_task(_kraken_universe_mgr.sync_universe)
    
    return {
        "status": "started",
        "message": "Kraken universe sync started in background. Check /stats for results."
    }


@router.get("/kraken-universe/sync-now")
async def sync_universe_now():
    """Sync Kraken universe immediately (synchronous)"""
    if not _kraken_universe_mgr:
        raise HTTPException(status_code=500, detail="Kraken Universe Manager not initialized")
    
    return await _kraken_universe_mgr.sync_universe()


@router.get("/kraken-universe/coins")
async def get_all_coins(quote_currency: str = "USD"):
    """Get all tradeable coins for a quote currency"""
    if not _kraken_universe_mgr:
        raise HTTPException(status_code=500, detail="Kraken Universe Manager not initialized")
    
    coins = await _kraken_universe_mgr.get_all_tradeable_coins(quote_currency)
    
    return {
        "quote_currency": quote_currency,
        "coins": coins,
        "count": len(coins)
    }


@router.get("/kraken-universe/unique-coins")
async def get_unique_coins():
    """Get list of all unique coin symbols"""
    if not _kraken_universe_mgr:
        raise HTTPException(status_code=500, detail="Kraken Universe Manager not initialized")
    
    coins = await _kraken_universe_mgr.get_all_unique_coins()
    
    return {
        "coins": coins,
        "count": len(coins)
    }


@router.get("/kraken-universe/check-new")
async def check_for_new_coins():
    """Check if Kraken has listed any new coins"""
    if not _kraken_universe_mgr:
        raise HTTPException(status_code=500, detail="Kraken Universe Manager not initialized")
    
    return await _kraken_universe_mgr.check_for_new_coins()


@router.get("/kraken-universe/coin/{symbol}")
async def get_coin_pairs(symbol: str):
    """Get all trading pairs for a specific coin"""
    if not _kraken_universe_mgr:
        raise HTTPException(status_code=500, detail="Kraken Universe Manager not initialized")
    
    pairs = await _kraken_universe_mgr.get_coin_pairs(symbol)
    
    return {
        "symbol": symbol.upper(),
        "pairs": pairs,
        "count": len(pairs)
    }


# ============ ON-CHAIN METRICS ROUTES ============

@router.get("/onchain/supported")
async def get_supported_chains():
    """Get list of supported chains for on-chain metrics"""
    if not _onchain_service:
        raise HTTPException(status_code=500, detail="On-Chain Metrics Service not initialized")
    
    return await _onchain_service.get_supported_chains()


@router.get("/onchain/btc/stats")
async def get_btc_network_stats():
    """Get Bitcoin network statistics"""
    if not _onchain_service:
        raise HTTPException(status_code=500, detail="On-Chain Metrics Service not initialized")
    
    return await _onchain_service.get_btc_stats()


@router.get("/onchain/btc/mempool")
async def get_btc_mempool():
    """Get Bitcoin mempool statistics"""
    if not _onchain_service:
        raise HTTPException(status_code=500, detail="On-Chain Metrics Service not initialized")
    
    return await _onchain_service.get_btc_mempool()


@router.get("/onchain/btc/fees")
async def get_btc_fees():
    """Get Bitcoin fee estimates"""
    if not _onchain_service:
        raise HTTPException(status_code=500, detail="On-Chain Metrics Service not initialized")
    
    return await _onchain_service.get_btc_fee_estimates()


@router.get("/onchain/btc/difficulty")
async def get_btc_difficulty():
    """Get Bitcoin difficulty adjustment info"""
    if not _onchain_service:
        raise HTTPException(status_code=500, detail="On-Chain Metrics Service not initialized")
    
    return await _onchain_service.get_btc_difficulty_adjustment()


@router.get("/onchain/{symbol}/stats")
async def get_chain_stats(symbol: str):
    """Get blockchain statistics for any supported chain"""
    if not _onchain_service:
        raise HTTPException(status_code=500, detail="On-Chain Metrics Service not initialized")
    
    return await _onchain_service.get_chain_stats(symbol)


@router.get("/onchain/{symbol}/whales")
async def get_whale_transactions(symbol: str, min_usd: float = 1000000):
    """Get large transactions (whale movements) for a chain"""
    if not _onchain_service:
        raise HTTPException(status_code=500, detail="On-Chain Metrics Service not initialized")
    
    txs = await _onchain_service.get_large_transactions(symbol, min_usd)
    
    return {
        "symbol": symbol.upper(),
        "min_usd": min_usd,
        "transactions": txs,
        "count": len(txs)
    }


@router.get("/onchain/{symbol}/comprehensive")
async def get_comprehensive_metrics(symbol: str):
    """Get comprehensive on-chain metrics for a coin"""
    if not _onchain_service:
        raise HTTPException(status_code=500, detail="On-Chain Metrics Service not initialized")
    
    return await _onchain_service.get_comprehensive_metrics(symbol)


@router.post("/onchain/batch")
async def batch_fetch_onchain(request: OnChainRequest):
    """Fetch on-chain metrics for multiple chains"""
    if not _onchain_service:
        raise HTTPException(status_code=500, detail="On-Chain Metrics Service not initialized")
    
    return await _onchain_service.batch_fetch_metrics(request.symbols)


@router.post("/onchain/{symbol}/snapshot")
async def store_metrics_snapshot(symbol: str):
    """Store on-chain metrics snapshot to database"""
    if not _onchain_service:
        raise HTTPException(status_code=500, detail="On-Chain Metrics Service not initialized")
    
    return await _onchain_service.store_metrics_snapshot(symbol)


@router.get("/onchain/{symbol}/history")
async def get_metrics_history(symbol: str, days: int = 30, limit: int = 100):
    """Get historical on-chain metrics from database"""
    if not _onchain_service:
        raise HTTPException(status_code=500, detail="On-Chain Metrics Service not initialized")
    
    data = await _onchain_service.get_historical_metrics(symbol, days, limit)
    
    return {
        "symbol": symbol.upper(),
        "days": days,
        "data": data,
        "count": len(data)
    }


# ============ MULTI-TIMEFRAME ROUTES ============

@router.get("/multitimeframe/stats")
async def get_mtf_storage_stats():
    """Get statistics about stored multi-timeframe data"""
    if not _mtf_service:
        raise HTTPException(status_code=500, detail="Multi-Timeframe Service not initialized")
    
    return await _mtf_service.get_storage_stats()


@router.post("/multitimeframe/download/{symbol}")
async def download_symbol_timeframes(
    symbol: str,
    background_tasks: BackgroundTasks,
    timeframes: Optional[str] = None
):
    """
    Download multi-timeframe data for a symbol.
    
    Args:
        symbol: Coin symbol (BTC, ETH, etc.)
        timeframes: Comma-separated timeframes (default: all)
    """
    if not _mtf_service:
        raise HTTPException(status_code=500, detail="Multi-Timeframe Service not initialized")
    
    tf_list = timeframes.split(",") if timeframes else None
    
    background_tasks.add_task(
        _mtf_service.download_all_timeframes,
        symbol,
        None,
        tf_list
    )
    
    return {
        "status": "started",
        "symbol": symbol.upper(),
        "timeframes": tf_list or "all",
        "message": "Download started in background"
    }


@router.get("/multitimeframe/download-now/{symbol}")
async def download_symbol_now(symbol: str, timeframes: Optional[str] = None):
    """Download multi-timeframe data immediately (synchronous)"""
    if not _mtf_service:
        raise HTTPException(status_code=500, detail="Multi-Timeframe Service not initialized")
    
    tf_list = timeframes.split(",") if timeframes else None
    
    return await _mtf_service.download_all_timeframes(symbol, None, tf_list)


@router.get("/multitimeframe/{symbol}/{timeframe}")
async def get_ohlc_data(
    symbol: str,
    timeframe: str,
    limit: int = 500
):
    """Get stored OHLC data for a symbol and timeframe"""
    if not _mtf_service:
        raise HTTPException(status_code=500, detail="Multi-Timeframe Service not initialized")
    
    return await _mtf_service.get_ohlc_data(symbol, timeframe, limit=limit)


@router.get("/multitimeframe/{symbol}/multi")
async def get_multi_timeframe_data(
    symbol: str,
    timeframes: Optional[str] = None,
    limit: int = 100
):
    """Get data for multiple timeframes at once"""
    if not _mtf_service:
        raise HTTPException(status_code=500, detail="Multi-Timeframe Service not initialized")
    
    tf_list = timeframes.split(",") if timeframes else ["1h", "4h", "1D"]
    
    return await _mtf_service.get_multi_timeframe_data(symbol, tf_list, limit)


@router.get("/multitimeframe/{symbol}/features")
async def get_training_features(symbol: str, timeframes: Optional[str] = None):
    """Get multi-timeframe features formatted for ML training"""
    if not _mtf_service:
        raise HTTPException(status_code=500, detail="Multi-Timeframe Service not initialized")
    
    tf_list = timeframes.split(",") if timeframes else ["1h", "4h", "1D"]
    
    return await _mtf_service.get_training_features(symbol, tf_list)


@router.post("/multitimeframe/backfill")
async def backfill_all_coins(
    request: DownloadHistoryRequest,
    background_tasks: BackgroundTasks
):
    """
    Backfill historical data for multiple coins.
    Runs in background due to potentially long execution time.
    """
    if not _mtf_service:
        raise HTTPException(status_code=500, detail="Multi-Timeframe Service not initialized")
    
    background_tasks.add_task(
        _mtf_service.backfill_all_kraken_coins,
        request.symbols,
        request.timeframes
    )
    
    return {
        "status": "started",
        "symbols": request.symbols or "all from Kraken universe",
        "timeframes": request.timeframes or ["1h", "4h", "1D"],
        "message": "Backfill started in background. This may take several minutes."
    }


# ============ DATA PROVIDER API KEYS ============

@router.get("/provider-keys/status")
async def get_provider_keys_status():
    """Get status of configured data provider API keys"""
    if not _db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    # Check which keys are configured
    keys_doc = await _db.data_provider_keys.find_one({"_id": "provider_keys"})
    
    configured = {
        "blockchair": False,
        "glassnode": False,
        "cryptoquant": False,
        "coinglass": False,
        "santiment": False
    }
    
    if keys_doc:
        for key in configured.keys():
            configured[key] = bool(keys_doc.get(f"{key}_api_key"))
    
    return {
        "configured": configured,
        "providers": [
            {
                "name": "Blockchair",
                "key": "blockchair",
                "configured": configured["blockchair"],
                "description": "Enhanced on-chain data (10k free requests/day)",
                "signup_url": "https://blockchair.com/api"
            },
            {
                "name": "Glassnode",
                "key": "glassnode",
                "configured": configured["glassnode"],
                "description": "Professional on-chain metrics",
                "signup_url": "https://glassnode.com"
            },
            {
                "name": "CryptoQuant",
                "key": "cryptoquant",
                "configured": configured["cryptoquant"],
                "description": "Exchange flows and whale tracking",
                "signup_url": "https://cryptoquant.com"
            },
            {
                "name": "Coinglass",
                "key": "coinglass",
                "configured": configured["coinglass"],
                "description": "Derivatives and liquidation data",
                "signup_url": "https://coinglass.com/api"
            },
            {
                "name": "Santiment",
                "key": "santiment",
                "configured": configured["santiment"],
                "description": "Social and development metrics",
                "signup_url": "https://santiment.net"
            }
        ]
    }


@router.post("/provider-keys/save")
async def save_provider_keys(request: DataProviderKeysRequest):
    """Save data provider API keys"""
    if not _db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    
    # Build update document (only non-None values)
    update_doc = {"_id": "provider_keys", "updated_at": datetime.utcnow()}
    
    if request.blockchair_api_key is not None:
        update_doc["blockchair_api_key"] = request.blockchair_api_key
    if request.glassnode_api_key is not None:
        update_doc["glassnode_api_key"] = request.glassnode_api_key
    if request.cryptoquant_api_key is not None:
        update_doc["cryptoquant_api_key"] = request.cryptoquant_api_key
    if request.coinglass_api_key is not None:
        update_doc["coinglass_api_key"] = request.coinglass_api_key
    if request.santiment_api_key is not None:
        update_doc["santiment_api_key"] = request.santiment_api_key
    
    # Upsert the keys
    await _db.data_provider_keys.replace_one(
        {"_id": "provider_keys"},
        update_doc,
        upsert=True
    )
    
    # Update service if available
    if _onchain_service:
        _onchain_service.set_api_keys({
            "blockchair": request.blockchair_api_key,
            "glassnode": request.glassnode_api_key,
            "cryptoquant": request.cryptoquant_api_key
        })
    
    return {
        "status": "saved",
        "message": "Data provider API keys updated successfully"
    }


# ============ COMPREHENSIVE DATA STATUS ============

@router.get("/status")
async def get_enhanced_data_status():
    """Get comprehensive status of all enhanced data services"""
    status = {
        "services": {},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Kraken Universe
    if _kraken_universe_mgr:
        try:
            universe_stats = await _kraken_universe_mgr.get_universe_stats()
            status["services"]["kraken_universe"] = {
                "status": "operational",
                "stats": universe_stats
            }
        except Exception as e:
            status["services"]["kraken_universe"] = {
                "status": "error",
                "error": str(e)
            }
    else:
        status["services"]["kraken_universe"] = {"status": "not_initialized"}
    
    # On-Chain Metrics
    if _onchain_service:
        try:
            supported = await _onchain_service.get_supported_chains()
            status["services"]["onchain_metrics"] = {
                "status": "operational",
                "supported_chains": supported["total"]
            }
        except Exception as e:
            status["services"]["onchain_metrics"] = {
                "status": "error",
                "error": str(e)
            }
    else:
        status["services"]["onchain_metrics"] = {"status": "not_initialized"}
    
    # Multi-Timeframe Historical
    if _mtf_service:
        try:
            mtf_stats = await _mtf_service.get_storage_stats()
            status["services"]["multitimeframe"] = {
                "status": "operational",
                "total_records": mtf_stats["total_records"],
                "timeframes": list(mtf_stats["timeframes"].keys())
            }
        except Exception as e:
            status["services"]["multitimeframe"] = {
                "status": "error",
                "error": str(e)
            }
    else:
        status["services"]["multitimeframe"] = {"status": "not_initialized"}
    
    # Provider Keys
    if _db:
        keys_doc = await _db.data_provider_keys.find_one({"_id": "provider_keys"})
        configured_count = 0
        if keys_doc:
            for key in ["blockchair", "glassnode", "cryptoquant", "coinglass", "santiment"]:
                if keys_doc.get(f"{key}_api_key"):
                    configured_count += 1
        
        status["services"]["provider_keys"] = {
            "status": "operational",
            "configured_count": configured_count
        }
    
    return status

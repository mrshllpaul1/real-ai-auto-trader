"""
Kraken Universe API Routes
Endpoints for managing and querying the Kraken coin universe.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timezone

router = APIRouter(prefix="/kraken-universe", tags=["Kraken Universe"])

# Dependencies
_kraken_universe = None

def set_dependencies(kraken_universe):
    global _kraken_universe
    _kraken_universe = kraken_universe


@router.get("/status")
async def get_universe_status():
    """
    Get status and statistics of the Kraken coin universe.
    Shows total coins, pairs availability, and last sync time.
    """
    if not _kraken_universe:
        raise HTTPException(status_code=503, detail="Kraken Universe service not initialized")
    
    return await _kraken_universe.get_universe_stats()


@router.post("/sync")
async def sync_kraken_universe():
    """
    Sync the complete Kraken universe to database.
    Fetches all assets and trading pairs from Kraken API.
    This may take 30-60 seconds.
    """
    if not _kraken_universe:
        raise HTTPException(status_code=503, detail="Kraken Universe service not initialized")
    
    return await _kraken_universe.sync_universe()


@router.get("/coins")
async def get_all_coins(
    has_usd_pair: Optional[bool] = Query(None, description="Filter by USD pair availability"),
    limit: Optional[int] = Query(None, description="Limit results")
):
    """
    Get all coins in the Kraken universe.
    Optionally filter by USD pair availability.
    """
    if not _kraken_universe:
        raise HTTPException(status_code=503, detail="Kraken Universe service not initialized")
    
    coins = await _kraken_universe.get_all_coins(has_usd_pair=has_usd_pair, limit=limit)
    
    return {
        "count": len(coins),
        "coins": coins
    }


@router.get("/coins/{symbol}")
async def get_coin_info(symbol: str):
    """
    Get detailed information for a specific coin.
    Includes all trading pairs and quote currencies.
    """
    if not _kraken_universe:
        raise HTTPException(status_code=503, detail="Kraken Universe service not initialized")
    
    coin = await _kraken_universe.get_coin_info(symbol)
    
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {symbol} not found in Kraken universe")
    
    return coin


@router.get("/search")
async def search_coins(
    q: str = Query(..., description="Search query (symbol or name)"),
    limit: int = Query(20, description="Max results")
):
    """
    Search coins by symbol or name.
    """
    if not _kraken_universe:
        raise HTTPException(status_code=503, detail="Kraken Universe service not initialized")
    
    results = await _kraken_universe.search_coins(q, limit=limit)
    
    return {
        "query": q,
        "count": len(results),
        "results": results
    }


@router.get("/tradeable")
async def get_tradeable_coins():
    """
    Get all coins that can be traded against USD.
    These are the most relevant for the trading bot.
    """
    if not _kraken_universe:
        raise HTTPException(status_code=503, detail="Kraken Universe service not initialized")
    
    coins = await _kraken_universe.get_all_coins(has_usd_pair=True)
    
    # Sort by number of pairs (more pairs = more liquid)
    coins.sort(key=lambda x: x.get('num_pairs', 0), reverse=True)
    
    return {
        "count": len(coins),
        "description": "All coins with USD trading pairs on Kraken",
        "coins": [
            {
                "symbol": c["symbol"],
                "name": c.get("name", c["symbol"]),
                "num_pairs": c.get("num_pairs", 0),
                "has_btc_pair": c.get("has_btc_pair", False),
                "has_eth_pair": c.get("has_eth_pair", False)
            }
            for c in coins
        ]
    }

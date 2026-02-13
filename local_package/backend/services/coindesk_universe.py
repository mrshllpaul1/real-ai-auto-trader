"""
CoinDesk Universe Service
Syncs all coins from CoinDesk and cross-references with Kraken.
Downloads OHLCV historical data for tradeable coins.
"""
import httpx
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)

class CoinDeskUniverseService:
    """
    Service to sync CoinDesk coin universe and download OHLCV data.
    """
    
    COINDESK_API_BASE = "https://data-api.coindesk.com"
    
    def __init__(self, db):
        self.db = db
        self.api_key = os.environ.get('COINDESK_API_KEY', '')
        self.collection = "coindesk_universe"
        self.ohlcv_collection = "historical_ohlcv"
        self.cross_ref_collection = "coin_cross_reference"
        
    def _get_headers(self):
        return {"x-api-key": self.api_key}
    
    async def sync_all_coins(self, progress_callback=None) -> Dict[str, Any]:
        """
        Sync all coins from CoinDesk API (3,000+ coins).
        """
        logger.info("Starting CoinDesk universe sync...")
        
        results = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "total_coins": 0,
            "pages_fetched": 0,
            "errors": []
        }
        
        all_coins = []
        page = 1
        page_size = 100
        
        async with httpx.AsyncClient(timeout=30) as client:
            while True:
                try:
                    response = await client.get(
                        f"{self.COINDESK_API_BASE}/asset/v1/top/list",
                        params={"page": page, "page_size": page_size},
                        headers=self._get_headers()
                    )
                    data = response.json()
                    
                    if data.get('Err'):
                        results["errors"].append(f"Page {page}: {data.get('Err')}")
                        break
                    
                    coins = data.get('Data', {}).get('LIST', [])
                    
                    if not coins:
                        break
                    
                    all_coins.extend(coins)
                    results["pages_fetched"] = page
                    
                    if progress_callback:
                        progress_callback(page, len(all_coins))
                    
                    logger.info(f"Page {page}: {len(coins)} coins (total: {len(all_coins)})")
                    
                    page += 1
                    await asyncio.sleep(0.2)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Error fetching page {page}: {e}")
                    results["errors"].append(f"Page {page}: {str(e)}")
                    break
        
        # Store coins in database
        stored = 0
        for coin in all_coins:
            try:
                coin_doc = {
                    "symbol": coin.get('SYMBOL', ''),
                    "name": coin.get('NAME', ''),
                    "coindesk_id": coin.get('ID', ''),
                    "asset_type": coin.get('ASSET_TYPE', ''),
                    "logo_url": coin.get('LOGO_URL', ''),
                    "launch_date": coin.get('LAUNCH_DATE', ''),
                    "market_cap_rank": coin.get('TOPLIST_RANK', 0),
                    "price_usd": coin.get('PRICE_USD', 0),
                    "market_cap_usd": coin.get('TOTAL_MKT_CAP_USD', 0),
                    "volume_24h_usd": coin.get('SPOT_MOVING_24_HOUR_QUOTE_VOLUME_USD', 0),
                    "change_24h_pct": coin.get('SPOT_MOVING_24_HOUR_CHANGE_PERCENTAGE_USD', 0),
                    "circulating_supply": coin.get('CIRCULATING_SUPPLY', 0),
                    "max_supply": coin.get('MAX_SUPPLY', 0),
                    "source": "coindesk",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                await self.db[self.collection].update_one(
                    {"symbol": coin_doc["symbol"]},
                    {"$set": coin_doc},
                    upsert=True
                )
                stored += 1
            except Exception as e:
                logger.error(f"Error storing coin {coin.get('SYMBOL')}: {e}")
        
        results["total_coins"] = stored
        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Synced {stored} coins from CoinDesk")
        
        return results
    
    async def cross_reference_with_kraken(self) -> Dict[str, Any]:
        """
        Cross-reference CoinDesk coins with Kraken tradeable coins.
        """
        logger.info("Cross-referencing CoinDesk with Kraken...")
        
        results = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "coindesk_total": 0,
            "kraken_total": 0,
            "matched": 0,
            "coindesk_only": 0,
            "kraken_only": 0,
            "matches": []
        }
        
        # Get all CoinDesk coins
        coindesk_coins = await self.db[self.collection].find(
            {}, {"_id": 0, "symbol": 1, "name": 1, "market_cap_rank": 1}
        ).to_list(5000)
        results["coindesk_total"] = len(coindesk_coins)
        
        # Get all Kraken coins
        kraken_coins = await self.db["kraken_universe"].find(
            {}, {"_id": 0, "symbol": 1, "name": 1, "has_usd_pair": 1}
        ).to_list(1000)
        results["kraken_total"] = len(kraken_coins)
        
        # Create lookup sets
        coindesk_symbols = {c["symbol"].upper() for c in coindesk_coins}
        kraken_symbols = {c["symbol"].upper() for c in kraken_coins}
        
        # Handle Kraken's special symbols
        kraken_symbol_map = {
            "XBT": "BTC",
            "XDG": "DOGE",
            "XXBT": "BTC",
            "XETH": "ETH",
        }
        
        # Normalize Kraken symbols
        kraken_normalized = set()
        for sym in kraken_symbols:
            normalized = kraken_symbol_map.get(sym, sym)
            kraken_normalized.add(normalized)
        
        # Find matches
        matched = coindesk_symbols & kraken_normalized
        coindesk_only = coindesk_symbols - kraken_normalized
        kraken_only = kraken_normalized - coindesk_symbols
        
        results["matched"] = len(matched)
        results["coindesk_only"] = len(coindesk_only)
        results["kraken_only"] = len(kraken_only)
        
        # Store cross-reference data
        for symbol in matched:
            coindesk_info = next((c for c in coindesk_coins if c["symbol"].upper() == symbol), {})
            kraken_info = next((c for c in kraken_coins if c["symbol"].upper() == symbol or 
                               kraken_symbol_map.get(c["symbol"].upper()) == symbol), {})
            
            cross_ref = {
                "symbol": symbol,
                "coindesk_name": coindesk_info.get("name", ""),
                "kraken_name": kraken_info.get("name", ""),
                "market_cap_rank": coindesk_info.get("market_cap_rank", 0),
                "tradeable_on_kraken": True,
                "has_usd_pair": kraken_info.get("has_usd_pair", False),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db[self.cross_ref_collection].update_one(
                {"symbol": symbol},
                {"$set": cross_ref},
                upsert=True
            )
            
            results["matches"].append({
                "symbol": symbol,
                "name": coindesk_info.get("name", ""),
                "rank": coindesk_info.get("market_cap_rank", 0)
            })
        
        # Sort matches by rank
        results["matches"].sort(key=lambda x: x.get("rank", 9999))
        
        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Cross-reference complete: {len(matched)} matched coins")
        
        return results
    
    async def download_ohlcv_for_tradeable(self, 
                                           days: int = 365,
                                           limit: int = None,
                                           progress_callback=None) -> Dict[str, Any]:
        """
        Download OHLCV data for all tradeable (Kraken) coins from CoinDesk.
        """
        logger.info(f"Starting OHLCV download for tradeable coins ({days} days)...")
        
        results = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "coins_to_process": 0,
            "coins_processed": 0,
            "total_records": 0,
            "errors": [],
            "coins_completed": []
        }
        
        # Get matched coins (tradeable on Kraken)
        matched_coins = await self.db[self.cross_ref_collection].find(
            {"tradeable_on_kraken": True},
            {"_id": 0, "symbol": 1, "market_cap_rank": 1}
        ).sort("market_cap_rank", 1).to_list(1000)
        
        if limit:
            matched_coins = matched_coins[:limit]
        
        results["coins_to_process"] = len(matched_coins)
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        async with httpx.AsyncClient(timeout=60) as client:
            for i, coin in enumerate(matched_coins):
                symbol = coin["symbol"]
                
                try:
                    # Fetch daily OHLCV from CoinDesk
                    response = await client.get(
                        f"{self.COINDESK_API_BASE}/index/cc/v1/historical/days",
                        params={
                            "market": "cadli",
                            "instrument": f"{symbol}-USD",
                            "limit": days,
                            "aggregate": 1,
                            "fill": "true",
                            "response_format": "JSON"
                        },
                        headers=self._get_headers()
                    )
                    
                    data = response.json()
                    
                    if data.get('Err'):
                        # Try alternative format
                        response = await client.get(
                            f"{self.COINDESK_API_BASE}/index/cc/v1/historical/days",
                            params={
                                "market": "ccagg",
                                "instrument": f"{symbol}-USD",
                                "limit": days,
                                "aggregate": 1,
                                "fill": "true",
                                "response_format": "JSON"
                            },
                            headers=self._get_headers()
                        )
                        data = response.json()
                    
                    ohlcv_data = data.get('Data', [])
                    
                    if not ohlcv_data:
                        results["errors"].append(f"{symbol}: No data")
                        continue
                    
                    # Store OHLCV records
                    records_stored = 0
                    for record in ohlcv_data:
                        try:
                            timestamp = record.get('TIMESTAMP', record.get('TIME', 0))
                            if isinstance(timestamp, int):
                                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                            else:
                                dt = datetime.now(timezone.utc)
                            
                            ohlcv_doc = {
                                "symbol": symbol,
                                "timestamp": dt.isoformat(),
                                "date": dt.strftime("%Y-%m-%d"),
                                "open": float(record.get('OPEN', 0)),
                                "high": float(record.get('HIGH', 0)),
                                "low": float(record.get('LOW', 0)),
                                "close": float(record.get('CLOSE', 0)),
                                "volume": float(record.get('VOLUME', record.get('TOTAL_VOLUME', 0))),
                                "volume_to": float(record.get('VOLUME_QUOTE', record.get('TOTAL_VOLUME_USD', 0))),
                                "source": "coindesk"
                            }
                            
                            await self.db[self.ohlcv_collection].update_one(
                                {"symbol": symbol, "date": ohlcv_doc["date"]},
                                {"$set": ohlcv_doc},
                                upsert=True
                            )
                            records_stored += 1
                        except Exception as e:
                            pass
                    
                    results["coins_processed"] += 1
                    results["total_records"] += records_stored
                    results["coins_completed"].append({
                        "symbol": symbol,
                        "records": records_stored
                    })
                    
                    if progress_callback:
                        progress_callback(i + 1, len(matched_coins), symbol, records_stored)
                    
                    logger.info(f"[{i+1}/{len(matched_coins)}] {symbol}: {records_stored} records")
                    
                    # Rate limiting
                    await asyncio.sleep(0.3)
                    
                except Exception as e:
                    logger.error(f"Error downloading {symbol}: {e}")
                    results["errors"].append(f"{symbol}: {str(e)}")
        
        results["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Store download metadata
        await self.db["ohlcv_download_log"].insert_one({
            "type": "tradeable_ohlcv_download",
            "timestamp": datetime.now(timezone.utc),
            "results": {
                "coins_processed": results["coins_processed"],
                "total_records": results["total_records"],
                "errors_count": len(results["errors"])
            }
        })
        
        logger.info(f"OHLCV download complete: {results['coins_processed']} coins, {results['total_records']} records")
        
        return results
    
    async def get_universe_stats(self) -> Dict[str, Any]:
        """Get statistics about the synced data"""
        coindesk_count = await self.db[self.collection].count_documents({})
        kraken_count = await self.db["kraken_universe"].count_documents({})
        matched_count = await self.db[self.cross_ref_collection].count_documents({"tradeable_on_kraken": True})
        ohlcv_count = await self.db[self.ohlcv_collection].count_documents({})
        ohlcv_coins = await self.db[self.ohlcv_collection].distinct("symbol")
        
        # Get date range
        earliest = await self.db[self.ohlcv_collection].find_one(
            {}, sort=[("date", 1)]
        )
        latest = await self.db[self.ohlcv_collection].find_one(
            {}, sort=[("date", -1)]
        )
        
        return {
            "coindesk_coins": coindesk_count,
            "kraken_coins": kraken_count,
            "matched_tradeable": matched_count,
            "ohlcv_records": ohlcv_count,
            "coins_with_ohlcv": len(ohlcv_coins),
            "ohlcv_date_range": {
                "earliest": earliest.get("date") if earliest else None,
                "latest": latest.get("date") if latest else None
            }
        }


# Global instance
_coindesk_universe = None

def get_coindesk_universe(db=None):
    global _coindesk_universe
    if _coindesk_universe is None and db is not None:
        _coindesk_universe = CoinDeskUniverseService(db)
    return _coindesk_universe

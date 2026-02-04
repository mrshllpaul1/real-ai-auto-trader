"""
Kraken Universe Service
Fetches and maintains the complete list of tradeable coins from Kraken exchange.
"""
import httpx
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class KrakenUniverseService:
    """
    Service to fetch and maintain the complete Kraken coin universe.
    """
    
    KRAKEN_API_BASE = "https://api.kraken.com/0/public"
    
    def __init__(self, db):
        self.db = db
        self.collection = "kraken_universe"
        self.pairs_collection = "kraken_pairs"
        
    async def fetch_all_assets(self) -> Dict[str, Any]:
        """Fetch all assets from Kraken API"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.KRAKEN_API_BASE}/Assets")
            data = response.json()
            
            if data.get('error'):
                logger.error(f"Kraken API error: {data['error']}")
                return {}
            
            return data.get('result', {})
    
    async def fetch_all_pairs(self) -> Dict[str, Any]:
        """Fetch all trading pairs from Kraken API"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.KRAKEN_API_BASE}/AssetPairs")
            data = response.json()
            
            if data.get('error'):
                logger.error(f"Kraken API error: {data['error']}")
                return {}
            
            return data.get('result', {})
    
    async def fetch_ticker_data(self, pairs: List[str]) -> Dict[str, Any]:
        """Fetch ticker data for given pairs"""
        # Kraken limits to ~50 pairs per request
        all_tickers = {}
        
        async with httpx.AsyncClient(timeout=30) as client:
            for i in range(0, len(pairs), 50):
                batch = pairs[i:i+50]
                pair_str = ','.join(batch)
                
                try:
                    response = await client.get(
                        f"{self.KRAKEN_API_BASE}/Ticker",
                        params={'pair': pair_str}
                    )
                    data = response.json()
                    
                    if not data.get('error'):
                        all_tickers.update(data.get('result', {}))
                    
                    await asyncio.sleep(0.5)  # Rate limiting
                except Exception as e:
                    logger.error(f"Error fetching tickers: {e}")
                    
        return all_tickers
    
    async def sync_universe(self) -> Dict[str, Any]:
        """
        Sync the complete Kraken universe to database.
        This fetches all assets, pairs, and basic market data.
        """
        logger.info("Starting Kraken universe sync...")
        
        results = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "assets": 0,
            "pairs": 0,
            "coins_synced": 0,
            "errors": []
        }
        
        try:
            # Fetch assets
            assets = await self.fetch_all_assets()
            results["assets"] = len(assets)
            logger.info(f"Fetched {len(assets)} assets")
            
            # Fetch trading pairs
            pairs = await self.fetch_all_pairs()
            results["pairs"] = len(pairs)
            logger.info(f"Fetched {len(pairs)} trading pairs")
            
            # Extract unique tradeable coins
            coins = {}
            for pair_name, pair_info in pairs.items():
                base = pair_info.get('base', '')
                quote = pair_info.get('quote', '')
                
                # Clean up base name
                clean_base = base
                if base.startswith('X') and len(base) > 3:
                    clean_base = base[1:]
                elif base.startswith('Z'):
                    continue  # Skip fiat
                
                # Skip staked versions
                if '.S' in clean_base or '.M' in clean_base or '.B' in clean_base:
                    continue
                
                # Skip fiat quotes for determining tradeable coins
                quote_clean = quote
                if quote.startswith('Z') or quote in ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY']:
                    pass  # This is a valid trading pair
                
                if clean_base not in coins:
                    asset_info = assets.get(base, {})
                    coins[clean_base] = {
                        "symbol": clean_base,
                        "kraken_symbol": base,
                        "name": asset_info.get('altname', clean_base),
                        "aclass": asset_info.get('aclass', 'currency'),
                        "decimals": asset_info.get('decimals', 8),
                        "display_decimals": asset_info.get('display_decimals', 5),
                        "trading_pairs": [],
                        "quote_currencies": set(),
                        "has_usd_pair": False,
                        "has_btc_pair": False,
                        "has_eth_pair": False,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                
                # Add pair info
                coins[clean_base]["trading_pairs"].append({
                    "pair": pair_name,
                    "altname": pair_info.get('altname', pair_name),
                    "base": base,
                    "quote": quote,
                    "lot_decimals": pair_info.get('lot_decimals', 8),
                    "pair_decimals": pair_info.get('pair_decimals', 5),
                    "ordermin": pair_info.get('ordermin', '0'),
                    "status": pair_info.get('status', 'online')
                })
                
                # Track quote currencies
                quote_symbol = quote[1:] if quote.startswith('Z') or quote.startswith('X') else quote
                coins[clean_base]["quote_currencies"].add(quote_symbol)
                
                # Check for major pairs
                if quote in ['ZUSD', 'USD', 'USDT', 'USDC']:
                    coins[clean_base]["has_usd_pair"] = True
                if quote in ['XXBT', 'XBT', 'BTC']:
                    coins[clean_base]["has_btc_pair"] = True
                if quote in ['XETH', 'ETH']:
                    coins[clean_base]["has_eth_pair"] = True
            
            # Convert sets to lists for MongoDB
            for symbol, coin_data in coins.items():
                coin_data["quote_currencies"] = list(coin_data["quote_currencies"])
                coin_data["num_pairs"] = len(coin_data["trading_pairs"])
            
            # Store in database
            stored = 0
            for symbol, coin_data in coins.items():
                await self.db[self.collection].update_one(
                    {"symbol": symbol},
                    {"$set": coin_data},
                    upsert=True
                )
                stored += 1
            
            results["coins_synced"] = stored
            results["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"Synced {stored} coins to database")
            
            # Store sync metadata
            await self.db["kraken_sync_log"].insert_one({
                "type": "universe_sync",
                "timestamp": datetime.now(timezone.utc),
                "results": results
            })
            
        except Exception as e:
            logger.error(f"Error syncing Kraken universe: {e}")
            results["errors"].append(str(e))
        
        return results
    
    async def get_universe_stats(self) -> Dict[str, Any]:
        """Get statistics about the stored Kraken universe"""
        total = await self.db[self.collection].count_documents({})
        with_usd = await self.db[self.collection].count_documents({"has_usd_pair": True})
        with_btc = await self.db[self.collection].count_documents({"has_btc_pair": True})
        with_eth = await self.db[self.collection].count_documents({"has_eth_pair": True})
        
        # Get sample coins
        sample = await self.db[self.collection].find(
            {"has_usd_pair": True},
            {"_id": 0, "symbol": 1, "name": 1, "num_pairs": 1}
        ).sort("num_pairs", -1).limit(20).to_list(20)
        
        # Get last sync time
        last_sync = await self.db["kraken_sync_log"].find_one(
            {"type": "universe_sync"},
            sort=[("timestamp", -1)]
        )
        
        return {
            "total_coins": total,
            "with_usd_pair": with_usd,
            "with_btc_pair": with_btc,
            "with_eth_pair": with_eth,
            "last_sync": last_sync.get("timestamp").isoformat() if last_sync else None,
            "top_coins_by_pairs": sample
        }
    
    async def get_all_coins(self, 
                           has_usd_pair: bool = None,
                           limit: int = None) -> List[Dict[str, Any]]:
        """Get all coins in the universe"""
        query = {}
        if has_usd_pair is not None:
            query["has_usd_pair"] = has_usd_pair
        
        cursor = self.db[self.collection].find(query, {"_id": 0})
        
        if limit:
            cursor = cursor.limit(limit)
        
        return await cursor.to_list(length=limit or 1000)
    
    async def get_coin_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed info for a specific coin"""
        return await self.db[self.collection].find_one(
            {"symbol": symbol.upper()},
            {"_id": 0}
        )
    
    async def search_coins(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search coins by symbol or name"""
        return await self.db[self.collection].find(
            {
                "$or": [
                    {"symbol": {"$regex": query, "$options": "i"}},
                    {"name": {"$regex": query, "$options": "i"}}
                ]
            },
            {"_id": 0, "symbol": 1, "name": 1, "has_usd_pair": 1, "num_pairs": 1}
        ).limit(limit).to_list(limit)


# Global instance
_kraken_universe = None

def get_kraken_universe(db=None):
    global _kraken_universe
    if _kraken_universe is None and db is not None:
        _kraken_universe = KrakenUniverseService(db)
    return _kraken_universe

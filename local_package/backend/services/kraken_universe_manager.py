"""
Kraken Universe Manager
Automatically fetches and maintains a complete list of all tradeable coins on Kraken.
Auto-expands the universe as new coins are listed.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set
from motor.motor_asyncio import AsyncIOMotorDatabase
from httpx import AsyncClient
import logging

logger = logging.getLogger(__name__)

# Kraken API endpoints
KRAKEN_API_URL = "https://api.kraken.com"


class KrakenUniverseManager:
    """
    Manages the complete Kraken trading universe.
    - Fetches all available trading pairs from Kraken
    - Auto-discovers new coins as they are listed
    - Maintains a database of all tradeable assets
    - Supports scheduled sync to keep universe current
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection_name = "kraken_universe"
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 3600  # 1 hour cache
        self._last_sync: Optional[datetime] = None
        
    async def fetch_all_asset_pairs(self) -> Dict[str, Any]:
        """
        Fetch ALL tradeable asset pairs from Kraken public API.
        Returns complete pair information including fees, minimums, etc.
        """
        try:
            async with AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{KRAKEN_API_URL}/0/public/AssetPairs",
                    headers={"User-Agent": "CryptoTradingBot/1.0"}
                )
                data = response.json()
                
                if data.get("error") and len(data["error"]) > 0:
                    logger.error(f"Kraken AssetPairs error: {data['error']}")
                    return {"error": data["error"]}
                
                return data.get("result", {})
        except Exception as e:
            logger.error(f"Error fetching Kraken asset pairs: {e}")
            return {"error": str(e)}
    
    async def fetch_all_assets(self) -> Dict[str, Any]:
        """
        Fetch ALL assets (coins) information from Kraken.
        """
        try:
            async with AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{KRAKEN_API_URL}/0/public/Assets",
                    headers={"User-Agent": "CryptoTradingBot/1.0"}
                )
                data = response.json()
                
                if data.get("error") and len(data["error"]) > 0:
                    logger.error(f"Kraken Assets error: {data['error']}")
                    return {"error": data["error"]}
                
                return data.get("result", {})
        except Exception as e:
            logger.error(f"Error fetching Kraken assets: {e}")
            return {"error": str(e)}
    
    async def sync_universe(self) -> Dict[str, Any]:
        """
        Sync the complete Kraken trading universe to database.
        This is the main method that should be called periodically.
        
        Returns:
            Dict with sync results including new coins discovered
        """
        logger.info("🔄 Starting Kraken universe sync...")
        
        # Fetch all asset pairs and assets
        pairs_data = await self.fetch_all_asset_pairs()
        assets_data = await self.fetch_all_assets()
        
        if "error" in pairs_data or "error" in assets_data:
            return {
                "status": "error",
                "error": pairs_data.get("error") or assets_data.get("error"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Get existing coins from database
        existing_coins = await self.db[self.collection_name].distinct("base_currency")
        existing_set = set(existing_coins)
        
        # Process all pairs
        processed_coins: Set[str] = set()
        new_coins: List[str] = []
        usd_pairs: List[Dict] = []
        all_pairs: List[Dict] = []
        
        for pair_name, pair_info in pairs_data.items():
            # Skip darkpool pairs (contain .d)
            if ".d" in pair_name:
                continue
            
            # Get base and quote currencies
            base = pair_info.get("base", "")
            quote = pair_info.get("quote", "")
            
            # Normalize base currency (remove X prefix for crypto, Z prefix for fiat)
            if base.startswith("X") and len(base) > 1:
                base_normalized = base[1:]
            elif base.startswith("Z") and len(base) > 1:
                base_normalized = base[1:]
            else:
                base_normalized = base
            
            # Normalize quote
            if quote.startswith("Z") and len(quote) > 1:
                quote_normalized = quote[1:]
            elif quote.startswith("X") and len(quote) > 1:
                quote_normalized = quote[1:]
            else:
                quote_normalized = quote
            
            # Create pair record
            pair_record = {
                "pair_name": pair_name,
                "altname": pair_info.get("altname", pair_name),
                "wsname": pair_info.get("wsname", ""),
                "base_currency": base_normalized,
                "quote_currency": quote_normalized,
                "base_raw": base,
                "quote_raw": quote,
                "lot_decimals": pair_info.get("lot_decimals", 8),
                "pair_decimals": pair_info.get("pair_decimals", 5),
                "lot_multiplier": pair_info.get("lot_multiplier", 1),
                "margin_call": pair_info.get("margin_call", 80),
                "margin_stop": pair_info.get("margin_stop", 40),
                "ordermin": pair_info.get("ordermin", "0"),
                "costmin": pair_info.get("costmin", "0"),
                "tick_size": pair_info.get("tick_size", "0.00001"),
                "status": pair_info.get("status", "online"),
                "fees": pair_info.get("fees", []),
                "fees_maker": pair_info.get("fees_maker", []),
                "updated_at": datetime.now(timezone.utc)
            }
            
            all_pairs.append(pair_record)
            
            # Track USD pairs specifically
            if quote_normalized in ["USD", "USDT", "USDC"]:
                usd_pairs.append(pair_record)
                processed_coins.add(base_normalized)
                
                # Check if this is a new coin
                if base_normalized not in existing_set:
                    new_coins.append(base_normalized)
        
        # Process asset information
        assets_info = {}
        for asset_name, asset_info in assets_data.items():
            # Normalize asset name
            if asset_name.startswith("X") and len(asset_name) > 1:
                normalized = asset_name[1:]
            elif asset_name.startswith("Z") and len(asset_name) > 1:
                normalized = asset_name[1:]
            else:
                normalized = asset_name
            
            assets_info[normalized] = {
                "raw_name": asset_name,
                "aclass": asset_info.get("aclass", "currency"),
                "altname": asset_info.get("altname", asset_name),
                "decimals": asset_info.get("decimals", 10),
                "display_decimals": asset_info.get("display_decimals", 5),
                "status": asset_info.get("status", "enabled")
            }
        
        # Store in database
        collection = self.db[self.collection_name]
        
        # Clear old data and insert fresh
        await collection.delete_many({})
        
        if all_pairs:
            # Enrich pairs with asset info
            for pair in all_pairs:
                base = pair["base_currency"]
                if base in assets_info:
                    pair["asset_info"] = assets_info[base]
            
            await collection.insert_many(all_pairs)
        
        # Create indexes
        await collection.create_index([("base_currency", 1)])
        await collection.create_index([("quote_currency", 1)])
        await collection.create_index([("pair_name", 1)])
        await collection.create_index([("altname", 1)])
        
        # Store sync metadata
        sync_result = {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_pairs": len(all_pairs),
            "usd_pairs": len(usd_pairs),
            "unique_coins": len(processed_coins),
            "new_coins_discovered": new_coins,
            "new_coins_count": len(new_coins)
        }
        
        await self.db.kraken_universe_sync.replace_one(
            {"_id": "latest_sync"},
            {"_id": "latest_sync", **sync_result},
            upsert=True
        )
        
        self._last_sync = datetime.now(timezone.utc)
        
        logger.info(f"✅ Kraken universe sync complete: {len(processed_coins)} coins, {len(new_coins)} new")
        
        return sync_result
    
    async def get_all_tradeable_coins(self, quote_currency: str = "USD") -> List[Dict[str, Any]]:
        """
        Get all tradeable coins for a specific quote currency.
        
        Args:
            quote_currency: Quote currency to filter by (USD, EUR, etc.)
        
        Returns:
            List of coin information
        """
        collection = self.db[self.collection_name]
        
        # Check if we have data, if not sync first
        count = await collection.count_documents({})
        if count == 0:
            await self.sync_universe()
        
        # Query for coins with the specified quote currency
        cursor = collection.find(
            {"quote_currency": {"$in": [quote_currency, f"Z{quote_currency}", quote_currency.upper()]}},
            {"_id": 0}
        ).sort("base_currency", 1)
        
        coins = await cursor.to_list(length=1000)
        
        return coins
    
    async def get_all_unique_coins(self) -> List[str]:
        """
        Get list of all unique tradeable coin symbols.
        """
        collection = self.db[self.collection_name]
        
        # Check if we have data
        count = await collection.count_documents({})
        if count == 0:
            await self.sync_universe()
        
        coins = await collection.distinct("base_currency")
        
        # Filter out fiat currencies
        fiat = {"USD", "EUR", "GBP", "CAD", "AUD", "CHF", "JPY"}
        crypto_coins = [c for c in coins if c not in fiat]
        
        return sorted(crypto_coins)
    
    async def get_coin_pairs(self, coin: str) -> List[Dict[str, Any]]:
        """
        Get all trading pairs for a specific coin.
        """
        collection = self.db[self.collection_name]
        
        cursor = collection.find(
            {"base_currency": coin.upper()},
            {"_id": 0}
        )
        
        pairs = await cursor.to_list(length=50)
        return pairs
    
    async def get_universe_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current Kraken universe.
        """
        collection = self.db[self.collection_name]
        
        total_pairs = await collection.count_documents({})
        
        if total_pairs == 0:
            return {
                "status": "not_synced",
                "message": "Universe not synced. Call sync_universe first.",
                "total_pairs": 0
            }
        
        # Get unique counts
        unique_base = await collection.distinct("base_currency")
        unique_quote = await collection.distinct("quote_currency")
        
        # Get USD pairs count
        usd_pairs = await collection.count_documents({
            "quote_currency": {"$in": ["USD", "ZUSD", "USDT", "USDC"]}
        })
        
        # Get sync metadata
        sync_info = await self.db.kraken_universe_sync.find_one({"_id": "latest_sync"})
        
        # Filter fiat from base currencies
        fiat = {"USD", "EUR", "GBP", "CAD", "AUD", "CHF", "JPY"}
        crypto_coins = [c for c in unique_base if c not in fiat]
        
        return {
            "status": "synced",
            "total_pairs": total_pairs,
            "usd_pairs": usd_pairs,
            "unique_crypto_coins": len(crypto_coins),
            "unique_quote_currencies": len(unique_quote),
            "crypto_coins": crypto_coins,
            "quote_currencies": unique_quote,
            "last_sync": sync_info.get("timestamp") if sync_info else None,
            "new_coins_in_last_sync": sync_info.get("new_coins_discovered", []) if sync_info else []
        }
    
    async def check_for_new_coins(self) -> Dict[str, Any]:
        """
        Check if there are new coins listed on Kraken since last sync.
        Useful for scheduled monitoring.
        """
        # Get current coins from DB
        current_coins = set(await self.get_all_unique_coins())
        
        # Fetch fresh data from Kraken
        pairs_data = await self.fetch_all_asset_pairs()
        
        if "error" in pairs_data:
            return {"error": pairs_data["error"]}
        
        # Extract all base currencies from fresh data
        fresh_coins: Set[str] = set()
        for pair_name, pair_info in pairs_data.items():
            if ".d" in pair_name:
                continue
            
            base = pair_info.get("base", "")
            if base.startswith("X") and len(base) > 1:
                base = base[1:]
            elif base.startswith("Z") and len(base) > 1:
                base = base[1:]
            
            quote = pair_info.get("quote", "")
            if quote.startswith("Z"):
                quote = quote[1:]
            
            # Only count USD-paired coins
            if quote in ["USD", "USDT", "USDC"]:
                fresh_coins.add(base)
        
        # Find new coins
        new_coins = fresh_coins - current_coins
        
        return {
            "current_count": len(current_coins),
            "fresh_count": len(fresh_coins),
            "new_coins": list(new_coins),
            "has_new_coins": len(new_coins) > 0,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_training_coin_list(self) -> List[str]:
        """
        Get list of coins suitable for AI training.
        Returns coin symbols that have USD pairs.
        """
        coins = await self.get_all_tradeable_coins("USD")
        
        # Return base currencies
        return list(set(c["base_currency"] for c in coins))


# Global instance
_kraken_universe_manager: Optional[KrakenUniverseManager] = None


def get_kraken_universe_manager(db: AsyncIOMotorDatabase = None) -> Optional[KrakenUniverseManager]:
    """Get or create Kraken Universe Manager instance"""
    global _kraken_universe_manager
    if _kraken_universe_manager is None and db is not None:
        _kraken_universe_manager = KrakenUniverseManager(db)
    return _kraken_universe_manager

"""
On-Chain Metrics Service
Fetches on-chain data from FREE APIs:
- Blockchain.com API (BTC)
- Blockchair API (multi-chain)
- Mempool.space (BTC)
- Public Ethereum RPC endpoints

Provides:
- Active addresses
- Transaction counts
- Network hash rate
- Exchange flows (estimated)
- Whale movements (large transactions)
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from httpx import AsyncClient
import logging

logger = logging.getLogger(__name__)

# Free API endpoints
BLOCKCHAIN_COM_API = "https://api.blockchain.info"
BLOCKCHAIR_API = "https://api.blockchair.com"
MEMPOOL_API = "https://mempool.space/api"


class OnChainMetricsService:
    """
    On-chain metrics using FREE public APIs.
    
    Supported chains:
    - Bitcoin (BTC): Blockchain.com + Mempool.space
    - Ethereum (ETH): Blockchair + public RPC
    - Other chains: Blockchair (limited free tier)
    
    Features:
    - Active address tracking
    - Transaction volume
    - Hash rate and difficulty
    - Large transaction monitoring (whale alerts)
    - Fee market analysis
    """
    
    # Chain mappings for Blockchair
    BLOCKCHAIR_CHAINS = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "LTC": "litecoin",
        "DOGE": "dogecoin",
        "BCH": "bitcoin-cash",
        "BSV": "bitcoin-sv",
        "XRP": "ripple",
        "XLM": "stellar",
        "ADA": "cardano",
        "DOT": "polkadot",
        "SOL": "solana",
        "MATIC": "polygon",
        "AVAX": "avalanche",
        "ATOM": "cosmos"
    }
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection_name = "onchain_metrics"
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minute cache
        
        # Optional API keys (for future premium tiers)
        self.blockchair_api_key: Optional[str] = None
        self.glassnode_api_key: Optional[str] = None
        self.cryptoquant_api_key: Optional[str] = None
    
    def set_api_keys(self, keys: Dict[str, str]):
        """Set optional API keys for premium data providers"""
        self.blockchair_api_key = keys.get("blockchair")
        self.glassnode_api_key = keys.get("glassnode")
        self.cryptoquant_api_key = keys.get("cryptoquant")
    
    async def _request(self, url: str, params: Dict = None, timeout: int = 30) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        try:
            async with AsyncClient(timeout=timeout) as client:
                response = await client.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    return {"error": "Rate limit exceeded"}
                else:
                    return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    # ============ BITCOIN METRICS (Blockchain.com + Mempool) ============
    
    async def get_btc_stats(self) -> Dict[str, Any]:
        """Get comprehensive Bitcoin network stats from Blockchain.com"""
        cache_key = "btc_stats"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now(timezone.utc).timestamp() - cached["timestamp"] < self._cache_ttl:
                return cached["data"]
        
        data = await self._request(f"{BLOCKCHAIN_COM_API}/stats")
        
        if "error" not in data:
            result = {
                "chain": "BTC",
                "market_price_usd": data.get("market_price_usd", 0),
                "hash_rate": data.get("hash_rate", 0),  # TH/s
                "total_fees_btc": data.get("total_fees_btc", 0) / 100000000,  # Convert from satoshi
                "n_btc_mined": data.get("n_btc_mined", 0) / 100000000,
                "n_tx": data.get("n_tx", 0),  # 24h transactions
                "n_blocks_mined": data.get("n_blocks_mined", 0),
                "minutes_between_blocks": data.get("minutes_between_blocks", 10),
                "totalbc": data.get("totalbc", 0) / 100000000,  # Total BTC in circulation
                "n_blocks_total": data.get("n_blocks_total", 0),
                "estimated_transaction_volume_usd": data.get("estimated_transaction_volume_usd", 0),
                "miners_revenue_btc": data.get("miners_revenue_btc", 0) / 100000000,
                "trade_volume_usd": data.get("trade_volume_usd", 0),
                "difficulty": data.get("difficulty", 0),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "blockchain.com"
            }
            
            self._cache[cache_key] = {
                "data": result,
                "timestamp": datetime.now(timezone.utc).timestamp()
            }
            
            return result
        
        return data
    
    async def get_btc_mempool(self) -> Dict[str, Any]:
        """Get Bitcoin mempool stats from mempool.space"""
        cache_key = "btc_mempool"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now(timezone.utc).timestamp() - cached["timestamp"] < 60:  # 1 min cache
                return cached["data"]
        
        data = await self._request(f"{MEMPOOL_API}/mempool")
        
        if "error" not in data:
            result = {
                "chain": "BTC",
                "count": data.get("count", 0),  # Unconfirmed tx count
                "vsize": data.get("vsize", 0),  # Total vsize
                "total_fee": data.get("total_fee", 0),  # Total fees in satoshi
                "fee_histogram": data.get("fee_histogram", []),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "mempool.space"
            }
            
            self._cache[cache_key] = {
                "data": result,
                "timestamp": datetime.now(timezone.utc).timestamp()
            }
            
            return result
        
        return data
    
    async def get_btc_fee_estimates(self) -> Dict[str, Any]:
        """Get Bitcoin fee estimates from mempool.space"""
        data = await self._request(f"{MEMPOOL_API}/v1/fees/recommended")
        
        if "error" not in data:
            return {
                "chain": "BTC",
                "fastest_fee": data.get("fastestFee", 0),  # sat/vB
                "half_hour_fee": data.get("halfHourFee", 0),
                "hour_fee": data.get("hourFee", 0),
                "economy_fee": data.get("economyFee", 0),
                "minimum_fee": data.get("minimumFee", 1),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "mempool.space"
            }
        
        return data
    
    async def get_btc_difficulty_adjustment(self) -> Dict[str, Any]:
        """Get Bitcoin difficulty adjustment info"""
        data = await self._request(f"{MEMPOOL_API}/v1/difficulty-adjustment")
        
        if "error" not in data:
            return {
                "chain": "BTC",
                "progress_percent": data.get("progressPercent", 0),
                "difficulty_change": data.get("difficultyChange", 0),
                "estimated_retarget_date": data.get("estimatedRetargetDate", 0),
                "remaining_blocks": data.get("remainingBlocks", 0),
                "remaining_time": data.get("remainingTime", 0),
                "previous_retarget": data.get("previousRetarget", 0),
                "next_retarget_height": data.get("nextRetargetHeight", 0),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "mempool.space"
            }
        
        return data
    
    # ============ BLOCKCHAIR MULTI-CHAIN METRICS ============
    
    async def get_chain_stats(self, symbol: str) -> Dict[str, Any]:
        """
        Get blockchain stats from Blockchair for supported chains.
        Free tier: 10,000 requests/day
        """
        chain = self.BLOCKCHAIR_CHAINS.get(symbol.upper())
        if not chain:
            return {"error": f"Chain {symbol} not supported by Blockchair"}
        
        cache_key = f"blockchair_{symbol}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now(timezone.utc).timestamp() - cached["timestamp"] < self._cache_ttl:
                return cached["data"]
        
        url = f"{BLOCKCHAIR_API}/{chain}/stats"
        params = {}
        if self.blockchair_api_key:
            params["key"] = self.blockchair_api_key
        
        data = await self._request(url, params)
        
        if "data" in data:
            stats = data["data"]
            result = {
                "chain": symbol.upper(),
                "blocks": stats.get("blocks", 0),
                "transactions": stats.get("transactions", 0),
                "outputs": stats.get("outputs", 0),
                "circulation": stats.get("circulation", 0),
                "blockchain_size": stats.get("blockchain_size", 0),
                "nodes": stats.get("nodes", 0),
                "difficulty": stats.get("difficulty", 0),
                "hashrate_24h": stats.get("hashrate_24h", "0"),
                "inflation_24h": stats.get("inflation_24h", 0),
                "average_transaction_fee_24h": stats.get("average_transaction_fee_24h", 0),
                "average_transaction_fee_usd_24h": stats.get("average_transaction_fee_usd_24h", 0),
                "median_transaction_fee_24h": stats.get("median_transaction_fee_24h", 0),
                "mempool_transactions": stats.get("mempool_transactions", 0),
                "mempool_size": stats.get("mempool_size", 0),
                "mempool_tps": stats.get("mempool_tps", 0),
                "transactions_24h": stats.get("transactions_24h", 0),
                "volume_24h": stats.get("volume_24h", 0),
                "market_price_usd": stats.get("market_price_usd", 0),
                "market_cap_usd": stats.get("market_cap_usd", 0),
                "market_dominance_percent": stats.get("market_dominance_percent", 0),
                "suggested_fee_per_byte": stats.get("suggested_transaction_fee_per_byte_sat", 0),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "blockchair"
            }
            
            self._cache[cache_key] = {
                "data": result,
                "timestamp": datetime.now(timezone.utc).timestamp()
            }
            
            return result
        
        return data
    
    async def get_large_transactions(self, symbol: str, min_usd: float = 1000000) -> List[Dict[str, Any]]:
        """
        Get large transactions (whale movements) from Blockchair.
        Default: transactions >= $1M USD
        """
        chain = self.BLOCKCHAIR_CHAINS.get(symbol.upper())
        if not chain:
            return []
        
        url = f"{BLOCKCHAIR_API}/{chain}/transactions"
        params = {
            "q": f"output_total_usd({min_usd}..)",
            "s": "output_total_usd(desc)",
            "limit": 10
        }
        if self.blockchair_api_key:
            params["key"] = self.blockchair_api_key
        
        data = await self._request(url, params)
        
        if "data" in data:
            transactions = []
            for tx in data["data"]:
                transactions.append({
                    "tx_hash": tx.get("hash", ""),
                    "block_id": tx.get("block_id", 0),
                    "time": tx.get("time", ""),
                    "input_count": tx.get("input_count", 0),
                    "output_count": tx.get("output_count", 0),
                    "input_total": tx.get("input_total", 0),
                    "output_total": tx.get("output_total", 0),
                    "output_total_usd": tx.get("output_total_usd", 0),
                    "fee": tx.get("fee", 0),
                    "fee_usd": tx.get("fee_usd", 0),
                    "is_coinbase": tx.get("is_coinbase", False)
                })
            return transactions
        
        return []
    
    # ============ AGGREGATED METRICS ============
    
    async def get_comprehensive_metrics(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive on-chain metrics for a coin.
        Combines multiple data sources.
        """
        symbol = symbol.upper()
        
        if symbol == "BTC":
            # Use specialized BTC APIs for better data
            btc_stats = await self.get_btc_stats()
            mempool = await self.get_btc_mempool()
            fees = await self.get_btc_fee_estimates()
            difficulty = await self.get_btc_difficulty_adjustment()
            
            return {
                "chain": "BTC",
                "network": btc_stats,
                "mempool": mempool,
                "fees": fees,
                "difficulty": difficulty,
                "whale_transactions": await self.get_large_transactions("BTC"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            # Use Blockchair for other chains
            stats = await self.get_chain_stats(symbol)
            
            return {
                "chain": symbol,
                "network": stats,
                "whale_transactions": await self.get_large_transactions(symbol),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def store_metrics_snapshot(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch and store metrics snapshot to database for historical tracking.
        """
        metrics = await self.get_comprehensive_metrics(symbol)
        
        if "error" not in metrics.get("network", {}):
            # Add metadata
            metrics["_stored_at"] = datetime.now(timezone.utc)
            metrics["symbol"] = symbol.upper()
            
            # Store in database
            await self.db[self.collection_name].insert_one(metrics)
            
            return {
                "status": "stored",
                "symbol": symbol,
                "timestamp": metrics["timestamp"]
            }
        
        return {"status": "error", "symbol": symbol, "error": metrics.get("network", {}).get("error")}
    
    async def get_historical_metrics(
        self,
        symbol: str,
        days: int = 30,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get historical on-chain metrics from database.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        cursor = self.db[self.collection_name].find(
            {
                "symbol": symbol.upper(),
                "_stored_at": {"$gte": cutoff}
            },
            {"_id": 0}
        ).sort("_stored_at", -1).limit(limit)
        
        return await cursor.to_list(length=limit)
    
    async def get_supported_chains(self) -> Dict[str, Any]:
        """Get list of supported chains and their status"""
        supported = []
        
        for symbol, chain in self.BLOCKCHAIR_CHAINS.items():
            supported.append({
                "symbol": symbol,
                "blockchair_chain": chain,
                "btc_specialized": symbol == "BTC",
                "eth_specialized": symbol == "ETH"
            })
        
        return {
            "supported_chains": supported,
            "total": len(supported),
            "free_apis_used": ["blockchain.com", "blockchair.com", "mempool.space"],
            "premium_apis_available": ["glassnode", "cryptoquant"],
            "premium_configured": {
                "blockchair": bool(self.blockchair_api_key),
                "glassnode": bool(self.glassnode_api_key),
                "cryptoquant": bool(self.cryptoquant_api_key)
            }
        }
    
    async def batch_fetch_metrics(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Fetch metrics for multiple chains in parallel.
        """
        tasks = [self.get_comprehensive_metrics(s) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        metrics = {}
        errors = []
        
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                errors.append({"symbol": symbol, "error": str(result)})
            elif "error" in result.get("network", {}):
                errors.append({"symbol": symbol, "error": result["network"]["error"]})
            else:
                metrics[symbol] = result
        
        return {
            "metrics": metrics,
            "errors": errors,
            "success_count": len(metrics),
            "error_count": len(errors),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global instance
_onchain_service: Optional[OnChainMetricsService] = None


def get_onchain_metrics_service(db: AsyncIOMotorDatabase = None) -> Optional[OnChainMetricsService]:
    """Get or create On-Chain Metrics Service instance"""
    global _onchain_service
    if _onchain_service is None and db is not None:
        _onchain_service = OnChainMetricsService(db)
    return _onchain_service

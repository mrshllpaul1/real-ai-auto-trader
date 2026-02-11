"""
MetaMask & Web3 Wallet Integration API Routes
==============================================
Connect MetaMask, track DeFi positions, LP tokens, NFTs.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import aiohttp
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/web3-wallet", tags=["Web3 Wallet"])

_db = None


def set_db(db):
    global _db
    _db = db


async def get_database():
    global _db
    if _db is None:
        from server import db
        _db = db
    return _db


class WalletConnection(BaseModel):
    address: str
    chain_id: int = 1  # 1=ETH, 56=BSC, 137=Polygon, 42161=Arbitrum
    wallet_type: str = "metamask"  # metamask, walletconnect, coinbase


class NFTAsset(BaseModel):
    contract_address: str
    token_id: str
    name: Optional[str] = None
    image_url: Optional[str] = None


# Chain configurations
CHAINS = {
    1: {"name": "Ethereum", "symbol": "ETH", "explorer": "https://etherscan.io"},
    56: {"name": "BNB Chain", "symbol": "BNB", "explorer": "https://bscscan.com"},
    137: {"name": "Polygon", "symbol": "MATIC", "explorer": "https://polygonscan.com"},
    42161: {"name": "Arbitrum", "symbol": "ETH", "explorer": "https://arbiscan.io"},
    10: {"name": "Optimism", "symbol": "ETH", "explorer": "https://optimistic.etherscan.io"},
    43114: {"name": "Avalanche", "symbol": "AVAX", "explorer": "https://snowtrace.io"},
    250: {"name": "Fantom", "symbol": "FTM", "explorer": "https://ftmscan.com"},
    8453: {"name": "Base", "symbol": "ETH", "explorer": "https://basescan.org"},
}

# Common DeFi protocols
DEFI_PROTOCOLS = {
    "uniswap_v3": {"name": "Uniswap V3", "type": "dex", "chains": [1, 137, 42161, 10]},
    "aave_v3": {"name": "Aave V3", "type": "lending", "chains": [1, 137, 42161, 10, 43114]},
    "curve": {"name": "Curve Finance", "type": "dex", "chains": [1, 137, 42161, 43114, 250]},
    "compound": {"name": "Compound", "type": "lending", "chains": [1]},
    "lido": {"name": "Lido", "type": "staking", "chains": [1]},
    "gmx": {"name": "GMX", "type": "perpetuals", "chains": [42161, 43114]},
    "pancakeswap": {"name": "PancakeSwap", "type": "dex", "chains": [56, 1]},
    "sushiswap": {"name": "SushiSwap", "type": "dex", "chains": [1, 137, 42161]},
}


@router.post("/connect")
async def connect_wallet(
    connection: WalletConnection,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Connect a Web3 wallet (MetaMask, etc.)"""
    # Validate address format
    address = connection.address.lower()
    if not address.startswith("0x") or len(address) != 42:
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    
    chain_info = CHAINS.get(connection.chain_id, {"name": "Unknown", "symbol": "?"})
    
    wallet_data = {
        "wallet_id": str(uuid.uuid4()),
        "user_id": user_id,
        "address": address,
        "chain_id": connection.chain_id,
        "chain_name": chain_info["name"],
        "wallet_type": connection.wallet_type,
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "last_synced": None,
        "is_primary": False
    }
    
    # Check if wallet already connected
    existing = await db.web3_wallets.find_one({
        "user_id": user_id,
        "address": address,
        "chain_id": connection.chain_id
    })
    
    if existing:
        return {
            "status": "already_connected",
            "wallet": {k: v for k, v in existing.items() if k != "_id"}
        }
    
    # Check if this is the first wallet (make it primary)
    wallet_count = await db.web3_wallets.count_documents({"user_id": user_id})
    if wallet_count == 0:
        wallet_data["is_primary"] = True
    
    await db.web3_wallets.insert_one(wallet_data)
    
    return {
        "status": "connected",
        "wallet": {k: v for k, v in wallet_data.items() if k != "_id"}
    }


@router.get("/wallets")
async def get_connected_wallets(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get all connected wallets for user"""
    wallets = await db.web3_wallets.find(
        {"user_id": user_id},
        {"_id": 0}
    ).to_list(50)
    
    # Enrich with chain info
    for wallet in wallets:
        chain_info = CHAINS.get(wallet.get("chain_id", 1), {})
        wallet["chain_info"] = chain_info
    
    return {
        "wallets": wallets,
        "total": len(wallets),
        "supported_chains": list(CHAINS.keys())
    }


@router.delete("/disconnect/{wallet_id}")
async def disconnect_wallet(
    wallet_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Disconnect a wallet"""
    result = await db.web3_wallets.delete_one({
        "wallet_id": wallet_id,
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    # Also remove cached balances
    await db.web3_balances.delete_many({"wallet_id": wallet_id})
    
    return {"status": "disconnected"}


@router.get("/balances/{address}")
async def get_wallet_balances(
    address: str,
    chain_id: int = 1,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get token balances for a wallet address"""
    address = address.lower()
    
    # Check cache first (cache for 5 minutes)
    cached = await db.web3_balances.find_one({
        "address": address,
        "chain_id": chain_id
    })
    
    if cached:
        # Check if cache is still valid (5 minutes)
        cached_time = cached.get("cached_at", "")
        try:
            cache_dt = datetime.fromisoformat(cached_time.replace("Z", "+00:00"))
            if (datetime.now(timezone.utc) - cache_dt).seconds < 300:
                return {
                    "balances": cached.get("balances", []),
                    "total_value_usd": cached.get("total_value_usd", 0),
                    "cached": True,
                    "cached_at": cached_time
                }
        except:
            pass
    
    # Fetch fresh balances (simulated - in production would use Alchemy/Moralis API)
    chain_info = CHAINS.get(chain_id, {"symbol": "ETH"})
    
    # Sample balances for demo
    balances = [
        {
            "token": chain_info["symbol"],
            "symbol": chain_info["symbol"],
            "balance": 2.5,
            "value_usd": 4500.00,
            "price_usd": 1800.00,
            "contract": "native",
            "logo": f"https://cryptologos.cc/logos/{chain_info['symbol'].lower()}-logo.png"
        },
        {
            "token": "USDC",
            "symbol": "USDC",
            "balance": 5000.00,
            "value_usd": 5000.00,
            "price_usd": 1.00,
            "contract": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "logo": "https://cryptologos.cc/logos/usd-coin-usdc-logo.png"
        },
        {
            "token": "WBTC",
            "symbol": "WBTC",
            "balance": 0.15,
            "value_usd": 10350.00,
            "price_usd": 69000.00,
            "contract": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
            "logo": "https://cryptologos.cc/logos/wrapped-bitcoin-wbtc-logo.png"
        }
    ]
    
    total_value = sum(b["value_usd"] for b in balances)
    
    # Cache the results
    await db.web3_balances.replace_one(
        {"address": address, "chain_id": chain_id},
        {
            "address": address,
            "chain_id": chain_id,
            "balances": balances,
            "total_value_usd": total_value,
            "cached_at": datetime.now(timezone.utc).isoformat()
        },
        upsert=True
    )
    
    return {
        "balances": balances,
        "total_value_usd": total_value,
        "chain": chain_info,
        "cached": False
    }


@router.get("/defi-positions/{address}")
async def get_defi_positions(
    address: str,
    chain_id: int = 1,
    db = Depends(get_database)
):
    """Get DeFi positions (LP tokens, lending, staking)"""
    address = address.lower()
    
    # Sample DeFi positions for demo
    positions = [
        {
            "protocol": "Uniswap V3",
            "type": "liquidity",
            "pool": "ETH/USDC",
            "position_id": "123456",
            "value_usd": 5000.00,
            "token0": {"symbol": "ETH", "amount": 1.5, "value_usd": 2700},
            "token1": {"symbol": "USDC", "amount": 2300, "value_usd": 2300},
            "fee_tier": "0.3%",
            "in_range": True,
            "unclaimed_fees": 45.50,
            "apr": 18.5
        },
        {
            "protocol": "Aave V3",
            "type": "lending",
            "asset": "USDC",
            "supplied": 10000.00,
            "value_usd": 10000.00,
            "apy": 4.5,
            "health_factor": 2.5,
            "collateral": True
        },
        {
            "protocol": "Lido",
            "type": "staking",
            "asset": "stETH",
            "staked": 2.0,
            "value_usd": 3600.00,
            "apy": 3.8,
            "rewards_accrued": 0.02
        },
        {
            "protocol": "Curve",
            "type": "liquidity",
            "pool": "3pool",
            "lp_tokens": 1500,
            "value_usd": 1500.00,
            "tokens": [
                {"symbol": "DAI", "amount": 500},
                {"symbol": "USDC", "amount": 500},
                {"symbol": "USDT", "amount": 500}
            ],
            "apr": 2.5,
            "rewards": [{"token": "CRV", "amount": 15, "value_usd": 7.50}]
        }
    ]
    
    total_value = sum(p["value_usd"] for p in positions)
    total_earnings = sum(p.get("unclaimed_fees", 0) + p.get("rewards_accrued", 0) * 1800 for p in positions)
    
    return {
        "positions": positions,
        "total_value_usd": total_value,
        "total_unclaimed_usd": round(total_earnings, 2),
        "protocols_count": len(set(p["protocol"] for p in positions)),
        "chain_id": chain_id
    }


@router.get("/nfts/{address}")
async def get_nft_holdings(
    address: str,
    chain_id: int = 1,
    db = Depends(get_database)
):
    """Get NFT holdings for a wallet"""
    address = address.lower()
    
    # Sample NFT holdings for demo
    nfts = [
        {
            "collection": "Bored Ape Yacht Club",
            "name": "BAYC #1234",
            "token_id": "1234",
            "contract": "0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d",
            "image_url": "https://i.seadn.io/gae/RBX3jwgNt_X-9oQbZ6nJGxV_cYVYCEOr5xG98ItK0LJZuT-wevQ2aQdFz-oAj-_fxCKuY4IaZyO6h_TU",
            "floor_price_eth": 30.5,
            "floor_price_usd": 54900.00,
            "rarity_rank": 2500,
            "traits": [
                {"type": "Background", "value": "Blue"},
                {"type": "Fur", "value": "Golden Brown"}
            ]
        },
        {
            "collection": "Pudgy Penguins",
            "name": "Pudgy Penguin #5678",
            "token_id": "5678",
            "contract": "0xbd3531da5cf5857e7cfaa92426877b022e612cf8",
            "image_url": "https://i.seadn.io/gae/pudgy-example",
            "floor_price_eth": 8.5,
            "floor_price_usd": 15300.00,
            "rarity_rank": 1200
        }
    ]
    
    total_value = sum(n["floor_price_usd"] for n in nfts)
    
    return {
        "nfts": nfts,
        "total_count": len(nfts),
        "total_floor_value_usd": total_value,
        "collections_count": len(set(n["collection"] for n in nfts))
    }


@router.get("/portfolio-summary/{address}")
async def get_web3_portfolio_summary(
    address: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get complete Web3 portfolio summary across all chains"""
    address = address.lower()
    
    # Get connected wallets for this address
    wallets = await db.web3_wallets.find(
        {"address": address},
        {"_id": 0}
    ).to_list(10)
    
    # Aggregate data (simplified)
    summary = {
        "address": address,
        "chains": [],
        "tokens": {
            "count": 8,
            "value_usd": 19850.00
        },
        "defi": {
            "positions_count": 4,
            "value_usd": 20100.00,
            "unclaimed_rewards_usd": 52.50
        },
        "nfts": {
            "count": 2,
            "floor_value_usd": 70200.00
        },
        "total_value_usd": 110150.00,
        "allocation": [
            {"category": "Tokens", "percentage": 18.0, "value_usd": 19850},
            {"category": "DeFi", "percentage": 18.3, "value_usd": 20100},
            {"category": "NFTs", "percentage": 63.7, "value_usd": 70200}
        ],
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    
    return summary


@router.get("/chains")
async def get_supported_chains():
    """Get list of supported blockchain networks"""
    return {
        "chains": [
            {"id": chain_id, **info}
            for chain_id, info in CHAINS.items()
        ]
    }


@router.get("/protocols")
async def get_supported_protocols():
    """Get list of supported DeFi protocols"""
    return {
        "protocols": [
            {"id": proto_id, **info}
            for proto_id, info in DEFI_PROTOCOLS.items()
        ]
    }


@router.post("/refresh/{address}")
async def refresh_wallet_data(
    address: str,
    chain_id: int = 1,
    db = Depends(get_database)
):
    """Force refresh wallet data"""
    address = address.lower()
    
    # Clear cached data
    await db.web3_balances.delete_many({"address": address, "chain_id": chain_id})
    
    # Fetch fresh data
    balances = await get_wallet_balances(address, chain_id, "default_user", db)
    positions = await get_defi_positions(address, chain_id, db)
    
    return {
        "status": "refreshed",
        "balances": balances,
        "defi_positions": positions,
        "refreshed_at": datetime.now(timezone.utc).isoformat()
    }

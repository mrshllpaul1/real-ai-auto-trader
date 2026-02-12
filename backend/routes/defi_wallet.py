"""
MetaMask & DeFi Wallet Integration API Routes
===============================================
Connect Web3 wallets and track DeFi positions.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/defi-wallet", tags=["DeFi Wallet"])

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


# =============================================================================
# MODELS
# =============================================================================

class WalletConnection(BaseModel):
    wallet_address: str
    wallet_type: str = "metamask"  # metamask, trust, coinbase, walletconnect
    chain: str = "ethereum"  # ethereum, bsc, polygon, arbitrum, optimism
    signature: Optional[str] = None  # For verification


class TokenBalance(BaseModel):
    token_address: str
    symbol: str
    name: str
    balance: float
    decimals: int
    price_usd: float
    value_usd: float
    chain: str


class DeFiPosition(BaseModel):
    protocol: str  # uniswap, aave, compound, curve, etc.
    position_type: str  # liquidity, lending, borrowing, staking
    tokens: List[str]
    value_usd: float
    apy: Optional[float] = None


# =============================================================================
# WALLET CONNECTION
# =============================================================================

@router.post("/connect")
async def connect_wallet(
    connection: WalletConnection,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Connect a Web3 wallet"""
    # Validate address format (basic check)
    if not connection.wallet_address.startswith("0x") or len(connection.wallet_address) != 42:
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    
    wallet_id = str(uuid.uuid4())
    
    wallet = {
        "wallet_id": wallet_id,
        "user_id": user_id,
        "wallet_address": connection.wallet_address.lower(),
        "wallet_type": connection.wallet_type,
        "chain": connection.chain,
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "last_synced": None,
        "status": "connected"
    }
    
    # Check if already connected
    existing = await db.connected_wallets.find_one({
        "user_id": user_id,
        "wallet_address": connection.wallet_address.lower()
    })
    
    if existing:
        return {"status": "already_connected", "wallet_id": existing.get("wallet_id")}
    
    await db.connected_wallets.insert_one(wallet)
    
    return {
        "status": "connected",
        "wallet_id": wallet_id,
        "address": connection.wallet_address,
        "message": f"Wallet connected on {connection.chain}"
    }


@router.get("/wallets")
async def list_connected_wallets(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """List all connected wallets"""
    wallets = await db.connected_wallets.find(
        {"user_id": user_id, "status": "connected"},
        {"_id": 0}
    ).to_list(20)
    
    return {"wallets": wallets, "total": len(wallets)}


@router.delete("/disconnect/{wallet_id}")
async def disconnect_wallet(wallet_id: str, db = Depends(get_database)):
    """Disconnect a wallet"""
    result = await db.connected_wallets.update_one(
        {"wallet_id": wallet_id},
        {"$set": {"status": "disconnected", "disconnected_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return {"status": "disconnected"}


# =============================================================================
# TOKEN BALANCES
# =============================================================================

@router.get("/balances/{wallet_address}")
async def get_token_balances(
    wallet_address: str,
    chain: str = "ethereum",
    db = Depends(get_database)
):
    """Get token balances for a wallet - requires blockchain API integration"""
    # Check if we have cached balances from a real blockchain API
    cached = await db.wallet_balances.find_one({
        "wallet_address": wallet_address.lower(),
        "chain": chain
    }, {"_id": 0})
    
    if cached:
        return {
            "wallet_address": wallet_address,
            "chain": chain,
            "balances": cached.get("balances", []),
            "total_value_usd": cached.get("total_value_usd", 0),
            "last_updated": cached.get("last_updated"),
            "data_source": "cached"
        }
    
    # No real data - return empty with instructions
    return {
        "wallet_address": wallet_address,
        "chain": chain,
        "balances": [],
        "total_value_usd": 0,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "message": "Connect blockchain API (Alchemy, Moralis) in Settings to fetch real wallet balances",
        "requires_api_key": True
    }


# =============================================================================
# DEFI POSITIONS
# =============================================================================

@router.get("/positions/{wallet_address}")
async def get_defi_positions(
    wallet_address: str,
    db = Depends(get_database)
):
    """Get DeFi positions (LP, lending, staking) - simulated"""
    
    positions = [
        {
            "position_id": "pos_1",
            "protocol": "Uniswap V3",
            "protocol_logo": "https://cryptologos.cc/logos/uniswap-uni-logo.png",
            "position_type": "liquidity",
            "pool": "ETH/USDC",
            "tokens": ["ETH", "USDC"],
            "deposited": {"ETH": 1.0, "USDC": 2500},
            "current_value_usd": 5100,
            "pnl_usd": 100,
            "pnl_pct": 2.0,
            "fee_tier": "0.3%",
            "fees_earned_usd": 45,
            "in_range": True,
            "chain": "ethereum"
        },
        {
            "position_id": "pos_2",
            "protocol": "Aave V3",
            "protocol_logo": "https://cryptologos.cc/logos/aave-aave-logo.png",
            "position_type": "lending",
            "asset": "USDC",
            "deposited_usd": 3000,
            "current_value_usd": 3090,
            "apy": 4.5,
            "earned_usd": 90,
            "health_factor": None,
            "chain": "ethereum"
        },
        {
            "position_id": "pos_3",
            "protocol": "Lido",
            "protocol_logo": "https://cryptologos.cc/logos/lido-dao-ldo-logo.png",
            "position_type": "staking",
            "asset": "ETH",
            "staked_amount": 2.0,
            "steth_balance": 2.01,
            "current_value_usd": 5025,
            "apy": 3.8,
            "rewards_earned": 0.01,
            "chain": "ethereum"
        },
        {
            "position_id": "pos_4",
            "protocol": "Curve",
            "protocol_logo": "https://cryptologos.cc/logos/curve-dao-token-crv-logo.png",
            "position_type": "liquidity",
            "pool": "3pool",
            "tokens": ["DAI", "USDC", "USDT"],
            "deposited_usd": 2000,
            "current_value_usd": 2015,
            "apy": 2.1,
            "crv_rewards": 12.5,
            "chain": "ethereum"
        }
    ]
    
    total_value = sum(p["current_value_usd"] for p in positions)
    total_pnl = sum(p.get("pnl_usd", p.get("earned_usd", 0)) for p in positions)
    
    return {
        "wallet_address": wallet_address,
        "positions": positions,
        "summary": {
            "total_positions": len(positions),
            "total_value_usd": round(total_value, 2),
            "total_pnl_usd": round(total_pnl, 2),
            "protocols_used": list(set(p["protocol"] for p in positions))
        },
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


# =============================================================================
# NFT HOLDINGS
# =============================================================================

@router.get("/nfts/{wallet_address}")
async def get_nft_holdings(
    wallet_address: str,
    db = Depends(get_database)
):
    """Get NFT holdings (simulated)"""
    
    nfts = [
        {
            "contract_address": "0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d",
            "token_id": "1234",
            "name": "Bored Ape #1234",
            "collection": "Bored Ape Yacht Club",
            "image_url": "https://placeholder.com/bayc.png",
            "floor_price_eth": 25,
            "floor_price_usd": 62500,
            "last_sale_eth": 30,
            "rarity_rank": 2500
        },
        {
            "contract_address": "0x60e4d786628fea6478f785a6d7e704777c86a7c6",
            "token_id": "5678",
            "name": "Mutant Ape #5678",
            "collection": "Mutant Ape Yacht Club",
            "image_url": "https://placeholder.com/mayc.png",
            "floor_price_eth": 5,
            "floor_price_usd": 12500,
            "last_sale_eth": 6,
            "rarity_rank": 8000
        }
    ]
    
    total_floor = sum(n["floor_price_usd"] for n in nfts)
    
    return {
        "wallet_address": wallet_address,
        "nfts": nfts,
        "total_count": len(nfts),
        "total_floor_value_usd": total_floor,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


# =============================================================================
# TRANSACTION HISTORY
# =============================================================================

@router.get("/transactions/{wallet_address}")
async def get_transaction_history(
    wallet_address: str,
    limit: int = 20,
    db = Depends(get_database)
):
    """Get recent transactions (simulated)"""
    
    transactions = [
        {
            "tx_hash": "0x1234...abcd",
            "type": "swap",
            "protocol": "Uniswap",
            "from_token": "ETH",
            "to_token": "USDC",
            "from_amount": 1.0,
            "to_amount": 2500,
            "gas_used_usd": 15,
            "timestamp": "2026-02-09T10:30:00Z",
            "status": "confirmed"
        },
        {
            "tx_hash": "0x5678...efgh",
            "type": "deposit",
            "protocol": "Aave",
            "token": "USDC",
            "amount": 1000,
            "gas_used_usd": 8,
            "timestamp": "2026-02-08T14:20:00Z",
            "status": "confirmed"
        },
        {
            "tx_hash": "0x9abc...ijkl",
            "type": "stake",
            "protocol": "Lido",
            "token": "ETH",
            "amount": 2.0,
            "gas_used_usd": 12,
            "timestamp": "2026-02-07T09:15:00Z",
            "status": "confirmed"
        }
    ]
    
    return {
        "wallet_address": wallet_address,
        "transactions": transactions[:limit],
        "total": len(transactions)
    }


# =============================================================================
# PORTFOLIO SUMMARY
# =============================================================================

@router.get("/portfolio/{wallet_address}")
async def get_full_portfolio(
    wallet_address: str,
    db = Depends(get_database)
):
    """Get complete DeFi portfolio summary"""
    
    # In production, aggregate from all sources
    token_value = 13475  # From balances
    defi_value = 15230   # From positions
    nft_value = 75000    # From NFTs
    
    return {
        "wallet_address": wallet_address,
        "portfolio": {
            "tokens": {
                "value_usd": token_value,
                "count": 4
            },
            "defi_positions": {
                "value_usd": defi_value,
                "count": 4
            },
            "nfts": {
                "floor_value_usd": nft_value,
                "count": 2
            }
        },
        "total_value_usd": token_value + defi_value + nft_value,
        "chains": ["ethereum"],
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


# =============================================================================
# SUPPORTED CHAINS & PROTOCOLS
# =============================================================================

@router.get("/supported")
async def get_supported_chains_protocols():
    """Get supported chains and protocols"""
    return {
        "chains": [
            {"id": "ethereum", "name": "Ethereum", "chain_id": 1, "icon": "🔷"},
            {"id": "bsc", "name": "BNB Chain", "chain_id": 56, "icon": "🟡"},
            {"id": "polygon", "name": "Polygon", "chain_id": 137, "icon": "🟣"},
            {"id": "arbitrum", "name": "Arbitrum", "chain_id": 42161, "icon": "🔵"},
            {"id": "optimism", "name": "Optimism", "chain_id": 10, "icon": "🔴"},
            {"id": "avalanche", "name": "Avalanche", "chain_id": 43114, "icon": "🔺"},
            {"id": "base", "name": "Base", "chain_id": 8453, "icon": "🔵"}
        ],
        "protocols": [
            {"id": "uniswap", "name": "Uniswap", "type": "dex", "chains": ["ethereum", "polygon", "arbitrum"]},
            {"id": "aave", "name": "Aave", "type": "lending", "chains": ["ethereum", "polygon", "avalanche"]},
            {"id": "compound", "name": "Compound", "type": "lending", "chains": ["ethereum"]},
            {"id": "curve", "name": "Curve", "type": "dex", "chains": ["ethereum", "polygon", "arbitrum"]},
            {"id": "lido", "name": "Lido", "type": "staking", "chains": ["ethereum", "polygon"]},
            {"id": "yearn", "name": "Yearn", "type": "yield", "chains": ["ethereum"]},
            {"id": "convex", "name": "Convex", "type": "yield", "chains": ["ethereum"]}
        ],
        "wallet_types": ["metamask", "trust", "coinbase", "walletconnect", "rainbow"]
    }

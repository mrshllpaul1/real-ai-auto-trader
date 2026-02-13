"""
DeFi Yield Farming API Routes
==============================
Auto-compound yield positions, yield aggregator integration.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/yield-farming", tags=["Yield Farming"])

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

class FarmDeposit(BaseModel):
    vault_id: str
    amount_usd: float
    token: str
    auto_compound: bool = True


class WithdrawRequest(BaseModel):
    position_id: str
    amount_percent: float = 100  # Withdraw percentage


# =============================================================================
# YIELD OPPORTUNITIES
# =============================================================================

@router.get("/opportunities")
async def get_yield_opportunities(
    chain: str = "all",
    min_apy: float = 0,
    risk_level: str = "all",  # low, medium, high, all
    db = Depends(get_database)
):
    """Get available yield farming opportunities"""
    
    opportunities = [
        # Stablecoin yields (Low Risk)
        {
            "vault_id": "aave-usdc-eth",
            "name": "USDC Lending",
            "protocol": "Aave V3",
            "chain": "ethereum",
            "token": "USDC",
            "apy": 4.5,
            "apy_breakdown": {"base": 3.2, "rewards": 1.3},
            "tvl": 2500000000,
            "risk_level": "low",
            "strategy": "Single-sided stablecoin lending",
            "auto_compound": True,
            "min_deposit": 100,
            "withdrawal_fee": 0,
            "deposit_fee": 0
        },
        {
            "vault_id": "curve-3pool",
            "name": "3pool LP",
            "protocol": "Curve + Convex",
            "chain": "ethereum",
            "token": "3CRV",
            "tokens_accepted": ["DAI", "USDC", "USDT"],
            "apy": 6.8,
            "apy_breakdown": {"base": 1.5, "crv": 3.2, "cvx": 2.1},
            "tvl": 1800000000,
            "risk_level": "low",
            "strategy": "Stablecoin LP with boosted rewards",
            "auto_compound": True,
            "min_deposit": 100,
            "withdrawal_fee": 0.04
        },
        # ETH yields (Medium Risk)
        {
            "vault_id": "lido-steth",
            "name": "stETH Staking",
            "protocol": "Lido",
            "chain": "ethereum",
            "token": "ETH",
            "apy": 3.8,
            "apy_breakdown": {"staking_rewards": 3.8},
            "tvl": 15000000000,
            "risk_level": "medium",
            "strategy": "Liquid ETH staking",
            "auto_compound": False,
            "min_deposit": 0.01,
            "withdrawal_fee": 0
        },
        {
            "vault_id": "reth-rocket",
            "name": "rETH Staking",
            "protocol": "Rocket Pool",
            "chain": "ethereum",
            "token": "ETH",
            "apy": 4.1,
            "apy_breakdown": {"staking_rewards": 4.1},
            "tvl": 2000000000,
            "risk_level": "medium",
            "strategy": "Decentralized ETH staking",
            "auto_compound": True,
            "min_deposit": 0.01,
            "withdrawal_fee": 0
        },
        {
            "vault_id": "uni-eth-usdc",
            "name": "ETH/USDC LP",
            "protocol": "Uniswap V3",
            "chain": "ethereum",
            "token": "UNI-V3-LP",
            "tokens_accepted": ["ETH", "USDC"],
            "apy": 25.5,
            "apy_breakdown": {"fees": 25.5},
            "tvl": 500000000,
            "risk_level": "medium",
            "strategy": "Concentrated liquidity",
            "auto_compound": False,
            "min_deposit": 500,
            "impermanent_loss_risk": "medium",
            "withdrawal_fee": 0
        },
        # High yield (High Risk)
        {
            "vault_id": "gmx-glp",
            "name": "GLP Vault",
            "protocol": "GMX",
            "chain": "arbitrum",
            "token": "GLP",
            "tokens_accepted": ["ETH", "USDC", "BTC"],
            "apy": 35.2,
            "apy_breakdown": {"eth_rewards": 20.5, "esGMX": 14.7},
            "tvl": 450000000,
            "risk_level": "high",
            "strategy": "Perpetuals liquidity provision",
            "auto_compound": True,
            "min_deposit": 100,
            "withdrawal_fee": 0.3
        },
        {
            "vault_id": "pendle-steth",
            "name": "stETH Yield",
            "protocol": "Pendle",
            "chain": "ethereum",
            "token": "PT-stETH",
            "apy": 12.5,
            "apy_breakdown": {"fixed_yield": 12.5},
            "tvl": 200000000,
            "risk_level": "medium",
            "strategy": "Fixed yield tokenization",
            "auto_compound": False,
            "min_deposit": 100,
            "maturity_date": "2026-12-31"
        },
        {
            "vault_id": "yearn-eth",
            "name": "ETH Vault",
            "protocol": "Yearn",
            "chain": "ethereum",
            "token": "yvETH",
            "apy": 8.2,
            "apy_breakdown": {"strategy_yield": 8.2},
            "tvl": 150000000,
            "risk_level": "medium",
            "strategy": "Auto-compounding multi-strategy",
            "auto_compound": True,
            "min_deposit": 0.1,
            "withdrawal_fee": 0
        },
        # BSC opportunities
        {
            "vault_id": "pancake-cake",
            "name": "CAKE Staking",
            "protocol": "PancakeSwap",
            "chain": "bsc",
            "token": "CAKE",
            "apy": 22.5,
            "apy_breakdown": {"staking": 22.5},
            "tvl": 800000000,
            "risk_level": "high",
            "strategy": "Single-sided CAKE staking",
            "auto_compound": True,
            "min_deposit": 10,
            "withdrawal_fee": 0
        },
        {
            "vault_id": "venus-bnb",
            "name": "BNB Lending",
            "protocol": "Venus",
            "chain": "bsc",
            "token": "BNB",
            "apy": 5.5,
            "apy_breakdown": {"lending": 3.2, "xvs": 2.3},
            "tvl": 500000000,
            "risk_level": "medium",
            "strategy": "BNB lending with XVS rewards",
            "auto_compound": True,
            "min_deposit": 0.1,
            "withdrawal_fee": 0
        }
    ]
    
    # Filter by chain
    if chain != "all":
        opportunities = [o for o in opportunities if o["chain"] == chain]
    
    # Filter by min APY
    opportunities = [o for o in opportunities if o["apy"] >= min_apy]
    
    # Filter by risk level
    if risk_level != "all":
        opportunities = [o for o in opportunities if o["risk_level"] == risk_level]
    
    # Sort by APY
    opportunities.sort(key=lambda x: x["apy"], reverse=True)
    
    return {
        "opportunities": opportunities,
        "total": len(opportunities),
        "filters": {"chain": chain, "min_apy": min_apy, "risk_level": risk_level}
    }


@router.get("/vault/{vault_id}")
async def get_vault_details(vault_id: str, db = Depends(get_database)):
    """Get detailed information about a specific vault"""
    # Get from opportunities
    opps = await get_yield_opportunities(db=db)
    vault = next((o for o in opps["opportunities"] if o["vault_id"] == vault_id), None)
    
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")
    
    # Add historical APY data
    vault["apy_history"] = [
        {"date": "2026-02-02", "apy": vault["apy"] * 0.95},
        {"date": "2026-02-03", "apy": vault["apy"] * 0.98},
        {"date": "2026-02-04", "apy": vault["apy"] * 1.02},
        {"date": "2026-02-05", "apy": vault["apy"] * 0.97},
        {"date": "2026-02-06", "apy": vault["apy"] * 1.01},
        {"date": "2026-02-07", "apy": vault["apy"] * 0.99},
        {"date": "2026-02-08", "apy": vault["apy"] * 1.0},
        {"date": "2026-02-09", "apy": vault["apy"]}
    ]
    
    return vault


# =============================================================================
# USER POSITIONS
# =============================================================================

@router.post("/deposit")
async def deposit_to_vault(
    deposit: FarmDeposit,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Deposit funds into a yield vault"""
    position_id = str(uuid.uuid4())
    
    # Get vault info
    opps = await get_yield_opportunities(db=db)
    vault = next((o for o in opps["opportunities"] if o["vault_id"] == deposit.vault_id), None)
    
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")
    
    if deposit.amount_usd < vault.get("min_deposit", 0):
        raise HTTPException(status_code=400, detail=f"Minimum deposit is ${vault['min_deposit']}")
    
    position = {
        "position_id": position_id,
        "user_id": user_id,
        "vault_id": deposit.vault_id,
        "vault_name": vault["name"],
        "protocol": vault["protocol"],
        "chain": vault["chain"],
        "token": deposit.token,
        "deposited_usd": deposit.amount_usd,
        "current_value_usd": deposit.amount_usd,
        "apy_at_deposit": vault["apy"],
        "current_apy": vault["apy"],
        "earned_usd": 0,
        "auto_compound": deposit.auto_compound,
        "status": "active",
        "deposited_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.yield_positions.insert_one(position)
    
    return {
        "status": "deposited",
        "position": {k: v for k, v in position.items() if k != "_id"},
        "message": f"Deposited ${deposit.amount_usd} into {vault['name']}"
    }


@router.get("/positions")
async def get_user_positions(
    user_id: str = "default_user",
    status: str = "active",
    db = Depends(get_database)
):
    """Get user's yield farming positions"""
    positions = await db.yield_positions.find(
        {"user_id": user_id, "status": status},
        {"_id": 0}
    ).to_list(100)
    
    # Simulate earnings (in production, calculate from on-chain data)
    total_deposited = 0
    total_current = 0
    total_earned = 0
    
    for pos in positions:
        # Simulate some earnings based on time and APY
        days_since_deposit = 7  # Simplified
        daily_rate = pos["current_apy"] / 365 / 100
        earned = pos["deposited_usd"] * daily_rate * days_since_deposit
        pos["earned_usd"] = round(earned, 2)
        pos["current_value_usd"] = round(pos["deposited_usd"] + earned, 2)
        
        total_deposited += pos["deposited_usd"]
        total_current += pos["current_value_usd"]
        total_earned += pos["earned_usd"]
    
    return {
        "positions": positions,
        "summary": {
            "total_positions": len(positions),
            "total_deposited_usd": round(total_deposited, 2),
            "total_current_value_usd": round(total_current, 2),
            "total_earned_usd": round(total_earned, 2),
            "overall_apy": round(total_earned / total_deposited * 365 / 7 * 100, 1) if total_deposited > 0 else 0
        }
    }


@router.post("/withdraw")
async def withdraw_from_vault(
    request: WithdrawRequest,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Withdraw from a yield position"""
    position = await db.yield_positions.find_one({
        "position_id": request.position_id,
        "user_id": user_id,
        "status": "active"
    })
    
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    # Calculate withdrawal
    withdraw_amount = position["current_value_usd"] * (request.amount_percent / 100)
    
    if request.amount_percent >= 100:
        # Full withdrawal
        await db.yield_positions.update_one(
            {"position_id": request.position_id},
            {"$set": {
                "status": "withdrawn",
                "withdrawn_amount": withdraw_amount,
                "withdrawn_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        # Partial withdrawal
        remaining = position["current_value_usd"] - withdraw_amount
        await db.yield_positions.update_one(
            {"position_id": request.position_id},
            {"$set": {
                "current_value_usd": remaining,
                "deposited_usd": remaining  # Reset basis
            }}
        )
    
    return {
        "status": "withdrawn",
        "amount_usd": round(withdraw_amount, 2),
        "position_id": request.position_id
    }


@router.post("/compound/{position_id}")
async def manual_compound(
    position_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Manually compound earnings into principal"""
    position = await db.yield_positions.find_one({
        "position_id": position_id,
        "user_id": user_id,
        "status": "active"
    })
    
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    if position.get("auto_compound"):
        return {"status": "auto_compound_enabled", "message": "Position auto-compounds automatically"}
    
    # Compound earnings
    earned = position.get("earned_usd", 0)
    new_principal = position["deposited_usd"] + earned
    
    await db.yield_positions.update_one(
        {"position_id": position_id},
        {"$set": {
            "deposited_usd": new_principal,
            "earned_usd": 0,
            "last_compounded": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "status": "compounded",
        "compounded_amount": round(earned, 2),
        "new_principal": round(new_principal, 2)
    }


# =============================================================================
# IMPERMANENT LOSS CALCULATOR
# =============================================================================

@router.post("/calculate-il")
async def calculate_impermanent_loss(
    initial_price_ratio: float,
    current_price_ratio: float
):
    """Calculate impermanent loss for LP positions"""
    # IL formula: IL = 2 * sqrt(price_ratio) / (1 + price_ratio) - 1
    import math
    
    ratio_change = current_price_ratio / initial_price_ratio
    il = 2 * math.sqrt(ratio_change) / (1 + ratio_change) - 1
    il_percent = il * 100
    
    return {
        "initial_price_ratio": initial_price_ratio,
        "current_price_ratio": current_price_ratio,
        "price_change_percent": round((ratio_change - 1) * 100, 2),
        "impermanent_loss_percent": round(il_percent, 2),
        "explanation": f"If you had just held the tokens, you would have {abs(il_percent):.2f}% more value" if il_percent < 0 else "No impermanent loss"
    }


# =============================================================================
# APY COMPARISON
# =============================================================================

@router.get("/compare")
async def compare_yield_options(
    token: str,
    db = Depends(get_database)
):
    """Compare yield options for a specific token"""
    opps = await get_yield_opportunities(db=db)
    
    # Filter by token
    matching = [
        o for o in opps["opportunities"]
        if token.upper() in o.get("token", "").upper() or 
           token.upper() in str(o.get("tokens_accepted", [])).upper()
    ]
    
    # Sort by APY
    matching.sort(key=lambda x: x["apy"], reverse=True)
    
    return {
        "token": token,
        "options": matching,
        "best_option": matching[0] if matching else None,
        "total_options": len(matching)
    }

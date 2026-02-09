"""
Portfolio Rebalancing API Routes
=================================
AI-powered portfolio rebalancing suggestions and automation.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import math

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rebalance", tags=["Portfolio Rebalancing"])

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

class RebalanceConfig(BaseModel):
    target_allocation: Dict[str, float]  # {"BTC": 40, "ETH": 30, "USDC": 30}
    rebalance_threshold: float = 5.0  # Rebalance when off by 5%
    min_trade_size: float = 50.0
    max_slippage_pct: float = 0.5
    auto_execute: bool = False


class ManualRebalance(BaseModel):
    trades: List[Dict[str, Any]]  # List of trades to execute


# =============================================================================
# PORTFOLIO ANALYSIS
# =============================================================================

async def get_current_portfolio(user_id: str, db) -> Dict:
    """Get current portfolio holdings across all position types"""
    
    # Get spot holdings
    holdings = await db.holdings.find(
        {"user_id": user_id},
        {"_id": 0}
    ).to_list(100)
    
    # Get perpetual positions
    perp_positions = await db.perp_positions.find(
        {"user_id": user_id, "status": "open"},
        {"_id": 0}
    ).to_list(100)
    
    # Get yield farming positions
    yield_positions = await db.yield_positions.find(
        {"user_id": user_id, "status": "active"},
        {"_id": 0}
    ).to_list(100)
    
    # Aggregate by asset
    portfolio = {}
    total_value = 0
    
    # Spot holdings
    for h in holdings:
        asset = h.get("symbol", "Unknown")
        value = h.get("value_usd", 0)
        if asset not in portfolio:
            portfolio[asset] = {"spot": 0, "perp": 0, "yield": 0, "total": 0}
        portfolio[asset]["spot"] += value
        portfolio[asset]["total"] += value
        total_value += value
    
    # Perpetual positions (margin)
    for p in perp_positions:
        symbol = p.get("symbol", "").split("-")[0]  # BTC-PERP -> BTC
        margin = p.get("margin", 0)
        if symbol not in portfolio:
            portfolio[symbol] = {"spot": 0, "perp": 0, "yield": 0, "total": 0}
        portfolio[symbol]["perp"] += margin
        portfolio[symbol]["total"] += margin
        total_value += margin
    
    # Yield farming (simplified)
    for y in yield_positions:
        token = y.get("token", "Unknown")
        value = y.get("current_value_usd", 0)
        if token not in portfolio:
            portfolio[token] = {"spot": 0, "perp": 0, "yield": 0, "total": 0}
        portfolio[token]["yield"] += value
        portfolio[token]["total"] += value
        total_value += value
    
    # Calculate percentages
    for asset in portfolio:
        portfolio[asset]["percentage"] = round(
            (portfolio[asset]["total"] / total_value * 100) if total_value > 0 else 0, 2
        )
    
    return {
        "holdings": portfolio,
        "total_value": round(total_value, 2)
    }


def calculate_rebalance_trades(
    current: Dict,
    target: Dict[str, float],
    total_value: float,
    min_trade_size: float
) -> List[Dict]:
    """Calculate trades needed to reach target allocation"""
    
    trades = []
    
    # Normalize target allocations
    target_sum = sum(target.values())
    normalized_target = {k: v / target_sum * 100 for k, v in target.items()}
    
    for asset, target_pct in normalized_target.items():
        current_holding = current.get(asset, {})
        current_pct = current_holding.get("percentage", 0)
        current_value = current_holding.get("total", 0)
        
        # Calculate difference
        diff_pct = target_pct - current_pct
        diff_value = (diff_pct / 100) * total_value
        
        if abs(diff_value) >= min_trade_size:
            trades.append({
                "asset": asset,
                "action": "buy" if diff_value > 0 else "sell",
                "amount_usd": abs(round(diff_value, 2)),
                "current_pct": current_pct,
                "target_pct": target_pct,
                "diff_pct": round(diff_pct, 2)
            })
    
    # Sort by absolute difference (largest first)
    trades.sort(key=lambda x: abs(x["diff_pct"]), reverse=True)
    
    return trades


def calculate_risk_adjusted_allocation(portfolio: Dict, risk_score: float) -> Dict[str, float]:
    """Calculate risk-adjusted target allocation based on current risk score"""
    
    # Base allocations for different risk levels
    conservative = {"BTC": 30, "ETH": 20, "USDC": 40, "OTHER": 10}
    balanced = {"BTC": 40, "ETH": 30, "USDC": 20, "OTHER": 10}
    aggressive = {"BTC": 50, "ETH": 35, "USDC": 5, "OTHER": 10}
    
    # Interpolate based on risk score
    if risk_score >= 70:  # High risk - suggest more conservative
        return conservative
    elif risk_score >= 40:
        return balanced
    else:
        return aggressive


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get("/analyze")
async def analyze_portfolio(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Analyze current portfolio allocation"""
    
    portfolio_data = await get_current_portfolio(user_id, db)
    
    # Get current allocation
    current_allocation = {
        asset: data["percentage"] 
        for asset, data in portfolio_data["holdings"].items()
    }
    
    # Check concentration risk
    max_allocation = max(current_allocation.values()) if current_allocation else 0
    concentration_risk = "high" if max_allocation > 50 else "medium" if max_allocation > 35 else "low"
    
    # Diversification score (0-100)
    num_assets = len(current_allocation)
    avg_allocation = 100 / num_assets if num_assets > 0 else 0
    diversification = sum(
        1 - abs(pct - avg_allocation) / 100 
        for pct in current_allocation.values()
    ) / num_assets * 100 if num_assets > 0 else 0
    
    return {
        "current_allocation": current_allocation,
        "total_value": portfolio_data["total_value"],
        "holdings_detail": portfolio_data["holdings"],
        "metrics": {
            "num_assets": num_assets,
            "concentration_risk": concentration_risk,
            "max_allocation": round(max_allocation, 2),
            "diversification_score": round(diversification, 1)
        }
    }


@router.post("/suggest")
async def suggest_rebalancing(
    target_allocation: Optional[Dict[str, float]] = None,
    risk_based: bool = True,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get AI-powered rebalancing suggestions"""
    
    # Get current portfolio
    portfolio_data = await get_current_portfolio(user_id, db)
    current = portfolio_data["holdings"]
    total_value = portfolio_data["total_value"]
    
    # Get risk score if risk-based allocation
    if risk_based and not target_allocation:
        # Fetch from risk analyzer
        try:
            from routes.risk_analyzer import calculate_perpetuals_risk, calculate_yield_risk
            
            perp_positions = await db.perp_positions.find(
                {"user_id": user_id, "status": "open"}, {"_id": 0}
            ).to_list(100)
            
            perp_risk = calculate_perpetuals_risk(perp_positions)
            risk_score = min(perp_risk["avg_leverage"] * 5, 100)  # Simplified
        except:
            risk_score = 50  # Default to balanced
        
        target_allocation = calculate_risk_adjusted_allocation(portfolio_data, risk_score)
    elif not target_allocation:
        # Default balanced allocation
        target_allocation = {"BTC": 40, "ETH": 30, "USDC": 20, "OTHER": 10}
    
    # Calculate required trades
    trades = calculate_rebalance_trades(current, target_allocation, total_value, 50.0)
    
    # Calculate impact metrics
    total_trade_volume = sum(t["amount_usd"] for t in trades)
    estimated_fees = total_trade_volume * 0.001  # 0.1% fee estimate
    
    # Risk impact assessment
    risk_impact = "positive" if any(
        t["asset"] in ["USDC", "USDT", "DAI"] and t["action"] == "buy" 
        for t in trades
    ) else "neutral"
    
    return {
        "current_allocation": {a: d["percentage"] for a, d in current.items()},
        "target_allocation": target_allocation,
        "suggested_trades": trades,
        "summary": {
            "total_trades": len(trades),
            "total_volume": round(total_trade_volume, 2),
            "estimated_fees": round(estimated_fees, 2),
            "risk_impact": risk_impact
        },
        "portfolio_value": total_value
    }


@router.post("/calculate")
async def calculate_custom_rebalance(
    config: RebalanceConfig,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Calculate rebalancing with custom target allocation"""
    
    portfolio_data = await get_current_portfolio(user_id, db)
    current = portfolio_data["holdings"]
    total_value = portfolio_data["total_value"]
    
    trades = calculate_rebalance_trades(
        current, 
        config.target_allocation, 
        total_value, 
        config.min_trade_size
    )
    
    # Filter by threshold
    filtered_trades = [
        t for t in trades 
        if abs(t["diff_pct"]) >= config.rebalance_threshold
    ]
    
    return {
        "trades": filtered_trades,
        "all_trades": trades,
        "config": config.dict(),
        "needs_rebalancing": len(filtered_trades) > 0
    }


@router.get("/templates")
async def get_allocation_templates():
    """Get predefined allocation templates"""
    
    return {
        "templates": [
            {
                "name": "Conservative",
                "description": "Low risk, heavy on stablecoins",
                "allocation": {"BTC": 25, "ETH": 15, "USDC": 50, "SOL": 5, "OTHER": 5},
                "risk_level": "low"
            },
            {
                "name": "Balanced",
                "description": "Moderate risk, diversified",
                "allocation": {"BTC": 40, "ETH": 30, "USDC": 20, "SOL": 5, "OTHER": 5},
                "risk_level": "medium"
            },
            {
                "name": "Growth",
                "description": "Higher risk, growth-focused",
                "allocation": {"BTC": 45, "ETH": 35, "SOL": 10, "USDC": 5, "OTHER": 5},
                "risk_level": "high"
            },
            {
                "name": "BTC Maximalist",
                "description": "Bitcoin-heavy portfolio",
                "allocation": {"BTC": 70, "ETH": 15, "USDC": 10, "OTHER": 5},
                "risk_level": "high"
            },
            {
                "name": "ETH Focused",
                "description": "Ethereum ecosystem heavy",
                "allocation": {"ETH": 50, "BTC": 25, "USDC": 15, "LINK": 5, "OTHER": 5},
                "risk_level": "medium"
            },
            {
                "name": "DeFi Yield",
                "description": "Optimized for DeFi yields",
                "allocation": {"ETH": 30, "USDC": 40, "USDT": 20, "OTHER": 10},
                "risk_level": "medium"
            },
            {
                "name": "Alt Season",
                "description": "High altcoin exposure",
                "allocation": {"BTC": 20, "ETH": 25, "SOL": 20, "ARB": 15, "LINK": 10, "OTHER": 10},
                "risk_level": "high"
            }
        ]
    }


@router.get("/history")
async def get_rebalance_history(
    limit: int = 20,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get rebalancing history"""
    
    history = await db.rebalance_history.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("executed_at", -1).limit(limit).to_list(limit)
    
    return {
        "history": history,
        "total": len(history)
    }


@router.post("/execute")
async def execute_rebalance(
    trades: List[Dict[str, Any]],
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Execute rebalancing trades (simulated)"""
    
    import uuid
    
    executed_trades = []
    total_volume = 0
    
    for trade in trades:
        # Simulate trade execution
        executed = {
            "trade_id": str(uuid.uuid4()),
            "asset": trade["asset"],
            "action": trade["action"],
            "amount_usd": trade["amount_usd"],
            "executed_price": trade.get("price", 0),  # Would get real price
            "status": "executed",
            "executed_at": datetime.now(timezone.utc).isoformat()
        }
        executed_trades.append(executed)
        total_volume += trade["amount_usd"]
    
    # Store rebalance event
    rebalance_record = {
        "rebalance_id": str(uuid.uuid4()),
        "user_id": user_id,
        "trades": executed_trades,
        "total_volume": total_volume,
        "executed_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.rebalance_history.insert_one(rebalance_record)
    
    return {
        "status": "executed",
        "trades": executed_trades,
        "total_volume": round(total_volume, 2),
        "rebalance_id": rebalance_record["rebalance_id"]
    }


@router.get("/config")
async def get_rebalance_config(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get user's rebalancing configuration"""
    
    config = await db.rebalance_config.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if not config:
        return {
            "configured": False,
            "config": None
        }
    
    return {
        "configured": True,
        "config": config
    }


@router.post("/config")
async def save_rebalance_config(
    config: RebalanceConfig,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Save rebalancing configuration"""
    
    config_data = {
        "user_id": user_id,
        **config.dict(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.rebalance_config.replace_one(
        {"user_id": user_id},
        config_data,
        upsert=True
    )
    
    return {"status": "saved", "config": config_data}


@router.get("/drift")
async def check_portfolio_drift(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Check if portfolio has drifted from target allocation"""
    
    # Get saved config
    config = await db.rebalance_config.find_one({"user_id": user_id})
    
    if not config or not config.get("target_allocation"):
        return {
            "has_target": False,
            "drift": None,
            "needs_rebalancing": False
        }
    
    # Get current allocation
    portfolio = await get_current_portfolio(user_id, db)
    current = {a: d["percentage"] for a, d in portfolio["holdings"].items()}
    target = config["target_allocation"]
    
    # Calculate drift for each asset
    drifts = {}
    max_drift = 0
    
    for asset, target_pct in target.items():
        current_pct = current.get(asset, 0)
        drift = current_pct - target_pct
        drifts[asset] = {
            "current": round(current_pct, 2),
            "target": target_pct,
            "drift": round(drift, 2)
        }
        max_drift = max(max_drift, abs(drift))
    
    threshold = config.get("rebalance_threshold", 5.0)
    
    return {
        "has_target": True,
        "drifts": drifts,
        "max_drift": round(max_drift, 2),
        "threshold": threshold,
        "needs_rebalancing": max_drift > threshold
    }

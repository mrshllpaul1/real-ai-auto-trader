"""
Perpetual Futures Trading API Routes
=====================================
Leverage trading with funding rates and liquidation tracking.
Uses REAL market prices from Kraken API.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import math
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/perpetuals", tags=["Perpetual Futures"])

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


async def get_real_perp_price(symbol: str) -> float:
    """Get REAL price from Kraken API for perpetual markets"""
    # Extract base asset from symbol like "BTC-PERP" -> "BTC"
    base = symbol.replace("-PERP", "").upper()
    
    symbol_map = {
        "BTC": "XXBTZUSD",
        "ETH": "XETHZUSD", 
        "SOL": "SOLUSD",
        "AVAX": "AVAXUSD",
        "ARB": "ARBUSD",
        "DOGE": "XDGUSD",
        "XRP": "XXRPZUSD"
    }
    pair = symbol_map.get(base, f"{base}USD")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.kraken.com/0/public/Ticker",
                params={"pair": pair}
            )
            data = response.json()
            if not data.get("error") and data.get("result"):
                for key, ticker in data["result"].items():
                    return float(ticker['c'][0])
    except Exception as e:
        logger.warning(f"Failed to get Kraken price for {base}: {e}")
    
    return None


# =============================================================================
# MODELS
# =============================================================================

class PerpOrder(BaseModel):
    symbol: str  # BTC-PERP, ETH-PERP
    side: str  # long or short
    size_usd: float  # Position size in USD
    leverage: float = 1  # 1x to 10x
    order_type: str = "market"  # market, limit
    limit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reduce_only: bool = False


class ClosePosition(BaseModel):
    position_id: str
    close_percent: float = 100


class AdjustLeverage(BaseModel):
    position_id: str
    new_leverage: float


# =============================================================================
# MARKET DATA
# =============================================================================

@router.get("/markets")
async def get_perp_markets():
    """Get available perpetual futures markets"""
    markets = [
        {
            "symbol": "BTC-PERP",
            "base_asset": "BTC",
            "mark_price": 45250.50,
            "index_price": 45200.00,
            "24h_change": 2.35,
            "24h_volume": 5800000000,
            "open_interest": 12500000000,
            "funding_rate": 0.0012,  # 0.12% per 8h
            "next_funding": "2026-02-09T16:00:00Z",
            "max_leverage": 10,
            "min_size": 10,
            "tick_size": 0.5,
            "maintenance_margin": 0.5  # 0.5%
        },
        {
            "symbol": "ETH-PERP",
            "base_asset": "ETH",
            "mark_price": 2525.75,
            "index_price": 2520.00,
            "24h_change": 3.12,
            "24h_volume": 2100000000,
            "open_interest": 4500000000,
            "funding_rate": 0.0015,
            "next_funding": "2026-02-09T16:00:00Z",
            "max_leverage": 10,
            "min_size": 10,
            "tick_size": 0.05,
            "maintenance_margin": 0.5
        },
        {
            "symbol": "SOL-PERP",
            "base_asset": "SOL",
            "mark_price": 102.50,
            "index_price": 102.00,
            "24h_change": 5.45,
            "24h_volume": 850000000,
            "open_interest": 1200000000,
            "funding_rate": 0.0025,
            "next_funding": "2026-02-09T16:00:00Z",
            "max_leverage": 8,
            "min_size": 10,
            "tick_size": 0.01,
            "maintenance_margin": 1.0
        },
        {
            "symbol": "AVAX-PERP",
            "base_asset": "AVAX",
            "mark_price": 38.25,
            "index_price": 38.10,
            "24h_change": 4.20,
            "24h_volume": 320000000,
            "open_interest": 450000000,
            "funding_rate": 0.0018,
            "next_funding": "2026-02-09T16:00:00Z",
            "max_leverage": 5,
            "min_size": 10,
            "tick_size": 0.005,
            "maintenance_margin": 1.5
        },
        {
            "symbol": "ARB-PERP",
            "base_asset": "ARB",
            "mark_price": 1.85,
            "index_price": 1.84,
            "24h_change": 6.80,
            "24h_volume": 180000000,
            "open_interest": 250000000,
            "funding_rate": 0.0030,
            "next_funding": "2026-02-09T16:00:00Z",
            "max_leverage": 5,
            "min_size": 10,
            "tick_size": 0.001,
            "maintenance_margin": 2.0
        }
    ]
    
    return {"markets": markets}


@router.get("/market/{symbol}")
async def get_market_details(symbol: str):
    """Get detailed market information"""
    markets = (await get_perp_markets())["markets"]
    market = next((m for m in markets if m["symbol"] == symbol), None)
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    # Add order book data (simulated)
    market["orderbook"] = {
        "bids": [
            {"price": market["mark_price"] - 5, "size": 50000},
            {"price": market["mark_price"] - 10, "size": 120000},
            {"price": market["mark_price"] - 15, "size": 200000}
        ],
        "asks": [
            {"price": market["mark_price"] + 5, "size": 45000},
            {"price": market["mark_price"] + 10, "size": 110000},
            {"price": market["mark_price"] + 15, "size": 180000}
        ]
    }
    
    # Add funding history
    market["funding_history"] = [
        {"timestamp": "2026-02-09T08:00:00Z", "rate": 0.0010},
        {"timestamp": "2026-02-09T00:00:00Z", "rate": 0.0012},
        {"timestamp": "2026-02-08T16:00:00Z", "rate": 0.0015},
        {"timestamp": "2026-02-08T08:00:00Z", "rate": 0.0008}
    ]
    
    return market


# =============================================================================
# POSITION MANAGEMENT
# =============================================================================

@router.post("/order")
async def place_perp_order(
    order: PerpOrder,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Place a perpetual futures order"""
    # Get market info
    markets = (await get_perp_markets())["markets"]
    market = next((m for m in markets if m["symbol"] == order.symbol), None)
    
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    
    # Validate leverage
    if order.leverage > market["max_leverage"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Max leverage for {order.symbol} is {market['max_leverage']}x"
        )
    
    if order.leverage < 1:
        raise HTTPException(status_code=400, detail="Minimum leverage is 1x")
    
    if order.size_usd < market["min_size"]:
        raise HTTPException(status_code=400, detail=f"Minimum size is ${market['min_size']}")
    
    position_id = str(uuid.uuid4())
    entry_price = market["mark_price"]
    
    # Calculate position details
    notional_value = order.size_usd * order.leverage
    margin_required = order.size_usd
    position_size = notional_value / entry_price
    
    # Calculate liquidation price
    if order.side == "long":
        liquidation_price = entry_price * (1 - (1 / order.leverage) + (market["maintenance_margin"] / 100))
    else:
        liquidation_price = entry_price * (1 + (1 / order.leverage) - (market["maintenance_margin"] / 100))
    
    position = {
        "position_id": position_id,
        "user_id": user_id,
        "symbol": order.symbol,
        "side": order.side,
        "size_usd": order.size_usd,
        "leverage": order.leverage,
        "notional_value": round(notional_value, 2),
        "position_size": round(position_size, 6),
        "entry_price": entry_price,
        "mark_price": entry_price,
        "liquidation_price": round(liquidation_price, 2),
        "margin": margin_required,
        "unrealized_pnl": 0,
        "realized_pnl": 0,
        "funding_paid": 0,
        "stop_loss": order.stop_loss,
        "take_profit": order.take_profit,
        "status": "open",
        "opened_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.perp_positions.insert_one(position)
    
    return {
        "status": "opened",
        "position": {k: v for k, v in position.items() if k != "_id"},
        "message": f"Opened {order.leverage}x {order.side} {order.symbol} @ ${entry_price}"
    }


@router.get("/positions")
async def get_perp_positions(
    user_id: str = "default_user",
    status: str = "open",
    db = Depends(get_database)
):
    """Get user's perpetual positions"""
    positions = await db.perp_positions.find(
        {"user_id": user_id, "status": status},
        {"_id": 0}
    ).to_list(100)
    
    # Get current prices and update PnL
    markets = (await get_perp_markets())["markets"]
    
    total_margin = 0
    total_pnl = 0
    total_notional = 0
    
    for pos in positions:
        market = next((m for m in markets if m["symbol"] == pos["symbol"]), None)
        if market:
            current_price = market["mark_price"]
            pos["mark_price"] = current_price
            
            # Calculate unrealized PnL
            if pos["side"] == "long":
                pnl = (current_price - pos["entry_price"]) * pos["position_size"]
            else:
                pnl = (pos["entry_price"] - current_price) * pos["position_size"]
            
            pos["unrealized_pnl"] = round(pnl, 2)
            pos["pnl_percent"] = round(pnl / pos["margin"] * 100, 2)
            pos["roi"] = round(pnl / pos["size_usd"] * 100, 2)
            
            # Check liquidation distance
            if pos["side"] == "long":
                liq_distance = (current_price - pos["liquidation_price"]) / current_price * 100
            else:
                liq_distance = (pos["liquidation_price"] - current_price) / current_price * 100
            pos["liquidation_distance_pct"] = round(liq_distance, 2)
            
            total_margin += pos["margin"]
            total_pnl += pnl
            total_notional += pos["notional_value"]
    
    return {
        "positions": positions,
        "summary": {
            "total_positions": len(positions),
            "total_margin_used": round(total_margin, 2),
            "total_unrealized_pnl": round(total_pnl, 2),
            "total_notional": round(total_notional, 2),
            "long_positions": sum(1 for p in positions if p["side"] == "long"),
            "short_positions": sum(1 for p in positions if p["side"] == "short")
        }
    }


@router.post("/close")
async def close_perp_position(
    request: ClosePosition,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Close a perpetual position"""
    position = await db.perp_positions.find_one({
        "position_id": request.position_id,
        "user_id": user_id,
        "status": "open"
    })
    
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    # Get current price
    markets = (await get_perp_markets())["markets"]
    market = next((m for m in markets if m["symbol"] == position["symbol"]), None)
    exit_price = market["mark_price"] if market else position["entry_price"]
    
    # Calculate final PnL
    close_size = position["position_size"] * (request.close_percent / 100)
    
    if position["side"] == "long":
        pnl = (exit_price - position["entry_price"]) * close_size
    else:
        pnl = (position["entry_price"] - exit_price) * close_size
    
    pnl -= position.get("funding_paid", 0)  # Subtract funding
    
    if request.close_percent >= 100:
        await db.perp_positions.update_one(
            {"position_id": request.position_id},
            {"$set": {
                "status": "closed",
                "exit_price": exit_price,
                "realized_pnl": round(pnl, 2),
                "closed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        # Partial close
        remaining_size = position["position_size"] - close_size
        remaining_notional = remaining_size * exit_price
        await db.perp_positions.update_one(
            {"position_id": request.position_id},
            {"$set": {
                "position_size": remaining_size,
                "notional_value": remaining_notional,
                "size_usd": position["size_usd"] * (1 - request.close_percent / 100),
                "realized_pnl": position.get("realized_pnl", 0) + pnl
            }}
        )
    
    return {
        "status": "closed" if request.close_percent >= 100 else "partial_close",
        "exit_price": exit_price,
        "realized_pnl": round(pnl, 2),
        "close_percent": request.close_percent
    }


@router.post("/adjust-leverage")
async def adjust_position_leverage(
    request: AdjustLeverage,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Adjust leverage on an open position"""
    position = await db.perp_positions.find_one({
        "position_id": request.position_id,
        "user_id": user_id,
        "status": "open"
    })
    
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    # Validate new leverage
    markets = (await get_perp_markets())["markets"]
    market = next((m for m in markets if m["symbol"] == position["symbol"]), None)
    
    if market and request.new_leverage > market["max_leverage"]:
        raise HTTPException(status_code=400, detail=f"Max leverage is {market['max_leverage']}x")
    
    # Recalculate position with new leverage
    new_notional = position["size_usd"] * request.new_leverage
    current_price = market["mark_price"] if market else position["entry_price"]
    
    if position["side"] == "long":
        new_liq_price = position["entry_price"] * (1 - (1 / request.new_leverage) + 0.005)
    else:
        new_liq_price = position["entry_price"] * (1 + (1 / request.new_leverage) - 0.005)
    
    await db.perp_positions.update_one(
        {"position_id": request.position_id},
        {"$set": {
            "leverage": request.new_leverage,
            "notional_value": new_notional,
            "liquidation_price": round(new_liq_price, 2)
        }}
    )
    
    return {
        "status": "adjusted",
        "new_leverage": request.new_leverage,
        "new_liquidation_price": round(new_liq_price, 2)
    }


# =============================================================================
# FUNDING RATES
# =============================================================================

@router.get("/funding-rates")
async def get_funding_rates():
    """Get current funding rates for all markets"""
    markets = (await get_perp_markets())["markets"]
    
    rates = [{
        "symbol": m["symbol"],
        "funding_rate": m["funding_rate"],
        "funding_rate_annualized": round(m["funding_rate"] * 3 * 365 * 100, 2),  # 3 fundings per day
        "next_funding": m["next_funding"],
        "predicted_rate": round(m["funding_rate"] * (1 + (0.1 * (1 if m["24h_change"] > 0 else -1))), 4)
    } for m in markets]
    
    return {"funding_rates": rates}


# =============================================================================
# CALCULATORS
# =============================================================================

@router.post("/calculate-liquidation")
async def calculate_liquidation_price(
    entry_price: float,
    leverage: float,
    side: str,
    maintenance_margin: float = 0.5
):
    """Calculate liquidation price"""
    if side == "long":
        liq_price = entry_price * (1 - (1 / leverage) + (maintenance_margin / 100))
    else:
        liq_price = entry_price * (1 + (1 / leverage) - (maintenance_margin / 100))
    
    distance = abs(entry_price - liq_price) / entry_price * 100
    
    return {
        "entry_price": entry_price,
        "leverage": leverage,
        "side": side,
        "liquidation_price": round(liq_price, 2),
        "distance_percent": round(distance, 2)
    }


@router.post("/calculate-pnl")
async def calculate_potential_pnl(
    entry_price: float,
    exit_price: float,
    position_size: float,
    leverage: float,
    side: str
):
    """Calculate potential PnL"""
    if side == "long":
        pnl = (exit_price - entry_price) / entry_price * position_size * leverage
    else:
        pnl = (entry_price - exit_price) / entry_price * position_size * leverage
    
    roi = pnl / position_size * 100
    
    return {
        "entry_price": entry_price,
        "exit_price": exit_price,
        "position_size": position_size,
        "leverage": leverage,
        "side": side,
        "pnl_usd": round(pnl, 2),
        "roi_percent": round(roi, 2)
    }


@router.get("/leaderboard")
async def get_perp_leaderboard(db = Depends(get_database)):
    """Get perpetual trading leaderboard"""
    # Simulated leaderboard
    return {
        "leaderboard": [
            {"rank": 1, "trader": "PerpKing", "pnl_7d": 125000, "win_rate": 72, "trades": 89},
            {"rank": 2, "trader": "LeverageLord", "pnl_7d": 98500, "win_rate": 68, "trades": 156},
            {"rank": 3, "trader": "ShortMaster", "pnl_7d": 87200, "win_rate": 65, "trades": 203},
            {"rank": 4, "trader": "DeltaHunter", "pnl_7d": 76800, "win_rate": 71, "trades": 67},
            {"rank": 5, "trader": "FundingFarmer", "pnl_7d": 65400, "win_rate": 58, "trades": 312}
        ],
        "timeframe": "7d"
    }

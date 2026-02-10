"""
Options Trading API Routes
===========================
Trade crypto options (calls, puts) with AI-powered Greeks calculation and strategy suggestions.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import math
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/options", tags=["Options Trading"])

# Global database reference
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

class OptionOrder(BaseModel):
    symbol: str  # e.g., "BTC"
    option_type: str  # "call" or "put"
    strike_price: float
    expiry_date: str  # ISO format
    quantity: float
    order_type: str = "market"  # market, limit
    limit_price: Optional[float] = None


class OptionPosition(BaseModel):
    position_id: str
    symbol: str
    option_type: str
    strike_price: float
    expiry_date: str
    quantity: float
    entry_price: float
    current_price: float
    pnl: float
    greeks: Dict[str, float]


class GreeksRequest(BaseModel):
    symbol: str
    current_price: float
    strike_price: float
    time_to_expiry: float  # in years
    volatility: float  # annualized
    risk_free_rate: float = 0.05
    option_type: str = "call"


# =============================================================================
# BLACK-SCHOLES GREEKS CALCULATION
# =============================================================================

def norm_cdf(x):
    """Cumulative distribution function for standard normal"""
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0


def norm_pdf(x):
    """Probability density function for standard normal"""
    return math.exp(-x**2 / 2) / math.sqrt(2 * math.pi)


def calculate_d1_d2(S, K, T, r, sigma):
    """Calculate d1 and d2 for Black-Scholes"""
    if T <= 0 or sigma <= 0:
        return 0, 0
    d1 = (math.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return d1, d2


def calculate_greeks(S, K, T, r, sigma, option_type="call"):
    """
    Calculate option Greeks using Black-Scholes model.
    
    S: Current price
    K: Strike price
    T: Time to expiry (years)
    r: Risk-free rate
    sigma: Volatility (annualized)
    """
    if T <= 0:
        return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0, "price": 0}
    
    d1, d2 = calculate_d1_d2(S, K, T, r, sigma)
    
    # Common calculations
    sqrt_T = math.sqrt(T)
    exp_rT = math.exp(-r * T)
    
    if option_type == "call":
        delta = norm_cdf(d1)
        price = S * norm_cdf(d1) - K * exp_rT * norm_cdf(d2)
        theta = (-S * norm_pdf(d1) * sigma / (2 * sqrt_T) - r * K * exp_rT * norm_cdf(d2)) / 365
        rho = K * T * exp_rT * norm_cdf(d2) / 100
    else:  # put
        delta = norm_cdf(d1) - 1
        price = K * exp_rT * norm_cdf(-d2) - S * norm_cdf(-d1)
        theta = (-S * norm_pdf(d1) * sigma / (2 * sqrt_T) + r * K * exp_rT * norm_cdf(-d2)) / 365
        rho = -K * T * exp_rT * norm_cdf(-d2) / 100
    
    # Same for both
    gamma = norm_pdf(d1) / (S * sigma * sqrt_T)
    vega = S * norm_pdf(d1) * sqrt_T / 100
    
    return {
        "delta": round(delta, 4),
        "gamma": round(gamma, 6),
        "theta": round(theta, 4),
        "vega": round(vega, 4),
        "rho": round(rho, 4),
        "price": round(price, 2),
        "d1": round(d1, 4),
        "d2": round(d2, 4)
    }


# =============================================================================
# API ENDPOINTS
# =============================================================================

async def get_real_price(symbol: str) -> float:
    """Get real price from Kraken API"""
    import httpx
    symbol_map = {
        "BTC": "XXBTZUSD",
        "ETH": "XETHZUSD",
        "SOL": "SOLUSD"
    }
    pair = symbol_map.get(symbol.upper(), f"{symbol.upper()}USD")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.kraken.com/0/public/Ticker",
                params={"pair": pair}
            )
            data = response.json()
            if not data.get("error") and data.get("result"):
                for key, ticker in data["result"].items():
                    # 'c' is the last trade closed [price, lot volume]
                    return float(ticker['c'][0])
    except Exception as e:
        logger.warning(f"Failed to get Kraken price for {symbol}: {e}")
    
    # Fallback to CoinGecko if Kraken fails
    try:
        coin_map = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana"}
        coin_id = coin_map.get(symbol.upper(), symbol.lower())
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.coingecko.com/api/v3/simple/price",
                params={"ids": coin_id, "vs_currencies": "usd"}
            )
            data = response.json()
            if coin_id in data:
                return float(data[coin_id]['usd'])
    except Exception as e:
        logger.warning(f"Failed to get CoinGecko price for {symbol}: {e}")
    
    return None


@router.get("/chain/{symbol}")
async def get_option_chain(
    symbol: str,
    db = Depends(get_database)
):
    """Get available options chain for a symbol with REAL market prices"""
    # Get REAL price from Kraken
    current_price = await get_real_price(symbol.upper())
    
    if current_price is None:
        raise HTTPException(status_code=503, detail=f"Unable to fetch real price for {symbol}")
    
    # Generate strikes around current price
    strikes = []
    base_strike = round(current_price / 1000) * 1000
    for i in range(-5, 6):
        strike = base_strike + i * (current_price * 0.05)
        strikes.append(round(strike, -2 if current_price > 1000 else 0))
    
    # Generate expiry dates (weekly for next 4 weeks, monthly for 3 months)
    expiries = []
    today = datetime.now(timezone.utc)
    
    # Weekly expiries
    for i in range(1, 5):
        expiry = today + timedelta(days=7*i)
        expiries.append({
            "date": expiry.strftime("%Y-%m-%d"),
            "days_to_expiry": 7*i,
            "type": "weekly"
        })
    
    # Monthly expiries
    for i in range(1, 4):
        expiry = today + timedelta(days=30*i)
        expiries.append({
            "date": expiry.strftime("%Y-%m-%d"),
            "days_to_expiry": 30*i,
            "type": "monthly"
        })
    
    # Generate options for each strike and expiry
    options = []
    volatility = 0.65  # 65% annualized volatility for crypto
    
    for expiry in expiries:
        T = expiry["days_to_expiry"] / 365
        for strike in strikes:
            call_greeks = calculate_greeks(current_price, strike, T, 0.05, volatility, "call")
            put_greeks = calculate_greeks(current_price, strike, T, 0.05, volatility, "put")
            
            options.append({
                "strike": strike,
                "expiry": expiry["date"],
                "days_to_expiry": expiry["days_to_expiry"],
                "call": {
                    "bid": round(call_greeks["price"] * 0.98, 2),
                    "ask": round(call_greeks["price"] * 1.02, 2),
                    "last": call_greeks["price"],
                    "volume": int(1000 * math.exp(-abs(strike - current_price) / current_price)),
                    "open_interest": int(5000 * math.exp(-abs(strike - current_price) / current_price)),
                    "greeks": call_greeks
                },
                "put": {
                    "bid": round(put_greeks["price"] * 0.98, 2),
                    "ask": round(put_greeks["price"] * 1.02, 2),
                    "last": put_greeks["price"],
                    "volume": int(800 * math.exp(-abs(strike - current_price) / current_price)),
                    "open_interest": int(4000 * math.exp(-abs(strike - current_price) / current_price)),
                    "greeks": put_greeks
                }
            })
    
    return {
        "symbol": symbol.upper(),
        "current_price": current_price,
        "strikes": strikes,
        "expiries": expiries,
        "options": options,
        "volatility": volatility,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


@router.post("/calculate-greeks")
async def calculate_option_greeks(request: GreeksRequest):
    """Calculate Greeks for a specific option"""
    greeks = calculate_greeks(
        S=request.current_price,
        K=request.strike_price,
        T=request.time_to_expiry,
        r=request.risk_free_rate,
        sigma=request.volatility,
        option_type=request.option_type
    )
    
    return {
        "symbol": request.symbol,
        "option_type": request.option_type,
        "strike": request.strike_price,
        "current_price": request.current_price,
        "time_to_expiry_years": request.time_to_expiry,
        "volatility": request.volatility,
        "greeks": greeks
    }


@router.post("/order")
async def place_option_order(
    order: OptionOrder,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Place an option order with REAL market prices"""
    # Get REAL price from Kraken
    current_price = await get_real_price(order.symbol.upper())
    
    if current_price is None:
        raise HTTPException(status_code=503, detail=f"Unable to fetch real price for {order.symbol}")
    
    # Calculate days to expiry
    expiry = datetime.fromisoformat(order.expiry_date.replace('Z', '+00:00'))
    days_to_expiry = (expiry - datetime.now(timezone.utc)).days
    T = max(days_to_expiry, 1) / 365
    
    # Calculate Greeks and price
    greeks = calculate_greeks(
        S=current_price,
        K=order.strike_price,
        T=T,
        r=0.05,
        sigma=0.65,
        option_type=order.option_type
    )
    
    # Create order record
    order_record = {
        "order_id": str(uuid.uuid4()),
        "user_id": user_id,
        "symbol": order.symbol.upper(),
        "option_type": order.option_type,
        "strike_price": order.strike_price,
        "expiry_date": order.expiry_date,
        "quantity": order.quantity,
        "order_type": order.order_type,
        "limit_price": order.limit_price,
        "fill_price": greeks["price"],
        "total_cost": greeks["price"] * order.quantity,
        "greeks": greeks,
        "status": "filled",  # Simulated instant fill
        "created_at": datetime.now(timezone.utc).isoformat(),
        "filled_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.option_orders.insert_one(order_record)
    
    # Create position
    position = {
        "position_id": str(uuid.uuid4()),
        "user_id": user_id,
        "symbol": order.symbol.upper(),
        "option_type": order.option_type,
        "strike_price": order.strike_price,
        "expiry_date": order.expiry_date,
        "quantity": order.quantity,
        "entry_price": greeks["price"],
        "current_price": greeks["price"],
        "pnl": 0,
        "greeks": greeks,
        "status": "open",
        "opened_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.option_positions.insert_one(position)
    
    return {
        "status": "success",
        "order": {k: v for k, v in order_record.items() if k != "_id"},
        "position": {k: v for k, v in position.items() if k != "_id"}
    }


@router.get("/positions")
async def get_option_positions(
    user_id: str = "default_user",
    status: str = "open",
    db = Depends(get_database)
):
    """Get user's option positions with REAL market prices"""
    positions = await db.option_positions.find(
        {"user_id": user_id, "status": status},
        {"_id": 0}
    ).to_list(100)
    
    # Update greeks and P&L for each position with REAL prices
    for pos in positions:
        current_price = await get_real_price(pos["symbol"])
        if current_price is None:
            current_price = pos.get("entry_price", 0)  # Fallback to entry price
        expiry = datetime.fromisoformat(pos["expiry_date"].replace('Z', '+00:00'))
        days_to_expiry = max((expiry - datetime.now(timezone.utc)).days, 0)
        T = max(days_to_expiry, 0.01) / 365
        
        # Recalculate greeks with current price
        greeks = calculate_greeks(
            S=current_price,
            K=pos["strike_price"],
            T=T,
            r=0.05,
            sigma=0.65,
            option_type=pos["option_type"]
        )
        
        pos["current_price"] = greeks["price"]
        pos["greeks"] = greeks
        pos["pnl"] = round((greeks["price"] - pos["entry_price"]) * pos["quantity"], 2)
        pos["pnl_pct"] = round((greeks["price"] - pos["entry_price"]) / pos["entry_price"] * 100, 2) if pos["entry_price"] > 0 else 0
        pos["days_to_expiry"] = days_to_expiry
    
    # Calculate totals
    total_value = sum(p["current_price"] * p["quantity"] for p in positions)
    total_pnl = sum(p["pnl"] for p in positions)
    
    return {
        "positions": positions,
        "summary": {
            "total_positions": len(positions),
            "total_value": round(total_value, 2),
            "total_pnl": round(total_pnl, 2),
            "calls": sum(1 for p in positions if p["option_type"] == "call"),
            "puts": sum(1 for p in positions if p["option_type"] == "put")
        }
    }


@router.post("/close/{position_id}")
async def close_option_position(
    position_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Close an option position"""
    position = await db.option_positions.find_one({
        "position_id": position_id,
        "user_id": user_id,
        "status": "open"
    })
    
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    # Calculate final P&L
    current_prices = {"BTC": 45000, "ETH": 2500, "SOL": 100}
    current_price = current_prices.get(position["symbol"], 1000)
    
    expiry = datetime.fromisoformat(position["expiry_date"].replace('Z', '+00:00'))
    days_to_expiry = max((expiry - datetime.now(timezone.utc)).days, 0)
    T = max(days_to_expiry, 0.01) / 365
    
    greeks = calculate_greeks(
        S=current_price,
        K=position["strike_price"],
        T=T,
        r=0.05,
        sigma=0.65,
        option_type=position["option_type"]
    )
    
    final_pnl = (greeks["price"] - position["entry_price"]) * position["quantity"]
    
    # Update position
    await db.option_positions.update_one(
        {"position_id": position_id},
        {
            "$set": {
                "status": "closed",
                "exit_price": greeks["price"],
                "final_pnl": round(final_pnl, 2),
                "closed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "status": "closed",
        "position_id": position_id,
        "exit_price": greeks["price"],
        "final_pnl": round(final_pnl, 2)
    }


@router.get("/strategies")
async def get_option_strategies():
    """Get available option strategies with explanations"""
    return {
        "strategies": [
            {
                "name": "Long Call",
                "description": "Bullish strategy - profit from price increase",
                "max_profit": "Unlimited",
                "max_loss": "Premium paid",
                "breakeven": "Strike + Premium",
                "best_for": "Strong bullish outlook",
                "legs": [{"type": "call", "action": "buy", "quantity": 1}]
            },
            {
                "name": "Long Put",
                "description": "Bearish strategy - profit from price decrease",
                "max_profit": "Strike - Premium (substantial)",
                "max_loss": "Premium paid",
                "breakeven": "Strike - Premium",
                "best_for": "Strong bearish outlook",
                "legs": [{"type": "put", "action": "buy", "quantity": 1}]
            },
            {
                "name": "Bull Call Spread",
                "description": "Moderately bullish - limited risk and reward",
                "max_profit": "Difference in strikes - Net premium",
                "max_loss": "Net premium paid",
                "breakeven": "Lower strike + Net premium",
                "best_for": "Moderate bullish outlook",
                "legs": [
                    {"type": "call", "action": "buy", "strike": "lower", "quantity": 1},
                    {"type": "call", "action": "sell", "strike": "higher", "quantity": 1}
                ]
            },
            {
                "name": "Bear Put Spread",
                "description": "Moderately bearish - limited risk and reward",
                "max_profit": "Difference in strikes - Net premium",
                "max_loss": "Net premium paid",
                "breakeven": "Higher strike - Net premium",
                "best_for": "Moderate bearish outlook",
                "legs": [
                    {"type": "put", "action": "buy", "strike": "higher", "quantity": 1},
                    {"type": "put", "action": "sell", "strike": "lower", "quantity": 1}
                ]
            },
            {
                "name": "Straddle",
                "description": "Profit from large price movement in either direction",
                "max_profit": "Unlimited",
                "max_loss": "Total premiums paid",
                "breakeven": "Strike ± Total premium",
                "best_for": "High volatility expected",
                "legs": [
                    {"type": "call", "action": "buy", "strike": "ATM", "quantity": 1},
                    {"type": "put", "action": "buy", "strike": "ATM", "quantity": 1}
                ]
            },
            {
                "name": "Iron Condor",
                "description": "Profit from low volatility - range-bound market",
                "max_profit": "Net premium received",
                "max_loss": "Width of spread - Net premium",
                "breakeven": "Between short strikes",
                "best_for": "Low volatility, range-bound",
                "legs": [
                    {"type": "put", "action": "sell", "strike": "lower-mid", "quantity": 1},
                    {"type": "put", "action": "buy", "strike": "lower", "quantity": 1},
                    {"type": "call", "action": "sell", "strike": "upper-mid", "quantity": 1},
                    {"type": "call", "action": "buy", "strike": "upper", "quantity": 1}
                ]
            }
        ]
    }


@router.get("/pnl-history")
async def get_options_pnl_history(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get historical P&L for options trading"""
    closed = await db.option_positions.find(
        {"user_id": user_id, "status": "closed"},
        {"_id": 0}
    ).sort("closed_at", -1).limit(100).to_list(100)
    
    total_pnl = sum(p.get("final_pnl", 0) for p in closed)
    wins = sum(1 for p in closed if p.get("final_pnl", 0) > 0)
    
    return {
        "history": closed,
        "stats": {
            "total_trades": len(closed),
            "total_pnl": round(total_pnl, 2),
            "win_rate": round(wins / len(closed) * 100, 1) if closed else 0,
            "avg_pnl": round(total_pnl / len(closed), 2) if closed else 0
        }
    }

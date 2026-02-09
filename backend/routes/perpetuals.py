"""
Perpetual Futures Trading API Routes
=====================================
Leverage trading with funding rates and liquidation tracking.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import math

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/perpetuals", tags=["Perpetual Futures"])

_db = None
_automated_trader = None
_prediction_services = None


def set_dependencies(database, automated_trader=None, prediction_services=None):
    """Set dependencies from main app"""
    global _db, _automated_trader, _prediction_services
    _db = database
    _automated_trader = automated_trader
    _prediction_services = prediction_services


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


# =============================================================================
# AI PREDICTION & SIGNAL ANALYSIS FOR FUTURES
# =============================================================================

class FuturesPredictionRequest(BaseModel):
    symbol: str  # BTC-PERP, ETH-PERP, etc.
    desired_leverage: Optional[float] = None  # If provided, calculates risk for specific leverage
    
    
@router.post("/ai-predictions")
async def get_futures_predictions(
    request: FuturesPredictionRequest,
    db = Depends(get_database)
):
    """
    Get AI predictions specifically tailored for futures/leveraged trading.
    
    Includes:
    - Standard AI signals (buy/sell/hold)
    - Optimal leverage recommendations
    - Liquidation risk assessment
    - Funding rate impact analysis
    - Volatility-adjusted position sizing
    - Entry/exit zone recommendations
    """
    # Extract base symbol from perpetual symbol (BTC-PERP -> BTC)
    base_symbol = request.symbol.replace('-PERP', '').replace('-PERPETUAL', '')
    
    if not _automated_trader:
        raise HTTPException(
            status_code=503,
            detail="Prediction services not available. AI trader not initialized."
        )
    
    try:
        # Get base prediction signals from automated trader
        signals = await _automated_trader.get_prediction_signals(base_symbol)
        
        # Get market data
        markets = (await get_perp_markets())["markets"]
        market = next((m for m in markets if m["symbol"] == request.symbol), None)
        
        if not market:
            raise HTTPException(status_code=404, detail=f"Market {request.symbol} not found")
        
        current_price = market["mark_price"]
        funding_rate = market.get("funding_rate", 0)
        
        # Calculate composite score
        composite = signals.get('composite', {})
        score = composite.get('score', 50)
        confidence = composite.get('confidence', 0)
        signal = composite.get('signal', 'hold')
        
        # Normalize score to -1 to +1 range for calculations
        normalized_score = (score - 50) / 50
        
        # === LEVERAGE RECOMMENDATION ===
        # Base leverage on signal strength and confidence
        # Strong signal + high confidence = higher leverage
        # Weak signal or low confidence = lower leverage
        
        signal_strength = abs(normalized_score)
        confidence_factor = confidence / 100
        
        # Base leverage calculation
        if signal_strength > 0.4 and confidence > 70:
            recommended_leverage = min(5.0, 2.0 + signal_strength * 6)  # 2-8x
        elif signal_strength > 0.2 and confidence > 60:
            recommended_leverage = min(3.0, 1.5 + signal_strength * 3)  # 1.5-4.5x
        else:
            recommended_leverage = 1.5  # Conservative for weak signals
        
        recommended_leverage = round(recommended_leverage, 1)
        
        # === VOLATILITY-ADJUSTED SIZING ===
        # Reduce size in high volatility environments
        volatility_factor = 1.0  # Default
        
        if 'advanced_ta' in signals.get('components', {}):
            volatility_regime = signals['components']['advanced_ta'].get('volatility_regime', 'normal')
            if volatility_regime == 'high':
                volatility_factor = 0.6  # Reduce size by 40%
            elif volatility_regime == 'extreme':
                volatility_factor = 0.4  # Reduce size by 60%
            elif volatility_regime == 'low':
                volatility_factor = 1.2  # Can size up 20%
        
        # === LIQUIDATION RISK ASSESSMENT ===
        leverage_to_analyze = request.desired_leverage if request.desired_leverage else recommended_leverage
        
        # Calculate liquidation price
        maintenance_margin = market.get("maintenance_margin", 0.5) / 100
        
        if normalized_score > 0:  # Bullish - would go long
            liquidation_price = current_price * (1 - (1 / leverage_to_analyze) + maintenance_margin)
            liquidation_distance_pct = ((current_price - liquidation_price) / current_price) * 100
        else:  # Bearish - would go short
            liquidation_price = current_price * (1 + (1 / leverage_to_analyze) - maintenance_margin)
            liquidation_distance_pct = ((liquidation_price - current_price) / current_price) * 100
        
        # Assess risk level
        if liquidation_distance_pct > 20:
            liquidation_risk = "low"
            risk_color = "success"
        elif liquidation_distance_pct > 10:
            liquidation_risk = "medium"
            risk_color = "warning"
        else:
            liquidation_risk = "high"
            risk_color = "danger"
        
        # === FUNDING RATE IMPACT ===
        # Positive funding = longs pay shorts (expensive to hold longs)
        # Negative funding = shorts pay longs (expensive to hold shorts)
        
        annual_funding_rate = funding_rate * 365 * 3  # Funding every 8 hours, so 3x per day
        funding_impact = "neutral"
        
        if normalized_score > 0:  # Want to go long
            if funding_rate > 0.001:  # Positive funding > 0.1%
                funding_impact = "negative"  # Expensive to hold long
            elif funding_rate < -0.0005:
                funding_impact = "positive"  # Getting paid to hold long
        else:  # Want to go short
            if funding_rate < -0.001:  # Negative funding
                funding_impact = "negative"  # Expensive to hold short
            elif funding_rate > 0.0005:
                funding_impact = "positive"  # Getting paid to hold short
        
        # === ENTRY/EXIT ZONES ===
        # Calculate support/resistance zones based on signal strength
        
        if normalized_score > 0:  # Bullish
            # Entry zones (support levels to buy at)
            optimal_entry = round(current_price * 0.99, 2)  # 1% below current
            aggressive_entry = round(current_price * 1.01, 2)  # 1% above (chase)
            conservative_entry = round(current_price * 0.97, 2)  # 3% below (wait for dip)
            
            # Exit zones (resistance levels to take profit)
            target_1 = round(current_price * (1 + 0.05 * signal_strength), 2)
            target_2 = round(current_price * (1 + 0.10 * signal_strength), 2)
            target_3 = round(current_price * (1 + 0.15 * signal_strength), 2)
            
            stop_loss = round(current_price * (1 - 0.05 / leverage_to_analyze), 2)
            
        else:  # Bearish
            # Entry zones (resistance levels to short at)
            optimal_entry = round(current_price * 1.01, 2)  # 1% above current
            aggressive_entry = round(current_price * 0.99, 2)  # 1% below (chase)
            conservative_entry = round(current_price * 1.03, 2)  # 3% above (wait for pump)
            
            # Exit zones (support levels to take profit)
            target_1 = round(current_price * (1 - 0.05 * abs(normalized_score)), 2)
            target_2 = round(current_price * (1 - 0.10 * abs(normalized_score)), 2)
            target_3 = round(current_price * (1 - 0.15 * abs(normalized_score)), 2)
            
            stop_loss = round(current_price * (1 + 0.05 / leverage_to_analyze), 2)
        
        # === POSITION SIZING RECOMMENDATION ===
        # Suggest position size based on account size and risk tolerance
        
        base_risk_per_trade = 2.0  # 2% of account as base risk
        
        # Adjust risk based on confidence
        if confidence > 80:
            risk_per_trade = base_risk_per_trade * 1.5  # 3% risk
        elif confidence > 70:
            risk_per_trade = base_risk_per_trade * 1.2  # 2.4% risk
        elif confidence < 50:
            risk_per_trade = base_risk_per_trade * 0.5  # 1% risk
        else:
            risk_per_trade = base_risk_per_trade
        
        risk_per_trade *= volatility_factor  # Adjust for volatility
        
        # === SIGNAL QUALITY ASSESSMENT ===
        models_agreeing = sum(
            1 for comp in signals.get('components', {}).values()
            if isinstance(comp, dict) and 
            ((comp.get('score', 50) > 60 and normalized_score > 0) or
             (comp.get('score', 50) < 40 and normalized_score < 0))
        )
        
        total_models = len(signals.get('components', {}))
        signal_consensus = (models_agreeing / total_models * 100) if total_models > 0 else 0
        
        if signal_consensus > 75:
            signal_quality = "excellent"
        elif signal_consensus > 60:
            signal_quality = "good"
        elif signal_consensus > 40:
            signal_quality = "fair"
        else:
            signal_quality = "poor"
        
        # === RISK/REWARD CALCULATION ===
        if abs(stop_loss - current_price) > 0:
            risk = abs(stop_loss - current_price)
            reward = abs(target_2 - current_price)  # Use target_2 as main target
            risk_reward_ratio = round(reward / risk, 2) if risk > 0 else 0
        else:
            risk_reward_ratio = 0
        
        # === TRADING RECOMMENDATION ===
        # Generate actionable recommendation
        
        if signal == 'strong_buy' or signal == 'strong_sell':
            action = "OPEN_POSITION"
            action_detail = f"Strong signal to {'LONG' if signal == 'strong_buy' else 'SHORT'}"
        elif signal == 'buy' or signal == 'sell':
            action = "CONSIDER_POSITION"
            action_detail = f"Moderate signal to {'LONG' if signal == 'buy' else 'SHORT'}"
        else:
            action = "WAIT"
            action_detail = "Wait for clearer signal"
        
        # Adjust recommendation based on additional factors
        if liquidation_risk == "high":
            action = "REDUCE_SIZE" if action == "OPEN_POSITION" else "WAIT"
            action_detail += " (High liquidation risk - reduce leverage or wait)"
        
        if funding_impact == "negative":
            action_detail += f" (Warning: Unfavorable funding rate {funding_rate*100:.3f}%)"
        
        if signal_quality == "poor":
            action = "WAIT"
            action_detail = "Wait - poor signal consensus across models"
        
        # Compile final response
        return {
            "symbol": request.symbol,
            "base_symbol": base_symbol,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            
            # Core Signal
            "signal": {
                "direction": signal,
                "score": score,
                "confidence": confidence,
                "quality": signal_quality,
                "consensus": round(signal_consensus, 1),
                "models_used": total_models,
                "models_agreeing": models_agreeing
            },
            
            # Trading Action
            "recommendation": {
                "action": action,
                "detail": action_detail,
                "side": "long" if normalized_score > 0 else "short"
            },
            
            # Leverage Analysis
            "leverage": {
                "recommended": recommended_leverage,
                "analyzed": leverage_to_analyze,
                "max_safe": market["max_leverage"],
                "rationale": f"Based on {int(confidence)}% confidence and {signal_strength:.2f} signal strength"
            },
            
            # Risk Analysis
            "risk": {
                "liquidation_price": round(liquidation_price, 2),
                "liquidation_distance_pct": round(liquidation_distance_pct, 2),
                "liquidation_risk_level": liquidation_risk,
                "risk_color": risk_color,
                "stop_loss": stop_loss,
                "risk_reward_ratio": risk_reward_ratio,
                "recommended_risk_per_trade_pct": round(risk_per_trade, 2)
            },
            
            # Funding Analysis
            "funding": {
                "current_rate": funding_rate,
                "rate_percent": round(funding_rate * 100, 4),
                "annual_rate_percent": round(annual_funding_rate * 100, 2),
                "impact": funding_impact,
                "next_funding_time": market.get("next_funding", "Unknown")
            },
            
            # Entry/Exit Strategy
            "zones": {
                "current_price": current_price,
                "entry": {
                    "optimal": optimal_entry,
                    "aggressive": aggressive_entry,
                    "conservative": conservative_entry
                },
                "targets": {
                    "target_1": target_1,
                    "target_2": target_2,
                    "target_3": target_3
                },
                "stop_loss": stop_loss
            },
            
            # Position Sizing
            "position_sizing": {
                "volatility_factor": round(volatility_factor, 2),
                "volatility_regime": signals.get('components', {}).get('advanced_ta', {}).get('volatility_regime', 'normal'),
                "risk_per_trade_pct": round(risk_per_trade, 2),
                "size_multiplier": round(volatility_factor, 2)
            },
            
            # Component Signals (for transparency)
            "component_signals": signals.get('components', {}),
            
            # Market Context
            "market": {
                "symbol": request.symbol,
                "mark_price": current_price,
                "index_price": market.get("index_price", current_price),
                "24h_change": market.get("24h_change", 0),
                "open_interest": market.get("open_interest", 0),
                "volume_24h": market.get("24h_volume", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting futures predictions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get predictions: {str(e)}"
        )


@router.get("/ai-signals")
async def get_all_futures_signals(
    min_confidence: float = 60.0,
    db = Depends(get_database)
):
    """
    Get AI signals for all available perpetual futures markets.
    Returns ranked list of trading opportunities.
    """
    if not _automated_trader:
        raise HTTPException(
            status_code=503,
            detail="Prediction services not available"
        )
    
    try:
        markets = (await get_perp_markets())["markets"]
        signals_list = []
        
        for market in markets:
            try:
                # Get predictions for each market
                request = FuturesPredictionRequest(symbol=market["symbol"])
                prediction = await get_futures_predictions(request, db)
                
                # Filter by confidence
                if prediction["signal"]["confidence"] >= min_confidence:
                    signals_list.append({
                        "symbol": market["symbol"],
                        "base_symbol": prediction["base_symbol"],
                        "signal": prediction["signal"]["direction"],
                        "score": prediction["signal"]["score"],
                        "confidence": prediction["signal"]["confidence"],
                        "quality": prediction["signal"]["quality"],
                        "action": prediction["recommendation"]["action"],
                        "side": prediction["recommendation"]["side"],
                        "recommended_leverage": prediction["leverage"]["recommended"],
                        "liquidation_risk": prediction["risk"]["liquidation_risk_level"],
                        "risk_reward_ratio": prediction["risk"]["risk_reward_ratio"],
                        "funding_impact": prediction["funding"]["impact"],
                        "current_price": prediction["market"]["mark_price"],
                        "optimal_entry": prediction["zones"]["entry"]["optimal"],
                        "target": prediction["zones"]["targets"]["target_2"],
                        "stop_loss": prediction["zones"]["stop_loss"]
                    })
            except Exception as e:
                logger.warning(f"Failed to get signal for {market['symbol']}: {e}")
                continue
        
        # Sort by confidence-weighted score
        signals_list.sort(
            key=lambda x: abs(x["score"] - 50) * x["confidence"] / 100,
            reverse=True
        )
        
        # Add rank
        for idx, signal in enumerate(signals_list):
            signal["rank"] = idx + 1
        
        # Calculate summary stats
        summary = {
            "total_signals": len(signals_list),
            "long_signals": sum(1 for s in signals_list if s["side"] == "long"),
            "short_signals": sum(1 for s in signals_list if s["side"] == "short"),
            "high_quality": sum(1 for s in signals_list if s["quality"] in ["excellent", "good"]),
            "avg_confidence": round(sum(s["confidence"] for s in signals_list) / len(signals_list), 1) if signals_list else 0,
            "strong_signals": sum(1 for s in signals_list if s["action"] == "OPEN_POSITION"),
            "low_risk_opportunities": sum(1 for s in signals_list if s["liquidation_risk"] == "low")
        }
        
        return {
            "signals": signals_list,
            "summary": summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "filters": {
                "min_confidence": min_confidence
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting all futures signals: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get signals: {str(e)}"
        )

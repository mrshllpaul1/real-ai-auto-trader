"""
Portfolio Risk Analyzer API Routes
===================================
Unified risk analysis combining perpetuals, yield farming, and options.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import math

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risk-analyzer", tags=["Portfolio Risk Analyzer"])

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
# UNIFIED RISK ANALYSIS
# =============================================================================

@router.get("/overview")
async def get_risk_overview(user_id: str = "default_user", db = Depends(get_database)):
    """Get comprehensive portfolio risk overview"""
    
    # Fetch all position data
    perp_positions = await db.perp_positions.find(
        {"user_id": user_id, "status": "open"}, {"_id": 0}
    ).to_list(100)
    
    yield_positions = await db.yield_positions.find(
        {"user_id": user_id, "status": "active"}, {"_id": 0}
    ).to_list(100)
    
    options_positions = await db.options_positions.find(
        {"user_id": user_id, "status": "open"}, {"_id": 0}
    ).to_list(100)
    
    # Calculate perpetuals risk
    perp_risk = calculate_perpetuals_risk(perp_positions)
    
    # Calculate yield farming risk
    yield_risk = calculate_yield_risk(yield_positions)
    
    # Calculate options risk (Greeks)
    options_risk = calculate_options_risk(options_positions)
    
    # Calculate overall risk score
    total_exposure = perp_risk["total_exposure"] + yield_risk["total_exposure"] + options_risk["total_exposure"]
    
    # Risk score calculation (0-100, higher = more risky)
    risk_components = []
    
    # Leverage risk (perpetuals)
    if perp_risk["avg_leverage"] > 0:
        leverage_risk = min(perp_risk["avg_leverage"] * 2, 100)  # 50x leverage = 100 risk
        risk_components.append(("Leverage", leverage_risk, perp_risk["total_exposure"]))
    
    # Liquidation proximity risk
    if perp_risk["nearest_liquidation_pct"] < 20:
        liq_risk = 100 - perp_risk["nearest_liquidation_pct"] * 5
        risk_components.append(("Liquidation", liq_risk, perp_risk["total_exposure"]))
    
    # Impermanent loss risk (yield)
    if yield_risk["il_exposure"] > 0:
        il_risk = yield_risk["avg_il_risk"]
        risk_components.append(("Impermanent Loss", il_risk, yield_risk["il_exposure"]))
    
    # Protocol risk (yield)
    if yield_risk["high_risk_exposure"] > 0:
        protocol_risk = 70
        risk_components.append(("Protocol Risk", protocol_risk, yield_risk["high_risk_exposure"]))
    
    # Options delta risk
    if abs(options_risk["net_delta"]) > 1:
        delta_risk = min(abs(options_risk["net_delta"]) * 20, 100)
        risk_components.append(("Delta Exposure", delta_risk, options_risk["total_exposure"]))
    
    # Options theta decay
    if options_risk["total_theta"] < -100:
        theta_risk = min(abs(options_risk["total_theta"]) / 10, 100)
        risk_components.append(("Time Decay", theta_risk, options_risk["total_exposure"]))
    
    # Weighted average risk score
    if total_exposure > 0:
        weighted_risk = sum(r[1] * r[2] for r in risk_components) / total_exposure if risk_components else 30
        overall_risk_score = min(max(weighted_risk, 0), 100)
    else:
        overall_risk_score = 0
    
    # Determine risk level
    if overall_risk_score >= 70:
        risk_level = "critical"
    elif overall_risk_score >= 50:
        risk_level = "high"
    elif overall_risk_score >= 30:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return {
        "overall_risk_score": round(overall_risk_score, 1),
        "risk_level": risk_level,
        "total_portfolio_value": round(total_exposure, 2),
        "risk_breakdown": {
            "perpetuals": perp_risk,
            "yield_farming": yield_risk,
            "options": options_risk
        },
        "risk_factors": [
            {"name": r[0], "score": round(r[1], 1), "exposure": round(r[2], 2)}
            for r in risk_components
        ],
        "recommendations": generate_recommendations(perp_risk, yield_risk, options_risk, overall_risk_score),
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


def calculate_perpetuals_risk(positions: List[Dict]) -> Dict:
    """Calculate risk metrics for perpetual positions"""
    
    if not positions:
        return {
            "total_exposure": 0,
            "total_margin": 0,
            "total_unrealized_pnl": 0,
            "avg_leverage": 0,
            "max_leverage": 0,
            "long_exposure": 0,
            "short_exposure": 0,
            "net_exposure": 0,
            "nearest_liquidation_pct": 100,
            "positions_at_risk": 0,
            "position_count": 0
        }
    
    total_exposure = sum(p.get("size_usd", 0) for p in positions)
    total_margin = sum(p.get("margin", 0) for p in positions)
    total_pnl = sum(p.get("unrealized_pnl", 0) for p in positions)
    
    leverages = [p.get("leverage", 1) for p in positions]
    avg_leverage = sum(leverages) / len(leverages) if leverages else 0
    max_leverage = max(leverages) if leverages else 0
    
    long_exposure = sum(p.get("size_usd", 0) for p in positions if p.get("side") == "long")
    short_exposure = sum(p.get("size_usd", 0) for p in positions if p.get("side") == "short")
    
    # Calculate liquidation proximity
    liq_distances = []
    positions_at_risk = 0
    
    for p in positions:
        entry = p.get("entry_price", 1)
        liq = p.get("liquidation_price", 0)
        mark = p.get("mark_price", entry)
        
        if p.get("side") == "long" and liq > 0:
            distance_pct = ((mark - liq) / mark) * 100
        elif p.get("side") == "short" and liq > 0:
            distance_pct = ((liq - mark) / mark) * 100
        else:
            distance_pct = 100
        
        liq_distances.append(distance_pct)
        if distance_pct < 10:
            positions_at_risk += 1
    
    nearest_liq = min(liq_distances) if liq_distances else 100
    
    return {
        "total_exposure": round(total_exposure, 2),
        "total_margin": round(total_margin, 2),
        "total_unrealized_pnl": round(total_pnl, 2),
        "avg_leverage": round(avg_leverage, 1),
        "max_leverage": max_leverage,
        "long_exposure": round(long_exposure, 2),
        "short_exposure": round(short_exposure, 2),
        "net_exposure": round(long_exposure - short_exposure, 2),
        "nearest_liquidation_pct": round(nearest_liq, 1),
        "positions_at_risk": positions_at_risk,
        "position_count": len(positions)
    }


def calculate_yield_risk(positions: List[Dict]) -> Dict:
    """Calculate risk metrics for yield farming positions"""
    
    if not positions:
        return {
            "total_exposure": 0,
            "total_earned": 0,
            "avg_apy": 0,
            "il_exposure": 0,
            "avg_il_risk": 0,
            "low_risk_exposure": 0,
            "medium_risk_exposure": 0,
            "high_risk_exposure": 0,
            "protocol_diversity": 0,
            "position_count": 0
        }
    
    total_value = sum(p.get("current_value_usd", 0) for p in positions)
    total_earned = sum(p.get("earned_usd", 0) for p in positions)
    
    apys = [p.get("current_apy", 0) for p in positions if p.get("current_apy")]
    avg_apy = sum(apys) / len(apys) if apys else 0
    
    # IL exposure (positions with IL risk)
    il_positions = [p for p in positions if p.get("has_il_risk", False)]
    il_exposure = sum(p.get("current_value_usd", 0) for p in il_positions)
    
    # Risk level breakdown
    low_risk = sum(p.get("current_value_usd", 0) for p in positions if p.get("risk_level") == "low")
    medium_risk = sum(p.get("current_value_usd", 0) for p in positions if p.get("risk_level") == "medium")
    high_risk = sum(p.get("current_value_usd", 0) for p in positions if p.get("risk_level") == "high")
    
    protocols = set(p.get("protocol") for p in positions if p.get("protocol"))
    
    # Average IL risk score (simplified)
    il_risks = [p.get("il_risk_score", 50) for p in il_positions]
    avg_il = sum(il_risks) / len(il_risks) if il_risks else 0
    
    return {
        "total_exposure": round(total_value, 2),
        "total_earned": round(total_earned, 2),
        "avg_apy": round(avg_apy, 1),
        "il_exposure": round(il_exposure, 2),
        "avg_il_risk": round(avg_il, 1),
        "low_risk_exposure": round(low_risk, 2),
        "medium_risk_exposure": round(medium_risk, 2),
        "high_risk_exposure": round(high_risk, 2),
        "protocol_diversity": len(protocols),
        "position_count": len(positions)
    }


def calculate_options_risk(positions: List[Dict]) -> Dict:
    """Calculate risk metrics for options positions (Greeks)"""
    
    if not positions:
        return {
            "total_exposure": 0,
            "total_premium_paid": 0,
            "total_premium_received": 0,
            "net_delta": 0,
            "net_gamma": 0,
            "total_theta": 0,
            "total_vega": 0,
            "max_loss": 0,
            "max_profit": 0,
            "calls_count": 0,
            "puts_count": 0,
            "position_count": 0
        }
    
    total_value = sum(abs(p.get("current_value", 0)) for p in positions)
    premium_paid = sum(p.get("premium_paid", 0) for p in positions if p.get("side") == "buy")
    premium_received = sum(p.get("premium_received", 0) for p in positions if p.get("side") == "sell")
    
    # Aggregate Greeks
    net_delta = sum(p.get("delta", 0) * p.get("quantity", 1) for p in positions)
    net_gamma = sum(p.get("gamma", 0) * p.get("quantity", 1) for p in positions)
    total_theta = sum(p.get("theta", 0) * p.get("quantity", 1) for p in positions)
    total_vega = sum(p.get("vega", 0) * p.get("quantity", 1) for p in positions)
    
    # Max loss/profit estimation
    max_loss = sum(p.get("max_loss", p.get("premium_paid", 0)) for p in positions)
    max_profit = sum(p.get("max_profit", 0) for p in positions)
    
    calls = len([p for p in positions if p.get("option_type") == "call"])
    puts = len([p for p in positions if p.get("option_type") == "put"])
    
    return {
        "total_exposure": round(total_value, 2),
        "total_premium_paid": round(premium_paid, 2),
        "total_premium_received": round(premium_received, 2),
        "net_delta": round(net_delta, 4),
        "net_gamma": round(net_gamma, 6),
        "total_theta": round(total_theta, 2),
        "total_vega": round(total_vega, 2),
        "max_loss": round(max_loss, 2),
        "max_profit": round(max_profit, 2),
        "calls_count": calls,
        "puts_count": puts,
        "position_count": len(positions)
    }


def generate_recommendations(perp_risk: Dict, yield_risk: Dict, options_risk: Dict, risk_score: float) -> List[Dict]:
    """Generate risk reduction recommendations"""
    
    recommendations = []
    
    # Perpetuals recommendations
    if perp_risk["avg_leverage"] > 20:
        recommendations.append({
            "type": "warning",
            "category": "perpetuals",
            "message": f"High average leverage ({perp_risk['avg_leverage']}x). Consider reducing to below 10x.",
            "priority": "high"
        })
    
    if perp_risk["positions_at_risk"] > 0:
        recommendations.append({
            "type": "critical",
            "category": "perpetuals",
            "message": f"{perp_risk['positions_at_risk']} position(s) near liquidation. Add margin or reduce position size.",
            "priority": "critical"
        })
    
    if abs(perp_risk["net_exposure"]) > perp_risk["total_exposure"] * 0.7:
        direction = "long" if perp_risk["net_exposure"] > 0 else "short"
        recommendations.append({
            "type": "info",
            "category": "perpetuals",
            "message": f"Portfolio is heavily {direction}-biased. Consider hedging with opposite positions.",
            "priority": "medium"
        })
    
    # Yield farming recommendations
    if yield_risk["high_risk_exposure"] > yield_risk["total_exposure"] * 0.5:
        recommendations.append({
            "type": "warning",
            "category": "yield",
            "message": "Over 50% in high-risk yield farms. Diversify to lower-risk protocols.",
            "priority": "high"
        })
    
    if yield_risk["protocol_diversity"] < 3 and yield_risk["total_exposure"] > 5000:
        recommendations.append({
            "type": "info",
            "category": "yield",
            "message": "Low protocol diversity. Spread across more protocols to reduce smart contract risk.",
            "priority": "medium"
        })
    
    if yield_risk["il_exposure"] > yield_risk["total_exposure"] * 0.6:
        recommendations.append({
            "type": "info",
            "category": "yield",
            "message": "High impermanent loss exposure. Consider single-sided staking options.",
            "priority": "medium"
        })
    
    # Options recommendations
    if abs(options_risk["net_delta"]) > 5:
        recommendations.append({
            "type": "warning",
            "category": "options",
            "message": f"High delta exposure ({options_risk['net_delta']:.2f}). Portfolio is not delta-neutral.",
            "priority": "medium"
        })
    
    if options_risk["total_theta"] < -200:
        recommendations.append({
            "type": "info",
            "category": "options",
            "message": f"Significant theta decay (${abs(options_risk['total_theta'])}/day). Consider time spreads.",
            "priority": "low"
        })
    
    # General recommendations
    if risk_score >= 70:
        recommendations.append({
            "type": "critical",
            "category": "general",
            "message": "Portfolio risk is critically high. Immediate action recommended.",
            "priority": "critical"
        })
    elif risk_score >= 50:
        recommendations.append({
            "type": "warning",
            "category": "general",
            "message": "Portfolio risk is elevated. Review and rebalance positions.",
            "priority": "high"
        })
    
    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    recommendations.sort(key=lambda x: priority_order.get(x["priority"], 4))
    
    return recommendations


# =============================================================================
# EXPOSURE BREAKDOWN
# =============================================================================

@router.get("/exposure")
async def get_exposure_breakdown(user_id: str = "default_user", db = Depends(get_database)):
    """Get detailed exposure breakdown by asset and position type"""
    
    perp_positions = await db.perp_positions.find(
        {"user_id": user_id, "status": "open"}, {"_id": 0}
    ).to_list(100)
    
    yield_positions = await db.yield_positions.find(
        {"user_id": user_id, "status": "active"}, {"_id": 0}
    ).to_list(100)
    
    options_positions = await db.options_positions.find(
        {"user_id": user_id, "status": "open"}, {"_id": 0}
    ).to_list(100)
    
    # Aggregate by asset
    asset_exposure = {}
    
    for p in perp_positions:
        symbol = p.get("symbol", "Unknown").split("-")[0]  # BTC-PERP -> BTC
        if symbol not in asset_exposure:
            asset_exposure[symbol] = {"perpetuals": 0, "yield": 0, "options": 0, "total": 0}
        asset_exposure[symbol]["perpetuals"] += p.get("size_usd", 0)
        asset_exposure[symbol]["total"] += p.get("size_usd", 0)
    
    for p in yield_positions:
        tokens = p.get("tokens", [p.get("token", "Unknown")])
        value_per_token = p.get("current_value_usd", 0) / len(tokens) if tokens else 0
        for token in tokens:
            if token not in asset_exposure:
                asset_exposure[token] = {"perpetuals": 0, "yield": 0, "options": 0, "total": 0}
            asset_exposure[token]["yield"] += value_per_token
            asset_exposure[token]["total"] += value_per_token
    
    for p in options_positions:
        symbol = p.get("underlying", "Unknown")
        if symbol not in asset_exposure:
            asset_exposure[symbol] = {"perpetuals": 0, "yield": 0, "options": 0, "total": 0}
        asset_exposure[symbol]["options"] += abs(p.get("current_value", 0))
        asset_exposure[symbol]["total"] += abs(p.get("current_value", 0))
    
    # Sort by total exposure
    sorted_assets = sorted(
        [{"asset": k, **v} for k, v in asset_exposure.items()],
        key=lambda x: x["total"],
        reverse=True
    )
    
    # Calculate totals
    total_perp = sum(a["perpetuals"] for a in sorted_assets)
    total_yield = sum(a["yield"] for a in sorted_assets)
    total_options = sum(a["options"] for a in sorted_assets)
    grand_total = total_perp + total_yield + total_options
    
    return {
        "by_asset": sorted_assets,
        "by_type": {
            "perpetuals": round(total_perp, 2),
            "yield_farming": round(total_yield, 2),
            "options": round(total_options, 2)
        },
        "total_exposure": round(grand_total, 2),
        "concentration": {
            "top_asset": sorted_assets[0]["asset"] if sorted_assets else None,
            "top_asset_pct": round(sorted_assets[0]["total"] / grand_total * 100, 1) if sorted_assets and grand_total > 0 else 0
        }
    }


# =============================================================================
# VALUE AT RISK (VaR)
# =============================================================================

@router.get("/var")
async def calculate_var(
    confidence: float = 95,
    time_horizon: int = 1,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Calculate Value at Risk (VaR) for the portfolio"""
    
    # Fetch positions
    perp_positions = await db.perp_positions.find(
        {"user_id": user_id, "status": "open"}, {"_id": 0}
    ).to_list(100)
    
    yield_positions = await db.yield_positions.find(
        {"user_id": user_id, "status": "active"}, {"_id": 0}
    ).to_list(100)
    
    options_positions = await db.options_positions.find(
        {"user_id": user_id, "status": "open"}, {"_id": 0}
    ).to_list(100)
    
    # Calculate total portfolio value
    perp_value = sum(p.get("margin", 0) + p.get("unrealized_pnl", 0) for p in perp_positions)
    yield_value = sum(p.get("current_value_usd", 0) for p in yield_positions)
    options_value = sum(abs(p.get("current_value", 0)) for p in options_positions)
    total_value = perp_value + yield_value + options_value
    
    if total_value == 0:
        return {
            "var_95": 0,
            "var_99": 0,
            "expected_shortfall": 0,
            "portfolio_value": 0,
            "methodology": "Parametric VaR using historical volatility assumptions"
        }
    
    # Simplified VaR calculation using assumed volatility
    # Crypto typically has high volatility (~50-80% annualized)
    avg_daily_vol = 0.04  # 4% daily volatility assumption
    
    # Adjust for leverage
    avg_leverage = 1
    if perp_positions:
        leverages = [p.get("leverage", 1) for p in perp_positions]
        perp_leverage = sum(leverages) / len(leverages)
        avg_leverage = (perp_value * perp_leverage + yield_value + options_value) / total_value if total_value > 0 else 1
    
    effective_vol = avg_daily_vol * avg_leverage * math.sqrt(time_horizon)
    
    # Z-scores for confidence levels
    z_scores = {95: 1.645, 99: 2.326}
    z_score = z_scores.get(int(confidence), 1.645)
    
    var_amount = total_value * effective_vol * z_score
    var_99 = total_value * effective_vol * 2.326
    
    # Expected Shortfall (average loss beyond VaR)
    es_multiplier = 1.25  # Simplified ES approximation
    expected_shortfall = var_amount * es_multiplier
    
    return {
        "var_95": round(var_amount, 2) if confidence == 95 else round(total_value * effective_vol * 1.645, 2),
        "var_99": round(var_99, 2),
        "expected_shortfall": round(expected_shortfall, 2),
        "portfolio_value": round(total_value, 2),
        "effective_leverage": round(avg_leverage, 2),
        "daily_volatility": f"{avg_daily_vol * 100}%",
        "time_horizon_days": time_horizon,
        "confidence_level": f"{confidence}%",
        "methodology": "Parametric VaR using historical volatility assumptions"
    }


# =============================================================================
# STRESS TEST
# =============================================================================

@router.post("/stress-test")
async def run_stress_test(
    scenario: str = "market_crash",
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Run stress test scenarios on the portfolio"""
    
    scenarios = {
        "market_crash": {"btc_move": -30, "eth_move": -35, "alt_move": -50, "vol_spike": 100},
        "flash_crash": {"btc_move": -15, "eth_move": -20, "alt_move": -30, "vol_spike": 200},
        "bull_run": {"btc_move": 25, "eth_move": 35, "alt_move": 60, "vol_spike": 50},
        "sideways": {"btc_move": -5, "eth_move": -5, "alt_move": -10, "vol_spike": -20},
        "black_swan": {"btc_move": -50, "eth_move": -60, "alt_move": -80, "vol_spike": 300}
    }
    
    if scenario not in scenarios:
        scenario = "market_crash"
    
    params = scenarios[scenario]
    
    # Fetch positions
    perp_positions = await db.perp_positions.find(
        {"user_id": user_id, "status": "open"}, {"_id": 0}
    ).to_list(100)
    
    yield_positions = await db.yield_positions.find(
        {"user_id": user_id, "status": "active"}, {"_id": 0}
    ).to_list(100)
    
    options_positions = await db.options_positions.find(
        {"user_id": user_id, "status": "open"}, {"_id": 0}
    ).to_list(100)
    
    # Calculate impact on perpetuals
    perp_impact = 0
    liquidations = 0
    
    for p in perp_positions:
        symbol = p.get("symbol", "")
        move = params["btc_move"] if "BTC" in symbol else params["eth_move"] if "ETH" in symbol else params["alt_move"]
        move_pct = move / 100
        
        size = p.get("size_usd", 0)
        side = p.get("side", "long")
        
        if side == "long":
            pnl = size * move_pct
        else:
            pnl = size * (-move_pct)
        
        perp_impact += pnl
        
        # Check for liquidation
        margin = p.get("margin", 0)
        if margin + pnl < margin * 0.1:  # Below maintenance margin
            liquidations += 1
    
    # Calculate impact on yield (simplified)
    yield_impact = 0
    for p in yield_positions:
        value = p.get("current_value_usd", 0)
        # Assume yield positions are mostly stablecoins or have IL protection
        risk_level = p.get("risk_level", "medium")
        
        if risk_level == "high":
            yield_impact += value * (params["alt_move"] / 100) * 0.5  # 50% correlation
        elif risk_level == "medium":
            yield_impact += value * (params["btc_move"] / 100) * 0.3
        # Low risk assumed stable
    
    # Calculate impact on options (simplified delta impact)
    options_impact = 0
    for p in options_positions:
        delta = p.get("delta", 0) * p.get("quantity", 1)
        underlying = p.get("underlying", "BTC")
        move = params["btc_move"] if underlying == "BTC" else params["eth_move"] if underlying == "ETH" else params["alt_move"]
        
        # Delta P&L approximation
        notional = p.get("notional_value", 1000)
        options_impact += delta * (move / 100) * notional
        
        # Vega impact from vol spike
        vega = p.get("vega", 0) * p.get("quantity", 1)
        options_impact += vega * params["vol_spike"]
    
    total_impact = perp_impact + yield_impact + options_impact
    
    # Current portfolio value
    current_perp = sum(p.get("margin", 0) + p.get("unrealized_pnl", 0) for p in perp_positions)
    current_yield = sum(p.get("current_value_usd", 0) for p in yield_positions)
    current_options = sum(abs(p.get("current_value", 0)) for p in options_positions)
    current_total = current_perp + current_yield + current_options
    
    return {
        "scenario": scenario,
        "scenario_params": params,
        "current_portfolio_value": round(current_total, 2),
        "projected_portfolio_value": round(current_total + total_impact, 2),
        "total_impact": round(total_impact, 2),
        "impact_breakdown": {
            "perpetuals": round(perp_impact, 2),
            "yield_farming": round(yield_impact, 2),
            "options": round(options_impact, 2)
        },
        "liquidations_triggered": liquidations,
        "survival": total_impact > -current_total * 0.9,
        "recommendations": [
            "Consider reducing leverage" if liquidations > 0 else None,
            "Add protective puts" if perp_impact < -current_perp * 0.5 else None,
            "Diversify yield positions" if yield_impact < -current_yield * 0.3 else None
        ]
    }


# =============================================================================
# CORRELATION MATRIX
# =============================================================================

@router.get("/correlations")
async def get_correlation_matrix():
    """Get asset correlation matrix for risk assessment"""
    
    # Simplified correlation matrix based on historical data
    correlations = {
        "BTC": {"BTC": 1.0, "ETH": 0.85, "SOL": 0.78, "LINK": 0.72, "DOGE": 0.65, "USD": 0.0},
        "ETH": {"BTC": 0.85, "ETH": 1.0, "SOL": 0.82, "LINK": 0.80, "DOGE": 0.60, "USD": 0.0},
        "SOL": {"BTC": 0.78, "ETH": 0.82, "SOL": 1.0, "LINK": 0.75, "DOGE": 0.55, "USD": 0.0},
        "LINK": {"BTC": 0.72, "ETH": 0.80, "SOL": 0.75, "LINK": 1.0, "DOGE": 0.50, "USD": 0.0},
        "DOGE": {"BTC": 0.65, "ETH": 0.60, "SOL": 0.55, "LINK": 0.50, "DOGE": 1.0, "USD": 0.0},
        "USD": {"BTC": 0.0, "ETH": 0.0, "SOL": 0.0, "LINK": 0.0, "DOGE": 0.0, "USD": 1.0}
    }
    
    return {
        "matrix": correlations,
        "high_correlation_pairs": [
            {"pair": "BTC-ETH", "correlation": 0.85},
            {"pair": "ETH-SOL", "correlation": 0.82},
            {"pair": "ETH-LINK", "correlation": 0.80}
        ],
        "diversification_tip": "Positions highly correlated to BTC may not provide effective diversification during market stress.",
        "last_updated": datetime.now(timezone.utc).isoformat()
    }

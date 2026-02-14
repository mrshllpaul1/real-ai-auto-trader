"""
AI Decisions API - Provides transparency into AI trading decisions
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

router = APIRouter()

async def get_database():
    from server import db
    return db

async def get_strategy_engine():
    from server import strategy_engine
    return strategy_engine

async def get_learning_engine():
    from server import learning_engine
    return learning_engine


class AIDecision(BaseModel):
    coin_id: str
    action: str
    confidence: float
    factors: List[Dict[str, Any]]
    reasoning: str
    is_gem: bool = False
    score: float
    timestamp: str


@router.get("/recent")
async def get_recent_decisions(
    limit: int = 20,
    db = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get recent AI trading decisions with full explanations
    """
    try:
        # Get recent strategies with AI analysis
        strategies = await db.strategies.find(
            {"status": {"$in": ["active", "executed"]}},
            {"_id": 0}
        ).sort("generated_at", -1).limit(limit).to_list(limit)
        
        # Get recent trades with AI scores
        trades = await db.ai_trades.find(
            {},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        # Get hidden gem selections
        gems = await db.hidden_gems.find(
            {"data_source": "REAL_MARKET_DATA"},
            {"_id": 0}
        ).sort("gain_multiplier", -1).limit(10).to_list(10)
        
        decisions = []
        
        # Process strategies into decisions
        for s in strategies:
            decision = {
                "coin_id": s.get("coin_id", "unknown"),
                "action": s.get("action", "ANALYZE"),
                "confidence": s.get("confidence_score", s.get("ai_score", 50)),
                "factors": _extract_factors(s),
                "reasoning": s.get("ai_reasoning", s.get("reasoning", "AI analysis based on technical indicators and market sentiment.")),
                "is_gem": s.get("is_gem", False),
                "score": s.get("total_score", s.get("ai_score", 50)),
                "timestamp": s.get("generated_at", datetime.now().isoformat()),
                "type": "strategy"
            }
            decisions.append(decision)
        
        # Process trades into decisions
        for t in trades:
            decision = {
                "coin_id": t.get("symbol", t.get("coin_id", "unknown")),
                "action": t.get("action", "TRADE"),
                "confidence": t.get("ai_confidence", t.get("confidence", 70)),
                "factors": _extract_trade_factors(t),
                "reasoning": t.get("ai_reasoning", f"Executed {t.get('action', 'trade')} based on AI strategy recommendations."),
                "is_gem": t.get("is_gem", False),
                "score": t.get("ai_score", 70),
                "timestamp": t.get("timestamp", datetime.now().isoformat()),
                "type": "trade"
            }
            decisions.append(decision)
        
        # Sort by timestamp
        decisions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {
            "decisions": decisions[:limit],
            "count": len(decisions[:limit]),
            "gem_candidates": [
                {
                    "coin_id": g.get("coin_id"),
                    "potential_multiplier": g.get("gain_multiplier", g.get("multiplier", 1)),
                    "entry_signals": g.get("entry_signals", []),
                    "confidence": g.get("confidence", 60)
                }
                for g in gems[:5]
            ],
            "fetched_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.get("/explain/{coin_id}")
async def explain_coin_decision(
    coin_id: str,
    db = Depends(get_database),
    strategy_engine = Depends(get_strategy_engine)
) -> Dict[str, Any]:
    """
    Get detailed AI explanation for a specific coin's recommendation
    """
    try:
        # Get latest strategy for this coin
        strategy = await db.strategies.find_one(
            {"coin_id": coin_id.lower()},
            {"_id": 0},
            sort=[("generated_at", -1)]
        )
        
        # Get historical patterns for this coin
        patterns = await db.historical_patterns.find(
            {"coin_id": coin_id.lower(), "data_source": "REAL_MARKET_DATA"},
            {"_id": 0}
        ).sort("date", -1).limit(10).to_list(10)
        
        # Get any hidden gem data
        gem_data = await db.hidden_gems.find_one(
            {"coin_id": coin_id.lower()},
            {"_id": 0},
            sort=[("gain_multiplier", -1)]
        )
        
        # Build comprehensive explanation
        explanation = {
            "coin_id": coin_id,
            "recommendation": strategy.get("action", "HOLD") if strategy else "ANALYZE",
            "confidence": strategy.get("confidence_score", 50) if strategy else 50,
            "analysis": {
                "technical": {
                    "signal": strategy.get("technical_signal", "NEUTRAL") if strategy else "NEUTRAL",
                    "rsi": strategy.get("rsi", 50) if strategy else 50,
                    "macd": strategy.get("macd", "neutral") if strategy else "neutral",
                    "trend": strategy.get("trend", "sideways") if strategy else "sideways"
                },
                "sentiment": {
                    "overall": strategy.get("sentiment", "neutral") if strategy else "neutral",
                    "news_sentiment": strategy.get("news_sentiment", "neutral") if strategy else "neutral"
                },
                "historical": {
                    "patterns_found": len(patterns),
                    "success_rate": _calculate_pattern_success(patterns),
                    "recent_patterns": [p.get("pattern_type") for p in patterns[:5]]
                }
            },
            "is_potential_gem": gem_data is not None,
            "gem_analysis": {
                "historical_multiplier": gem_data.get("gain_multiplier", 1) if gem_data else None,
                "entry_signals": gem_data.get("entry_signals", []) if gem_data else [],
                "gem_type": gem_data.get("gem_type", "none") if gem_data else "none"
            } if gem_data else None,
            "factors": _extract_factors(strategy) if strategy else [],
            "reasoning": _generate_detailed_reasoning(strategy, patterns, gem_data),
            "data_source": "REAL_MARKET_DATA",
            "generated_at": datetime.now().isoformat()
        }
        
        return explanation
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.get("/factors")
async def get_decision_factors(
    db = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get aggregated AI decision factors and their impact
    """
    try:
        # Aggregate factor performance
        patterns = await db.historical_patterns.find(
            {"data_source": "REAL_MARKET_DATA"},
            {"_id": 0}
        ).to_list(1000)
        
        factor_stats = {
            "momentum": {"total": 0, "successful": 0, "avg_score": 0},
            "volume": {"total": 0, "successful": 0, "avg_score": 0},
            "trend": {"total": 0, "successful": 0, "avg_score": 0},
            "sentiment": {"total": 0, "successful": 0, "avg_score": 0},
            "volatility": {"total": 0, "successful": 0, "avg_score": 0}
        }
        
        for p in patterns:
            pattern_type = p.get("pattern_type", "")
            success = p.get("success", False)
            
            if "momentum" in pattern_type or p.get("macd"):
                factor_stats["momentum"]["total"] += 1
                if success:
                    factor_stats["momentum"]["successful"] += 1
            
            if p.get("volume_ratio", 1) > 1.5:
                factor_stats["volume"]["total"] += 1
                if success:
                    factor_stats["volume"]["successful"] += 1
            
            if "trend" in pattern_type or "continuation" in pattern_type:
                factor_stats["trend"]["total"] += 1
                if success:
                    factor_stats["trend"]["successful"] += 1
        
        # Calculate success rates
        for factor, stats in factor_stats.items():
            if stats["total"] > 0:
                stats["success_rate"] = round(stats["successful"] / stats["total"] * 100, 1)
            else:
                stats["success_rate"] = 0
        
        return {
            "factors": factor_stats,
            "most_reliable": max(factor_stats.items(), key=lambda x: x[1].get("success_rate", 0))[0],
            "total_patterns_analyzed": len(patterns),
            "data_source": "REAL_MARKET_DATA"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


def _extract_factors(strategy: dict) -> List[Dict[str, Any]]:
    """Extract decision factors from strategy"""
    factors = []
    
    if not strategy:
        return factors
    
    # Technical factors
    if strategy.get("momentum_score") or strategy.get("rsi"):
        rsi = strategy.get("rsi", 50)
        factors.append({
            "type": "momentum",
            "name": "Price Momentum (RSI)",
            "score": min(100, max(0, 100 - abs(rsi - 50) * 2)),
            "impact": "positive" if 30 < rsi < 70 else "negative",
            "value": f"RSI: {rsi}"
        })
    
    if strategy.get("volume_score") or strategy.get("volume_ratio"):
        vol_ratio = strategy.get("volume_ratio", 1)
        factors.append({
            "type": "volume",
            "name": "Trading Volume",
            "score": min(100, vol_ratio * 50),
            "impact": "positive" if vol_ratio > 1.2 else "neutral",
            "value": f"{vol_ratio:.1f}x avg"
        })
    
    if strategy.get("trend") or strategy.get("trend_score"):
        trend = strategy.get("trend", "neutral")
        factors.append({
            "type": "trend",
            "name": "Trend Analysis",
            "score": 80 if trend == "bullish" else 50 if trend == "neutral" else 30,
            "impact": "positive" if trend == "bullish" else "negative" if trend == "bearish" else "neutral",
            "value": trend.capitalize()
        })
    
    if strategy.get("sentiment") or strategy.get("news_sentiment"):
        sentiment = strategy.get("sentiment", strategy.get("news_sentiment", "neutral"))
        factors.append({
            "type": "sentiment",
            "name": "Market Sentiment",
            "score": 80 if sentiment == "positive" else 50 if sentiment == "neutral" else 30,
            "impact": "positive" if sentiment == "positive" else "negative" if sentiment == "negative" else "neutral",
            "value": sentiment.capitalize()
        })
    
    if strategy.get("volatility") or strategy.get("volatility_score"):
        vol = strategy.get("volatility", 0.05)
        factors.append({
            "type": "volatility",
            "name": "Volatility",
            "score": 70 if 0.02 < vol < 0.08 else 40,
            "impact": "positive" if 0.02 < vol < 0.08 else "neutral",
            "value": f"{vol*100:.1f}%"
        })
    
    # Add AI confidence as a factor
    if strategy.get("ai_score") or strategy.get("confidence_score"):
        score = strategy.get("ai_score", strategy.get("confidence_score", 50))
        factors.append({
            "type": "ai_confidence",
            "name": "AI Confidence",
            "score": score,
            "impact": "positive" if score > 70 else "neutral" if score > 50 else "negative",
            "value": f"{score:.0f}%"
        })
    
    return factors


def _extract_trade_factors(trade: dict) -> List[Dict[str, Any]]:
    """Extract factors from trade data"""
    factors = []
    
    if trade.get("entry_price") and trade.get("current_price"):
        pnl_pct = ((trade["current_price"] - trade["entry_price"]) / trade["entry_price"]) * 100
        factors.append({
            "type": "performance",
            "name": "Position P&L",
            "score": 50 + pnl_pct,
            "impact": "positive" if pnl_pct > 0 else "negative",
            "value": f"{pnl_pct:+.1f}%"
        })
    
    if trade.get("ai_confidence"):
        factors.append({
            "type": "ai_confidence",
            "name": "AI Confidence",
            "score": trade["ai_confidence"],
            "impact": "positive" if trade["ai_confidence"] > 70 else "neutral",
            "value": f"{trade['ai_confidence']:.0f}%"
        })
    
    return factors


def _calculate_pattern_success(patterns: list) -> float:
    """Calculate success rate from patterns"""
    if not patterns:
        return 0
    successful = sum(1 for p in patterns if p.get("success", False))
    return round(successful / len(patterns) * 100, 1)


def _generate_detailed_reasoning(strategy: dict, patterns: list, gem_data: dict) -> str:
    """Generate detailed AI reasoning text"""
    parts = []
    
    if strategy:
        signal = strategy.get("technical_signal", "NEUTRAL")
        confidence = strategy.get("confidence_score", 50)
        
        if confidence > 75:
            parts.append(f"High confidence ({confidence:.0f}%) {signal.lower()} signal detected.")
        elif confidence > 50:
            parts.append(f"Moderate confidence ({confidence:.0f}%) with {signal.lower()} technical indicators.")
        else:
            parts.append(f"Low confidence ({confidence:.0f}%) - exercise caution.")
    
    if patterns:
        success_rate = _calculate_pattern_success(patterns)
        parts.append(f"Historical pattern analysis shows {success_rate:.0f}% success rate from {len(patterns)} similar situations.")
    
    if gem_data:
        mult = gem_data.get("gain_multiplier", 1)
        parts.append(f"Identified as potential hidden gem with historical {mult:.1f}x gains in similar conditions.")
    
    if not parts:
        parts.append("AI analysis in progress. Monitoring market conditions for optimal entry points.")
    
    return " ".join(parts)

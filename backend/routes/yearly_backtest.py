"""
Yearly Adaptive Backtest API Routes
====================================
API endpoints for running comprehensive yearly backtests with weekly adaptation.
Supports years 2020-2026.
Includes Live Trading activation based on proven strategy parameters.
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/yearly-backtest", tags=["Yearly Adaptive Backtest"])

# Global state
_db = None
_running_backtests = {}
_backtest_results = {}
_live_trading_active = False
_live_trading_config = None


def set_db(db):
    global _db
    _db = db


class YearlyBacktestRequest(BaseModel):
    year: int = 2025  # Year to backtest (2020-2025)
    initial_capital: float = 100000
    coins: Optional[List[str]] = None  # None = use top 30 default coins
    use_all_kraken_coins: bool = False  # If true, use all 600+ Kraken coins


class MultiYearBacktestRequest(BaseModel):
    years: List[int] = [2020, 2021, 2022, 2023, 2024, 2025]
    initial_capital: float = 100000
    coins: Optional[List[str]] = None


class BacktestResponse(BaseModel):
    backtest_id: str
    status: str
    message: str


@router.post("/run", response_model=BacktestResponse)
async def run_yearly_backtest(
    request: YearlyBacktestRequest,
    background_tasks: BackgroundTasks
):
    """
    Run a full year backtest with weekly adaptive strategy.
    
    Supported years: 2020, 2021, 2022, 2023, 2024, 2025
    
    Features:
    - Tests across selected coins (or all Kraken coins)
    - Adapts strategy parameters weekly based on market regime
    - Generates recommended portfolio for live trading
    - Provides auto-trade signals
    
    Returns backtest_id for tracking progress.
    """
    backtest_id = str(uuid.uuid4())
    year = request.year
    
    if year < 2020 or year > 2026:
        raise HTTPException(status_code=400, detail="Year must be between 2020 and 2026")
    
    try:
        from services.yearly_adaptive_backtest import run_yearly_adaptive_backtest, TOP_COINS, COINS_BY_YEAR
        
        # Determine coins to use
        coins = request.coins
        if request.use_all_kraken_coins:
            # Get coins from Kraken universe
            if _db:
                try:
                    universe = await _db.kraken_universe.find_one({"type": "universe"})
                    if universe and "crypto_coins" in universe:
                        coins = universe["crypto_coins"][:100]  # Limit to top 100 for performance
                except Exception as e:
                    logger.warning(f"Could not fetch Kraken universe: {e}")
                    coins = COINS_BY_YEAR.get(year, TOP_COINS[:50])
            else:
                coins = COINS_BY_YEAR.get(year, TOP_COINS[:50])
        elif not coins:
            coins = COINS_BY_YEAR.get(year, TOP_COINS[:30])[:30]
        
        _running_backtests[backtest_id] = {
            "status": "starting",
            "year": year,
            "progress": 0,
            "coins_count": len(coins),
            "initial_capital": request.initial_capital
        }
        
        # Run backtest in background
        async def run_backtest_task():
            try:
                _running_backtests[backtest_id]["status"] = "running"
                _running_backtests[backtest_id]["progress"] = 10
                
                results = await run_yearly_adaptive_backtest(
                    year=year,
                    initial_capital=request.initial_capital,
                    coins=coins,
                    db=_db
                )
                
                _running_backtests[backtest_id]["status"] = "completed"
                _running_backtests[backtest_id]["progress"] = 100
                _backtest_results[backtest_id] = results
                
            except Exception as e:
                logger.error(f"Backtest {backtest_id} failed: {e}")
                _running_backtests[backtest_id]["status"] = "failed"
                _running_backtests[backtest_id]["error"] = str(e)
        
        background_tasks.add_task(run_backtest_task)
        
        return BacktestResponse(
            backtest_id=backtest_id,
            status="started",
            message=f"Year {year} backtest started with {len(coins)} coins and ${request.initial_capital:,.2f} initial capital"
        )
        
    except Exception as e:
        logger.error(f"Failed to start backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{backtest_id}")
async def get_backtest_status(backtest_id: str):
    """Get status of a running or completed backtest"""
    if backtest_id in _running_backtests:
        status = _running_backtests[backtest_id].copy()
        
        if backtest_id in _backtest_results:
            status["results_available"] = True
        
        return status
    
    raise HTTPException(status_code=404, detail="Backtest not found")


@router.get("/results/{backtest_id}")
async def get_backtest_results(backtest_id: str):
    """Get full results of a completed backtest"""
    if backtest_id in _backtest_results:
        return _backtest_results[backtest_id]
    
    if backtest_id in _running_backtests:
        status = _running_backtests[backtest_id]
        if status["status"] == "running":
            raise HTTPException(status_code=202, detail="Backtest still running")
        elif status["status"] == "failed":
            raise HTTPException(status_code=500, detail=status.get("error", "Backtest failed"))
    
    raise HTTPException(status_code=404, detail="Backtest results not found")


@router.post("/quick-test")
async def run_quick_yearly_test(year: int = 2025, initial_capital: float = 1000):
    """
    Run a quick synchronous yearly backtest with top 20 coins.
    Returns results immediately (may take 5-10 seconds).
    
    Supported years: 2020, 2021, 2022, 2023, 2024, 2025, 2026
    Default initial capital: $1,000
    """
    if year < 2020 or year > 2026:
        raise HTTPException(status_code=400, detail="Year must be between 2020 and 2026")
    
    try:
        from services.yearly_adaptive_backtest import run_yearly_adaptive_backtest, COINS_BY_YEAR
        
        coins = COINS_BY_YEAR.get(year, COINS_BY_YEAR[2025])[:20]
        
        results = await run_yearly_adaptive_backtest(
            year=year,
            initial_capital=initial_capital,
            coins=coins,
            db=_db
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Quick test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-year")
async def run_multi_year_backtest_endpoint(request: MultiYearBacktestRequest):
    """
    Run backtests across multiple years (2020-2025).
    
    This runs each year sequentially, compounding capital from year to year.
    Returns aggregate metrics including CAGR and overall win rate.
    """
    for year in request.years:
        if year < 2020 or year > 2026:
            raise HTTPException(status_code=400, detail=f"Year {year} not supported. Must be between 2020 and 2026")
    
    try:
        from services.yearly_adaptive_backtest import run_multi_year_backtest
        
        results = await run_multi_year_backtest(
            years=request.years,
            initial_capital=request.initial_capital,
            coins=request.coins,
            db=_db
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Multi-year backtest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommended-portfolio")
async def get_recommended_portfolio():
    """
    Get the recommended portfolio based on latest backtest results.
    Returns optimal coin allocation and strategy parameters for live trading.
    """
    # Find most recent completed backtest
    latest_result = None
    latest_id = None
    
    for backtest_id, results in _backtest_results.items():
        if results.get("status") == "completed":
            latest_result = results
            latest_id = backtest_id
    
    if not latest_result:
        # Run a quick backtest to generate recommendations
        try:
            from services.yearly_adaptive_backtest import run_yearly_adaptive_backtest, TOP_COINS
            latest_result = await run_yearly_adaptive_backtest(
                initial_capital=100000,
                coins=TOP_COINS[:20],
                db=_db
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Could not generate portfolio: {e}")
    
    if latest_result and "recommended_portfolio" in latest_result:
        return {
            "status": "success",
            "backtest_id": latest_id,
            "backtest_metrics": {
                "win_rate": latest_result.get("win_rate"),
                "total_return": latest_result.get("total_return_pct"),
                "sharpe_ratio": latest_result.get("sharpe_ratio"),
                "max_drawdown": latest_result.get("max_drawdown_pct")
            },
            "recommended_portfolio": latest_result["recommended_portfolio"],
            "top_coins": latest_result.get("top_coins", [])[:5],
            "auto_trade_ready": latest_result.get("auto_trade_ready", False)
        }
    
    raise HTTPException(status_code=404, detail="No portfolio recommendations available")


@router.get("/strategy-params")
async def get_current_strategy_params():
    """
    Get current adaptive strategy parameters optimized for live trading.
    """
    from services.yearly_adaptive_backtest import AdaptiveStrategy, MARKET_REGIMES
    
    # Create strategy and adapt to current market conditions
    strategy = AdaptiveStrategy()
    
    # Get current market regime (simplified - in production would use real market data)
    import random
    current_regime = random.choice(["bull_weak", "sideways", "recovery"])
    
    strategy.adapt_to_regime(current_regime, recent_win_rate=0.6)
    
    return {
        "current_regime": current_regime,
        "adapted_params": strategy.params,
        "available_regimes": list(MARKET_REGIMES.keys()),
        "regime_descriptions": {
            "bull_strong": "Strong uptrend with high momentum",
            "bull_weak": "Mild uptrend with moderate momentum",
            "bear_strong": "Strong downtrend with capitulation",
            "bear_weak": "Mild correction or pullback",
            "sideways": "Range-bound consolidation",
            "high_volatility": "Choppy market with large swings",
            "recovery": "Bottoming pattern with accumulation"
        }
    }


@router.get("/market-calendar")
async def get_market_calendar(year: Optional[int] = None):
    """
    Get the market events calendar used for regime detection.
    Can specify a year (2020-2026) or get all years.
    Returns week-by-week breakdown with month, regime, event details, and sentiment data.
    """
    from services.yearly_adaptive_backtest import (
        MARKET_EVENTS_2020, MARKET_EVENTS_2021, MARKET_EVENTS_2022,
        MARKET_EVENTS_2023, MARKET_EVENTS_2024, MARKET_EVENTS_2025,
        MARKET_EVENTS_2026, MARKET_EVENTS_BY_YEAR,
        HISTORICAL_SENTIMENT_BY_YEAR, get_weekly_sentiment
    )
    
    all_calendars = {
        2020: MARKET_EVENTS_2020,
        2021: MARKET_EVENTS_2021,
        2022: MARKET_EVENTS_2022,
        2023: MARKET_EVENTS_2023,
        2024: MARKET_EVENTS_2024,
        2025: MARKET_EVENTS_2025,
        2026: MARKET_EVENTS_2026
    }
    
    def get_calendar_summary(events, calendar_year):
        """Build detailed calendar summary for a year"""
        months = ["January", "February", "March", "April", "May", "June", 
                  "July", "August", "September", "October", "November", "December"]
        
        # Enrich events with sentiment data
        enriched_events = []
        for event in events:
            sentiment = get_weekly_sentiment(calendar_year, event["week"])
            enriched_event = {
                **event,
                "sentiment": sentiment["fear_greed_value"],
                "sentiment_category": sentiment["category"],
                "sentiment_signal": sentiment["signal"]
            }
            enriched_events.append(enriched_event)
        
        # Group events by month
        events_by_month = {month: [] for month in months}
        for event in enriched_events:
            # Use month from event if available, otherwise calculate from week
            if "month" in event:
                month = event["month"]
            else:
                # Calculate approximate month from week number (1-52)
                week = event.get("week", 1)
                month_idx = min(11, (week - 1) * 12 // 52)
                month = months[month_idx]
            
            if month in events_by_month:
                events_by_month[month].append(event)
        
        # Calculate regime distribution
        regime_counts = {}
        for event in enriched_events:
            regime = event["regime"]
            regime_counts[regime] = regime_counts.get(regime, 0) + 1
        
        # Calculate sentiment distribution
        sentiment_counts = {"extreme_fear": 0, "fear": 0, "neutral": 0, "greed": 0, "extreme_greed": 0}
        for event in enriched_events:
            sentiment_counts[event["sentiment_category"]] += 1
        
        # Find key events
        key_events = [e for e in enriched_events if e["regime"] in ["crash", "euphoria", "high_volatility"]]
        
        # Calculate average sentiment by quarter
        sentiment_by_quarter = {}
        for q, q_events in [
            ("Q1", [e for e in enriched_events if e["week"] <= 13]),
            ("Q2", [e for e in enriched_events if 13 < e["week"] <= 26]),
            ("Q3", [e for e in enriched_events if 26 < e["week"] <= 39]),
            ("Q4", [e for e in enriched_events if e["week"] > 39])
        ]:
            if q_events:
                avg_sentiment = sum(e["sentiment"] for e in q_events) / len(q_events)
                sentiment_by_quarter[q] = {
                    "average_sentiment": round(avg_sentiment, 1),
                    "weeks": len(q_events)
                }
        
        return {
            "year": calendar_year,
            "total_weeks": len(enriched_events),
            "events": enriched_events,
            "events_by_month": events_by_month,
            "regime_distribution": regime_counts,
            "sentiment_distribution": sentiment_counts,
            "sentiment_by_quarter": sentiment_by_quarter,
            "key_events": key_events,
            "regimes_by_quarter": {
                "Q1": [e for e in enriched_events if e["week"] <= 13],
                "Q2": [e for e in enriched_events if 13 < e["week"] <= 26],
                "Q3": [e for e in enriched_events if 26 < e["week"] <= 39],
                "Q4": [e for e in enriched_events if e["week"] > 39]
            }
        }
    
    if year:
        if year not in all_calendars:
            raise HTTPException(status_code=400, detail=f"Year {year} not available. Choose from 2020-2026")
        
        return get_calendar_summary(all_calendars[year], year)
    
    # Return all years
    return {
        "available_years": list(all_calendars.keys()),
        "calendars": {
            yr: get_calendar_summary(events, yr) 
            for yr, events in all_calendars.items()
        }
    }


@router.get("/coins")
async def get_available_coins():
    """
    Get list of coins available for backtesting.
    """
    from services.yearly_adaptive_backtest import TOP_COINS
    
    kraken_coins = []
    if _db is not None:
        try:
            universe = await _db.kraken_universe.find_one({"type": "universe"})
            if universe and "crypto_coins" in universe:
                kraken_coins = universe["crypto_coins"]
        except Exception:
            pass
    
    return {
        "default_top_coins": TOP_COINS,
        "kraken_universe_coins": len(kraken_coins),
        "kraken_coins_sample": kraken_coins[:50] if kraken_coins else [],
        "recommended_for_backtest": TOP_COINS[:30]
    }



# ============================================================================
# LIVE TRADING ENDPOINTS - Based on Adaptive Strategy
# ============================================================================

class LiveTradingConfig(BaseModel):
    """Configuration for live adaptive trading"""
    enabled: bool = True
    amount_per_trade_usd: float = 50.0  # USD per trade
    max_positions: int = 10
    stop_loss_pct: float = 3.0  # Default stop loss
    take_profit_pct: float = 5.0  # Default take profit
    use_regime_adaptation: bool = True  # Adapt to market regime
    coins: Optional[List[str]] = None  # If None, use top coins from backtest
    paper_mode: bool = False  # If True, paper trading only


class LiveTradingSignal(BaseModel):
    """A live trading signal generated by the adaptive strategy"""
    coin: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    regime: str
    stop_loss: float
    take_profit: float
    position_size_pct: float
    reason: str


@router.post("/live-trading/activate")
async def activate_live_trading(config: LiveTradingConfig):
    """
    Activate live trading using the proven adaptive strategy parameters.
    This will apply the regime-based strategy from backtesting to real trades.
    """
    global _live_trading_active, _live_trading_config
    
    # Check Kraken API keys
    kraken_key = os.getenv('KRAKEN_API_KEY')
    kraken_secret = os.getenv('KRAKEN_API_SECRET')
    
    if not config.paper_mode and (not kraken_key or not kraken_secret):
        raise HTTPException(
            status_code=400, 
            detail="Kraken API keys required for live trading. Set paper_mode=True for paper trading."
        )
    
    # Get current market regime
    from services.yearly_adaptive_backtest import (
        MARKET_EVENTS_2025, MARKET_EVENTS_2026, 
        REGIME_PARAMS, TOP_COINS
    )
    
    # Determine current week of year
    now = datetime.now(timezone.utc)
    current_week = now.isocalendar()[1]
    current_year = now.year
    
    # Get market events for current year
    if current_year == 2025:
        events = MARKET_EVENTS_2025
    elif current_year == 2026:
        events = MARKET_EVENTS_2026
    else:
        events = MARKET_EVENTS_2025  # Default to 2025
    
    # Find current regime
    current_regime = "sideways"  # Default
    current_event = None
    for event in events:
        if event["week"] == current_week:
            current_regime = event["regime"]
            current_event = event
            break
    
    # Get regime-specific parameters
    regime_params = REGIME_PARAMS.get(current_regime, REGIME_PARAMS["sideways"])
    
    # Apply regime-based stop loss and take profit if using adaptation
    if config.use_regime_adaptation:
        config.stop_loss_pct = regime_params.get("stop_loss", 3.0)
        config.take_profit_pct = regime_params.get("take_profit", 5.0)
    
    # Set coins to trade
    coins_to_trade = config.coins if config.coins else TOP_COINS[:config.max_positions]
    
    # Store configuration
    _live_trading_config = {
        **config.model_dump(),
        "coins": coins_to_trade,
        "current_regime": current_regime,
        "regime_params": regime_params,
        "current_event": current_event,
        "activated_at": now.isoformat(),
        "week": current_week
    }
    _live_trading_active = True
    
    # Save to database
    if _db is not None:
        await _db.adaptive_live_trading.replace_one(
            {"type": "config"},
            {"type": "config", **_live_trading_config},
            upsert=True
        )
    
    return {
        "success": True,
        "message": "Adaptive live trading activated" + (" (PAPER MODE)" if config.paper_mode else " (REAL MONEY)"),
        "config": _live_trading_config,
        "strategy": {
            "regime": current_regime,
            "event": current_event.get("event") if current_event else "Unknown",
            "stop_loss": config.stop_loss_pct,
            "take_profit": config.take_profit_pct,
            "position_size_factor": regime_params.get("position_size", 1.0),
            "min_confidence": regime_params.get("min_confidence", 60)
        },
        "coins": coins_to_trade,
        "warning": "⚠️ Real money trading involves risk. Monitor positions closely." if not config.paper_mode else None
    }


@router.post("/live-trading/deactivate")
async def deactivate_live_trading():
    """Deactivate live adaptive trading"""
    global _live_trading_active
    
    _live_trading_active = False
    
    if _db is not None and _live_trading_config:
        await _db.adaptive_live_trading.update_one(
            {"type": "config"},
            {"$set": {"enabled": False, "deactivated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {
        "success": True,
        "message": "Adaptive live trading deactivated",
        "was_active": _live_trading_config is not None
    }


@router.get("/live-trading/status")
async def get_live_trading_status():
    """Get current live trading status and regime"""
    from services.yearly_adaptive_backtest import (
        MARKET_EVENTS_2025, MARKET_EVENTS_2026, REGIME_PARAMS
    )
    
    # Get current regime
    now = datetime.now(timezone.utc)
    current_week = now.isocalendar()[1]
    current_year = now.year
    
    events = MARKET_EVENTS_2026 if current_year >= 2026 else MARKET_EVENTS_2025
    current_event = next((e for e in events if e["week"] == current_week), None)
    current_regime = current_event["regime"] if current_event else "sideways"
    regime_params = REGIME_PARAMS.get(current_regime, REGIME_PARAMS["sideways"])
    
    return {
        "active": _live_trading_active,
        "config": _live_trading_config,
        "current_market": {
            "week": current_week,
            "year": current_year,
            "regime": current_regime,
            "event": current_event.get("event") if current_event else "Unknown",
            "date_range": current_event.get("date_range") if current_event else None,
            "recommended_params": {
                "stop_loss": regime_params.get("stop_loss"),
                "take_profit": regime_params.get("take_profit"),
                "position_size_factor": regime_params.get("position_size"),
                "min_confidence": regime_params.get("min_confidence")
            }
        }
    }


@router.get("/live-trading/signals")
async def get_live_trading_signals():
    """
    Get current trading signals based on adaptive strategy.
    These signals use the regime-aware parameters from backtesting.
    """
    from services.yearly_adaptive_backtest import (
        MARKET_EVENTS_2025, MARKET_EVENTS_2026, REGIME_PARAMS, TOP_COINS
    )
    
    # Get current regime
    now = datetime.now(timezone.utc)
    current_week = now.isocalendar()[1]
    current_year = now.year
    
    events = MARKET_EVENTS_2026 if current_year >= 2026 else MARKET_EVENTS_2025
    current_event = next((e for e in events if e["week"] == current_week), None)
    current_regime = current_event["regime"] if current_event else "sideways"
    regime_params = REGIME_PARAMS.get(current_regime, REGIME_PARAMS["sideways"])
    
    # Get real market data if available
    signals = []
    try:
        from routes.spot_trading import get_all_pairs
        pairs_data = await get_all_pairs()
        market_prices = {p["symbol"]: p for p in pairs_data.get("pairs", [])}
    except Exception:
        market_prices = {}
    
    # Generate signals based on regime
    coins_to_analyze = _live_trading_config.get("coins", TOP_COINS[:10]) if _live_trading_config else TOP_COINS[:10]
    
    for coin in coins_to_analyze:
        market_data = market_prices.get(coin, {})
        change_24h = market_data.get("change_24h", 0)
        
        # Regime-based signal generation
        signal = _generate_regime_signal(coin, current_regime, regime_params, change_24h)
        if signal:
            signals.append(signal)
    
    return {
        "regime": current_regime,
        "event": current_event.get("event") if current_event else "Unknown",
        "signals": signals,
        "timestamp": now.isoformat(),
        "signal_count": len(signals)
    }


def _generate_regime_signal(coin: str, regime: str, params: dict, change_24h: float) -> Optional[dict]:
    """Generate a trading signal based on current regime and market conditions"""
    
    # Base confidence from regime
    base_confidence = params.get("min_confidence", 60)
    stop_loss = params.get("stop_loss", 3.0)
    take_profit = params.get("take_profit", 5.0)
    position_size = params.get("position_size", 1.0)
    
    action = "HOLD"
    confidence = base_confidence
    reason = ""
    
    # Regime-specific logic
    if regime in ["bull_strong", "euphoria"]:
        if change_24h > 0:
            action = "BUY"
            confidence = min(95, base_confidence + change_24h * 2)
            reason = f"Strong bullish regime with {change_24h:.1f}% gain"
        elif change_24h < -3:
            action = "BUY"  # Buy the dip in strong bull
            confidence = base_confidence + 5
            reason = "Dip buying opportunity in bull market"
    
    elif regime in ["bull_weak", "recovery"]:
        if change_24h > 1:
            action = "BUY"
            confidence = base_confidence + change_24h
            reason = f"Recovery signal with {change_24h:.1f}% gain"
        elif change_24h < -5:
            action = "HOLD"
            reason = "Waiting for clearer signal in weak bull"
    
    elif regime in ["bear_weak", "bear_strong"]:
        if change_24h < -2:
            action = "SELL"
            confidence = min(90, base_confidence + abs(change_24h))
            reason = f"Bear market protection, {change_24h:.1f}% loss"
        elif change_24h > 3:
            action = "HOLD"  # Don't chase pumps in bear market
            reason = "Avoiding bear market rally trap"
    
    elif regime == "high_volatility":
        # Tighter stops in high volatility
        stop_loss = min(stop_loss, 2.0)
        take_profit = min(take_profit, 4.0)
        if abs(change_24h) > 5:
            action = "HOLD"
            reason = "High volatility - reducing exposure"
        else:
            action = "HOLD"
            reason = "Waiting for volatility to settle"
    
    elif regime == "crash":
        action = "SELL"
        confidence = 85
        reason = "Crash protection - exiting positions"
    
    else:  # sideways
        if change_24h > 2:
            action = "BUY"
            confidence = base_confidence
            reason = "Breakout attempt in sideways market"
        elif change_24h < -2:
            action = "SELL"
            confidence = base_confidence
            reason = "Breakdown in sideways market"
    
    # Only return actionable signals
    if action == "HOLD" and confidence < 70:
        return None
    
    return {
        "coin": coin,
        "action": action,
        "confidence": round(confidence, 1),
        "regime": regime,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "position_size_pct": position_size * 10,  # As percentage of portfolio
        "reason": reason,
        "change_24h": change_24h
    }



# Track last known regime for change detection
_last_known_regime = None


@router.get("/live-trading/check-regime-change")
async def check_regime_change():
    """
    Check if market regime has changed since last check.
    If changed, sends a notification.
    """
    global _last_known_regime
    
    from services.yearly_adaptive_backtest import (
        MARKET_EVENTS_2025, MARKET_EVENTS_2026, REGIME_PARAMS
    )
    
    # Get current regime
    now = datetime.now(timezone.utc)
    current_week = now.isocalendar()[1]
    current_year = now.year
    
    events = MARKET_EVENTS_2026 if current_year >= 2026 else MARKET_EVENTS_2025
    current_event = next((e for e in events if e["week"] == current_week), None)
    current_regime = current_event["regime"] if current_event else "sideways"
    
    changed = False
    old_regime = _last_known_regime
    
    if _last_known_regime and _last_known_regime != current_regime:
        changed = True
        
        # Send notification if DB is available
        if _db is not None:
            try:
                from services.notification_service import NotificationService
                notif_service = NotificationService(_db)
                await notif_service.notify_regime_change(
                    old_regime=_last_known_regime,
                    new_regime=current_regime,
                    week=current_week,
                    event=current_event.get("event") if current_event else "Unknown"
                )
            except Exception as e:
                logger.error(f"Failed to send regime change notification: {e}")
    
    _last_known_regime = current_regime
    
    return {
        "changed": changed,
        "old_regime": old_regime,
        "current_regime": current_regime,
        "week": current_week,
        "event": current_event.get("event") if current_event else "Unknown",
        "checked_at": now.isoformat()
    }


@router.post("/live-trading/execute-all-signals")
async def execute_all_signals():
    """
    Execute all actionable trading signals at once.
    Only executes BUY/SELL signals, not HOLD.
    Requires live trading to be active.
    """
    if not _live_trading_active:
        raise HTTPException(status_code=400, detail="Live trading is not active")
    
    if not _live_trading_config:
        raise HTTPException(status_code=400, detail="No trading configuration")
    
    # Get current signals
    signals_response = await get_live_trading_signals()
    signals = signals_response.get("signals", [])
    
    # Filter to actionable signals only
    actionable = [s for s in signals if s["action"] in ["BUY", "SELL"]]
    
    if not actionable:
        return {
            "success": True,
            "message": "No actionable signals at this time",
            "executed": 0,
            "signals_checked": len(signals)
        }
    
    # Execute each signal
    executed = []
    errors = []
    
    from routes.spot_trading import place_spot_order, SpotOrderRequest
    
    for signal in actionable:
        try:
            order = SpotOrderRequest(
                symbol=signal["coin"],
                side=signal["action"].lower(),
                order_type="market",
                usd_amount=_live_trading_config.get("amount_per_trade_usd", 25) if signal["action"] == "BUY" else None,
                use_ai_timing=True
            )
            
            # Only execute if not in paper mode (or execute paper trades)
            if _live_trading_config.get("paper_mode", True):
                executed.append({
                    "coin": signal["coin"],
                    "action": signal["action"],
                    "status": "paper_executed",
                    "amount_usd": _live_trading_config.get("amount_per_trade_usd", 25)
                })
            else:
                result = await place_spot_order(order)
                executed.append({
                    "coin": signal["coin"],
                    "action": signal["action"],
                    "status": "executed",
                    "result": result
                })
        except Exception as e:
            errors.append({
                "coin": signal["coin"],
                "action": signal["action"],
                "error": str(e)
            })
    
    return {
        "success": True,
        "message": f"Executed {len(executed)} signals",
        "executed": executed,
        "errors": errors,
        "regime": signals_response.get("regime"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

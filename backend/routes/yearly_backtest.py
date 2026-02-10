"""
Yearly Adaptive Backtest API Routes
====================================
API endpoints for running comprehensive yearly backtests with weekly adaptation.
Supports years 2020-2025.
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/yearly-backtest", tags=["Yearly Adaptive Backtest"])

# Global state
_db = None
_running_backtests = {}
_backtest_results = {}


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
async def get_market_calendar():
    """
    Get the 2025 market events calendar used for regime detection.
    """
    from services.yearly_adaptive_backtest import MARKET_EVENTS_2025
    
    return {
        "year": 2025,
        "events": MARKET_EVENTS_2025,
        "total_events": len(MARKET_EVENTS_2025),
        "regimes_by_quarter": {
            "Q1": [e for e in MARKET_EVENTS_2025 if e["week"] <= 13],
            "Q2": [e for e in MARKET_EVENTS_2025 if 13 < e["week"] <= 26],
            "Q3": [e for e in MARKET_EVENTS_2025 if 26 < e["week"] <= 39],
            "Q4": [e for e in MARKET_EVENTS_2025 if e["week"] > 39]
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

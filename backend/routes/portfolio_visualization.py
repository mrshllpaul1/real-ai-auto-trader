"""
Portfolio Visualization API Routes
Provides data for portfolio composition, performance history, and analytics.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timezone, timedelta
from enum import Enum

router = APIRouter(prefix="/portfolio/visualization", tags=["Portfolio Visualization"])

# Global references
_db = None
_isolated_portfolio = None


def set_dependencies(database, portfolio_manager):
    """Set dependencies from main app"""
    global _db, _isolated_portfolio
    _db = database
    _isolated_portfolio = portfolio_manager


class TimeRange(str, Enum):
    ONE_DAY = "1d"
    SEVEN_DAYS = "7d"
    THIRTY_DAYS = "30d"
    NINETY_DAYS = "90d"
    ALL_TIME = "all"


@router.get("/composition")
async def get_portfolio_composition():
    """
    Get portfolio composition for pie chart visualization.
    
    Returns breakdown by:
    - Individual coin holdings
    - Cash vs invested
    - Position types (main, gem, swap)
    """
    if _isolated_portfolio is None:
        raise HTTPException(status_code=503, detail="Portfolio manager not initialized")
    
    positions = await _isolated_portfolio.get_ai_positions()
    budget_status = await _isolated_portfolio.get_budget_status()
    
    if not budget_status.get("allocated"):
        return {
            "composition": [],
            "total_value": 0,
            "cash_pct": 100,
            "invested_pct": 0,
            "message": "No budget allocated"
        }
    
    total_value = budget_status.get("current_value", 0)
    cash_available = budget_status.get("cash_available", 0)
    
    # By coin
    coin_breakdown = []
    for pos in positions:
        value = pos.get("current_value", pos.get("entry_value", 0))
        coin_breakdown.append({
            "name": pos.get("coin_id", "Unknown").upper(),
            "symbol": pos.get("symbol", ""),
            "value": round(value, 2),
            "percentage": round((value / total_value * 100) if total_value > 0 else 0, 2),
            "pnl_pct": pos.get("pnl_pct", 0),
            "position_type": pos.get("position_type", "main"),
            "is_gem": pos.get("is_gem", False)
        })
    
    # Add cash as a component
    if cash_available > 0:
        coin_breakdown.append({
            "name": "CASH",
            "symbol": "USD",
            "value": round(cash_available, 2),
            "percentage": round((cash_available / total_value * 100) if total_value > 0 else 0, 2),
            "pnl_pct": 0,
            "position_type": "cash",
            "is_gem": False
        })
    
    # Sort by value descending
    coin_breakdown.sort(key=lambda x: x["value"], reverse=True)
    
    # By position type
    type_breakdown = {}
    for pos in positions:
        ptype = pos.get("position_type", "main")
        value = pos.get("current_value", pos.get("entry_value", 0))
        if ptype not in type_breakdown:
            type_breakdown[ptype] = 0
        type_breakdown[ptype] += value
    
    type_composition = [
        {"name": k.upper(), "value": round(v, 2), "percentage": round((v / total_value * 100) if total_value > 0 else 0, 2)}
        for k, v in type_breakdown.items()
    ]
    
    return {
        "composition": coin_breakdown,
        "type_breakdown": type_composition,
        "total_value": round(total_value, 2),
        "cash_available": round(cash_available, 2),
        "cash_pct": round((cash_available / total_value * 100) if total_value > 0 else 0, 2),
        "invested_pct": round(((total_value - cash_available) / total_value * 100) if total_value > 0 else 0, 2),
        "positions_count": len(positions)
    }


@router.get("/performance-history")
async def get_performance_history(
    range: TimeRange = Query(TimeRange.THIRTY_DAYS, description="Time range for history")
):
    """
    Get portfolio performance history for line chart visualization.
    
    Returns daily portfolio values over time.
    """
    if _db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    # Determine date range
    now = datetime.now(timezone.utc)
    if range == TimeRange.ONE_DAY:
        start_date = now - timedelta(days=1)
    elif range == TimeRange.SEVEN_DAYS:
        start_date = now - timedelta(days=7)
    elif range == TimeRange.THIRTY_DAYS:
        start_date = now - timedelta(days=30)
    elif range == TimeRange.NINETY_DAYS:
        start_date = now - timedelta(days=90)
    else:
        start_date = now - timedelta(days=365)  # All time = 1 year max
    
    # Get historical snapshots
    snapshots = await _db.portfolio_snapshots.find(
        {"timestamp": {"$gte": start_date.isoformat()}},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(500)
    
    # If no snapshots, create synthetic data from transactions
    if not snapshots:
        snapshots = await _generate_history_from_transactions(start_date)
    
    # Format for chart
    history = []
    for snap in snapshots:
        ts = snap.get("timestamp")
        if isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except:
                dt = datetime.now(timezone.utc)
        else:
            dt = ts or datetime.now(timezone.utc)
        
        history.append({
            "date": dt.strftime("%Y-%m-%d"),
            "timestamp": dt.isoformat(),
            "value": round(snap.get("total_value", 0), 2),
            "invested": round(snap.get("invested", 0), 2),
            "pnl": round(snap.get("pnl", 0), 2),
            "pnl_pct": round(snap.get("pnl_pct", 0), 2)
        })
    
    # Calculate stats
    if history:
        start_value = history[0]["value"] if history[0]["value"] > 0 else None
        end_value = history[-1]["value"]
        
        if start_value and start_value > 0:
            period_return = ((end_value - start_value) / start_value) * 100
        else:
            period_return = 0
        
        high = max(h["value"] for h in history)
        low = min(h["value"] for h in history) if any(h["value"] > 0 for h in history) else 0
    else:
        period_return = 0
        high = 0
        low = 0
    
    return {
        "range": range.value,
        "history": history,
        "stats": {
            "period_return": round(period_return, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "data_points": len(history)
        }
    }


async def _generate_history_from_transactions(start_date: datetime):
    """Generate historical data from transactions when no snapshots exist"""
    
    # Get budget info
    budget = await _db.trading_budgets.find_one({"user_id": "default"}, {"_id": 0})
    if not budget:
        return []
    
    initial_budget = budget.get("initial_budget", 0)
    
    # Get transactions
    transactions = await _db.ai_transactions.find(
        {"timestamp": {"$gte": start_date.isoformat()}},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(1000)
    
    if not transactions:
        # Return current state as single point
        current_value = budget.get("cash_available", 0) + budget.get("positions_value", 0)
        return [{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_value": current_value,
            "invested": initial_budget,
            "pnl": current_value - initial_budget,
            "pnl_pct": ((current_value / initial_budget) - 1) * 100 if initial_budget > 0 else 0
        }]
    
    # Group by day and calculate running value
    history = []
    running_value = initial_budget
    
    for tx in transactions:
        ts = tx.get("timestamp")
        if isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except:
                continue
        else:
            continue
        
        # Simple approximation - buys reduce cash, sells increase
        if tx.get("type") == "buy":
            pass  # Value stays same (cash -> position)
        elif tx.get("type") == "sell":
            pnl = tx.get("pnl", 0)
            running_value += pnl
        
        history.append({
            "timestamp": dt.isoformat(),
            "total_value": running_value,
            "invested": initial_budget,
            "pnl": running_value - initial_budget,
            "pnl_pct": ((running_value / initial_budget) - 1) * 100 if initial_budget > 0 else 0
        })
    
    return history


@router.get("/summary")
async def get_portfolio_summary():
    """
    Get comprehensive portfolio summary with key metrics.
    """
    if _isolated_portfolio is None:
        raise HTTPException(status_code=503, detail="Portfolio manager not initialized")
    
    budget_status = await _isolated_portfolio.get_budget_status()
    positions = await _isolated_portfolio.get_ai_positions()
    
    if not budget_status.get("allocated"):
        return {
            "allocated": False,
            "message": "No budget allocated"
        }
    
    # Calculate metrics
    total_value = budget_status.get("current_value", 0)
    initial_budget = budget_status.get("initial_budget", 0)
    total_pnl = total_value - initial_budget
    pnl_pct = ((total_value / initial_budget) - 1) * 100 if initial_budget > 0 else 0
    
    # Best and worst performers
    positions_with_pnl = [(p, p.get("pnl_pct", 0)) for p in positions]
    positions_with_pnl.sort(key=lambda x: x[1], reverse=True)
    
    best_performer = None
    worst_performer = None
    
    if positions_with_pnl:
        best = positions_with_pnl[0]
        worst = positions_with_pnl[-1]
        
        best_performer = {
            "coin_id": best[0].get("coin_id", "").upper(),
            "pnl_pct": round(best[1], 2),
            "value": round(best[0].get("current_value", 0), 2)
        }
        
        worst_performer = {
            "coin_id": worst[0].get("coin_id", "").upper(),
            "pnl_pct": round(worst[1], 2),
            "value": round(worst[0].get("current_value", 0), 2)
        }
    
    # Gems count
    gems_count = sum(1 for p in positions if p.get("is_gem") or p.get("position_type") == "gem")
    
    # Average position size
    avg_position_size = (total_value - budget_status.get("cash_available", 0)) / len(positions) if positions else 0
    
    return {
        "allocated": True,
        "initial_budget": round(initial_budget, 2),
        "current_value": round(total_value, 2),
        "cash_available": round(budget_status.get("cash_available", 0), 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(pnl_pct, 2),
        "positions_count": len(positions),
        "gems_count": gems_count,
        "trades_executed": budget_status.get("trades_executed", 0),
        "best_performer": best_performer,
        "worst_performer": worst_performer,
        "avg_position_size": round(avg_position_size, 2),
        "real_trading_enabled": budget_status.get("real_trading_enabled", False)
    }


@router.get("/top-performers")
async def get_top_performers(limit: int = Query(5, ge=1, le=20)):
    """Get top performing positions"""
    if _isolated_portfolio is None:
        raise HTTPException(status_code=503, detail="Portfolio manager not initialized")
    
    positions = await _isolated_portfolio.get_ai_positions()
    
    # Sort by P&L percentage
    sorted_positions = sorted(positions, key=lambda x: x.get("pnl_pct", 0), reverse=True)
    
    top = []
    for pos in sorted_positions[:limit]:
        top.append({
            "coin_id": pos.get("coin_id", "").upper(),
            "symbol": pos.get("symbol", ""),
            "pnl_pct": round(pos.get("pnl_pct", 0), 2),
            "pnl_usd": round(pos.get("pnl_usd", 0), 2),
            "current_value": round(pos.get("current_value", 0), 2),
            "entry_value": round(pos.get("entry_value", 0), 2),
            "position_type": pos.get("position_type", "main"),
            "is_gem": pos.get("is_gem", False)
        })
    
    return {"top_performers": top}


@router.get("/worst-performers")
async def get_worst_performers(limit: int = Query(5, ge=1, le=20)):
    """Get worst performing positions"""
    if _isolated_portfolio is None:
        raise HTTPException(status_code=503, detail="Portfolio manager not initialized")
    
    positions = await _isolated_portfolio.get_ai_positions()
    
    # Sort by P&L percentage ascending
    sorted_positions = sorted(positions, key=lambda x: x.get("pnl_pct", 0))
    
    worst = []
    for pos in sorted_positions[:limit]:
        worst.append({
            "coin_id": pos.get("coin_id", "").upper(),
            "symbol": pos.get("symbol", ""),
            "pnl_pct": round(pos.get("pnl_pct", 0), 2),
            "pnl_usd": round(pos.get("pnl_usd", 0), 2),
            "current_value": round(pos.get("current_value", 0), 2),
            "entry_value": round(pos.get("entry_value", 0), 2),
            "position_type": pos.get("position_type", "main"),
            "is_gem": pos.get("is_gem", False)
        })
    
    return {"worst_performers": worst}


@router.post("/snapshot")
async def create_portfolio_snapshot():
    """
    Create a snapshot of current portfolio state.
    Called automatically by scheduler, can also be triggered manually.
    """
    if _isolated_portfolio is None or _db is None:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    budget_status = await _isolated_portfolio.get_budget_status()
    
    if not budget_status.get("allocated"):
        return {"success": False, "message": "No budget allocated"}
    
    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_value": budget_status.get("current_value", 0),
        "cash_available": budget_status.get("cash_available", 0),
        "positions_value": budget_status.get("positions_value", 0),
        "invested": budget_status.get("initial_budget", 0),
        "pnl": budget_status.get("current_value", 0) - budget_status.get("initial_budget", 0),
        "pnl_pct": budget_status.get("pnl_pct", 0),
        "positions_count": budget_status.get("positions_count", 0)
    }
    
    await _db.portfolio_snapshots.insert_one(snapshot)
    snapshot.pop("_id", None)
    
    return {"success": True, "snapshot": snapshot}



@router.get("/kraken-portfolio")
async def get_kraken_portfolio():
    """
    Get REAL Kraken portfolio balance with current prices.
    Shows actual holdings from Kraken account.
    """
    import os
    import httpx
    
    kraken_api_key = os.getenv('KRAKEN_API_KEY')
    kraken_api_secret = os.getenv('KRAKEN_API_SECRET')
    
    if not kraken_api_key or not kraken_api_secret:
        return {
            "connected": False,
            "message": "Kraken API keys not configured",
            "total_value_usd": 0,
            "holdings": []
        }
    
    try:
        from services.kraken_service import KrakenAuthenticator, KrakenTradeService
        auth = KrakenAuthenticator(kraken_api_key, kraken_api_secret)
        kraken = KrakenTradeService(auth)
        
        # Get balance
        balance = await kraken.get_balance()
        
        # Filter out zero balances and format holdings
        holdings = []
        total_usd = 0
        
        # Symbol mapping for price lookup - Kraken uses different formats
        symbol_map = {
            'XXBT': 'BTC', 'XETH': 'ETH', 'XXRP': 'XRP', 'XLTC': 'LTC',
            'XXLM': 'XLM', 'XDOGE': 'DOGE', 'ZUSD': 'USD', 'USDT': 'USDT',
            'XXDG': 'DOGE', 'XZEC': 'ZEC', 'XREP': 'REP', 'XMLN': 'MLN'
        }
        
        # Kraken pair format mapping for price lookup
        pair_formats = {
            'BTC': 'XXBTZUSD', 'ETH': 'XETHZUSD', 'XRP': 'XXRPZUSD',
            'LTC': 'XLTCZUSD', 'XLM': 'XXLMZUSD', 'DOGE': 'XDGUSD',
            'SOL': 'SOLUSD', 'DOT': 'DOTUSD', 'AAVE': 'AAVEUSD',
            'UNI': 'UNIUSD', 'LINK': 'LINKUSD', 'MATIC': 'MATICUSD',
            'APT': 'APTUSD', 'SUI': 'SUIUSD', 'AVAX': 'AVAXUSD',
            'ADA': 'ADAUSD', 'ATOM': 'ATOMUSD', 'NEAR': 'NEARUSD',
            'ARB': 'ARBUSD', 'OP': 'OPUSD', 'FTM': 'FTMUSD'
        }
        
        for asset, amount in balance.items():
            amount_float = float(amount)
            if amount_float < 0.00001:
                continue
            
            # Normalize asset symbol
            normalized = symbol_map.get(asset, asset.replace('X', '').replace('Z', '').replace('.S', ''))
            
            # USD and stablecoins are 1:1
            if normalized in ['USD', 'USDT', 'USDC', 'USDG', 'DAI']:
                value_usd = amount_float
                price = 1.0
            else:
                # Get price from Kraken - try multiple pair formats
                price = 0
                pairs_to_try = [
                    pair_formats.get(normalized, f"{normalized}USD"),
                    f"{normalized}USD",
                    f"X{normalized}ZUSD",
                    f"{asset}ZUSD",
                    f"{asset}USD"
                ]
                
                for pair in pairs_to_try:
                    try:
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            response = await client.get(
                                "https://api.kraken.com/0/public/Ticker",
                                params={"pair": pair}
                            )
                            data = response.json()
                            if data.get("result") and not data.get("error"):
                                for key, ticker in data["result"].items():
                                    price = float(ticker['c'][0])
                                    break
                                if price > 0:
                                    break
                    except:
                        continue
                
                value_usd = amount_float * price
            
            total_usd += value_usd
            
            holdings.append({
                "asset": normalized,
                "original_asset": asset,
                "amount": round(amount_float, 8),
                "price_usd": round(price, 4),
                "value_usd": round(value_usd, 2),
                "percentage": 0  # Will be calculated below
            })
        
        # Calculate percentages
        for h in holdings:
            h["percentage"] = round((h["value_usd"] / total_usd * 100) if total_usd > 0 else 0, 2)
        
        # Sort by value
        holdings.sort(key=lambda x: x["value_usd"], reverse=True)
        
        return {
            "connected": True,
            "total_value_usd": round(total_usd, 2),
            "holdings_count": len(holdings),
            "holdings": holdings,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "total_value_usd": 0,
            "holdings": []
        }



# Global scheduler reference for snapshot management
_scheduler = None


def set_scheduler(scheduler_service):
    """Set scheduler reference for snapshot scheduling"""
    global _scheduler
    _scheduler = scheduler_service


@router.post("/snapshot/schedule")
async def setup_automatic_snapshots(
    interval_hours: int = Query(24, ge=1, le=168, description="Interval in hours (1-168)"),
    hour: int = Query(0, ge=0, le=23, description="Hour of day for daily snapshots (0-23)")
):
    """
    Setup automatic portfolio snapshots.
    
    Options:
    - interval_hours=24, hour=0: Daily at midnight UTC (default)
    - interval_hours=24, hour=8: Daily at 8 AM UTC
    - interval_hours=6: Every 6 hours
    - interval_hours=1: Hourly (for active trading)
    
    Snapshots build up the performance history chart automatically.
    """
    if _scheduler is None:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    
    result = await _scheduler.add_portfolio_snapshot_job(
        interval_hours=interval_hours,
        hour=hour
    )
    
    return {
        **result,
        "message": f"Automatic snapshots scheduled: {result.get('schedule')}",
        "note": "Snapshots will populate the performance history chart over time"
    }


@router.get("/snapshot/schedule")
async def get_snapshot_schedule():
    """Get current snapshot schedule status"""
    if _scheduler is None:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    
    status = _scheduler.get_status()
    
    # Find snapshot job
    snapshot_job = None
    for job in status.get('jobs', []):
        if job.get('id') == 'portfolio_snapshot':
            snapshot_job = job
            break
    
    active_config = _scheduler.active_jobs.get('portfolio_snapshot', None)
    
    return {
        "scheduled": snapshot_job is not None,
        "job": snapshot_job,
        "config": active_config,
        "scheduler_running": status.get('running', False)
    }


@router.delete("/snapshot/schedule")
async def remove_snapshot_schedule():
    """Remove automatic snapshot scheduling"""
    if _scheduler is None:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    
    job_id = 'portfolio_snapshot'
    
    if _scheduler.scheduler.get_job(job_id):
        _scheduler.scheduler.remove_job(job_id)
        _scheduler.active_jobs.pop(job_id, None)
        return {"success": True, "message": "Snapshot schedule removed"}
    
    return {"success": False, "message": "No snapshot schedule found"}


@router.get("/snapshot/history")
async def get_snapshot_history(limit: int = Query(100, ge=1, le=1000)):
    """Get history of portfolio snapshots"""
    if _db is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    snapshots = await _db.portfolio_snapshots.find(
        {}, {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return {
        "count": len(snapshots),
        "snapshots": snapshots
    }


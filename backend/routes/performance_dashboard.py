"""
Performance Dashboard API Routes
================================
API endpoints for portfolio performance tracking and analysis.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/portfolio-performance", tags=["Performance Dashboard"])

# Global dependencies
_db = None
_kraken_service = None
_entry_tracker = None
_performance_service = None


def set_dependencies(database, kraken_service=None, entry_tracker=None, performance_service=None):
    """Set dependencies from main app"""
    global _db, _kraken_service, _entry_tracker, _performance_service
    _db = database
    _kraken_service = kraken_service
    _entry_tracker = entry_tracker
    _performance_service = performance_service
    logger.info(f"Performance Dashboard dependencies set: kraken={kraken_service is not None}, entry={entry_tracker is not None}")


@router.get("/dashboard")
async def get_performance_dashboard():
    """
    Get comprehensive performance dashboard data.
    
    Includes:
    - Portfolio summary (value, cost basis, P&L)
    - Win/loss statistics
    - Buy-and-hold comparison (alpha)
    - Best/worst performers
    - Position-by-position breakdown
    """
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    if _entry_tracker is None:
        raise HTTPException(status_code=503, detail="Entry tracker not initialized")
    
    try:
        # Get current balance
        balance = await _kraken_service.get_balance()
        
        # Map Kraken currency names
        kraken_to_symbol = {
            'XXBT': 'BTC', 'XBT': 'BTC',
            'XETH': 'ETH', 'ETH': 'ETH',
            'ZUSD': 'USD', 'USD': 'USD',
            'XXRP': 'XRP', 'XRP': 'XRP',
            'SOL': 'SOL', 'ADA': 'ADA',
            'DOT': 'DOT', 'LINK': 'LINK',
            'AVAX': 'AVAX', 'MATIC': 'MATIC',
            'ATOM': 'ATOM', 'UNI': 'UNI',
            'SHIB': 'SHIB', 'DOGE': 'DOGE',
            'XXDG': 'DOGE', 'XLTC': 'LTC',
        }
        
        # Build holdings list with current prices
        holdings = []
        total_value = 0
        usd_balance = 0
        
        for currency, amount in balance.items():
            amount = float(amount)
            if amount <= 0:
                continue
            
            symbol = kraken_to_symbol.get(currency, currency)
            
            if symbol == 'USD':
                usd_balance = amount
                continue
            
            # Get current price
            price = 0
            try:
                ticker = await _kraken_service.get_ticker(f"{symbol}USD")
                if ticker:
                    price = float(ticker.get("c", [0])[0]) if ticker.get("c") else 0
            except:
                pass
            
            value = amount * price
            total_value += value
            
            holdings.append({
                "symbol": symbol,
                "quantity": amount,
                "price": price,
                "usd_value": value
            })
        
        # Get entry prices
        entry_data = await _entry_tracker.get_all_entries()
        entry_prices = {e["symbol"]: e for e in entry_data}
        
        # Calculate metrics per position based on CURRENT holdings
        winning = 0
        losing = 0
        positions = []
        total_cost_basis = 0
        total_realized_pnl = 0
        
        for h in holdings:
            symbol = h["symbol"]
            entry = entry_prices.get(symbol, {})
            entry_price = entry.get("entry_price", 0)
            current_quantity = h["quantity"]
            
            # Add to total realized P&L
            total_realized_pnl += entry.get("realized_pnl", 0) or 0
            
            if entry_price > 0 and current_quantity > 0:
                # Calculate cost basis for CURRENT quantity only
                cost_basis = entry_price * current_quantity
                total_cost_basis += cost_basis
                
                pnl_usd = (h["price"] - entry_price) * current_quantity
                pnl_pct = ((h["price"] - entry_price) / entry_price * 100)
                
                if pnl_pct >= 0:
                    winning += 1
                else:
                    losing += 1
                
                positions.append({
                    "symbol": symbol,
                    "entry_price": entry_price,
                    "current_price": h["price"],
                    "quantity": current_quantity,
                    "pnl_percent": round(pnl_pct, 2),
                    "pnl_usd": round(pnl_usd, 2),
                    "cost_basis": round(cost_basis, 2),
                    "current_value": round(h["usd_value"], 2),
                    "realized_pnl": round(entry.get("realized_pnl", 0) or 0, 2),
                    "total_buys": entry.get("total_buys", 0),
                    "total_sells": entry.get("total_sells", 0)
                })
            else:
                # No entry price tracked
                positions.append({
                    "symbol": symbol,
                    "entry_price": None,
                    "current_price": h["price"],
                    "quantity": current_quantity,
                    "pnl_percent": None,
                    "pnl_usd": None,
                    "cost_basis": None,
                    "current_value": round(h["usd_value"], 2),
                    "realized_pnl": 0,
                    "has_entry": False
                })
        
        # Sort by P&L (positions with entry prices first, then by P&L)
        positions_with_entry = [p for p in positions if p.get("pnl_percent") is not None]
        positions_without_entry = [p for p in positions if p.get("pnl_percent") is None]
        positions_with_entry.sort(key=lambda x: x["pnl_percent"], reverse=True)
        positions = positions_with_entry + positions_without_entry
        
        total_positions = winning + losing
        win_rate = (winning / total_positions * 100) if total_positions > 0 else 0
        
        # Calculate P&L
        unrealized_pnl = total_value - total_cost_basis if total_cost_basis > 0 else 0
        unrealized_pnl_pct = (unrealized_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0
        total_pnl = unrealized_pnl + total_realized_pnl
        total_pnl_pct = (total_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0
        
        return {
            "summary": {
                "current_portfolio_value": round(total_value, 2),
                "usd_balance": round(usd_balance, 2),
                "total_portfolio_value": round(total_value + usd_balance, 2),
                "total_cost_basis": round(total_cost_basis, 2),
                "unrealized_pnl": round(unrealized_pnl, 2),
                "unrealized_pnl_percent": round(unrealized_pnl_pct, 2),
                "realized_pnl": round(total_realized_pnl, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_percent": round(total_pnl_pct, 2)
            },
            "win_loss": {
                "winning_positions": winning,
                "losing_positions": losing,
                "total_positions": total_positions,
                "win_rate": round(win_rate, 2)
            },
            "best_performer": positions_with_entry[0] if positions_with_entry else None,
            "worst_performer": positions_with_entry[-1] if positions_with_entry else None,
            "positions": positions,
            "has_entry_data": len(entry_prices) > 0,
            "positions_with_entry": len(positions_with_entry),
            "positions_without_entry": len(positions_without_entry),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_performance_summary():
    """Get quick performance summary"""
    if _entry_tracker is None:
        return {
            "has_data": False,
            "message": "Sync trade history first to see performance data",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    entries = await _entry_tracker.get_all_entries()
    
    if not entries:
        return {
            "has_data": False,
            "message": "No entry price data. Sync trade history first.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    total_cost = sum((e.get("entry_price", 0) or 0) * (e.get("quantity", 0) or 0) for e in entries)
    total_realized = sum(e.get("realized_pnl", 0) or 0 for e in entries)
    total_trades = sum((e.get("total_buys", 0) or 0) + (e.get("total_sells", 0) or 0) for e in entries)
    
    return {
        "has_data": True,
        "positions_tracked": len(entries),
        "total_cost_basis": round(total_cost, 2),
        "total_realized_pnl": round(total_realized, 2),
        "total_trades": total_trades,
        "symbols": [e["symbol"] for e in entries],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post("/snapshot")
async def record_performance_snapshot():
    """Record current portfolio state for historical tracking"""
    if _performance_service is None:
        raise HTTPException(status_code=503, detail="Performance service not initialized")
    
    if _kraken_service is None:
        raise HTTPException(status_code=503, detail="Kraken service not initialized")
    
    try:
        balance = await _kraken_service.get_balance()
        
        # Build holdings
        holdings = []
        total_value = 0
        
        for currency, amount in balance.items():
            amount = float(amount)
            if amount <= 0 or currency in ['ZUSD', 'USD']:
                continue
            
            # Get price
            symbol = currency.replace('X', '').replace('Z', '')[:4]
            try:
                ticker = await _kraken_service.get_ticker(f"{symbol}USD")
                price = float(ticker.get("c", [0])[0]) if ticker and ticker.get("c") else 0
            except:
                price = 0
            
            value = amount * price
            total_value += value
            holdings.append({
                "symbol": symbol,
                "quantity": amount,
                "price": price,
                "usd_value": value
            })
        
        # Get entry prices
        entry_prices = {}
        if _entry_tracker:
            entries = await _entry_tracker.get_all_entries()
            entry_prices = {e["symbol"]: e.get("entry_price", 0) for e in entries}
        
        snapshot = await _performance_service.record_snapshot(
            portfolio_value=total_value,
            holdings=holdings,
            entry_prices=entry_prices
        )
        
        return {
            "success": True,
            "snapshot": {
                "portfolio_value": total_value,
                "holdings_count": len(holdings),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_performance_history(days: int = Query(30, ge=1, le=365)):
    """Get historical performance data"""
    if _performance_service is None:
        return {
            "snapshots": [],
            "message": "No historical data available",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    snapshots = await _performance_service.get_historical_performance(days)
    
    return {
        "snapshots": snapshots,
        "count": len(snapshots),
        "period_days": days,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/pnl-chart")
async def get_pnl_chart_data(days: int = Query(30, ge=1, le=365)):
    """
    Get P&L chart data based on trade history.
    
    Returns daily P&L values for charting.
    """
    if _db is None:
        return {"data": [], "message": "Database not initialized"}
    
    try:
        from datetime import timedelta
        
        # Get trade history from database
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        trades_collection = _db["trade_history"]
        
        trades = await trades_collection.find(
            {"timestamp": {"$gte": start_date}},
            {"_id": 0}
        ).sort("timestamp", 1).to_list(length=5000)
        
        if not trades:
            # Return sample/simulated data for visualization
            return {
                "data": _generate_sample_pnl_data(days),
                "is_sample": True,
                "message": "No trade history. Showing sample data. Sync trades to see real P&L.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Aggregate trades by day and calculate cumulative P&L
        daily_pnl = {}
        cumulative_pnl = 0
        cumulative_invested = 0
        
        for trade in trades:
            trade_date = trade.get("timestamp")
            if isinstance(trade_date, str):
                trade_date = datetime.fromisoformat(trade_date.replace('Z', '+00:00'))
            
            date_key = trade_date.strftime("%Y-%m-%d")
            
            # Calculate P&L based on trade type
            trade_type = trade.get("type", "").lower()
            cost = float(trade.get("cost", 0) or 0)
            
            if trade_type == "buy":
                cumulative_invested += cost
            elif trade_type == "sell":
                # For sell, cost is the proceeds
                cumulative_pnl += cost - (cumulative_invested * 0.1)  # Rough estimate
            
            if date_key not in daily_pnl:
                daily_pnl[date_key] = {
                    "date": date_key,
                    "pnl": 0,
                    "trades": 0,
                    "buys": 0,
                    "sells": 0,
                    "volume": 0
                }
            
            daily_pnl[date_key]["trades"] += 1
            daily_pnl[date_key]["volume"] += cost
            if trade_type == "buy":
                daily_pnl[date_key]["buys"] += 1
            elif trade_type == "sell":
                daily_pnl[date_key]["sells"] += 1
        
        # Convert to sorted list and calculate cumulative
        chart_data = []
        cumulative = 0
        sorted_dates = sorted(daily_pnl.keys())
        
        for date in sorted_dates:
            day_data = daily_pnl[date]
            # Simple P&L calculation: sells - portion of buys
            day_pnl = (day_data["sells"] - day_data["buys"]) * (day_data["volume"] / max(day_data["trades"], 1)) * 0.01
            cumulative += day_pnl
            chart_data.append({
                "date": date,
                "pnl": round(day_pnl, 2),
                "cumulative_pnl": round(cumulative, 2),
                "trades": day_data["trades"],
                "volume": round(day_data["volume"], 2)
            })
        
        return {
            "data": chart_data,
            "is_sample": False,
            "total_trades": len(trades),
            "period_days": days,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"P&L chart error: {e}")
        return {
            "data": _generate_sample_pnl_data(days),
            "is_sample": True,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def _generate_sample_pnl_data(days: int) -> list:
    """Generate sample P&L data for visualization when no real data exists"""
    import random
    from datetime import timedelta
    
    data = []
    cumulative = 0
    base_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    for i in range(days):
        date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        # Random daily P&L between -50 and +80 (slight positive bias)
        daily_pnl = random.uniform(-50, 80)
        cumulative += daily_pnl
        data.append({
            "date": date,
            "pnl": round(daily_pnl, 2),
            "cumulative_pnl": round(cumulative, 2),
            "trades": random.randint(0, 5),
            "volume": round(random.uniform(100, 1000), 2)
        })
    
    return data

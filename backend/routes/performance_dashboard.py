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
router = APIRouter(prefix="/performance", tags=["Performance Dashboard"])

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
        
        # Calculate total cost basis and realized P&L
        total_cost_basis = 0
        total_realized_pnl = 0
        
        for entry in entry_data:
            cost = (entry.get("entry_price", 0) or 0) * (entry.get("quantity", 0) or 0)
            total_cost_basis += cost
            total_realized_pnl += entry.get("realized_pnl", 0) or 0
        
        # Calculate performance metrics
        if _performance_service:
            metrics = await _performance_service.get_performance_metrics(
                current_portfolio_value=total_value,
                total_cost_basis=total_cost_basis,
                total_realized_pnl=total_realized_pnl,
                holdings=holdings,
                entry_prices=entry_prices
            )
        else:
            # Calculate basic metrics without service
            unrealized_pnl = total_value - total_cost_basis if total_cost_basis > 0 else 0
            total_pnl = unrealized_pnl + total_realized_pnl
            
            # Calculate per-position
            winning = 0
            losing = 0
            positions = []
            
            for h in holdings:
                entry = entry_prices.get(h["symbol"], {})
                entry_price = entry.get("entry_price", 0)
                
                if entry_price > 0:
                    pnl_pct = ((h["price"] - entry_price) / entry_price * 100)
                    pnl_usd = (h["price"] - entry_price) * h["quantity"]
                    
                    if pnl_pct >= 0:
                        winning += 1
                    else:
                        losing += 1
                    
                    positions.append({
                        "symbol": h["symbol"],
                        "entry_price": entry_price,
                        "current_price": h["price"],
                        "quantity": h["quantity"],
                        "pnl_percent": round(pnl_pct, 2),
                        "pnl_usd": round(pnl_usd, 2),
                        "cost_basis": entry_price * h["quantity"],
                        "current_value": h["usd_value"],
                        "realized_pnl": entry.get("realized_pnl", 0)
                    })
            
            total_positions = winning + losing
            win_rate = (winning / total_positions * 100) if total_positions > 0 else 0
            
            # Sort by P&L
            positions.sort(key=lambda x: x["pnl_percent"], reverse=True)
            
            metrics = {
                "summary": {
                    "current_portfolio_value": round(total_value, 2),
                    "usd_balance": round(usd_balance, 2),
                    "total_portfolio_value": round(total_value + usd_balance, 2),
                    "total_cost_basis": round(total_cost_basis, 2),
                    "unrealized_pnl": round(unrealized_pnl, 2),
                    "unrealized_pnl_percent": round((unrealized_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0, 2),
                    "realized_pnl": round(total_realized_pnl, 2),
                    "total_pnl": round(total_pnl, 2),
                    "total_pnl_percent": round((total_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0, 2)
                },
                "win_loss": {
                    "winning_positions": winning,
                    "losing_positions": losing,
                    "total_positions": total_positions,
                    "win_rate": round(win_rate, 2)
                },
                "comparison": {
                    "buy_hold_value": round(total_cost_basis, 2),
                    "buy_hold_current": round(total_value, 2),
                    "buy_hold_pnl": round(unrealized_pnl, 2),
                    "buy_hold_pnl_percent": round((unrealized_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0, 2),
                    "alpha": 0,
                    "outperforming": False
                },
                "best_performer": positions[0] if positions else None,
                "worst_performer": positions[-1] if positions else None,
                "positions": positions,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Add extra context
        metrics["has_entry_data"] = len(entry_prices) > 0
        metrics["positions_with_entry"] = len([p for p in metrics.get("positions", []) if p.get("entry_price")])
        metrics["positions_without_entry"] = len(holdings) - metrics["positions_with_entry"]
        
        return metrics
        
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

"""
Export API Routes
=================
Export trades, portfolio data to CSV/Excel formats.
"""

import logging
import csv
import io
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["Export"])

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


@router.get("/trades-csv")
async def export_trades_csv(
    user_id: str = "default_user",
    days: int = Query(30, ge=1, le=365),
    coin: Optional[str] = None,
    db = Depends(get_database)
):
    """Export trade history to CSV file"""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    query = {
        "user_id": user_id,
        "executed_at": {"$gte": start_date.isoformat()}
    }
    if coin:
        query["symbol"] = {"$regex": coin, "$options": "i"}
    
    trades = await db.trade_history.find(query, {"_id": 0}).sort("executed_at", -1).to_list(10000)
    
    if not trades:
        # Return empty CSV with headers
        trades = []
    
    # Create CSV in memory
    output = io.StringIO()
    fieldnames = [
        "date", "time", "symbol", "side", "quantity", "price", 
        "amount_usd", "fee", "pnl", "pnl_percent", "strategy", "notes"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for trade in trades:
        exec_time = trade.get("executed_at", "")
        if isinstance(exec_time, str) and exec_time:
            try:
                dt = datetime.fromisoformat(exec_time.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
                time_str = dt.strftime("%H:%M:%S")
            except:
                date_str = exec_time[:10] if len(exec_time) > 10 else exec_time
                time_str = exec_time[11:19] if len(exec_time) > 19 else ""
        else:
            date_str = ""
            time_str = ""
        
        writer.writerow({
            "date": date_str,
            "time": time_str,
            "symbol": trade.get("symbol", ""),
            "side": trade.get("side", ""),
            "quantity": trade.get("quantity", 0),
            "price": trade.get("price", 0),
            "amount_usd": trade.get("amount_usd", 0),
            "fee": trade.get("fee", 0),
            "pnl": trade.get("pnl", 0),
            "pnl_percent": trade.get("pnl_percent", 0),
            "strategy": trade.get("strategy", "manual"),
            "notes": trade.get("notes", "")
        })
    
    output.seek(0)
    
    filename = f"trades_{user_id}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/portfolio-csv")
async def export_portfolio_csv(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Export current portfolio to CSV"""
    # Get portfolio data
    portfolio = await db.portfolios.find_one({"user_id": user_id}, {"_id": 0})
    
    output = io.StringIO()
    fieldnames = ["asset", "quantity", "avg_price", "current_price", "value_usd", "pnl", "pnl_percent", "allocation"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    if portfolio and portfolio.get("holdings"):
        total_value = sum(h.get("value_usd", 0) for h in portfolio["holdings"])
        for holding in portfolio["holdings"]:
            value = holding.get("value_usd", 0)
            writer.writerow({
                "asset": holding.get("asset", ""),
                "quantity": holding.get("quantity", 0),
                "avg_price": holding.get("avg_price", 0),
                "current_price": holding.get("current_price", 0),
                "value_usd": value,
                "pnl": holding.get("pnl", 0),
                "pnl_percent": holding.get("pnl_percent", 0),
                "allocation": round(value / total_value * 100, 2) if total_value > 0 else 0
            })
    
    output.seek(0)
    filename = f"portfolio_{user_id}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/pnl-report")
async def export_pnl_report(
    user_id: str = "default_user",
    year: int = Query(default=None),
    db = Depends(get_database)
):
    """Export P&L report for tax purposes"""
    if year is None:
        year = datetime.now().year
    
    start_date = datetime(year, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    
    trades = await db.trade_history.find({
        "user_id": user_id,
        "executed_at": {
            "$gte": start_date.isoformat(),
            "$lte": end_date.isoformat()
        }
    }, {"_id": 0}).sort("executed_at", 1).to_list(50000)
    
    output = io.StringIO()
    fieldnames = [
        "date", "asset", "type", "quantity", "cost_basis", 
        "proceeds", "gain_loss", "holding_period", "term"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    total_short_term = 0
    total_long_term = 0
    
    for trade in trades:
        if trade.get("side", "").upper() == "SELL":
            pnl = trade.get("pnl", 0)
            # Assume short-term for simplicity (holding period tracking would need enhancement)
            term = "short-term"
            total_short_term += pnl
            
            exec_time = trade.get("executed_at", "")
            try:
                dt = datetime.fromisoformat(exec_time.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
            except:
                date_str = exec_time[:10] if len(exec_time) > 10 else exec_time
            
            writer.writerow({
                "date": date_str,
                "asset": trade.get("symbol", ""),
                "type": "SALE",
                "quantity": trade.get("quantity", 0),
                "cost_basis": trade.get("amount_usd", 0) - pnl,
                "proceeds": trade.get("amount_usd", 0),
                "gain_loss": pnl,
                "holding_period": "<1 year",
                "term": term
            })
    
    # Add summary row
    writer.writerow({})
    writer.writerow({
        "date": "SUMMARY",
        "asset": f"Year {year}",
        "type": "",
        "quantity": "",
        "cost_basis": "",
        "proceeds": "",
        "gain_loss": total_short_term + total_long_term,
        "holding_period": "",
        "term": f"ST: ${total_short_term:.2f}, LT: ${total_long_term:.2f}"
    })
    
    output.seek(0)
    filename = f"pnl_report_{year}_{user_id}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

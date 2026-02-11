"""
CSV Export API Routes
Provides functionality to export trading data, portfolio, and performance metrics to CSV format
"""

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from typing import Optional, List
from datetime import datetime, timedelta
from io import StringIO
import csv
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/export", tags=["Export"])

# Global database reference
_db = None


def set_dependencies(database):
    """Set database dependency from main app"""
    global _db
    _db = database


@router.get("/trades/csv")
async def export_trades_csv(
    user_id: str = Query(..., description="User ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    mode: Optional[str] = Query(None, description="Trading mode filter (paper/real)")
):
    """
    Export trade history to CSV format
    
    Returns:
        CSV file with columns: timestamp, coin_pair, action, amount, price, total_value, mode, status, profit_loss
    """
    try:
        if _db is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Build query filter
        query_filter = {"user_id": user_id}
        
        # Add date filters if provided
        if start_date or end_date:
            date_filter = {}
            if start_date:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                date_filter["$gte"] = start_dt
            if end_date:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                date_filter["$lt"] = end_dt
            query_filter["timestamp"] = date_filter
        
        # Add mode filter if provided
        if mode:
            query_filter["mode"] = mode
        
        # Fetch trades from database
        trades = await _db.trades.find(query_filter).sort("timestamp", -1).to_list(length=10000)
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Timestamp",
            "Coin Pair",
            "Action",
            "Amount",
            "Price",
            "Total Value",
            "Mode",
            "Status",
            "Profit/Loss",
            "Fee",
            "Trade ID"
        ])
        
        # Write data rows
        for trade in trades:
            writer.writerow([
                trade.get("timestamp", "").isoformat() if isinstance(trade.get("timestamp"), datetime) else trade.get("timestamp", ""),
                trade.get("coin_pair", ""),
                trade.get("action", ""),
                trade.get("amount", 0),
                trade.get("price", 0),
                trade.get("total_value", 0),
                trade.get("mode", "paper"),
                trade.get("status", "pending"),
                trade.get("profit_loss", 0),
                trade.get("fee", 0),
                str(trade.get("_id", trade.get("trade_id", "")))
            ])
        
        # Create response
        output.seek(0)
        filename = f"trades_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error exporting trades: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export trades: {str(e)}")


@router.get("/portfolio/csv")
async def export_portfolio_csv(
    user_id: str = Query(..., description="User ID")
):
    """
    Export current portfolio holdings to CSV format
    
    Returns:
        CSV file with columns: asset, symbol, amount, current_price, total_value, allocation_percent, profit_loss
    """
    try:
        if _db is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Fetch portfolio data
        portfolio = await _db.portfolios.find_one({"user_id": user_id})
        
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Asset",
            "Symbol",
            "Amount",
            "Current Price (USD)",
            "Total Value (USD)",
            "Allocation %",
            "24h Change %",
            "Profit/Loss"
        ])
        
        # Calculate totals
        assets = portfolio.get("assets", [])
        total_value = sum(asset.get("value", 0) for asset in assets)
        
        # Write data rows
        for asset in assets:
            allocation = (asset.get("value", 0) / total_value * 100) if total_value > 0 else 0
            writer.writerow([
                asset.get("name", ""),
                asset.get("symbol", ""),
                asset.get("amount", 0),
                asset.get("price", 0),
                asset.get("value", 0),
                f"{allocation:.2f}",
                asset.get("change_24h", 0),
                asset.get("profit_loss", 0)
            ])
        
        # Add summary row
        writer.writerow([])
        writer.writerow(["TOTAL", "", "", "", total_value, "100.00", "", ""])
        
        # Create response
        output.seek(0)
        filename = f"portfolio_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export portfolio: {str(e)}")


@router.get("/performance/csv")
async def export_performance_csv(
    user_id: str = Query(..., description="User ID"),
    days: int = Query(30, description="Number of days to export (default: 30)")
):
    """
    Export performance history to CSV format
    
    Returns:
        CSV file with columns: date, portfolio_value, profit_loss, profit_loss_percent, daily_return, trades_count
    """
    try:
        if _db is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Fetch performance data
        performance_data = await _db.performance_history.find({
            "user_id": user_id,
            "date": {"$gte": start_date, "$lte": end_date}
        }).sort("date", 1).to_list(length=1000)
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Date",
            "Portfolio Value (USD)",
            "Profit/Loss (USD)",
            "Profit/Loss %",
            "Daily Return %",
            "Trades Count",
            "Win Rate %"
        ])
        
        # Write data rows
        for record in performance_data:
            writer.writerow([
                record.get("date", "").strftime("%Y-%m-%d") if isinstance(record.get("date"), datetime) else record.get("date", ""),
                record.get("portfolio_value", 0),
                record.get("profit_loss", 0),
                record.get("profit_loss_percent", 0),
                record.get("daily_return", 0),
                record.get("trades_count", 0),
                record.get("win_rate", 0)
            ])
        
        # Create response
        output.seek(0)
        filename = f"performance_{user_id}_{days}days_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export performance: {str(e)}")


@router.get("/strategies/csv")
async def export_strategies_csv(
    user_id: str = Query(..., description="User ID")
):
    """
    Export AI strategies to CSV format
    
    Returns:
        CSV file with columns: strategy_name, coin, action, confidence, indicators, created_date, status
    """
    try:
        if _db is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Fetch strategies
        strategies = await _db.strategies.find({
            "user_id": user_id
        }).sort("created_at", -1).to_list(length=1000)
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Strategy Name",
            "Coin",
            "Action",
            "Confidence %",
            "Key Indicators",
            "Entry Price",
            "Target Price",
            "Stop Loss",
            "Created Date",
            "Status",
            "Strategy ID"
        ])
        
        # Write data rows
        for strategy in strategies:
            indicators = ", ".join(strategy.get("indicators", [])) if isinstance(strategy.get("indicators"), list) else ""
            writer.writerow([
                strategy.get("name", ""),
                strategy.get("coin", ""),
                strategy.get("action", ""),
                strategy.get("confidence", 0),
                indicators,
                strategy.get("entry_price", 0),
                strategy.get("target_price", 0),
                strategy.get("stop_loss", 0),
                strategy.get("created_at", "").isoformat() if isinstance(strategy.get("created_at"), datetime) else strategy.get("created_at", ""),
                strategy.get("status", "active"),
                str(strategy.get("_id", strategy.get("strategy_id", "")))
            ])
        
        # Create response
        output.seek(0)
        filename = f"strategies_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting strategies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export strategies: {str(e)}")

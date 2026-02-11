"""
Tax Reporting API Routes
=========================
Generate tax reports, calculate gains/losses.
"""

import logging
import csv
import io
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tax", tags=["Tax Reporting"])

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


class TaxSettings(BaseModel):
    cost_basis_method: str = "fifo"  # fifo, lifo, hifo, average
    country: str = "US"
    tax_year: int = 2025
    include_fees: bool = True


@router.get("/summary")
async def get_tax_summary(
    year: int = Query(default=None),
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get tax summary for a year"""
    if year is None:
        year = datetime.now().year
    
    start_date = datetime(year, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    
    # Get all trades for the year
    trades = await db.trade_history.find({
        "user_id": user_id,
        "executed_at": {
            "$gte": start_date.isoformat(),
            "$lte": end_date.isoformat()
        }
    }, {"_id": 0}).to_list(50000)
    
    # Calculate summary
    total_proceeds = 0
    total_cost_basis = 0
    short_term_gains = 0
    long_term_gains = 0
    total_fees = 0
    
    disposals = []  # Sells
    acquisitions = []  # Buys
    
    for trade in trades:
        side = trade.get("side", "").upper()
        amount = trade.get("amount_usd", 0)
        pnl = trade.get("pnl", 0)
        fee = trade.get("fee", 0)
        
        total_fees += fee
        
        if side == "SELL":
            total_proceeds += amount
            total_cost_basis += (amount - pnl)
            # Assume short-term for simplicity
            short_term_gains += pnl
            disposals.append(trade)
        elif side == "BUY":
            acquisitions.append(trade)
    
    net_gain_loss = short_term_gains + long_term_gains
    
    # Estimated tax (simplified US tax calculation)
    short_term_tax_rate = 0.35  # Assume 35% bracket
    long_term_tax_rate = 0.15
    
    estimated_tax = (
        max(0, short_term_gains) * short_term_tax_rate +
        max(0, long_term_gains) * long_term_tax_rate
    )
    
    return {
        "year": year,
        "summary": {
            "total_proceeds": round(total_proceeds, 2),
            "total_cost_basis": round(total_cost_basis, 2),
            "net_gain_loss": round(net_gain_loss, 2),
            "short_term_gains": round(short_term_gains, 2),
            "long_term_gains": round(long_term_gains, 2),
            "total_fees": round(total_fees, 2),
            "estimated_tax": round(estimated_tax, 2)
        },
        "stats": {
            "total_trades": len(trades),
            "disposals": len(disposals),
            "acquisitions": len(acquisitions)
        },
        "warning": "This is an estimate. Consult a tax professional for accurate filing."
    }


@router.get("/report/8949")
async def generate_form_8949(
    year: int = Query(default=None),
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Generate IRS Form 8949 compatible data"""
    if year is None:
        year = datetime.now().year
    
    start_date = datetime(year, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    
    trades = await db.trade_history.find({
        "user_id": user_id,
        "side": {"$in": ["sell", "SELL"]},
        "executed_at": {
            "$gte": start_date.isoformat(),
            "$lte": end_date.isoformat()
        }
    }, {"_id": 0}).sort("executed_at", 1).to_list(50000)
    
    # Format for Form 8949
    part_i = []  # Short-term (held <= 1 year)
    part_ii = []  # Long-term (held > 1 year)
    
    for trade in trades:
        exec_time = trade.get("executed_at", "")
        try:
            dt = datetime.fromisoformat(exec_time.replace("Z", "+00:00"))
            date_sold = dt.strftime("%m/%d/%Y")
        except:
            date_sold = ""
        
        entry = {
            "description": trade.get("symbol", "CRYPTO"),
            "date_acquired": "Various",
            "date_sold": date_sold,
            "proceeds": round(trade.get("amount_usd", 0), 2),
            "cost_basis": round(trade.get("amount_usd", 0) - trade.get("pnl", 0), 2),
            "adjustment_code": "",
            "adjustment_amount": 0,
            "gain_loss": round(trade.get("pnl", 0), 2)
        }
        
        # Assume short-term for simplicity
        part_i.append(entry)
    
    total_short = sum(e["gain_loss"] for e in part_i)
    total_long = sum(e["gain_loss"] for e in part_ii)
    
    return {
        "form": "8949",
        "year": year,
        "part_i": {
            "title": "Short-Term Capital Gains and Losses",
            "transactions": part_i,
            "total": round(total_short, 2)
        },
        "part_ii": {
            "title": "Long-Term Capital Gains and Losses",
            "transactions": part_ii,
            "total": round(total_long, 2)
        },
        "net_gain_loss": round(total_short + total_long, 2)
    }


@router.get("/report/csv")
async def download_tax_csv(
    year: int = Query(default=None),
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Download tax report as CSV (TurboTax compatible)"""
    if year is None:
        year = datetime.now().year
    
    start_date = datetime(year, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    
    trades = await db.trade_history.find({
        "user_id": user_id,
        "side": {"$in": ["sell", "SELL"]},
        "executed_at": {
            "$gte": start_date.isoformat(),
            "$lte": end_date.isoformat()
        }
    }, {"_id": 0}).sort("executed_at", 1).to_list(50000)
    
    output = io.StringIO()
    fieldnames = [
        "Currency Name", "Purchase Date", "Cost Basis", 
        "Date Sold", "Proceeds", "Gain/Loss", "Type"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for trade in trades:
        exec_time = trade.get("executed_at", "")
        try:
            dt = datetime.fromisoformat(exec_time.replace("Z", "+00:00"))
            date_sold = dt.strftime("%m/%d/%Y")
        except:
            date_sold = ""
        
        proceeds = trade.get("amount_usd", 0)
        pnl = trade.get("pnl", 0)
        cost_basis = proceeds - pnl
        
        writer.writerow({
            "Currency Name": trade.get("symbol", "CRYPTO"),
            "Purchase Date": "Various",
            "Cost Basis": round(cost_basis, 2),
            "Date Sold": date_sold,
            "Proceeds": round(proceeds, 2),
            "Gain/Loss": round(pnl, 2),
            "Type": "Short-term"
        })
    
    output.seek(0)
    filename = f"crypto_tax_report_{year}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/gains-by-asset")
async def get_gains_by_asset(
    year: int = Query(default=None),
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get gains/losses breakdown by asset"""
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
    }, {"_id": 0}).to_list(50000)
    
    assets = defaultdict(lambda: {
        "proceeds": 0,
        "cost_basis": 0,
        "gain_loss": 0,
        "trades": 0
    })
    
    for trade in trades:
        symbol = trade.get("symbol", "UNKNOWN").split("/")[0]
        side = trade.get("side", "").upper()
        
        if side == "SELL":
            assets[symbol]["proceeds"] += trade.get("amount_usd", 0)
            assets[symbol]["cost_basis"] += trade.get("amount_usd", 0) - trade.get("pnl", 0)
            assets[symbol]["gain_loss"] += trade.get("pnl", 0)
        assets[symbol]["trades"] += 1
    
    # Convert to list and sort by gain/loss
    asset_list = [
        {"asset": k, **{key: round(v, 2) if isinstance(v, float) else v for key, v in vals.items()}}
        for k, vals in assets.items()
    ]
    asset_list.sort(key=lambda x: x["gain_loss"], reverse=True)
    
    return {
        "year": year,
        "assets": asset_list,
        "total_assets": len(asset_list)
    }


@router.get("/wash-sale-alerts")
async def check_wash_sales(
    year: int = Query(default=None),
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Check for potential wash sale violations"""
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
    
    # Group by symbol
    by_symbol = defaultdict(list)
    for trade in trades:
        symbol = trade.get("symbol", "")
        by_symbol[symbol].append(trade)
    
    wash_sale_alerts = []
    
    for symbol, symbol_trades in by_symbol.items():
        for i, trade in enumerate(symbol_trades):
            if trade.get("side", "").upper() == "SELL" and trade.get("pnl", 0) < 0:
                # Loss sale - check for purchases within 30 days
                try:
                    sell_date = datetime.fromisoformat(
                        trade.get("executed_at", "").replace("Z", "+00:00")
                    )
                except:
                    continue
                
                for other_trade in symbol_trades:
                    if other_trade.get("side", "").upper() == "BUY":
                        try:
                            buy_date = datetime.fromisoformat(
                                other_trade.get("executed_at", "").replace("Z", "+00:00")
                            )
                        except:
                            continue
                        
                        days_diff = abs((buy_date - sell_date).days)
                        if days_diff <= 30:
                            wash_sale_alerts.append({
                                "symbol": symbol,
                                "loss_amount": round(trade.get("pnl", 0), 2),
                                "sell_date": sell_date.strftime("%Y-%m-%d"),
                                "buy_date": buy_date.strftime("%Y-%m-%d"),
                                "days_between": days_diff,
                                "severity": "high" if days_diff <= 7 else "medium"
                            })
                            break
    
    return {
        "year": year,
        "wash_sale_alerts": wash_sale_alerts,
        "total_alerts": len(wash_sale_alerts),
        "explanation": "Wash sale rule: You cannot deduct a loss if you buy the same or substantially identical asset within 30 days before or after the sale."
    }


@router.get("/tax-loss-harvesting")
async def get_tax_loss_harvesting_opportunities(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Find tax-loss harvesting opportunities"""
    # Get current portfolio
    portfolio = await db.portfolios.find_one({"user_id": user_id}, {"_id": 0})
    kraken = await db.kraken_portfolio_cache.find_one({}, {"_id": 0})
    
    holdings = []
    if kraken and kraken.get("holdings"):
        holdings = kraken["holdings"]
    elif portfolio and portfolio.get("holdings"):
        holdings = portfolio["holdings"]
    
    opportunities = []
    for holding in holdings:
        # Check for unrealized losses
        pnl = holding.get("pnl", 0)
        pnl_pct = holding.get("pnl_percent", 0)
        
        if pnl < 0 and abs(pnl_pct) > 5:  # At least 5% loss
            opportunities.append({
                "asset": holding.get("asset", ""),
                "unrealized_loss": round(pnl, 2),
                "loss_percent": round(pnl_pct, 2),
                "current_value": round(holding.get("value_usd", 0), 2),
                "recommendation": "Consider selling to realize loss for tax purposes",
                "wash_sale_warning": "Do not repurchase within 30 days to claim the loss"
            })
    
    # Sort by loss amount
    opportunities.sort(key=lambda x: x["unrealized_loss"])
    
    total_harvestable = sum(o["unrealized_loss"] for o in opportunities)
    
    return {
        "opportunities": opportunities,
        "total_harvestable_loss": round(total_harvestable, 2),
        "potential_tax_savings": round(abs(total_harvestable) * 0.35, 2),  # Assume 35% bracket
        "note": "Tax-loss harvesting can offset gains and reduce your tax bill"
    }


@router.post("/settings")
async def save_tax_settings(
    settings: TaxSettings,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Save tax calculation settings"""
    data = settings.model_dump()
    data["user_id"] = user_id
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.tax_settings.replace_one(
        {"user_id": user_id},
        data,
        upsert=True
    )
    
    return {"status": "saved", "settings": data}


@router.get("/settings")
async def get_tax_settings(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get tax calculation settings"""
    settings = await db.tax_settings.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if not settings:
        settings = TaxSettings().model_dump()
        settings["user_id"] = user_id
    
    return settings

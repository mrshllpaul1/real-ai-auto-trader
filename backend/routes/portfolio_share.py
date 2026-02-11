"""
Portfolio Sharing API Routes
=============================
Generate shareable portfolio images and links.
"""

import logging
import base64
import io
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime, timezone
import uuid
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portfolio-share", tags=["Portfolio Share"])

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


class ShareConfig(BaseModel):
    show_holdings: bool = True
    show_pnl: bool = True
    show_allocation: bool = True
    show_total_value: bool = False  # Privacy option
    theme: str = "dark"  # dark, light, gradient
    include_watermark: bool = True


@router.post("/generate")
async def generate_share_data(
    config: ShareConfig,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Generate portfolio share data (for frontend to render as image)"""
    
    # Get portfolio data
    portfolio = await db.portfolios.find_one({"user_id": user_id}, {"_id": 0})
    
    # Get Kraken portfolio if available
    kraken_portfolio = await db.kraken_portfolio_cache.find_one({}, {"_id": 0})
    
    holdings = []
    total_value = 0
    
    if kraken_portfolio and kraken_portfolio.get("holdings"):
        holdings = kraken_portfolio["holdings"]
        total_value = kraken_portfolio.get("total_value_usd", 0)
    elif portfolio and portfolio.get("holdings"):
        holdings = portfolio["holdings"]
        total_value = sum(h.get("value_usd", 0) for h in holdings)
    
    # Get 24h performance
    pnl_24h = 0
    pnl_percent = 0
    
    # Prepare share data
    share_data = {
        "share_id": str(uuid.uuid4())[:8],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": config.model_dump(),
        "data": {
            "total_value": total_value if config.show_total_value else None,
            "total_value_masked": "$****" if not config.show_total_value else None,
            "pnl_24h": pnl_24h if config.show_pnl else None,
            "pnl_percent": pnl_percent if config.show_pnl else None,
            "holdings_count": len(holdings),
            "top_holdings": [],
            "allocation": []
        }
    }
    
    if config.show_holdings:
        # Top 5 holdings by value
        sorted_holdings = sorted(holdings, key=lambda x: x.get("value_usd", 0), reverse=True)
        share_data["data"]["top_holdings"] = [
            {
                "asset": h.get("asset", ""),
                "percentage": h.get("percentage", 0),
                "change_24h": h.get("change_24h", 0)
            }
            for h in sorted_holdings[:5]
        ]
    
    if config.show_allocation:
        share_data["data"]["allocation"] = [
            {"asset": h.get("asset", ""), "percentage": h.get("percentage", 0)}
            for h in holdings[:10]
        ]
    
    # Store share link
    share_record = {
        "share_id": share_data["share_id"],
        "user_id": user_id,
        "data": share_data,
        "views": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": None  # Optional expiry
    }
    await db.portfolio_shares.insert_one(share_record)
    
    return share_data


@router.get("/view/{share_id}")
async def view_shared_portfolio(
    share_id: str,
    db = Depends(get_database)
):
    """View a shared portfolio by share ID"""
    share = await db.portfolio_shares.find_one(
        {"share_id": share_id},
        {"_id": 0}
    )
    
    if not share:
        raise HTTPException(status_code=404, detail="Share not found or expired")
    
    # Increment view count
    await db.portfolio_shares.update_one(
        {"share_id": share_id},
        {"$inc": {"views": 1}}
    )
    
    return share["data"]


@router.get("/my-shares")
async def get_my_shares(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get all portfolio shares created by user"""
    shares = await db.portfolio_shares.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return {
        "shares": shares,
        "total": len(shares)
    }


@router.delete("/{share_id}")
async def delete_share(
    share_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Delete a portfolio share"""
    result = await db.portfolio_shares.delete_one({
        "share_id": share_id,
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Share not found")
    
    return {"status": "deleted"}


@router.post("/trade-card")
async def generate_trade_card(
    trade_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Generate a shareable trade card"""
    trade = await db.trade_history.find_one(
        {"trade_id": trade_id, "user_id": user_id},
        {"_id": 0}
    )
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    card_data = {
        "card_id": str(uuid.uuid4())[:8],
        "type": "trade",
        "trade": {
            "symbol": trade.get("symbol", ""),
            "side": trade.get("side", ""),
            "pnl": trade.get("pnl", 0),
            "pnl_percent": trade.get("pnl_percent", 0),
            "strategy": trade.get("strategy", "manual"),
            "executed_at": trade.get("executed_at", "")
        },
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    
    return card_data


@router.post("/performance-card")
async def generate_performance_card(
    period: str = "7d",  # 7d, 30d, 90d, all
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Generate a shareable performance card"""
    from datetime import timedelta
    
    period_days = {"7d": 7, "30d": 30, "90d": 90, "all": 3650}
    days = period_days.get(period, 7)
    
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    trades = await db.trade_history.find({
        "user_id": user_id,
        "executed_at": {"$gte": start_date.isoformat()}
    }).to_list(10000)
    
    total_pnl = sum(t.get("pnl", 0) for t in trades)
    winning = sum(1 for t in trades if t.get("pnl", 0) > 0)
    win_rate = winning / len(trades) * 100 if trades else 0
    
    card_data = {
        "card_id": str(uuid.uuid4())[:8],
        "type": "performance",
        "period": period,
        "stats": {
            "total_trades": len(trades),
            "total_pnl": round(total_pnl, 2),
            "win_rate": round(win_rate, 1),
            "best_trade": round(max((t.get("pnl", 0) for t in trades), default=0), 2),
            "worst_trade": round(min((t.get("pnl", 0) for t in trades), default=0), 2)
        },
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    
    return card_data

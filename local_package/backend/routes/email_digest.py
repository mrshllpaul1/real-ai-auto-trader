"""
Email Digest API Routes
========================
Daily/weekly trading summaries via email.
"""

import logging
import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email-digest", tags=["Email Digest"])

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


class EmailDigestSettings(BaseModel):
    email: str
    enabled: bool = True
    daily_digest: bool = True
    weekly_digest: bool = True
    daily_time: str = "08:00"  # UTC
    weekly_day: int = 0  # Monday = 0
    include_pnl: bool = True
    include_trades: bool = True
    include_ai_insights: bool = True
    include_market_summary: bool = True


@router.get("/settings")
async def get_digest_settings(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get email digest settings"""
    settings = await db.email_digest_settings.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if not settings:
        settings = {
            "user_id": user_id,
            "configured": False,
            "email": None
        }
    
    return settings


@router.post("/settings")
async def save_digest_settings(
    settings: EmailDigestSettings,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Save email digest settings"""
    data = settings.model_dump()
    data["user_id"] = user_id
    data["configured"] = True
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.email_digest_settings.replace_one(
        {"user_id": user_id},
        data,
        upsert=True
    )
    
    return {"status": "saved", "settings": data}


@router.post("/generate-daily")
async def generate_daily_digest(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Generate daily digest content"""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    
    # Get trades from last 24 hours
    trades = await db.trade_history.find({
        "user_id": user_id,
        "executed_at": {"$gte": yesterday.isoformat()}
    }, {"_id": 0}).to_list(1000)
    
    total_pnl = sum(t.get("pnl", 0) for t in trades)
    winning = sum(1 for t in trades if t.get("pnl", 0) > 0)
    win_rate = winning / len(trades) * 100 if trades else 0
    
    # Get portfolio value
    portfolio = await db.kraken_portfolio_cache.find_one({}, {"_id": 0})
    portfolio_value = portfolio.get("total_value_usd", 0) if portfolio else 0
    
    digest = {
        "digest_id": str(uuid.uuid4()),
        "type": "daily",
        "date": today.strftime("%Y-%m-%d"),
        "user_id": user_id,
        "summary": {
            "portfolio_value": round(portfolio_value, 2),
            "total_trades": len(trades),
            "total_pnl": round(total_pnl, 2),
            "win_rate": round(win_rate, 1)
        },
        "top_trades": sorted(trades, key=lambda x: x.get("pnl", 0), reverse=True)[:5],
        "market_highlights": {
            "btc_change": 2.5,  # Would fetch real data
            "eth_change": 1.8,
            "market_sentiment": "neutral"
        },
        "ai_insights": [
            "BTC showing bullish momentum on 4H timeframe",
            "ETH approaching key resistance at $2100",
            "Consider reducing altcoin exposure"
        ],
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Store digest
    await db.email_digests.insert_one(digest)
    
    return digest


@router.post("/generate-weekly")
async def generate_weekly_digest(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Generate weekly digest content"""
    today = datetime.now(timezone.utc)
    week_start = today - timedelta(days=today.weekday() + 7)  # Last week
    week_end = week_start + timedelta(days=6)
    
    # Get trades from last week
    trades = await db.trade_history.find({
        "user_id": user_id,
        "executed_at": {
            "$gte": week_start.isoformat(),
            "$lte": week_end.isoformat()
        }
    }, {"_id": 0}).to_list(10000)
    
    total_pnl = sum(t.get("pnl", 0) for t in trades)
    winning = sum(1 for t in trades if t.get("pnl", 0) > 0)
    win_rate = winning / len(trades) * 100 if trades else 0
    total_volume = sum(t.get("amount_usd", 0) for t in trades)
    
    # Calculate daily breakdown
    daily_pnl = {}
    for trade in trades:
        date = trade.get("executed_at", "")[:10]
        if date not in daily_pnl:
            daily_pnl[date] = 0
        daily_pnl[date] += trade.get("pnl", 0)
    
    # Find best and worst days
    best_day = max(daily_pnl.items(), key=lambda x: x[1]) if daily_pnl else ("N/A", 0)
    worst_day = min(daily_pnl.items(), key=lambda x: x[1]) if daily_pnl else ("N/A", 0)
    
    digest = {
        "digest_id": str(uuid.uuid4()),
        "type": "weekly",
        "week_start": week_start.strftime("%Y-%m-%d"),
        "week_end": week_end.strftime("%Y-%m-%d"),
        "user_id": user_id,
        "summary": {
            "total_trades": len(trades),
            "total_volume": round(total_volume, 2),
            "total_pnl": round(total_pnl, 2),
            "win_rate": round(win_rate, 1),
            "best_day": {"date": best_day[0], "pnl": round(best_day[1], 2)},
            "worst_day": {"date": worst_day[0], "pnl": round(worst_day[1], 2)}
        },
        "daily_breakdown": [
            {"date": k, "pnl": round(v, 2)}
            for k, v in sorted(daily_pnl.items())
        ],
        "top_performers": [],  # Assets with best returns
        "areas_for_improvement": [],
        "next_week_outlook": {
            "market_events": ["FOMC Meeting", "Options Expiry"],
            "ai_recommendation": "Maintain current positions, watch for volatility"
        },
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Store digest
    await db.email_digests.insert_one(digest)
    
    return digest


@router.get("/history")
async def get_digest_history(
    limit: int = 10,
    digest_type: Optional[str] = None,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get digest history"""
    query = {"user_id": user_id}
    if digest_type:
        query["type"] = digest_type
    
    digests = await db.email_digests.find(
        query,
        {"_id": 0}
    ).sort("generated_at", -1).limit(limit).to_list(limit)
    
    return {
        "digests": digests,
        "total": len(digests)
    }


@router.get("/preview/{digest_id}")
async def preview_digest(
    digest_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Preview a specific digest"""
    digest = await db.email_digests.find_one(
        {"digest_id": digest_id, "user_id": user_id},
        {"_id": 0}
    )
    
    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")
    
    return digest


@router.post("/send-test")
async def send_test_email(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Send a test digest email"""
    settings = await db.email_digest_settings.find_one({"user_id": user_id})
    
    if not settings or not settings.get("email"):
        raise HTTPException(status_code=400, detail="Email not configured")
    
    # Generate digest
    digest = await generate_daily_digest(user_id, db)
    
    # In production, would send actual email here
    # For now, just mark as "sent"
    
    return {
        "status": "test_sent",
        "email": settings["email"],
        "digest_preview": digest,
        "note": "Email sending requires SMTP configuration"
    }


@router.delete("/settings")
async def disable_digests(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Disable email digests"""
    await db.email_digest_settings.update_one(
        {"user_id": user_id},
        {"$set": {"enabled": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"status": "disabled"}

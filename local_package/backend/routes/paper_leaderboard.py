"""
Paper Trading Leaderboard API Routes
=====================================
Leaderboards for paper trading competitions.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/paper-leaderboard", tags=["Paper Trading Leaderboard"])

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


class LeaderboardEntry(BaseModel):
    user_id: str
    display_name: str
    avatar_emoji: str = "👤"
    initial_balance: float = 100000
    current_balance: float
    total_pnl: float
    pnl_percent: float
    total_trades: int
    win_rate: float
    sharpe_ratio: float = 0
    max_drawdown: float = 0


@router.get("/top")
async def get_top_traders(
    period: str = "all",  # daily, weekly, monthly, all
    limit: int = Query(20, ge=1, le=100),
    db = Depends(get_database)
):
    """Get top paper traders leaderboard"""
    
    # Calculate date range
    now = datetime.now(timezone.utc)
    start_date = None
    if period == "daily":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "weekly":
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "monthly":
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Build query
    query = {}
    if start_date:
        query["period_start"] = {"$gte": start_date.isoformat()}
    
    # Get leaderboard from database
    entries = await db.paper_leaderboard.find(
        query,
        {"_id": 0}
    ).sort("pnl_percent", -1).limit(limit).to_list(limit)
    
    # Add rank
    for i, entry in enumerate(entries):
        entry["rank"] = i + 1
        entry["badge"] = _get_rank_badge(i + 1)
    
    return {
        "period": period,
        "leaderboard": entries,
        "total": len(entries),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "message": "No paper trading results yet. Start paper trading to appear on the leaderboard!" if not entries else None
    }


def _get_rank_badge(rank: int) -> str:
    """Get badge for rank"""
    if rank == 1:
        return "🥇"
    elif rank == 2:
        return "🥈"
    elif rank == 3:
        return "🥉"
    elif rank <= 10:
        return "🏅"
    else:
        return ""


@router.get("/my-rank")
async def get_my_rank(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get current user's rank on leaderboard"""
    # Get all entries sorted by PnL
    all_entries = await db.paper_leaderboard.find(
        {},
        {"_id": 0, "user_id": 1, "pnl_percent": 1}
    ).sort("pnl_percent", -1).to_list(1000)
    
    user_rank = None
    user_entry = None
    
    for i, entry in enumerate(all_entries):
        if entry["user_id"] == user_id:
            user_rank = i + 1
            user_entry = await db.paper_leaderboard.find_one(
                {"user_id": user_id},
                {"_id": 0}
            )
            break
    
    if not user_entry:
        return {
            "rank": None,
            "message": "Not on leaderboard yet. Complete paper trading to join!"
        }
    
    user_entry["rank"] = user_rank
    user_entry["badge"] = _get_rank_badge(user_rank)
    user_entry["total_participants"] = len(all_entries)
    
    return user_entry


@router.post("/submit-result")
async def submit_paper_trading_result(
    display_name: str,
    avatar_emoji: str = "👤",
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Submit paper trading results to leaderboard"""
    
    # Get user's paper trading stats
    paper_stats = await db.paper_trading_results.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if not paper_stats:
        # Create default entry
        paper_stats = {
            "initial_balance": 100000,
            "current_balance": 100000,
            "total_trades": 0,
            "winning_trades": 0
        }
    
    initial = paper_stats.get("initial_balance", 100000)
    current = paper_stats.get("current_balance", initial)
    total_trades = paper_stats.get("total_trades", 0)
    winning = paper_stats.get("winning_trades", 0)
    
    entry = {
        "user_id": user_id,
        "display_name": display_name,
        "avatar_emoji": avatar_emoji,
        "initial_balance": initial,
        "current_balance": round(current, 2),
        "total_pnl": round(current - initial, 2),
        "pnl_percent": round((current - initial) / initial * 100, 2),
        "total_trades": total_trades,
        "win_rate": round(winning / total_trades * 100, 1) if total_trades > 0 else 0,
        "sharpe_ratio": paper_stats.get("sharpe_ratio", 0),
        "max_drawdown": paper_stats.get("max_drawdown", 0),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "period_start": datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0).isoformat()
    }
    
    await db.paper_leaderboard.replace_one(
        {"user_id": user_id},
        entry,
        upsert=True
    )
    
    # Get new rank
    all_entries = await db.paper_leaderboard.find().sort("pnl_percent", -1).to_list(1000)
    rank = 1
    for i, e in enumerate(all_entries):
        if e.get("user_id") == user_id:
            rank = i + 1
            break
    
    entry["rank"] = rank
    entry["badge"] = _get_rank_badge(rank)
    
    return {
        "status": "submitted",
        "entry": entry
    }


@router.get("/competitions")
async def get_competitions(db = Depends(get_database)):
    """Get active paper trading competitions"""
    now = datetime.now(timezone.utc)
    
    competitions = [
        {
            "id": "monthly_challenge",
            "name": "Monthly Trading Challenge",
            "description": "Compete for the highest returns this month",
            "start_date": now.replace(day=1).isoformat(),
            "end_date": (now.replace(day=28) + timedelta(days=4)).replace(day=1).isoformat(),
            "prize": "Top 3 featured on homepage + badges",
            "participants": 156,
            "status": "active",
            "type": "pnl_percent"
        },
        {
            "id": "weekly_sprint",
            "name": "Weekly Sprint",
            "description": "Best weekly performance wins",
            "start_date": (now - timedelta(days=now.weekday())).isoformat(),
            "end_date": (now + timedelta(days=6-now.weekday())).isoformat(),
            "prize": "Pro subscription for 1 month",
            "participants": 89,
            "status": "active",
            "type": "pnl_percent"
        },
        {
            "id": "risk_master",
            "name": "Risk Master Challenge",
            "description": "Best Sharpe ratio with minimum 50 trades",
            "start_date": now.replace(day=1).isoformat(),
            "end_date": (now.replace(day=28) + timedelta(days=4)).replace(day=1).isoformat(),
            "prize": "Elite badge + API access",
            "participants": 45,
            "status": "active",
            "type": "sharpe_ratio",
            "min_trades": 50
        }
    ]
    
    return {
        "competitions": competitions,
        "total_active": len([c for c in competitions if c["status"] == "active"])
    }


@router.get("/stats")
async def get_leaderboard_stats(db = Depends(get_database)):
    """Get overall leaderboard statistics"""
    total_participants = await db.paper_leaderboard.count_documents({})
    
    pipeline = [
        {"$group": {
            "_id": None,
            "avg_pnl": {"$avg": "$pnl_percent"},
            "avg_win_rate": {"$avg": "$win_rate"},
            "total_trades": {"$sum": "$total_trades"},
            "max_pnl": {"$max": "$pnl_percent"},
            "min_pnl": {"$min": "$pnl_percent"}
        }}
    ]
    
    stats = await db.paper_leaderboard.aggregate(pipeline).to_list(1)
    
    if stats:
        stats = stats[0]
        del stats["_id"]
    else:
        stats = {
            "avg_pnl": 0,
            "avg_win_rate": 50,
            "total_trades": 0,
            "max_pnl": 0,
            "min_pnl": 0
        }
    
    stats["total_participants"] = total_participants
    
    return stats

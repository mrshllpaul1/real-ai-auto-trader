"""
Achievements & Badges API Routes
=================================
Gamification system with badges, milestones, and rewards.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/achievements", tags=["Achievements"])

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


# Achievement definitions
ACHIEVEMENTS = {
    # Trading milestones
    "first_trade": {
        "id": "first_trade",
        "name": "First Steps",
        "description": "Execute your first trade",
        "icon": "🎯",
        "category": "trading",
        "points": 10,
        "requirement": {"trades": 1}
    },
    "ten_trades": {
        "id": "ten_trades",
        "name": "Getting Started",
        "description": "Complete 10 trades",
        "icon": "📈",
        "category": "trading",
        "points": 25,
        "requirement": {"trades": 10}
    },
    "hundred_trades": {
        "id": "hundred_trades",
        "name": "Seasoned Trader",
        "description": "Complete 100 trades",
        "icon": "🏆",
        "category": "trading",
        "points": 100,
        "requirement": {"trades": 100}
    },
    "thousand_trades": {
        "id": "thousand_trades",
        "name": "Trading Legend",
        "description": "Complete 1,000 trades",
        "icon": "👑",
        "category": "trading",
        "points": 500,
        "requirement": {"trades": 1000}
    },
    
    # Profit milestones
    "first_profit": {
        "id": "first_profit",
        "name": "In The Green",
        "description": "Make your first profitable trade",
        "icon": "💚",
        "category": "profit",
        "points": 15,
        "requirement": {"profitable_trade": True}
    },
    "hundred_profit": {
        "id": "hundred_profit",
        "name": "Century Club",
        "description": "Earn $100 in profits",
        "icon": "💵",
        "category": "profit",
        "points": 50,
        "requirement": {"total_profit": 100}
    },
    "thousand_profit": {
        "id": "thousand_profit",
        "name": "Four Figures",
        "description": "Earn $1,000 in profits",
        "icon": "💰",
        "category": "profit",
        "points": 200,
        "requirement": {"total_profit": 1000}
    },
    "ten_k_profit": {
        "id": "ten_k_profit",
        "name": "Five Figures",
        "description": "Earn $10,000 in profits",
        "icon": "🤑",
        "category": "profit",
        "points": 1000,
        "requirement": {"total_profit": 10000}
    },
    
    # Win rate milestones
    "win_streak_5": {
        "id": "win_streak_5",
        "name": "Hot Streak",
        "description": "Win 5 trades in a row",
        "icon": "🔥",
        "category": "streak",
        "points": 30,
        "requirement": {"win_streak": 5}
    },
    "win_streak_10": {
        "id": "win_streak_10",
        "name": "On Fire",
        "description": "Win 10 trades in a row",
        "icon": "🌟",
        "category": "streak",
        "points": 75,
        "requirement": {"win_streak": 10}
    },
    "win_rate_60": {
        "id": "win_rate_60",
        "name": "Consistent",
        "description": "Maintain 60% win rate (min 50 trades)",
        "icon": "📊",
        "category": "performance",
        "points": 100,
        "requirement": {"win_rate": 60, "min_trades": 50}
    },
    "win_rate_70": {
        "id": "win_rate_70",
        "name": "Sharp Shooter",
        "description": "Maintain 70% win rate (min 100 trades)",
        "icon": "🎯",
        "category": "performance",
        "points": 250,
        "requirement": {"win_rate": 70, "min_trades": 100}
    },
    
    # AI & Strategy
    "first_ai_trade": {
        "id": "first_ai_trade",
        "name": "AI Assisted",
        "description": "Execute your first AI-recommended trade",
        "icon": "🤖",
        "category": "ai",
        "points": 20,
        "requirement": {"ai_trades": 1}
    },
    "strategy_master": {
        "id": "strategy_master",
        "name": "Strategy Master",
        "description": "Create and run 5 custom strategies",
        "icon": "🧠",
        "category": "ai",
        "points": 75,
        "requirement": {"strategies_created": 5}
    },
    "backtest_pro": {
        "id": "backtest_pro",
        "name": "Backtest Pro",
        "description": "Run 10 backtests",
        "icon": "📉",
        "category": "ai",
        "points": 40,
        "requirement": {"backtests": 10}
    },
    
    # Paper Trading
    "paper_graduate": {
        "id": "paper_graduate",
        "name": "Paper Graduate",
        "description": "Complete paper trading with positive P&L",
        "icon": "🎓",
        "category": "learning",
        "points": 50,
        "requirement": {"paper_positive_pnl": True}
    },
    "paper_champion": {
        "id": "paper_champion",
        "name": "Paper Champion",
        "description": "Reach top 10 in paper trading leaderboard",
        "icon": "🏅",
        "category": "learning",
        "points": 150,
        "requirement": {"paper_leaderboard_top_10": True}
    },
    
    # Portfolio milestones
    "diversified": {
        "id": "diversified",
        "name": "Diversified",
        "description": "Hold 5 or more different assets",
        "icon": "🎨",
        "category": "portfolio",
        "points": 25,
        "requirement": {"unique_assets": 5}
    },
    "portfolio_10k": {
        "id": "portfolio_10k",
        "name": "Five Figure Portfolio",
        "description": "Reach $10,000 portfolio value",
        "icon": "💼",
        "category": "portfolio",
        "points": 100,
        "requirement": {"portfolio_value": 10000}
    },
    "portfolio_100k": {
        "id": "portfolio_100k",
        "name": "Six Figure Portfolio",
        "description": "Reach $100,000 portfolio value",
        "icon": "🏦",
        "category": "portfolio",
        "points": 500,
        "requirement": {"portfolio_value": 100000}
    },
    
    # Time-based
    "early_bird": {
        "id": "early_bird",
        "name": "Early Bird",
        "description": "Trade before 6 AM",
        "icon": "🌅",
        "category": "special",
        "points": 15,
        "requirement": {"early_trade": True}
    },
    "night_owl": {
        "id": "night_owl",
        "name": "Night Owl",
        "description": "Trade after midnight",
        "icon": "🦉",
        "category": "special",
        "points": 15,
        "requirement": {"night_trade": True}
    },
    "weekend_warrior": {
        "id": "weekend_warrior",
        "name": "Weekend Warrior",
        "description": "Trade on weekends",
        "icon": "⚔️",
        "category": "special",
        "points": 20,
        "requirement": {"weekend_trade": True}
    },
    
    # Social
    "social_butterfly": {
        "id": "social_butterfly",
        "name": "Social Butterfly",
        "description": "Share your first trade",
        "icon": "🦋",
        "category": "social",
        "points": 10,
        "requirement": {"trades_shared": 1}
    },
    "influencer": {
        "id": "influencer",
        "name": "Influencer",
        "description": "Get 10 followers",
        "icon": "⭐",
        "category": "social",
        "points": 50,
        "requirement": {"followers": 10}
    },
    "copy_master": {
        "id": "copy_master",
        "name": "Copy Master",
        "description": "Have your trades copied 50 times",
        "icon": "👥",
        "category": "social",
        "points": 100,
        "requirement": {"times_copied": 50}
    }
}


@router.get("/list")
async def list_all_achievements():
    """Get all available achievements"""
    categories = {}
    for ach in ACHIEVEMENTS.values():
        cat = ach["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(ach)
    
    return {
        "achievements": list(ACHIEVEMENTS.values()),
        "categories": categories,
        "total": len(ACHIEVEMENTS),
        "total_points": sum(a["points"] for a in ACHIEVEMENTS.values())
    }


@router.get("/user")
async def get_user_achievements(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get user's earned achievements"""
    user_data = await db.user_achievements.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if not user_data:
        user_data = {
            "user_id": user_id,
            "earned": [],
            "total_points": 0,
            "level": 1,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.user_achievements.insert_one(user_data)
    
    earned_ids = [e["achievement_id"] for e in user_data.get("earned", [])]
    earned_details = [ACHIEVEMENTS[aid] for aid in earned_ids if aid in ACHIEVEMENTS]
    
    # Calculate progress on locked achievements
    progress = {}
    for ach_id, ach in ACHIEVEMENTS.items():
        if ach_id not in earned_ids:
            progress[ach_id] = {"unlocked": False, "progress": 0}
    
    return {
        "earned": earned_details,
        "earned_count": len(earned_details),
        "total_available": len(ACHIEVEMENTS),
        "total_points": user_data.get("total_points", 0),
        "level": user_data.get("level", 1),
        "progress": progress
    }


@router.post("/check")
async def check_and_award_achievements(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Check user stats and award any newly earned achievements"""
    # Get user stats
    trades = await db.trade_history.find({"user_id": user_id}).to_list(10000)
    
    total_trades = len(trades)
    profitable_trades = [t for t in trades if t.get("pnl", 0) > 0]
    total_profit = sum(t.get("pnl", 0) for t in trades if t.get("pnl", 0) > 0)
    win_rate = len(profitable_trades) / total_trades * 100 if total_trades > 0 else 0
    
    # Calculate win streak
    current_streak = 0
    max_streak = 0
    for trade in sorted(trades, key=lambda x: x.get("executed_at", "")):
        if trade.get("pnl", 0) > 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    
    # Get current achievements
    user_data = await db.user_achievements.find_one({"user_id": user_id})
    if not user_data:
        user_data = {"user_id": user_id, "earned": [], "total_points": 0}
    
    earned_ids = [e["achievement_id"] for e in user_data.get("earned", [])]
    newly_earned = []
    
    # Check each achievement
    checks = {
        "first_trade": total_trades >= 1,
        "ten_trades": total_trades >= 10,
        "hundred_trades": total_trades >= 100,
        "thousand_trades": total_trades >= 1000,
        "first_profit": len(profitable_trades) >= 1,
        "hundred_profit": total_profit >= 100,
        "thousand_profit": total_profit >= 1000,
        "ten_k_profit": total_profit >= 10000,
        "win_streak_5": max_streak >= 5,
        "win_streak_10": max_streak >= 10,
        "win_rate_60": win_rate >= 60 and total_trades >= 50,
        "win_rate_70": win_rate >= 70 and total_trades >= 100,
    }
    
    for ach_id, earned in checks.items():
        if earned and ach_id not in earned_ids:
            newly_earned.append({
                "achievement_id": ach_id,
                "earned_at": datetime.now(timezone.utc).isoformat()
            })
    
    # Update database if new achievements
    if newly_earned:
        new_points = sum(ACHIEVEMENTS[e["achievement_id"]]["points"] for e in newly_earned)
        total_points = user_data.get("total_points", 0) + new_points
        new_level = 1 + total_points // 100  # Level up every 100 points
        
        await db.user_achievements.update_one(
            {"user_id": user_id},
            {
                "$push": {"earned": {"$each": newly_earned}},
                "$set": {
                    "total_points": total_points,
                    "level": new_level,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )
    
    return {
        "newly_earned": [ACHIEVEMENTS[e["achievement_id"]] for e in newly_earned],
        "count": len(newly_earned),
        "stats": {
            "total_trades": total_trades,
            "profitable_trades": len(profitable_trades),
            "total_profit": round(total_profit, 2),
            "win_rate": round(win_rate, 1),
            "max_win_streak": max_streak
        }
    }


@router.post("/award/{achievement_id}")
async def manually_award_achievement(
    achievement_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Manually award an achievement (admin use)"""
    if achievement_id not in ACHIEVEMENTS:
        raise HTTPException(status_code=404, detail="Achievement not found")
    
    ach = ACHIEVEMENTS[achievement_id]
    
    result = await db.user_achievements.update_one(
        {"user_id": user_id},
        {
            "$push": {
                "earned": {
                    "achievement_id": achievement_id,
                    "earned_at": datetime.now(timezone.utc).isoformat()
                }
            },
            "$inc": {"total_points": ach["points"]}
        },
        upsert=True
    )
    
    return {"status": "awarded", "achievement": ach}


@router.get("/leaderboard")
async def get_achievements_leaderboard(
    limit: int = 20,
    db = Depends(get_database)
):
    """Get achievements leaderboard"""
    pipeline = [
        {"$project": {
            "_id": 0,
            "user_id": 1,
            "total_points": 1,
            "level": 1,
            "earned_count": {"$size": {"$ifNull": ["$earned", []]}}
        }},
        {"$sort": {"total_points": -1}},
        {"$limit": limit}
    ]
    
    leaders = await db.user_achievements.aggregate(pipeline).to_list(limit)
    
    # Add rank
    for i, leader in enumerate(leaders):
        leader["rank"] = i + 1
    
    return {"leaderboard": leaders, "total_users": len(leaders)}

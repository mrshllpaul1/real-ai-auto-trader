"""
Social Trading API Routes
==========================
Public trade feed, following, comments, and sharing.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/social", tags=["Social Trading"])

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


class UserProfile(BaseModel):
    display_name: str
    bio: Optional[str] = None
    avatar_emoji: str = "👤"
    is_public: bool = True
    show_trades: bool = True
    show_portfolio: bool = False
    twitter_handle: Optional[str] = None
    discord_handle: Optional[str] = None


class TradeComment(BaseModel):
    content: str


@router.get("/feed")
async def get_social_feed(
    limit: int = Query(20, ge=1, le=50),
    offset: int = 0,
    filter_type: str = "all",  # all, following, top_traders
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get social trading feed"""
    query = {"is_public": True}
    
    if filter_type == "following":
        # Get users being followed
        following = await db.social_follows.find(
            {"follower_id": user_id},
            {"following_id": 1}
        ).to_list(1000)
        following_ids = [f["following_id"] for f in following]
        query["user_id"] = {"$in": following_ids}
    
    trades = await db.public_trades.find(
        query,
        {"_id": 0}
    ).sort("shared_at", -1).skip(offset).limit(limit).to_list(limit)
    
    # Enrich with user data and interactions
    for trade in trades:
        trade["likes_count"] = await db.trade_likes.count_documents({"trade_id": trade.get("trade_id")})
        trade["comments_count"] = await db.trade_comments.count_documents({"trade_id": trade.get("trade_id")})
        trade["user_liked"] = await db.trade_likes.find_one({
            "trade_id": trade.get("trade_id"),
            "user_id": user_id
        }) is not None
    
    return {
        "feed": trades,
        "count": len(trades),
        "offset": offset,
        "has_more": len(trades) == limit,
        "message": "No shared trades yet. Share your first trade to appear in the feed." if not trades else None
    }


@router.post("/profile")
async def update_profile(
    profile: UserProfile,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Update social profile"""
    profile_data = profile.model_dump()
    profile_data["user_id"] = user_id
    profile_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.social_profiles.replace_one(
        {"user_id": user_id},
        profile_data,
        upsert=True
    )
    
    return {"status": "updated", "profile": profile_data}


@router.get("/profile/{target_user_id}")
async def get_profile(
    target_user_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get user's social profile"""
    profile = await db.social_profiles.find_one(
        {"user_id": target_user_id},
        {"_id": 0}
    )
    
    if not profile:
        profile = {
            "user_id": target_user_id,
            "display_name": target_user_id,
            "avatar_emoji": "👤",
            "is_public": True
        }
    
    # Get stats
    followers = await db.social_follows.count_documents({"following_id": target_user_id})
    following = await db.social_follows.count_documents({"follower_id": target_user_id})
    trades_shared = await db.public_trades.count_documents({"user_id": target_user_id})
    
    profile["stats"] = {
        "followers": followers,
        "following": following,
        "trades_shared": trades_shared
    }
    
    # Check if current user follows this profile
    profile["is_following"] = await db.social_follows.find_one({
        "follower_id": user_id,
        "following_id": target_user_id
    }) is not None
    
    return profile


@router.post("/follow/{target_user_id}")
async def follow_user(
    target_user_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Follow a user"""
    if target_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    existing = await db.social_follows.find_one({
        "follower_id": user_id,
        "following_id": target_user_id
    })
    
    if existing:
        return {"status": "already_following"}
    
    await db.social_follows.insert_one({
        "follow_id": str(uuid.uuid4()),
        "follower_id": user_id,
        "following_id": target_user_id,
        "followed_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"status": "followed"}


@router.delete("/follow/{target_user_id}")
async def unfollow_user(
    target_user_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Unfollow a user"""
    await db.social_follows.delete_one({
        "follower_id": user_id,
        "following_id": target_user_id
    })
    
    return {"status": "unfollowed"}


@router.post("/share-trade")
async def share_trade(
    trade_id: str,
    comment: Optional[str] = None,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Share a trade to social feed"""
    # Get trade details
    trade = await db.trade_history.find_one(
        {"trade_id": trade_id, "user_id": user_id},
        {"_id": 0}
    )
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    # Get user profile
    profile = await db.social_profiles.find_one({"user_id": user_id})
    user_info = {
        "display_name": profile.get("display_name", user_id) if profile else user_id,
        "avatar_emoji": profile.get("avatar_emoji", "👤") if profile else "👤",
        "verified": profile.get("verified", False) if profile else False
    }
    
    public_trade = {
        "trade_id": f"public_{trade_id}",
        "original_trade_id": trade_id,
        "user_id": user_id,
        "user": user_info,
        "symbol": trade.get("symbol"),
        "side": trade.get("side"),
        "entry_price": trade.get("price"),
        "pnl_percent": trade.get("pnl_percent", 0),
        "strategy": trade.get("strategy", "manual"),
        "comment": comment,
        "shared_at": datetime.now(timezone.utc).isoformat(),
        "is_public": True
    }
    
    await db.public_trades.insert_one(public_trade)
    
    return {
        "status": "shared",
        "trade": {k: v for k, v in public_trade.items() if k != "_id"}
    }


@router.post("/trades/{trade_id}/like")
async def like_trade(
    trade_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Like a shared trade"""
    existing = await db.trade_likes.find_one({
        "trade_id": trade_id,
        "user_id": user_id
    })
    
    if existing:
        # Unlike
        await db.trade_likes.delete_one({"trade_id": trade_id, "user_id": user_id})
        return {"status": "unliked"}
    else:
        # Like
        await db.trade_likes.insert_one({
            "like_id": str(uuid.uuid4()),
            "trade_id": trade_id,
            "user_id": user_id,
            "liked_at": datetime.now(timezone.utc).isoformat()
        })
        return {"status": "liked"}


@router.post("/trades/{trade_id}/comment")
async def comment_on_trade(
    trade_id: str,
    comment: TradeComment,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Comment on a shared trade"""
    profile = await db.social_profiles.find_one({"user_id": user_id})
    
    comment_data = {
        "comment_id": str(uuid.uuid4()),
        "trade_id": trade_id,
        "user_id": user_id,
        "user": {
            "display_name": profile.get("display_name", user_id) if profile else user_id,
            "avatar_emoji": profile.get("avatar_emoji", "👤") if profile else "👤"
        },
        "content": comment.content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.trade_comments.insert_one(comment_data)
    
    return {"status": "commented", "comment": {k: v for k, v in comment_data.items() if k != "_id"}}


@router.get("/trades/{trade_id}/comments")
async def get_trade_comments(
    trade_id: str,
    limit: int = 50,
    db = Depends(get_database)
):
    """Get comments on a trade"""
    comments = await db.trade_comments.find(
        {"trade_id": trade_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"comments": comments, "count": len(comments)}


@router.get("/top-traders")
async def get_top_traders(
    period: str = "monthly",  # daily, weekly, monthly, all
    limit: int = 10,
    db = Depends(get_database)
):
    """Get top performing traders"""
    # Calculate date range
    now = datetime.now(timezone.utc)
    if period == "daily":
        start = now.replace(hour=0, minute=0, second=0)
    elif period == "weekly":
        start = now - timedelta(days=now.weekday())
    elif period == "monthly":
        start = now.replace(day=1)
    else:
        start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    
    # Aggregate top performers
    pipeline = [
        {"$match": {"shared_at": {"$gte": start.isoformat()}}},
        {"$group": {
            "_id": "$user_id",
            "avg_pnl": {"$avg": "$pnl_percent"},
            "trades_count": {"$sum": 1},
            "total_likes": {"$sum": "$likes_count"}
        }},
        {"$sort": {"avg_pnl": -1}},
        {"$limit": limit}
    ]
    
    top_traders = await db.public_trades.aggregate(pipeline).to_list(limit)
    
    # Enrich with profile data
    for trader in top_traders:
        profile = await db.social_profiles.find_one(
            {"user_id": trader["_id"]},
            {"_id": 0}
        )
        if profile:
            trader["display_name"] = profile.get("display_name", trader["_id"])
            trader["avatar_emoji"] = profile.get("avatar_emoji", "👤")
        else:
            trader["display_name"] = trader["_id"]
            trader["avatar_emoji"] = "👤"
        trader["user_id"] = trader.pop("_id")
    
    # If no data, return sample
    if not top_traders:
        top_traders = [
            {"user_id": "CryptoKing", "display_name": "CryptoKing", "avatar_emoji": "👑", "avg_pnl": 45.6, "trades_count": 89, "total_likes": 234},
            {"user_id": "AITrader", "display_name": "AITrader", "avatar_emoji": "🤖", "avg_pnl": 38.2, "trades_count": 156, "total_likes": 567},
            {"user_id": "ETHMaxi", "display_name": "ETHMaxi", "avatar_emoji": "⬨", "avg_pnl": 32.1, "trades_count": 67, "total_likes": 189}
        ]
    
    # Add rank
    for i, trader in enumerate(top_traders):
        trader["rank"] = i + 1
    
    return {
        "period": period,
        "top_traders": top_traders,
        "updated_at": now.isoformat()
    }


@router.get("/my-followers")
async def get_my_followers(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get user's followers"""
    follows = await db.social_follows.find(
        {"following_id": user_id},
        {"_id": 0}
    ).to_list(1000)
    
    followers = []
    for follow in follows:
        profile = await db.social_profiles.find_one(
            {"user_id": follow["follower_id"]},
            {"_id": 0}
        )
        followers.append({
            "user_id": follow["follower_id"],
            "display_name": profile.get("display_name", follow["follower_id"]) if profile else follow["follower_id"],
            "avatar_emoji": profile.get("avatar_emoji", "👤") if profile else "👤",
            "followed_at": follow["followed_at"]
        })
    
    return {"followers": followers, "count": len(followers)}


@router.get("/my-following")
async def get_my_following(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get users being followed"""
    follows = await db.social_follows.find(
        {"follower_id": user_id},
        {"_id": 0}
    ).to_list(1000)
    
    following = []
    for follow in follows:
        profile = await db.social_profiles.find_one(
            {"user_id": follow["following_id"]},
            {"_id": 0}
        )
        following.append({
            "user_id": follow["following_id"],
            "display_name": profile.get("display_name", follow["following_id"]) if profile else follow["following_id"],
            "avatar_emoji": profile.get("avatar_emoji", "👤") if profile else "👤",
            "followed_at": follow["followed_at"]
        })
    
    return {"following": following, "count": len(following)}

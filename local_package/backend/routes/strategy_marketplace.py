"""
Strategy Marketplace API Routes
================================
Publish, discover, and subscribe to trading strategies.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/marketplace", tags=["Strategy Marketplace"])

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


class StrategyListing(BaseModel):
    name: str
    description: str
    strategy_type: str  # momentum, mean_reversion, trend_following, etc.
    timeframe: str  # 1h, 4h, 1d, etc.
    coins: List[str]
    price_monthly: float = 0  # 0 = free
    is_public: bool = True


class StrategyReview(BaseModel):
    rating: int  # 1-5
    comment: Optional[str] = None


@router.get("/strategies")
async def list_strategies(
    category: Optional[str] = None,
    sort_by: str = "subscribers",  # subscribers, rating, returns, newest
    price_filter: str = "all",  # all, free, paid
    limit: int = Query(20, ge=1, le=50),
    db = Depends(get_database)
):
    """List available strategies in marketplace"""
    query = {"is_public": True, "status": "active"}
    
    if category:
        query["strategy_type"] = category
    
    if price_filter == "free":
        query["price_monthly"] = 0
    elif price_filter == "paid":
        query["price_monthly"] = {"$gt": 0}
    
    sort_field = {
        "subscribers": ("subscribers_count", -1),
        "rating": ("avg_rating", -1),
        "returns": ("performance.total_return", -1),
        "newest": ("created_at", -1)
    }.get(sort_by, ("subscribers_count", -1))
    
    strategies = await db.marketplace_strategies.find(
        query,
        {"_id": 0}
    ).sort(sort_field[0], sort_field[1]).limit(limit).to_list(limit)
    
    return {
        "strategies": strategies,
        "total": len(strategies),
        "filters": {
            "category": category,
            "sort_by": sort_by,
            "price_filter": price_filter
        },
        "message": "No strategies published yet. Be the first to publish a strategy!" if not strategies else None
    }


@router.get("/strategies/{strategy_id}")
async def get_strategy_details(
    strategy_id: str,
    db = Depends(get_database)
):
    """Get detailed strategy information"""
    strategy = await db.marketplace_strategies.find_one(
        {"strategy_id": strategy_id},
        {"_id": 0}
    )
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    # Get reviews
    reviews = await db.strategy_reviews.find(
        {"strategy_id": strategy_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    strategy["recent_reviews"] = reviews
    
    return strategy


@router.post("/strategies")
async def publish_strategy(
    listing: StrategyListing,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Publish a new strategy to marketplace"""
    strategy_id = f"strat_{str(uuid.uuid4())[:8]}"
    
    strategy = {
        "strategy_id": strategy_id,
        "creator_id": user_id,
        "creator": {"name": user_id, "verified": False},
        "name": listing.name,
        "description": listing.description,
        "strategy_type": listing.strategy_type,
        "timeframe": listing.timeframe,
        "coins": listing.coins,
        "price_monthly": listing.price_monthly,
        "is_public": listing.is_public,
        "status": "pending_review",
        "performance": {
            "total_return": 0,
            "win_rate": 0,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "trades_count": 0
        },
        "subscribers_count": 0,
        "avg_rating": 0,
        "reviews_count": 0,
        "revenue_share": 0.70,  # Creator gets 70%
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tags": []
    }
    
    await db.marketplace_strategies.insert_one(strategy)
    
    return {
        "status": "submitted",
        "strategy_id": strategy_id,
        "message": "Strategy submitted for review. Will be live within 24 hours."
    }


@router.post("/strategies/{strategy_id}/subscribe")
async def subscribe_to_strategy(
    strategy_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Subscribe to a marketplace strategy"""
    # Check if already subscribed
    existing = await db.strategy_subscriptions.find_one({
        "user_id": user_id,
        "strategy_id": strategy_id,
        "status": "active"
    })
    
    if existing:
        return {"status": "already_subscribed", "subscription": existing}
    
    subscription = {
        "subscription_id": str(uuid.uuid4()),
        "user_id": user_id,
        "strategy_id": strategy_id,
        "status": "active",
        "subscribed_at": datetime.now(timezone.utc).isoformat(),
        "auto_trade": False,
        "allocation_percent": 10
    }
    
    await db.strategy_subscriptions.insert_one(subscription)
    
    # Increment subscriber count
    await db.marketplace_strategies.update_one(
        {"strategy_id": strategy_id},
        {"$inc": {"subscribers_count": 1}}
    )
    
    return {
        "status": "subscribed",
        "subscription": {k: v for k, v in subscription.items() if k != "_id"}
    }


@router.delete("/strategies/{strategy_id}/subscribe")
async def unsubscribe_from_strategy(
    strategy_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Unsubscribe from a strategy"""
    result = await db.strategy_subscriptions.update_one(
        {"user_id": user_id, "strategy_id": strategy_id, "status": "active"},
        {"$set": {"status": "cancelled", "cancelled_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count > 0:
        await db.marketplace_strategies.update_one(
            {"strategy_id": strategy_id},
            {"$inc": {"subscribers_count": -1}}
        )
    
    return {"status": "unsubscribed"}


@router.get("/my-subscriptions")
async def get_my_subscriptions(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get user's strategy subscriptions"""
    subscriptions = await db.strategy_subscriptions.find(
        {"user_id": user_id, "status": "active"},
        {"_id": 0}
    ).to_list(50)
    
    # Enrich with strategy details
    for sub in subscriptions:
        strategy = await db.marketplace_strategies.find_one(
            {"strategy_id": sub["strategy_id"]},
            {"_id": 0, "name": 1, "performance": 1}
        )
        if strategy:
            sub["strategy_name"] = strategy.get("name")
            sub["strategy_performance"] = strategy.get("performance")
    
    return {
        "subscriptions": subscriptions,
        "total": len(subscriptions)
    }


@router.post("/strategies/{strategy_id}/review")
async def review_strategy(
    strategy_id: str,
    review: StrategyReview,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Leave a review for a strategy"""
    # Check if user is subscribed
    subscription = await db.strategy_subscriptions.find_one({
        "user_id": user_id,
        "strategy_id": strategy_id
    })
    
    if not subscription:
        raise HTTPException(status_code=400, detail="Must be subscribed to review")
    
    review_data = {
        "review_id": str(uuid.uuid4()),
        "strategy_id": strategy_id,
        "user_id": user_id,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.strategy_reviews.insert_one(review_data)
    
    # Update average rating
    pipeline = [
        {"$match": {"strategy_id": strategy_id}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}
    ]
    result = await db.strategy_reviews.aggregate(pipeline).to_list(1)
    
    if result:
        await db.marketplace_strategies.update_one(
            {"strategy_id": strategy_id},
            {"$set": {
                "avg_rating": round(result[0]["avg"], 1),
                "reviews_count": result[0]["count"]
            }}
        )
    
    return {"status": "reviewed", "review": review_data}


@router.get("/categories")
async def get_strategy_categories():
    """Get available strategy categories"""
    return {
        "categories": [
            {"id": "momentum", "name": "Momentum", "icon": "🚀", "description": "Trade with price momentum"},
            {"id": "mean_reversion", "name": "Mean Reversion", "icon": "🔄", "description": "Buy dips, sell rallies"},
            {"id": "trend_following", "name": "Trend Following", "icon": "📈", "description": "Follow the trend"},
            {"id": "dca", "name": "DCA", "icon": "💰", "description": "Dollar-cost averaging"},
            {"id": "scalping", "name": "Scalping", "icon": "⚡", "description": "Quick in-and-out trades"},
            {"id": "swing", "name": "Swing Trading", "icon": "🎢", "description": "Multi-day positions"},
            {"id": "ai_ml", "name": "AI/ML", "icon": "🤖", "description": "Machine learning based"},
            {"id": "arbitrage", "name": "Arbitrage", "icon": "⚖️", "description": "Cross-exchange opportunities"}
        ]
    }


@router.get("/my-published")
async def get_my_published_strategies(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Get strategies published by user"""
    strategies = await db.marketplace_strategies.find(
        {"creator_id": user_id},
        {"_id": 0}
    ).to_list(50)
    
    # Calculate revenue
    total_subscribers = sum(s.get("subscribers_count", 0) for s in strategies)
    total_revenue = sum(
        s.get("subscribers_count", 0) * s.get("price_monthly", 0) * s.get("revenue_share", 0.7)
        for s in strategies
    )
    
    return {
        "strategies": strategies,
        "total": len(strategies),
        "total_subscribers": total_subscribers,
        "estimated_monthly_revenue": round(total_revenue, 2)
    }

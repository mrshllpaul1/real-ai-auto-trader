"""
Copy Trading API Routes
========================
Enable users to follow and copy trades from successful traders.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/copy-trading", tags=["Copy Trading"])

# Global database reference
_db = None


def set_db(db):
    """Set database reference"""
    global _db
    _db = db


async def get_database():
    global _db
    if _db is None:
        from server import db
        _db = db
    return _db


# =============================================================================
# MODELS
# =============================================================================

class TraderProfile(BaseModel):
    trader_id: str
    display_name: str
    bio: Optional[str] = None
    is_public: bool = True
    min_copy_amount: float = 50.0
    max_copiers: int = 100
    profit_share_pct: float = 10.0  # Percentage of profits shared with copier


class FollowRequest(BaseModel):
    trader_id: str
    copy_amount: float
    copy_percentage: float = 100.0  # Copy 100% of trades by default
    max_trade_size: Optional[float] = None
    stop_loss_pct: Optional[float] = None


class CopySettings(BaseModel):
    copy_percentage: float = 100.0
    max_trade_size: Optional[float] = None
    stop_loss_pct: Optional[float] = None
    enabled: bool = True


# =============================================================================
# LEADERBOARD ENDPOINTS
# =============================================================================

@router.get("/leaderboard")
async def get_leaderboard(
    timeframe: str = "30d",
    sort_by: str = "roi",
    limit: int = 20,
    db = Depends(get_database)
):
    """
    Get top traders leaderboard.
    Timeframes: 7d, 30d, 90d, all
    Sort by: roi, win_rate, total_trades, copiers
    """
    try:
        # Calculate date filter
        days_map = {"7d": 7, "30d": 30, "90d": 90, "all": 3650}
        days = days_map.get(timeframe, 30)
        
        from datetime import timedelta
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get all public traders with their stats
        traders = await db.trader_profiles.find(
            {"is_public": True}
        ).to_list(100)
        
        leaderboard = []
        for trader in traders:
            trader_id = trader.get("trader_id")
            
            # Get trade history for this trader
            trades = await db.copy_trade_history.find({
                "trader_id": trader_id,
                "executed_at": {"$gte": start_date.isoformat()}
            }).to_list(1000)
            
            if not trades:
                # Use mock data for demo
                stats = {
                    "total_trades": 0,
                    "win_rate": 0,
                    "roi": 0,
                    "avg_trade_size": 0,
                    "copiers": 0
                }
            else:
                wins = sum(1 for t in trades if t.get("profit", 0) > 0)
                total_profit = sum(t.get("profit", 0) for t in trades)
                total_invested = sum(t.get("amount", 0) for t in trades)
                
                stats = {
                    "total_trades": len(trades),
                    "win_rate": round((wins / len(trades)) * 100, 1) if trades else 0,
                    "roi": round((total_profit / total_invested) * 100, 1) if total_invested > 0 else 0,
                    "avg_trade_size": round(total_invested / len(trades), 2) if trades else 0
                }
            
            # Get copier count
            copier_count = await db.copy_relationships.count_documents({
                "trader_id": trader_id,
                "active": True
            })
            
            leaderboard.append({
                "trader_id": trader_id,
                "display_name": trader.get("display_name", f"Trader_{trader_id[:8]}"),
                "bio": trader.get("bio"),
                "profit_share_pct": trader.get("profit_share_pct", 10),
                "copiers": copier_count,
                "stats": stats,
                "joined_at": trader.get("created_at")
            })
        
        # Sort by requested field
        sort_key = {
            "roi": lambda x: x["stats"]["roi"],
            "win_rate": lambda x: x["stats"]["win_rate"],
            "total_trades": lambda x: x["stats"]["total_trades"],
            "copiers": lambda x: x["copiers"]
        }.get(sort_by, lambda x: x["stats"]["roi"])
        
        leaderboard.sort(key=sort_key, reverse=True)
        
        return {
            "leaderboard": leaderboard[:limit],
            "timeframe": timeframe,
            "sort_by": sort_by,
            "total_traders": len(leaderboard),
            "message": "No traders found. Create a trader profile to appear on the leaderboard." if not leaderboard else None
        }
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# TRADER PROFILE ENDPOINTS
# =============================================================================

@router.post("/profile/create")
async def create_trader_profile(
    profile: TraderProfile,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Create or update trader profile to become a signal provider"""
    try:
        profile_data = {
            "trader_id": profile.trader_id or user_id,
            "user_id": user_id,
            "display_name": profile.display_name,
            "bio": profile.bio,
            "is_public": profile.is_public,
            "min_copy_amount": profile.min_copy_amount,
            "max_copiers": profile.max_copiers,
            "profit_share_pct": profile.profit_share_pct,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.trader_profiles.replace_one(
            {"trader_id": profile.trader_id},
            profile_data,
            upsert=True
        )
        
        return {"status": "success", "message": "Trader profile created", "profile": profile_data}
    except Exception as e:
        logger.error(f"Error creating trader profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{trader_id}")
async def get_trader_profile(trader_id: str, db = Depends(get_database)):
    """Get detailed trader profile"""
    try:
        profile = await db.trader_profiles.find_one(
            {"trader_id": trader_id},
            {"_id": 0}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Trader not found")
        
        # Get recent trades
        recent_trades = await db.copy_trade_history.find(
            {"trader_id": trader_id}
        ).sort("executed_at", -1).limit(10).to_list(10)
        
        # Get copier count
        copier_count = await db.copy_relationships.count_documents({
            "trader_id": trader_id,
            "active": True
        })
        
        return {
            "profile": profile,
            "copiers": copier_count,
            "recent_trades": [{k: v for k, v in t.items() if k != "_id"} for t in recent_trades]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trader profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# FOLLOWING ENDPOINTS
# =============================================================================

@router.post("/follow")
async def follow_trader(
    request: FollowRequest,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Start copying a trader's trades"""
    try:
        # Check if trader exists
        trader = await db.trader_profiles.find_one({"trader_id": request.trader_id})
        if not trader:
            raise HTTPException(status_code=404, detail="Trader not found")
        
        # Check minimum copy amount
        if request.copy_amount < trader.get("min_copy_amount", 50):
            raise HTTPException(
                status_code=400, 
                detail=f"Minimum copy amount is ${trader.get('min_copy_amount', 50)}"
            )
        
        # Check if already following
        existing = await db.copy_relationships.find_one({
            "user_id": user_id,
            "trader_id": request.trader_id
        })
        
        if existing and existing.get("active"):
            raise HTTPException(status_code=400, detail="Already following this trader")
        
        # Create copy relationship
        relationship = {
            "relationship_id": str(uuid.uuid4()),
            "user_id": user_id,
            "trader_id": request.trader_id,
            "copy_amount": request.copy_amount,
            "copy_percentage": request.copy_percentage,
            "max_trade_size": request.max_trade_size,
            "stop_loss_pct": request.stop_loss_pct,
            "active": True,
            "total_copied": 0,
            "total_profit": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.copy_relationships.replace_one(
            {"user_id": user_id, "trader_id": request.trader_id},
            relationship,
            upsert=True
        )
        
        return {
            "status": "success",
            "message": f"Now copying {trader.get('display_name', request.trader_id)}",
            "relationship": relationship
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error following trader: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unfollow/{trader_id}")
async def unfollow_trader(
    trader_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Stop copying a trader"""
    try:
        result = await db.copy_relationships.update_one(
            {"user_id": user_id, "trader_id": trader_id},
            {"$set": {"active": False, "ended_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Not following this trader")
        
        return {"status": "success", "message": "Unfollowed trader"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unfollowing trader: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/following")
async def get_following(user_id: str = "default_user", db = Depends(get_database)):
    """Get list of traders user is following"""
    try:
        relationships = await db.copy_relationships.find(
            {"user_id": user_id, "active": True},
            {"_id": 0}
        ).to_list(50)
        
        # Enrich with trader details
        for rel in relationships:
            trader = await db.trader_profiles.find_one(
                {"trader_id": rel["trader_id"]},
                {"_id": 0, "display_name": 1, "profit_share_pct": 1}
            )
            if trader:
                rel["trader_name"] = trader.get("display_name")
                rel["profit_share_pct"] = trader.get("profit_share_pct")
        
        return {
            "following": relationships,
            "total": len(relationships)
        }
    except Exception as e:
        logger.error(f"Error getting following list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings/{trader_id}")
async def update_copy_settings(
    trader_id: str,
    settings: CopySettings,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Update copy trading settings for a specific trader"""
    try:
        result = await db.copy_relationships.update_one(
            {"user_id": user_id, "trader_id": trader_id},
            {"$set": {
                "copy_percentage": settings.copy_percentage,
                "max_trade_size": settings.max_trade_size,
                "stop_loss_pct": settings.stop_loss_pct,
                "enabled": settings.enabled,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Copy relationship not found")
        
        return {"status": "success", "message": "Settings updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating copy settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# COPY HISTORY ENDPOINTS
# =============================================================================

@router.get("/history")
async def get_copy_history(
    user_id: str = "default_user",
    limit: int = 50,
    db = Depends(get_database)
):
    """Get history of copied trades"""
    try:
        history = await db.copied_trades.find(
            {"copier_id": user_id},
            {"_id": 0}
        ).sort("copied_at", -1).limit(limit).to_list(limit)
        
        # Calculate stats
        total_profit = sum(t.get("profit", 0) for t in history)
        total_invested = sum(t.get("amount", 0) for t in history)
        wins = sum(1 for t in history if t.get("profit", 0) > 0)
        
        return {
            "history": history,
            "stats": {
                "total_trades": len(history),
                "total_profit": round(total_profit, 2),
                "total_invested": round(total_invested, 2),
                "win_rate": round((wins / len(history)) * 100, 1) if history else 0,
                "roi": round((total_profit / total_invested) * 100, 1) if total_invested > 0 else 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting copy history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_copy_trading_stats(user_id: str = "default_user", db = Depends(get_database)):
    """Get overall copy trading statistics"""
    try:
        # Get all active relationships
        relationships = await db.copy_relationships.find(
            {"user_id": user_id, "active": True}
        ).to_list(50)
        
        # Get all copied trades
        all_trades = await db.copied_trades.find(
            {"copier_id": user_id}
        ).to_list(1000)
        
        total_allocated = sum(r.get("copy_amount", 0) for r in relationships)
        total_profit = sum(t.get("profit", 0) for t in all_trades)
        total_trades = len(all_trades)
        
        return {
            "traders_following": len(relationships),
            "total_allocated": round(total_allocated, 2),
            "total_profit": round(total_profit, 2),
            "total_trades_copied": total_trades,
            "active_copies": sum(1 for r in relationships if r.get("enabled", True)),
            "best_performing_trader": None  # Would calculate from data
        }
    except Exception as e:
        logger.error(f"Error getting copy trading stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

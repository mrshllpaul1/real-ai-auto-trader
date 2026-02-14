from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter()

class TraderProfileCreate(BaseModel):
    display_name: str
    bio: str = ""
    is_public: bool = True

class CopyTradingSettings(BaseModel):
    max_position_pct: float = 10
    max_daily_trades: int = 5
    copy_stop_loss: bool = True
    copy_take_profit: bool = True
    mode: str = 'paper'

class ShareStrategyRequest(BaseModel):
    name: str
    description: str = ""
    parameters: Dict[str, Any]
    backtest_results: Dict[str, Any] = {}
    is_public: bool = True

async def get_social_service():
    from server import db
    from services.social_trading import SocialTradingService
    return SocialTradingService(db)

# ============= PROFILE =============

@router.post("/profile/{user_id}")
async def create_profile(
    user_id: str,
    profile: TraderProfileCreate,
    service = Depends(get_social_service)
):
    """Create or update trader profile"""
    try:
        return await service.create_trader_profile(
            user_id,
            profile.display_name,
            profile.bio,
            profile.is_public
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.get("/profile/{user_id}")
async def get_profile(
    user_id: str,
    service = Depends(get_social_service)
):
    """Get trader profile"""
    try:
        profile = await service.get_trader_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

# ============= LEADERBOARD =============

@router.get("/leaderboard")
async def get_leaderboard(
    sort_by: str = 'total_profit_pct',
    limit: int = 20,
    service = Depends(get_social_service)
):
    """Get top traders leaderboard"""
    try:
        traders = await service.get_leaderboard(sort_by, limit)
        return {"traders": traders, "count": len(traders)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.get("/leaderboard/weekly")
async def get_weekly_top(
    limit: int = 10,
    service = Depends(get_social_service)
):
    """Get top performers this week"""
    try:
        return await service.get_weekly_top_performers(limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

# ============= FOLLOWING =============

@router.post("/follow/{trader_id}")
async def follow_trader(
    trader_id: str,
    user_id: str,
    service = Depends(get_social_service)
):
    """Follow a trader"""
    try:
        return await service.follow_trader(user_id, trader_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.delete("/follow/{trader_id}")
async def unfollow_trader(
    trader_id: str,
    user_id: str,
    service = Depends(get_social_service)
):
    """Unfollow a trader"""
    try:
        return await service.unfollow_trader(user_id, trader_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.get("/following/{user_id}")
async def get_following(
    user_id: str,
    service = Depends(get_social_service)
):
    """Get traders a user follows"""
    try:
        following = await service.get_following(user_id)
        return {"following": following, "count": len(following)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.get("/followers/{user_id}")
async def get_followers(
    user_id: str,
    service = Depends(get_social_service)
):
    """Get user's followers"""
    try:
        followers = await service.get_followers(user_id)
        return {"followers": followers, "count": len(followers)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

# ============= COPY TRADING =============

@router.post("/copy/{trader_id}")
async def enable_copy_trading(
    trader_id: str,
    user_id: str,
    settings: CopyTradingSettings,
    service = Depends(get_social_service)
):
    """Enable copy trading for a trader"""
    try:
        return await service.enable_copy_trading(user_id, trader_id, settings.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.delete("/copy/{trader_id}")
async def disable_copy_trading(
    trader_id: str,
    user_id: str,
    service = Depends(get_social_service)
):
    """Disable copy trading"""
    try:
        return await service.disable_copy_trading(user_id, trader_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.get("/copy-settings/{user_id}")
async def get_copy_settings(
    user_id: str,
    service = Depends(get_social_service)
):
    """Get copy trading settings"""
    try:
        settings = await service.get_copy_settings(user_id)
        return {"settings": settings, "count": len(settings)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

# ============= STRATEGIES =============

@router.post("/strategies/share")
async def share_strategy(
    user_id: str,
    strategy: ShareStrategyRequest,
    service = Depends(get_social_service)
):
    """Share a trading strategy"""
    try:
        return await service.share_strategy(user_id, strategy.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.get("/strategies")
async def get_shared_strategies(
    sort_by: str = 'likes',
    limit: int = 20,
    service = Depends(get_social_service)
):
    """Get public shared strategies"""
    try:
        strategies = await service.get_shared_strategies(sort_by, limit)
        return {"strategies": strategies, "count": len(strategies)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.post("/strategies/{strategy_id}/like")
async def like_strategy(
    strategy_id: str,
    user_id: str,
    service = Depends(get_social_service)
):
    """Like a strategy"""
    try:
        return await service.like_strategy(user_id, strategy_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@router.post("/strategies/{strategy_id}/copy")
async def copy_strategy(
    strategy_id: str,
    user_id: str,
    service = Depends(get_social_service)
):
    """Copy a strategy"""
    try:
        return await service.copy_strategy(user_id, strategy_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

# ============= ACTIVITY FEED =============

@router.get("/feed/{user_id}")
async def get_activity_feed(
    user_id: str,
    limit: int = 50,
    service = Depends(get_social_service)
):
    """Get activity feed from followed traders"""
    try:
        activities = await service.get_activity_feed(user_id, limit)
        return {"activities": activities, "count": len(activities)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

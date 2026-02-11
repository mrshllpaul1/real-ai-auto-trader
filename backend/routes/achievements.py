"""
Achievement & Badge API Routes
Gamification endpoints for user achievements and progress
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/achievements", tags=["Achievements"])

# Global references
_db = None
_achievement_service = None


def set_dependencies(database, achievement_service):
    """Set dependencies from main app"""
    global _db, _achievement_service
    _db = database
    _achievement_service = achievement_service


@router.get("/{user_id}")
async def get_user_achievements(user_id: str):
    """
    Get all achievements earned by a user
    
    Args:
        user_id: User ID
    
    Returns:
        Dict with earned achievements, total points, and achievement details
    """
    try:
        if _achievement_service is None:
            raise HTTPException(status_code=500, detail="Achievement service not initialized")
        
        achievements = await _achievement_service.get_user_achievements(user_id)
        
        return {
            "success": True,
            **achievements
        }
        
    except Exception as e:
        logger.error(f"Error getting achievements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/progress")
async def get_achievement_progress(user_id: str):
    """
    Get progress towards unearned achievements
    
    Args:
        user_id: User ID
    
    Returns:
        List of achievements with progress percentages
    """
    try:
        if _achievement_service is None:
            raise HTTPException(status_code=500, detail="Achievement service not initialized")
        
        progress = await _achievement_service.get_achievement_progress(user_id)
        
        return {
            "success": True,
            "progress": progress
        }
        
    except Exception as e:
        logger.error(f"Error getting achievement progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/check")
async def check_achievements(user_id: str):
    """
    Check and award new achievements for a user
    
    Args:
        user_id: User ID
    
    Returns:
        List of newly earned achievements
    """
    try:
        if _achievement_service is None:
            raise HTTPException(status_code=500, detail="Achievement service not initialized")
        
        new_achievements = await _achievement_service.check_achievements(user_id)
        
        return {
            "success": True,
            "new_achievements": new_achievements,
            "count": len(new_achievements)
        }
        
    except Exception as e:
        logger.error(f"Error checking achievements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/stats")
async def get_user_stats(user_id: str):
    """
    Get user statistics used for achievement calculations
    
    Args:
        user_id: User ID
    
    Returns:
        Dict with user trading statistics
    """
    try:
        if _achievement_service is None:
            raise HTTPException(status_code=500, detail="Achievement service not initialized")
        
        stats = await _achievement_service.get_user_stats(user_id)
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list/all")
async def list_all_achievements():
    """
    Get list of all available achievements
    
    Returns:
        Dict with all achievement definitions
    """
    try:
        from services.achievement_service import ACHIEVEMENTS
        
        # Convert achievements to list format
        achievements_list = []
        for achievement_id, achievement in ACHIEVEMENTS.items():
            achievement_data = {
                **achievement,
                "condition": None  # Don't expose condition function
            }
            achievements_list.append(achievement_data)
        
        return {
            "success": True,
            "achievements": achievements_list,
            "total": len(achievements_list)
        }
        
    except Exception as e:
        logger.error(f"Error listing achievements: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard/top")
async def get_achievement_leaderboard(limit: int = Query(10, ge=1, le=100)):
    """
    Get achievement leaderboard (top users by points)
    
    Args:
        limit: Number of users to return (default: 10, max: 100)
    
    Returns:
        List of top users with achievement points
    """
    try:
        if _db is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Get top users by achievement points
        leaderboard = await _db.achievements.find(
            {},
            {"user_id": 1, "total_points": 1, "earned": 1, "_id": 0}
        ).sort("total_points", -1).limit(limit).to_list(length=limit)
        
        # Enrich with user info
        enriched = []
        for entry in leaderboard:
            user = await _db.users.find_one({"user_id": entry["user_id"]})
            enriched.append({
                "user_id": entry["user_id"],
                "username": user.get("username", "Anonymous") if user else "Anonymous",
                "total_points": entry.get("total_points", 0),
                "achievements_count": len(entry.get("earned", []))
            })
        
        return {
            "success": True,
            "leaderboard": enriched
        }
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

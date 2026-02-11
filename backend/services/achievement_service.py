"""
Achievement & Badge System
Gamification system to reward user milestones and encourage engagement
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BadgeCategory(str, Enum):
    """Badge categories"""
    TRADING = "trading"
    PROFIT = "profit"
    STRATEGY = "strategy"
    AI = "ai"
    MILESTONE = "milestone"
    SPECIAL = "special"


class BadgeRarity(str, Enum):
    """Badge rarity levels"""
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


# Achievement definitions
ACHIEVEMENTS = {
    # Trading achievements
    "first_trade": {
        "id": "first_trade",
        "name": "First Steps",
        "description": "Execute your first trade",
        "category": BadgeCategory.TRADING,
        "rarity": BadgeRarity.COMMON,
        "icon": "🎯",
        "points": 10,
        "condition": lambda stats: stats.get("total_trades", 0) >= 1
    },
    "trader_10": {
        "id": "trader_10",
        "name": "Active Trader",
        "description": "Execute 10 trades",
        "category": BadgeCategory.TRADING,
        "rarity": BadgeRarity.COMMON,
        "icon": "📈",
        "points": 25,
        "condition": lambda stats: stats.get("total_trades", 0) >= 10
    },
    "trader_100": {
        "id": "trader_100",
        "name": "Seasoned Trader",
        "description": "Execute 100 trades",
        "category": BadgeCategory.TRADING,
        "rarity": BadgeRarity.RARE,
        "icon": "💹",
        "points": 100,
        "condition": lambda stats: stats.get("total_trades", 0) >= 100
    },
    "trader_1000": {
        "id": "trader_1000",
        "name": "Master Trader",
        "description": "Execute 1,000 trades",
        "category": BadgeCategory.TRADING,
        "rarity": BadgeRarity.EPIC,
        "icon": "🏆",
        "points": 500,
        "condition": lambda stats: stats.get("total_trades", 0) >= 1000
    },
    
    # Profit achievements
    "first_profit": {
        "id": "first_profit",
        "name": "First Win",
        "description": "Make your first profitable trade",
        "category": BadgeCategory.PROFIT,
        "rarity": BadgeRarity.COMMON,
        "icon": "💚",
        "points": 15,
        "condition": lambda stats: stats.get("winning_trades", 0) >= 1
    },
    "profit_100": {
        "id": "profit_100",
        "name": "Hundred Club",
        "description": "Earn $100 in total profit",
        "category": BadgeCategory.PROFIT,
        "rarity": BadgeRarity.COMMON,
        "icon": "💵",
        "points": 50,
        "condition": lambda stats: stats.get("total_profit", 0) >= 100
    },
    "profit_1k": {
        "id": "profit_1k",
        "name": "Thousand Club",
        "description": "Earn $1,000 in total profit",
        "category": BadgeCategory.PROFIT,
        "rarity": BadgeRarity.RARE,
        "icon": "💸",
        "points": 200,
        "condition": lambda stats: stats.get("total_profit", 0) >= 1000
    },
    "profit_10k": {
        "id": "profit_10k",
        "name": "High Roller",
        "description": "Earn $10,000 in total profit",
        "category": BadgeCategory.PROFIT,
        "rarity": BadgeRarity.EPIC,
        "icon": "💰",
        "points": 1000,
        "condition": lambda stats: stats.get("total_profit", 0) >= 10000
    },
    "profit_100k": {
        "id": "profit_100k",
        "name": "Whale",
        "description": "Earn $100,000 in total profit",
        "category": BadgeCategory.PROFIT,
        "rarity": BadgeRarity.LEGENDARY,
        "icon": "🐋",
        "points": 5000,
        "condition": lambda stats: stats.get("total_profit", 0) >= 100000
    },
    
    # Win rate achievements
    "consistent_50": {
        "id": "consistent_50",
        "name": "Consistent",
        "description": "Achieve 50%+ win rate over 20 trades",
        "category": BadgeCategory.PROFIT,
        "rarity": BadgeRarity.RARE,
        "icon": "⚖️",
        "points": 150,
        "condition": lambda stats: stats.get("total_trades", 0) >= 20 and stats.get("win_rate", 0) >= 50
    },
    "consistent_70": {
        "id": "consistent_70",
        "name": "Sharp",
        "description": "Achieve 70%+ win rate over 50 trades",
        "category": BadgeCategory.PROFIT,
        "rarity": BadgeRarity.EPIC,
        "icon": "🎯",
        "points": 500,
        "condition": lambda stats: stats.get("total_trades", 0) >= 50 and stats.get("win_rate", 0) >= 70
    },
    "consistent_90": {
        "id": "consistent_90",
        "name": "Legendary Trader",
        "description": "Achieve 90%+ win rate over 100 trades",
        "category": BadgeCategory.PROFIT,
        "rarity": BadgeRarity.LEGENDARY,
        "icon": "👑",
        "points": 2000,
        "condition": lambda stats: stats.get("total_trades", 0) >= 100 and stats.get("win_rate", 0) >= 90
    },
    
    # AI & Strategy achievements
    "first_strategy": {
        "id": "first_strategy",
        "name": "Strategist",
        "description": "Create your first AI strategy",
        "category": BadgeCategory.STRATEGY,
        "rarity": BadgeRarity.COMMON,
        "icon": "🧠",
        "points": 20,
        "condition": lambda stats: stats.get("strategies_created", 0) >= 1
    },
    "ai_trained": {
        "id": "ai_trained",
        "name": "AI Trainer",
        "description": "Train an AI model",
        "category": BadgeCategory.AI,
        "rarity": BadgeRarity.RARE,
        "icon": "🤖",
        "points": 100,
        "condition": lambda stats: stats.get("models_trained", 0) >= 1
    },
    "tethys_master": {
        "id": "tethys_master",
        "name": "Tethys Master",
        "description": "Run Tethys AI for 100 hours",
        "category": BadgeCategory.AI,
        "rarity": BadgeRarity.EPIC,
        "icon": "🔮",
        "points": 300,
        "condition": lambda stats: stats.get("tethys_hours", 0) >= 100
    },
    
    # Milestone achievements
    "early_adopter": {
        "id": "early_adopter",
        "name": "Early Adopter",
        "description": "Join the platform in its first year",
        "category": BadgeCategory.MILESTONE,
        "rarity": BadgeRarity.SPECIAL,
        "icon": "🌟",
        "points": 200,
        "condition": lambda stats: True  # Special condition
    },
    "daily_streak_7": {
        "id": "daily_streak_7",
        "name": "Committed",
        "description": "Login for 7 consecutive days",
        "category": BadgeCategory.MILESTONE,
        "rarity": BadgeRarity.RARE,
        "icon": "🔥",
        "points": 100,
        "condition": lambda stats: stats.get("login_streak", 0) >= 7
    },
    "daily_streak_30": {
        "id": "daily_streak_30",
        "name": "Dedicated",
        "description": "Login for 30 consecutive days",
        "category": BadgeCategory.MILESTONE,
        "rarity": BadgeRarity.EPIC,
        "icon": "⚡",
        "points": 500,
        "condition": lambda stats: stats.get("login_streak", 0) >= 30
    },
    "portfolio_1k": {
        "id": "portfolio_1k",
        "name": "Building Wealth",
        "description": "Reach $1,000 portfolio value",
        "category": BadgeCategory.MILESTONE,
        "rarity": BadgeRarity.COMMON,
        "icon": "📊",
        "points": 50,
        "condition": lambda stats: stats.get("portfolio_value", 0) >= 1000
    },
    "portfolio_10k": {
        "id": "portfolio_10k",
        "name": "Wealth Builder",
        "description": "Reach $10,000 portfolio value",
        "category": BadgeCategory.MILESTONE,
        "rarity": BadgeRarity.RARE,
        "icon": "💎",
        "points": 300,
        "condition": lambda stats: stats.get("portfolio_value", 0) >= 10000
    },
    "portfolio_100k": {
        "id": "portfolio_100k",
        "name": "Six Figures",
        "description": "Reach $100,000 portfolio value",
        "category": BadgeCategory.MILESTONE,
        "rarity": BadgeRarity.EPIC,
        "icon": "💍",
        "points": 1500,
        "condition": lambda stats: stats.get("portfolio_value", 0) >= 100000
    },
    "portfolio_1m": {
        "id": "portfolio_1m",
        "name": "Millionaire",
        "description": "Reach $1,000,000 portfolio value",
        "category": BadgeCategory.MILESTONE,
        "rarity": BadgeRarity.LEGENDARY,
        "icon": "🏰",
        "points": 10000,
        "condition": lambda stats: stats.get("portfolio_value", 0) >= 1000000
    }
}


class AchievementService:
    """Service for managing achievements and badges"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Gather user statistics for achievement checking"""
        try:
            # Get trading stats
            trades = await self.db.trades.find({"user_id": user_id}).to_list(length=10000)
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.get("profit_loss", 0) > 0])
            total_profit = sum(t.get("profit_loss", 0) for t in trades)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Get portfolio value
            portfolio = await self.db.portfolios.find_one({"user_id": user_id})
            portfolio_value = portfolio.get("total_value", 0) if portfolio else 0
            
            # Get strategy count
            strategies = await self.db.strategies.count_documents({"user_id": user_id})
            
            # Get model training count
            training_records = await self.db.training_history.count_documents({"user_id": user_id})
            
            # Get Tethys usage
            tethys_logs = await self.db.tethys_logs.find({"user_id": user_id}).to_list(length=10000)
            tethys_hours = sum(log.get("duration_hours", 0) for log in tethys_logs)
            
            # Get login streak
            user = await self.db.users.find_one({"user_id": user_id})
            login_streak = user.get("login_streak", 0) if user else 0
            
            return {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "total_profit": total_profit,
                "win_rate": win_rate,
                "portfolio_value": portfolio_value,
                "strategies_created": strategies,
                "models_trained": training_records,
                "tethys_hours": tethys_hours,
                "login_streak": login_streak
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {}
    
    async def check_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        """Check and award new achievements"""
        try:
            # Get user stats
            stats = await self.get_user_stats(user_id)
            
            # Get already earned achievements
            user_achievements = await self.db.achievements.find_one({"user_id": user_id})
            earned_ids = set(user_achievements.get("earned", [])) if user_achievements else set()
            
            # Check each achievement
            new_achievements = []
            
            for achievement_id, achievement in ACHIEVEMENTS.items():
                if achievement_id in earned_ids:
                    continue
                
                # Check if condition is met
                if achievement["condition"](stats):
                    # Award achievement
                    await self.award_achievement(user_id, achievement_id)
                    new_achievements.append(achievement)
            
            return new_achievements
            
        except Exception as e:
            logger.error(f"Error checking achievements: {str(e)}")
            return []
    
    async def award_achievement(self, user_id: str, achievement_id: str):
        """Award an achievement to a user"""
        try:
            achievement = ACHIEVEMENTS.get(achievement_id)
            if not achievement:
                return
            
            # Update user achievements
            await self.db.achievements.update_one(
                {"user_id": user_id},
                {
                    "$addToSet": {"earned": achievement_id},
                    "$inc": {"total_points": achievement["points"]},
                    "$set": {
                        f"achievement_dates.{achievement_id}": datetime.now()
                    }
                },
                upsert=True
            )
            
            logger.info(f"Awarded '{achievement['name']}' to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error awarding achievement: {str(e)}")
    
    async def get_user_achievements(self, user_id: str) -> Dict[str, Any]:
        """Get all achievements for a user"""
        try:
            user_achievements = await self.db.achievements.find_one({"user_id": user_id})
            
            if not user_achievements:
                return {
                    "earned": [],
                    "total_points": 0,
                    "achievements": []
                }
            
            earned_ids = user_achievements.get("earned", [])
            
            # Build achievement details
            achievements = []
            for achievement_id in earned_ids:
                achievement = ACHIEVEMENTS.get(achievement_id)
                if achievement:
                    achievement_data = {
                        **achievement,
                        "earned_date": user_achievements.get("achievement_dates", {}).get(achievement_id)
                    }
                    achievements.append(achievement_data)
            
            return {
                "earned": earned_ids,
                "total_points": user_achievements.get("total_points", 0),
                "achievements": achievements
            }
            
        except Exception as e:
            logger.error(f"Error getting user achievements: {str(e)}")
            return {"earned": [], "total_points": 0, "achievements": []}
    
    async def get_achievement_progress(self, user_id: str) -> List[Dict[str, Any]]:
        """Get progress towards unearned achievements"""
        try:
            stats = await self.get_user_stats(user_id)
            user_achievements = await self.db.achievements.find_one({"user_id": user_id})
            earned_ids = set(user_achievements.get("earned", [])) if user_achievements else set()
            
            progress = []
            
            for achievement_id, achievement in ACHIEVEMENTS.items():
                if achievement_id in earned_ids:
                    continue
                
                # Calculate progress based on achievement type using a lookup table
                current = 0
                target = 0
                
                # Achievement target lookup table for accuracy
                achievement_targets = {
                    "trader_10": 10,
                    "trader_100": 100,
                    "trader_1000": 1000,
                    "profit_100": 100,
                    "profit_1k": 1000,
                    "profit_10k": 10000,
                    "profit_100k": 100000,
                    "consistent_50": 50,
                    "consistent_70": 70,
                    "consistent_90": 90,
                    "portfolio_1k": 1000,
                    "portfolio_10k": 10000,
                    "portfolio_100k": 100000,
                    "portfolio_1m": 1000000,
                }
                
                if "trader_" in achievement_id:
                    current = stats.get("total_trades", 0)
                    target = achievement_targets.get(achievement_id, 0)
                elif "profit_" in achievement_id:
                    current = stats.get("total_profit", 0)
                    target = achievement_targets.get(achievement_id, 0)
                elif "consistent_" in achievement_id:
                    current = stats.get("win_rate", 0)
                    target = achievement_targets.get(achievement_id, 0)
                elif "portfolio_" in achievement_id:
                    current = stats.get("portfolio_value", 0)
                    target = achievement_targets.get(achievement_id, 0)
                
                progress_pct = min(100, (current / target * 100)) if target > 0 else 0
                
                progress.append({
                    **achievement,
                    "current": current,
                    "target": target,
                    "progress": progress_pct
                })
            
            return progress
            
        except Exception as e:
            logger.error(f"Error getting achievement progress: {str(e)}")
            return []

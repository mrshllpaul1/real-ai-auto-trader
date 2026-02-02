"""
Budget Manager Service
Controls real money trading budget - only uses allocated funds, never touches other assets.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class BudgetManager:
    """
    Manages trading budget to ensure we only use allocated funds.
    NEVER touches user's existing assets - only uses the budget they provide.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.trading_budgets
    
    async def get_budget(self, user_id: str = "default") -> Dict[str, Any]:
        """Get current budget allocation"""
        budget = await self.collection.find_one(
            {"user_id": user_id},
            {"_id": 0}
        )
        
        if not budget:
            # Default budget - no real money allocated
            return {
                "user_id": user_id,
                "allocated_budget": 0,
                "used_budget": 0,
                "available_budget": 0,
                "paper_budget": 500,
                "real_trading_enabled": False,
                "created_at": datetime.utcnow().isoformat()
            }
        
        return budget
    
    async def set_budget(
        self,
        amount: float,
        user_id: str = "default",
        enable_real_trading: bool = False
    ) -> Dict[str, Any]:
        """
        Set the trading budget. This is the ONLY money the system will use.
        Will NEVER touch any other assets in your Kraken account.
        """
        if amount < 0:
            raise ValueError("Budget cannot be negative")
        
        existing = await self.get_budget(user_id)
        used = existing.get("used_budget", 0)
        
        budget = {
            "user_id": user_id,
            "allocated_budget": amount,
            "used_budget": used,
            "available_budget": max(0, amount - used),
            "paper_budget": 500,  # Paper trading always available
            "real_trading_enabled": enable_real_trading and amount > 0,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await self.collection.update_one(
            {"user_id": user_id},
            {"$set": budget},
            upsert=True
        )
        
        logger.info(f"Budget set: ${amount} (Real trading: {budget['real_trading_enabled']})")
        return budget
    
    async def allocate_funds(
        self,
        amount: float,
        purpose: str,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Allocate funds from the budget for a trade.
        Returns allocation details or error if insufficient funds.
        """
        budget = await self.get_budget(user_id)
        available = budget.get("available_budget", 0)
        
        if amount > available:
            return {
                "success": False,
                "error": f"Insufficient budget. Requested: ${amount:.2f}, Available: ${available:.2f}",
                "available": available,
                "requested": amount
            }
        
        # Update budget
        new_used = budget.get("used_budget", 0) + amount
        new_available = budget.get("allocated_budget", 0) - new_used
        
        await self.collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "used_budget": new_used,
                "available_budget": new_available,
                "last_allocation_at": datetime.utcnow().isoformat()
            }}
        )
        
        # Record allocation
        await self.db.budget_allocations.insert_one({
            "user_id": user_id,
            "amount": amount,
            "purpose": purpose,
            "timestamp": datetime.utcnow().isoformat(),
            "remaining_budget": new_available
        })
        
        return {
            "success": True,
            "allocated": amount,
            "remaining_budget": new_available,
            "purpose": purpose
        }
    
    async def release_funds(
        self,
        amount: float,
        reason: str,
        pnl: float = 0,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Release funds back to the budget (when position closes).
        Includes any profit/loss from the trade.
        """
        budget = await self.get_budget(user_id)
        
        # Calculate return: original amount + profit/loss
        return_amount = amount + pnl
        
        new_used = max(0, budget.get("used_budget", 0) - amount)
        new_available = budget.get("allocated_budget", 0) - new_used + pnl
        
        # Update allocated budget if we made profit
        new_allocated = budget.get("allocated_budget", 0) + max(0, pnl)
        
        await self.collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "allocated_budget": new_allocated,
                "used_budget": new_used,
                "available_budget": new_available,
                "last_release_at": datetime.utcnow().isoformat()
            }}
        )
        
        # Record release
        await self.db.budget_releases.insert_one({
            "user_id": user_id,
            "original_amount": amount,
            "pnl": pnl,
            "return_amount": return_amount,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "success": True,
            "released": amount,
            "pnl": pnl,
            "new_available": new_available,
            "reason": reason
        }
    
    async def can_trade_real(self, amount: float, user_id: str = "default") -> Dict[str, Any]:
        """Check if real trading is allowed and has sufficient budget"""
        budget = await self.get_budget(user_id)
        
        if not budget.get("real_trading_enabled"):
            return {
                "allowed": False,
                "reason": "Real trading not enabled. Set a budget first.",
                "budget": budget
            }
        
        if amount > budget.get("available_budget", 0):
            return {
                "allowed": False,
                "reason": f"Insufficient budget. Need ${amount:.2f}, have ${budget['available_budget']:.2f}",
                "budget": budget
            }
        
        return {
            "allowed": True,
            "available": budget["available_budget"],
            "budget": budget
        }
    
    async def get_budget_history(self, user_id: str = "default", limit: int = 50) -> list:
        """Get budget allocation/release history"""
        allocations = await self.db.budget_allocations.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        releases = await self.db.budget_releases.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        # Combine and sort
        history = [
            {**a, "type": "allocation"} for a in allocations
        ] + [
            {**r, "type": "release"} for r in releases
        ]
        
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        return history[:limit]

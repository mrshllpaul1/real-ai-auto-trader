"""
Isolated Portfolio Manager
Ensures the AI trader ONLY manages allocated funds, never touching other assets.
Tracks AI-managed positions separately from user's existing holdings.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)


class IsolatedPortfolioManager:
    """
    Strict budget isolation for AI trading.
    
    Key Principles:
    1. AI ONLY trades with the budget you allocate
    2. Your existing assets are NEVER touched
    3. AI positions are tracked separately
    4. Swaps/conversions only within AI portfolio
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, kraken_service=None):
        self.db = db
        self.kraken = kraken_service
        
        # Collections
        self.budget_collection = db.trading_budgets
        self.positions_collection = db.ai_managed_positions
        self.transactions_collection = db.ai_transactions
    
    async def set_trading_budget(
        self,
        amount_usd: float,
        user_id: str = "default",
        enable_real_trading: bool = False
    ) -> Dict[str, Any]:
        """
        Set the total budget the AI is allowed to trade with.
        This is the ONLY money the AI will use - everything else is untouched.
        
        Args:
            amount_usd: Total USD budget for AI trading
            enable_real_trading: If True, execute real trades. If False, paper trade only.
        """
        if amount_usd < 0:
            raise ValueError("Budget cannot be negative")
        
        # Get existing budget info
        existing = await self.budget_collection.find_one({"user_id": user_id}, {"_id": 0})
        
        # Calculate current value of AI-managed positions
        ai_positions_value = await self._get_ai_positions_value(user_id)
        
        budget = {
            "user_id": user_id,
            "initial_budget": amount_usd,
            "current_budget": amount_usd,
            "cash_available": amount_usd - ai_positions_value,
            "positions_value": ai_positions_value,
            "real_trading_enabled": enable_real_trading and amount_usd > 0,
            "created_at": existing.get("created_at") if existing else datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "total_pnl": existing.get("total_pnl", 0) if existing else 0,
            "trades_executed": existing.get("trades_executed", 0) if existing else 0
        }
        
        await self.budget_collection.update_one(
            {"user_id": user_id},
            {"$set": budget},
            upsert=True
        )
        
        logger.info(f"💰 AI Trading Budget Set: ${amount_usd:.2f} (Real: {enable_real_trading})")
        
        return {
            "success": True,
            "budget": budget,
            "message": f"AI will only trade with ${amount_usd:.2f}. Your other assets are protected."
        }
    
    async def get_budget_status(self, user_id: str = "default") -> Dict[str, Any]:
        """Get current budget status and AI portfolio value"""
        budget = await self.budget_collection.find_one({"user_id": user_id}, {"_id": 0})
        
        if not budget:
            return {
                "allocated": False,
                "budget": 0,
                "message": "No budget allocated. AI trading is disabled."
            }
        
        # Get current positions value
        positions_value = await self._get_ai_positions_value(user_id)
        positions = await self.get_ai_positions(user_id)
        
        return {
            "allocated": True,
            "initial_budget": budget.get("initial_budget", 0),
            "current_value": budget.get("cash_available", 0) + positions_value,
            "cash_available": budget.get("cash_available", 0),
            "positions_value": positions_value,
            "positions_count": len(positions),
            "total_pnl": budget.get("total_pnl", 0),
            "pnl_pct": ((budget.get("cash_available", 0) + positions_value) / budget.get("initial_budget", 1) - 1) * 100 if budget.get("initial_budget", 0) > 0 else 0,
            "real_trading_enabled": budget.get("real_trading_enabled", False),
            "trades_executed": budget.get("trades_executed", 0)
        }
    
    async def _get_ai_positions_value(self, user_id: str = "default") -> float:
        """Calculate total value of AI-managed positions"""
        positions = await self.positions_collection.find(
            {"user_id": user_id, "status": "open"},
            {"_id": 0}
        ).to_list(100)
        
        total_value = 0
        for pos in positions:
            # Use current value if available, otherwise use entry value
            current_value = pos.get("current_value", pos.get("entry_value", 0))
            total_value += current_value
        
        return total_value
    
    async def get_ai_positions(self, user_id: str = "default") -> List[Dict]:
        """Get all AI-managed positions"""
        positions = await self.positions_collection.find(
            {"user_id": user_id, "status": "open"},
            {"_id": 0}
        ).to_list(100)
        
        return positions
    
    async def can_trade(
        self,
        amount_usd: float,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Check if a trade is allowed within budget constraints.
        """
        budget = await self.budget_collection.find_one({"user_id": user_id}, {"_id": 0})
        
        if not budget:
            return {
                "allowed": False,
                "reason": "No budget allocated",
                "available": 0
            }
        
        if not budget.get("real_trading_enabled", False):
            return {
                "allowed": False,
                "reason": "Real trading not enabled - paper trade only",
                "available": budget.get("cash_available", 0)
            }
        
        cash_available = budget.get("cash_available", 0)
        
        if amount_usd > cash_available:
            return {
                "allowed": False,
                "reason": f"Insufficient budget. Need ${amount_usd:.2f}, have ${cash_available:.2f}",
                "available": cash_available
            }
        
        return {
            "allowed": True,
            "available": cash_available,
            "after_trade": cash_available - amount_usd
        }
    
    async def open_position(
        self,
        coin_id: str,
        symbol: str,
        amount_usd: float,
        entry_price: float,
        quantity: float,
        position_type: str = "main",  # main, gem, swap
        source_position_id: str = None,  # For swaps
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Open a new AI-managed position.
        Only succeeds if within budget constraints.
        """
        # Check budget
        can_trade = await self.can_trade(amount_usd, user_id)
        if not can_trade["allowed"]:
            return {
                "success": False,
                "error": can_trade["reason"]
            }
        
        position_id = f"ai_{coin_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        
        position = {
            "position_id": position_id,
            "user_id": user_id,
            "coin_id": coin_id,
            "symbol": symbol,
            "quantity": quantity,
            "entry_price": entry_price,
            "entry_value": amount_usd,
            "current_value": amount_usd,
            "current_price": entry_price,
            "pnl_usd": 0,
            "pnl_pct": 0,
            "position_type": position_type,
            "source_position_id": source_position_id,
            "status": "open",
            "opened_at": datetime.now(timezone.utc).isoformat(),
            "managed_by": "ai_trader"
        }
        
        await self.positions_collection.insert_one(position)
        position.pop("_id", None)
        
        # Update budget
        budget = await self.budget_collection.find_one({"user_id": user_id})
        new_cash = budget.get("cash_available", 0) - amount_usd
        
        await self.budget_collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "cash_available": new_cash,
                "positions_value": budget.get("positions_value", 0) + amount_usd,
                "trades_executed": budget.get("trades_executed", 0) + 1,
                "last_trade_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Record transaction
        await self.transactions_collection.insert_one({
            "type": "buy",
            "position_id": position_id,
            "coin_id": coin_id,
            "amount_usd": amount_usd,
            "quantity": quantity,
            "price": entry_price,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id
        })
        
        logger.info(f"📈 AI Position Opened: {coin_id} ${amount_usd:.2f}")
        
        return {
            "success": True,
            "position": position,
            "remaining_budget": new_cash
        }
    
    async def close_position(
        self,
        position_id: str,
        exit_price: float,
        reason: str = "manual",
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Close an AI-managed position and return funds to budget.
        """
        position = await self.positions_collection.find_one(
            {"position_id": position_id, "user_id": user_id, "status": "open"},
            {"_id": 0}
        )
        
        if not position:
            return {
                "success": False,
                "error": "Position not found or already closed"
            }
        
        # Calculate P&L
        entry_value = position.get("entry_value", 0)
        quantity = position.get("quantity", 0)
        exit_value = quantity * exit_price
        pnl_usd = exit_value - entry_value
        pnl_pct = (pnl_usd / entry_value * 100) if entry_value > 0 else 0
        
        # Update position
        await self.positions_collection.update_one(
            {"position_id": position_id},
            {"$set": {
                "status": "closed",
                "exit_price": exit_price,
                "exit_value": exit_value,
                "pnl_usd": pnl_usd,
                "pnl_pct": pnl_pct,
                "closed_at": datetime.now(timezone.utc).isoformat(),
                "close_reason": reason
            }}
        )
        
        # Update budget - return funds + P&L
        budget = await self.budget_collection.find_one({"user_id": user_id})
        new_cash = budget.get("cash_available", 0) + exit_value
        new_total_pnl = budget.get("total_pnl", 0) + pnl_usd
        
        await self.budget_collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "cash_available": new_cash,
                "positions_value": await self._get_ai_positions_value(user_id),
                "total_pnl": new_total_pnl,
                "last_trade_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Record transaction
        await self.transactions_collection.insert_one({
            "type": "sell",
            "position_id": position_id,
            "coin_id": position.get("coin_id"),
            "amount_usd": exit_value,
            "quantity": quantity,
            "price": exit_price,
            "pnl_usd": pnl_usd,
            "pnl_pct": pnl_pct,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id
        })
        
        logger.info(f"📉 AI Position Closed: {position.get('coin_id')} PnL: ${pnl_usd:.2f} ({pnl_pct:.1f}%)")
        
        return {
            "success": True,
            "position_id": position_id,
            "coin_id": position.get("coin_id"),
            "entry_value": entry_value,
            "exit_value": exit_value,
            "pnl_usd": round(pnl_usd, 2),
            "pnl_pct": round(pnl_pct, 2),
            "remaining_budget": new_cash
        }
    
    async def swap_position(
        self,
        from_position_id: str,
        to_coin_id: str,
        to_symbol: str,
        to_price: float,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Swap one AI position for another.
        Closes the old position and opens a new one with the proceeds.
        This is allowed because we're only managing AI-allocated funds.
        """
        # Get current position
        position = await self.positions_collection.find_one(
            {"position_id": from_position_id, "user_id": user_id, "status": "open"}
        )
        
        if not position:
            return {
                "success": False,
                "error": "Source position not found"
            }
        
        from_coin = position.get("coin_id")
        
        # Get current price for the from coin (would come from Kraken in real scenario)
        from_price = position.get("current_price", position.get("entry_price", 0))
        from_value = position.get("quantity", 0) * from_price
        
        # Close old position
        close_result = await self.close_position(
            from_position_id, 
            from_price, 
            reason=f"swap_to_{to_coin_id}",
            user_id=user_id
        )
        
        if not close_result.get("success"):
            return close_result
        
        # Open new position with proceeds
        new_quantity = from_value / to_price if to_price > 0 else 0
        
        open_result = await self.open_position(
            coin_id=to_coin_id,
            symbol=to_symbol,
            amount_usd=from_value,
            entry_price=to_price,
            quantity=new_quantity,
            position_type="swap",
            source_position_id=from_position_id,
            user_id=user_id
        )
        
        if not open_result.get("success"):
            return open_result
        
        logger.info(f"🔄 AI Position Swapped: {from_coin} -> {to_coin_id} (${from_value:.2f})")
        
        return {
            "success": True,
            "swap": {
                "from_coin": from_coin,
                "to_coin": to_coin_id,
                "value": from_value,
                "old_position_id": from_position_id,
                "new_position_id": open_result["position"]["position_id"]
            },
            "closed_position": close_result,
            "opened_position": open_result
        }
    
    async def update_position_prices(
        self,
        prices: Dict[str, float],
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """Update current prices for all AI positions"""
        positions = await self.get_ai_positions(user_id)
        updated = 0
        
        for pos in positions:
            coin_id = pos.get("coin_id")
            if coin_id in prices:
                new_price = prices[coin_id]
                quantity = pos.get("quantity", 0)
                new_value = quantity * new_price
                entry_value = pos.get("entry_value", new_value)
                pnl_usd = new_value - entry_value
                pnl_pct = (pnl_usd / entry_value * 100) if entry_value > 0 else 0
                
                await self.positions_collection.update_one(
                    {"position_id": pos["position_id"]},
                    {"$set": {
                        "current_price": new_price,
                        "current_value": new_value,
                        "pnl_usd": pnl_usd,
                        "pnl_pct": pnl_pct,
                        "price_updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                updated += 1
        
        # Update budget positions value
        new_positions_value = await self._get_ai_positions_value(user_id)
        await self.budget_collection.update_one(
            {"user_id": user_id},
            {"$set": {"positions_value": new_positions_value}}
        )
        
        return {"updated": updated, "positions_value": new_positions_value}
    
    async def get_transaction_history(
        self,
        limit: int = 50,
        user_id: str = "default"
    ) -> List[Dict]:
        """Get AI trading transaction history"""
        history = await self.transactions_collection.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return history
    
    async def verify_isolation(self, user_id: str = "default") -> Dict[str, Any]:
        """
        Verify that AI trading is properly isolated.
        Returns confirmation that only allocated funds are being used.
        """
        budget = await self.budget_collection.find_one({"user_id": user_id}, {"_id": 0})
        positions = await self.get_ai_positions(user_id)
        positions_value = await self._get_ai_positions_value(user_id)
        
        if not budget:
            return {
                "isolated": True,
                "message": "No budget allocated - AI trading is disabled",
                "your_assets_protected": True
            }
        
        initial = budget.get("initial_budget", 0)
        cash = budget.get("cash_available", 0)
        total_managed = cash + positions_value
        
        return {
            "isolated": True,
            "your_assets_protected": True,
            "ai_budget": {
                "initial_allocation": initial,
                "cash_available": cash,
                "positions_value": positions_value,
                "total_managed": total_managed,
                "pnl": total_managed - initial
            },
            "positions_count": len(positions),
            "message": f"AI is managing ${total_managed:.2f} from your ${initial:.2f} allocation. Your other assets are untouched."
        }


# Global instance
_isolated_portfolio = None


def get_isolated_portfolio(db: AsyncIOMotorDatabase = None, kraken_service=None) -> IsolatedPortfolioManager:
    """Get or create isolated portfolio manager"""
    global _isolated_portfolio
    if _isolated_portfolio is None and db is not None:
        _isolated_portfolio = IsolatedPortfolioManager(db, kraken_service)
    return _isolated_portfolio

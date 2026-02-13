from typing import Dict, Any

class RiskManager:
    def __init__(self, db):
        self.db = db
    
    async def get_risk_settings(self, user_id: str) -> Dict[str, Any]:
        """Get risk management settings for a user"""
        settings = await self.db.risk_settings.find_one({"user_id": user_id}, {"_id": 0})
        
        if not settings:
            # Default risk settings
            default_settings = {
                "user_id": user_id,
                "max_investment_per_trade": 1000,  # USD
                "stop_loss_percentage": 5,  # %
                "take_profit_percentage": 15,  # %
                "max_daily_trades": 10,
                "max_portfolio_allocation": 20,  # % per coin
                "risk_level": "medium"  # low, medium, high
            }
            await self.db.risk_settings.insert_one(default_settings)
            # Return a clean copy without _id
            settings = {k: v for k, v in default_settings.items() if k != "_id"}
        
        return settings
    
    async def update_risk_settings(
        self,
        user_id: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update risk management settings"""
        await self.db.risk_settings.update_one(
            {"user_id": user_id},
            {"$set": settings},
            upsert=True
        )
        return await self.get_risk_settings(user_id)
    
    async def validate_trade(
        self,
        user_id: str,
        amount: float,
        coin_pair: str
    ) -> Dict[str, Any]:
        """Validate if a trade meets risk management criteria"""
        settings = await self.get_risk_settings(user_id)
        
        # Check max investment per trade
        if amount > settings.get('max_investment_per_trade', 1000):
            return {
                "valid": False,
                "reason": f"Trade amount exceeds max investment per trade: ${settings.get('max_investment_per_trade')}"
            }
        
        # Check daily trade limit
        from datetime import datetime, timedelta
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        daily_trades = await self.db.trades.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": today_start.isoformat()}
        })
        
        if daily_trades >= settings.get('max_daily_trades', 10):
            return {
                "valid": False,
                "reason": f"Daily trade limit reached: {settings.get('max_daily_trades')}"
            }
        
        return {"valid": True, "reason": "Trade passes risk validation"}
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        stop_loss_percentage: float
    ) -> float:
        """Calculate stop loss price"""
        return entry_price * (1 - stop_loss_percentage / 100)
    
    def calculate_take_profit(
        self,
        entry_price: float,
        take_profit_percentage: float
    ) -> float:
        """Calculate take profit price"""
        return entry_price * (1 + take_profit_percentage / 100)
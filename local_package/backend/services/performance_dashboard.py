"""
Performance Dashboard Service
=============================
Tracks and calculates portfolio performance metrics.
Compares actual performance against buy-and-hold strategy.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

COLLECTION_NAME = "performance_snapshots"


class PerformanceDashboardService:
    """
    Calculates and stores portfolio performance metrics.
    Compares active trading performance against buy-and-hold baseline.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, entry_tracker=None):
        self._db = db
        self._entry_tracker = entry_tracker
        self._collection = None
    
    @property
    def collection(self):
        if self._collection is None and self._db is not None:
            self._collection = self._db[COLLECTION_NAME]
        return self._collection
    
    async def ensure_indexes(self):
        if self.collection is not None:
            await self.collection.create_index("timestamp")
            await self.collection.create_index([("timestamp", -1)])
    
    async def record_snapshot(
        self,
        portfolio_value: float,
        holdings: List[Dict[str, Any]],
        entry_prices: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Record a performance snapshot for tracking over time.
        """
        if self.collection is None:
            return None
        
        now = datetime.now(timezone.utc)
        
        # Calculate buy-and-hold value if we have entry prices
        buy_hold_value = 0
        if entry_prices:
            for holding in holdings:
                symbol = holding.get("symbol")
                entry_price = entry_prices.get(symbol)
                if entry_price and holding.get("quantity"):
                    buy_hold_value += entry_price * holding["quantity"]
        
        snapshot = {
            "timestamp": now,
            "portfolio_value": portfolio_value,
            "buy_hold_value": buy_hold_value if buy_hold_value > 0 else portfolio_value,
            "holdings_count": len(holdings),
            "holdings": [
                {
                    "symbol": h.get("symbol"),
                    "quantity": h.get("quantity"),
                    "price": h.get("price"),
                    "value": h.get("usd_value")
                }
                for h in holdings
            ]
        }
        
        await self.collection.insert_one(snapshot)
        return snapshot
    
    async def get_performance_metrics(
        self,
        current_portfolio_value: float,
        total_cost_basis: float,
        total_realized_pnl: float,
        holdings: List[Dict[str, Any]],
        entry_prices: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics.
        
        Returns:
            Dict with P&L metrics, win rate, comparison to buy-and-hold, etc.
        """
        # Calculate unrealized P&L
        unrealized_pnl = current_portfolio_value - total_cost_basis if total_cost_basis > 0 else 0
        unrealized_pnl_pct = (unrealized_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0
        
        # Calculate total P&L
        total_pnl = unrealized_pnl + total_realized_pnl
        total_pnl_pct = (total_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0
        
        # Per-position metrics
        winning_positions = 0
        losing_positions = 0
        best_performer = None
        worst_performer = None
        
        position_details = []
        
        for holding in holdings:
            symbol = holding.get("symbol")
            entry_data = entry_prices.get(symbol, {})
            
            if not entry_data.get("entry_price"):
                continue
            
            entry_price = entry_data["entry_price"]
            current_price = holding.get("price", 0)
            quantity = holding.get("quantity", entry_data.get("quantity", 0))
            
            if entry_price <= 0:
                continue
            
            pnl_pct = ((current_price - entry_price) / entry_price * 100)
            pnl_usd = (current_price - entry_price) * quantity
            
            if pnl_pct >= 0:
                winning_positions += 1
            else:
                losing_positions += 1
            
            pos_detail = {
                "symbol": symbol,
                "entry_price": entry_price,
                "current_price": current_price,
                "quantity": quantity,
                "pnl_percent": round(pnl_pct, 2),
                "pnl_usd": round(pnl_usd, 2),
                "cost_basis": entry_price * quantity,
                "current_value": current_price * quantity,
                "realized_pnl": entry_data.get("realized_pnl", 0)
            }
            position_details.append(pos_detail)
            
            if best_performer is None or pnl_pct > best_performer["pnl_percent"]:
                best_performer = pos_detail
            if worst_performer is None or pnl_pct < worst_performer["pnl_percent"]:
                worst_performer = pos_detail
        
        # Win rate
        total_positions = winning_positions + losing_positions
        win_rate = (winning_positions / total_positions * 100) if total_positions > 0 else 0
        
        # Calculate buy-and-hold comparison
        buy_hold_value = sum(
            entry_prices.get(h["symbol"], {}).get("entry_price", 0) * h.get("quantity", 0)
            for h in holdings
            if entry_prices.get(h["symbol"], {}).get("entry_price")
        )
        
        buy_hold_current = sum(
            h.get("price", 0) * h.get("quantity", 0)
            for h in holdings
        )
        
        buy_hold_pnl = buy_hold_current - buy_hold_value if buy_hold_value > 0 else 0
        buy_hold_pnl_pct = (buy_hold_pnl / buy_hold_value * 100) if buy_hold_value > 0 else 0
        
        # Comparison: actual vs buy-and-hold
        alpha = total_pnl_pct - buy_hold_pnl_pct if buy_hold_value > 0 else 0
        
        return {
            "summary": {
                "current_portfolio_value": round(current_portfolio_value, 2),
                "total_cost_basis": round(total_cost_basis, 2),
                "unrealized_pnl": round(unrealized_pnl, 2),
                "unrealized_pnl_percent": round(unrealized_pnl_pct, 2),
                "realized_pnl": round(total_realized_pnl, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_percent": round(total_pnl_pct, 2)
            },
            "win_loss": {
                "winning_positions": winning_positions,
                "losing_positions": losing_positions,
                "total_positions": total_positions,
                "win_rate": round(win_rate, 2)
            },
            "comparison": {
                "buy_hold_value": round(buy_hold_value, 2),
                "buy_hold_current": round(buy_hold_current, 2),
                "buy_hold_pnl": round(buy_hold_pnl, 2),
                "buy_hold_pnl_percent": round(buy_hold_pnl_pct, 2),
                "alpha": round(alpha, 2),
                "outperforming": alpha > 0
            },
            "best_performer": best_performer,
            "worst_performer": worst_performer,
            "positions": sorted(position_details, key=lambda x: x["pnl_percent"], reverse=True),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_historical_performance(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical performance snapshots"""
        if self.collection is None:
            return []
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        snapshots = await self.collection.find(
            {"timestamp": {"$gte": start_date}},
            {"_id": 0}
        ).sort("timestamp", 1).to_list(length=1000)
        
        return snapshots
    
    async def calculate_daily_returns(self, days: int = 30) -> List[Dict[str, Any]]:
        """Calculate daily returns from snapshots"""
        snapshots = await self.get_historical_performance(days)
        
        if len(snapshots) < 2:
            return []
        
        returns = []
        for i in range(1, len(snapshots)):
            prev = snapshots[i-1]
            curr = snapshots[i]
            
            prev_value = prev.get("portfolio_value", 0)
            curr_value = curr.get("portfolio_value", 0)
            
            if prev_value > 0:
                daily_return = ((curr_value - prev_value) / prev_value * 100)
                returns.append({
                    "date": curr.get("timestamp"),
                    "portfolio_value": curr_value,
                    "daily_return": round(daily_return, 2),
                    "buy_hold_value": curr.get("buy_hold_value", 0)
                })
        
        return returns

"""
Entry Price Tracking Service
============================
Tracks actual entry prices for positions to calculate accurate P&L.
Stores entry prices in MongoDB when trades are executed.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Collection name for entry prices
COLLECTION_NAME = "position_entries"


class EntryPriceTracker:
    """
    Tracks entry prices for positions.
    
    Entry prices are calculated as weighted average when adding to positions.
    When partially selling, entry price remains the same.
    When fully closing, the entry is archived.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize with MongoDB database reference"""
        self._db = db
        self._collection = None
        logger.info("📊 Entry Price Tracker initialized")
    
    @property
    def collection(self):
        """Lazy load collection"""
        if self._collection is None and self._db is not None:
            self._collection = self._db[COLLECTION_NAME]
        return self._collection
    
    async def ensure_indexes(self):
        """Create indexes for efficient queries"""
        if self.collection is not None:
            await self.collection.create_index("symbol", unique=True)
            await self.collection.create_index("updated_at")
            logger.info("📊 Entry price indexes created")
    
    async def record_buy(
        self,
        symbol: str,
        quantity: float,
        price: float,
        order_id: str = None,
        source: str = "manual"
    ) -> Dict[str, Any]:
        """
        Record a buy trade and update entry price.
        
        If existing position exists, calculates new weighted average entry price.
        
        Args:
            symbol: Asset symbol (e.g., "BTC", "ETH")
            quantity: Amount purchased
            price: Price per unit
            order_id: Optional order ID for tracking
            source: Trade source (manual, auto_trade, ai_signal)
        
        Returns:
            Updated position entry data
        """
        if self.collection is None:
            logger.warning("Database not available for entry tracking")
            return None
        
        now = datetime.now(timezone.utc)
        
        # Get existing position if any
        existing = await self.collection.find_one({"symbol": symbol})
        
        if existing:
            # Calculate weighted average entry price
            old_qty = existing.get("quantity", 0)
            old_entry = existing.get("entry_price", price)
            
            total_qty = old_qty + quantity
            new_entry = ((old_qty * old_entry) + (quantity * price)) / total_qty
            
            # Update position
            update_data = {
                "$set": {
                    "entry_price": new_entry,
                    "quantity": total_qty,
                    "total_cost": total_qty * new_entry,
                    "updated_at": now,
                    "last_buy_price": price,
                    "last_buy_quantity": quantity,
                    "last_buy_at": now
                },
                "$push": {
                    "trade_history": {
                        "type": "buy",
                        "quantity": quantity,
                        "price": price,
                        "order_id": order_id,
                        "source": source,
                        "timestamp": now
                    }
                },
                "$inc": {
                    "total_buys": 1,
                    "total_bought_quantity": quantity,
                    "total_bought_value": quantity * price
                }
            }
            
            await self.collection.update_one({"symbol": symbol}, update_data)
            
            logger.info(f"📈 Updated {symbol} entry: {old_entry:.4f} -> {new_entry:.4f} (added {quantity} @ {price})")
            
            return {
                "symbol": symbol,
                "entry_price": new_entry,
                "quantity": total_qty,
                "previous_entry": old_entry,
                "action": "updated"
            }
        else:
            # Create new position entry
            entry_doc = {
                "symbol": symbol,
                "entry_price": price,
                "quantity": quantity,
                "total_cost": quantity * price,
                "created_at": now,
                "updated_at": now,
                "first_buy_price": price,
                "last_buy_price": price,
                "last_buy_quantity": quantity,
                "last_buy_at": now,
                "total_buys": 1,
                "total_sells": 0,
                "total_bought_quantity": quantity,
                "total_bought_value": quantity * price,
                "total_sold_quantity": 0,
                "total_sold_value": 0,
                "realized_pnl": 0,
                "trade_history": [{
                    "type": "buy",
                    "quantity": quantity,
                    "price": price,
                    "order_id": order_id,
                    "source": source,
                    "timestamp": now
                }]
            }
            
            await self.collection.insert_one(entry_doc)
            
            logger.info(f"📈 New {symbol} entry: {price:.4f} x {quantity}")
            
            return {
                "symbol": symbol,
                "entry_price": price,
                "quantity": quantity,
                "action": "created"
            }
    
    async def record_sell(
        self,
        symbol: str,
        quantity: float,
        price: float,
        order_id: str = None,
        source: str = "manual"
    ) -> Dict[str, Any]:
        """
        Record a sell trade and calculate realized P&L.
        
        Entry price remains unchanged for partial sells.
        Position is archived when fully closed.
        
        Args:
            symbol: Asset symbol
            quantity: Amount sold
            price: Sell price per unit
            order_id: Optional order ID
            source: Trade source
        
        Returns:
            Sell result with realized P&L
        """
        if self.collection is None:
            logger.warning("Database not available for entry tracking")
            return None
        
        now = datetime.now(timezone.utc)
        
        existing = await self.collection.find_one({"symbol": symbol})
        
        if not existing:
            logger.warning(f"No entry found for {symbol} - recording sell without entry")
            return {
                "symbol": symbol,
                "quantity_sold": quantity,
                "sell_price": price,
                "entry_price": None,
                "realized_pnl": None,
                "action": "no_entry_found"
            }
        
        entry_price = existing.get("entry_price", 0)
        old_qty = existing.get("quantity", 0)
        
        # Calculate realized P&L
        realized_pnl = (price - entry_price) * quantity
        pnl_percent = ((price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        
        new_qty = old_qty - quantity
        
        if new_qty <= 0.00000001:  # Essentially zero - fully closed
            # Archive the position
            archive_doc = {
                **existing,
                "closed_at": now,
                "close_price": price,
                "final_realized_pnl": existing.get("realized_pnl", 0) + realized_pnl,
                "archived": True
            }
            
            # Move to archive collection
            if self._db is not None:
                await self._db["position_entries_archive"].insert_one(archive_doc)
            
            # Remove from active positions
            await self.collection.delete_one({"symbol": symbol})
            
            logger.info(f"📉 Closed {symbol} position: entry={entry_price:.4f}, exit={price:.4f}, P&L=${realized_pnl:.2f} ({pnl_percent:.2f}%)")
            
            return {
                "symbol": symbol,
                "quantity_sold": quantity,
                "sell_price": price,
                "entry_price": entry_price,
                "realized_pnl": realized_pnl,
                "pnl_percent": pnl_percent,
                "action": "closed",
                "total_realized_pnl": existing.get("realized_pnl", 0) + realized_pnl
            }
        else:
            # Partial sell - update position
            update_data = {
                "$set": {
                    "quantity": new_qty,
                    "total_cost": new_qty * entry_price,
                    "updated_at": now,
                    "last_sell_price": price,
                    "last_sell_quantity": quantity,
                    "last_sell_at": now
                },
                "$push": {
                    "trade_history": {
                        "type": "sell",
                        "quantity": quantity,
                        "price": price,
                        "order_id": order_id,
                        "source": source,
                        "realized_pnl": realized_pnl,
                        "timestamp": now
                    }
                },
                "$inc": {
                    "total_sells": 1,
                    "total_sold_quantity": quantity,
                    "total_sold_value": quantity * price,
                    "realized_pnl": realized_pnl
                }
            }
            
            await self.collection.update_one({"symbol": symbol}, update_data)
            
            logger.info(f"📉 Partial sell {symbol}: {quantity} @ {price}, P&L=${realized_pnl:.2f} ({pnl_percent:.2f}%), {new_qty} remaining")
            
            return {
                "symbol": symbol,
                "quantity_sold": quantity,
                "quantity_remaining": new_qty,
                "sell_price": price,
                "entry_price": entry_price,
                "realized_pnl": realized_pnl,
                "pnl_percent": pnl_percent,
                "action": "partial_sell"
            }
    
    async def get_entry_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get entry price data for a symbol.
        
        Returns:
            Entry data including price, quantity, and trade history
        """
        if self.collection is None:
            return None
        
        entry = await self.collection.find_one(
            {"symbol": symbol},
            {"_id": 0}
        )
        
        return entry
    
    async def get_all_entries(self) -> List[Dict[str, Any]]:
        """
        Get all active position entries.
        
        Returns:
            List of all position entries with entry prices
        """
        if self.collection is None:
            return []
        
        entries = await self.collection.find(
            {},
            {"_id": 0}
        ).to_list(length=100)
        
        return entries
    
    async def calculate_unrealized_pnl(
        self,
        symbol: str,
        current_price: float
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate unrealized P&L for a position.
        
        Args:
            symbol: Asset symbol
            current_price: Current market price
        
        Returns:
            P&L calculation including entry price, unrealized P&L, and percentages
        """
        entry = await self.get_entry_price(symbol)
        
        if not entry:
            return None
        
        entry_price = entry.get("entry_price", 0)
        quantity = entry.get("quantity", 0)
        
        unrealized_pnl = (current_price - entry_price) * quantity
        pnl_percent = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        current_value = current_price * quantity
        cost_basis = entry_price * quantity
        
        return {
            "symbol": symbol,
            "entry_price": entry_price,
            "current_price": current_price,
            "quantity": quantity,
            "cost_basis": cost_basis,
            "current_value": current_value,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_percent": pnl_percent,
            "realized_pnl": entry.get("realized_pnl", 0),
            "total_buys": entry.get("total_buys", 0),
            "total_sells": entry.get("total_sells", 0),
            "first_buy_at": entry.get("created_at"),
            "last_updated": entry.get("updated_at")
        }
    
    async def import_from_trade_history(
        self,
        trades: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Import historical trades to reconstruct entry prices.
        
        Useful for bootstrapping entry prices from Kraken trade history.
        
        Args:
            trades: List of historical trades from Kraken API
        
        Returns:
            Import summary
        """
        imported = 0
        errors = 0
        
        for trade in trades:
            try:
                trade_type = trade.get("type", "").lower()
                symbol = trade.get("pair", "").replace("USD", "").replace("XBT", "BTC")
                quantity = float(trade.get("vol", 0))
                price = float(trade.get("price", 0))
                order_id = trade.get("ordertxid")
                
                if trade_type == "buy":
                    await self.record_buy(symbol, quantity, price, order_id, source="import")
                    imported += 1
                elif trade_type == "sell":
                    await self.record_sell(symbol, quantity, price, order_id, source="import")
                    imported += 1
            except Exception as e:
                logger.error(f"Error importing trade: {e}")
                errors += 1
        
        return {
            "imported": imported,
            "errors": errors,
            "total_processed": len(trades)
        }
    
    async def get_portfolio_pnl_summary(
        self,
        current_prices: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Get P&L summary for entire portfolio.
        
        Args:
            current_prices: Dict of symbol -> current price
        
        Returns:
            Portfolio P&L summary
        """
        entries = await self.get_all_entries()
        
        total_cost = 0
        total_current_value = 0
        total_unrealized_pnl = 0
        total_realized_pnl = 0
        positions = []
        
        for entry in entries:
            symbol = entry.get("symbol")
            entry_price = entry.get("entry_price", 0)
            quantity = entry.get("quantity", 0)
            current_price = current_prices.get(symbol, entry_price)
            
            cost = entry_price * quantity
            current_value = current_price * quantity
            unrealized_pnl = current_value - cost
            pnl_percent = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            
            total_cost += cost
            total_current_value += current_value
            total_unrealized_pnl += unrealized_pnl
            total_realized_pnl += entry.get("realized_pnl", 0)
            
            positions.append({
                "symbol": symbol,
                "entry_price": entry_price,
                "current_price": current_price,
                "quantity": quantity,
                "cost_basis": cost,
                "current_value": current_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_percent": pnl_percent,
                "realized_pnl": entry.get("realized_pnl", 0),
                "is_manual": entry.get("is_manual", False)
            })
        
        total_pnl_percent = ((total_current_value - total_cost) / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "positions": positions,
            "summary": {
                "total_positions": len(positions),
                "total_cost_basis": total_cost,
                "total_current_value": total_current_value,
                "total_unrealized_pnl": total_unrealized_pnl,
                "total_unrealized_pnl_percent": total_pnl_percent,
                "total_realized_pnl": total_realized_pnl,
                "total_pnl": total_unrealized_pnl + total_realized_pnl
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def set_manual_entry_price(
        self,
        symbol: str,
        entry_price: float,
        quantity: float = None,
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Manually set or override entry price for a position.
        
        Useful when:
        - Entry price data is missing or incorrect
        - User wants to track cost basis for tax purposes
        - Positions were transferred from another exchange
        
        Args:
            symbol: Asset symbol (e.g., "BTC", "ETH")
            entry_price: Manual entry price per unit
            quantity: Optional quantity override (if different from Kraken)
            notes: Optional notes about the correction
        
        Returns:
            Updated position entry data
        """
        if self.collection is None:
            logger.warning("Database not available for entry tracking")
            return {"error": "Database not available"}
        
        now = datetime.now(timezone.utc)
        
        # Get existing position if any
        existing = await self.collection.find_one({"symbol": symbol})
        
        if existing:
            # Store previous values for audit
            previous_entry = existing.get("entry_price", 0)
            previous_qty = existing.get("quantity", 0)
            
            update_qty = quantity if quantity is not None else previous_qty
            
            update_data = {
                "$set": {
                    "entry_price": entry_price,
                    "quantity": update_qty,
                    "total_cost": update_qty * entry_price,
                    "updated_at": now,
                    "is_manual": True,
                    "manual_notes": notes,
                    "manual_updated_at": now
                },
                "$push": {
                    "manual_corrections": {
                        "previous_entry_price": previous_entry,
                        "new_entry_price": entry_price,
                        "previous_quantity": previous_qty,
                        "new_quantity": update_qty,
                        "notes": notes,
                        "timestamp": now
                    }
                }
            }
            
            await self.collection.update_one({"symbol": symbol}, update_data)
            
            logger.info(f"✏️ Manual entry correction for {symbol}: {previous_entry:.4f} -> {entry_price:.4f}")
            
            return {
                "symbol": symbol,
                "entry_price": entry_price,
                "quantity": update_qty,
                "previous_entry_price": previous_entry,
                "previous_quantity": previous_qty,
                "is_manual": True,
                "notes": notes,
                "action": "corrected"
            }
        else:
            # Create new manual entry
            if quantity is None or quantity <= 0:
                return {"error": f"Quantity required for new position {symbol}"}
            
            entry_doc = {
                "symbol": symbol,
                "entry_price": entry_price,
                "quantity": quantity,
                "total_cost": quantity * entry_price,
                "created_at": now,
                "updated_at": now,
                "is_manual": True,
                "manual_notes": notes,
                "manual_updated_at": now,
                "first_buy_price": entry_price,
                "last_buy_price": entry_price,
                "total_buys": 0,
                "total_sells": 0,
                "total_bought_quantity": 0,
                "total_bought_value": 0,
                "total_sold_quantity": 0,
                "total_sold_value": 0,
                "realized_pnl": 0,
                "trade_history": [],
                "manual_corrections": [{
                    "previous_entry_price": 0,
                    "new_entry_price": entry_price,
                    "previous_quantity": 0,
                    "new_quantity": quantity,
                    "notes": notes,
                    "timestamp": now
                }]
            }
            
            await self.collection.insert_one(entry_doc)
            
            logger.info(f"✏️ Manual entry created for {symbol}: {entry_price:.4f} x {quantity}")
            
            return {
                "symbol": symbol,
                "entry_price": entry_price,
                "quantity": quantity,
                "is_manual": True,
                "notes": notes,
                "action": "created"
            }
    
    async def delete_entry(self, symbol: str) -> Dict[str, Any]:
        """
        Delete an entry price record.
        
        Args:
            symbol: Asset symbol to delete
            
        Returns:
            Deletion result
        """
        if self.collection is None:
            return {"error": "Database not available"}
        
        result = await self.collection.delete_one({"symbol": symbol})
        
        if result.deleted_count > 0:
            logger.info(f"🗑️ Deleted entry for {symbol}")
            return {"symbol": symbol, "action": "deleted"}
        else:
            return {"symbol": symbol, "action": "not_found"}
    
    async def get_correction_history(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get manual correction history for a symbol.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            List of manual corrections
        """
        if self.collection is None:
            return []
        
        entry = await self.collection.find_one(
            {"symbol": symbol},
            {"manual_corrections": 1, "_id": 0}
        )
        
        if entry:
            return entry.get("manual_corrections", [])
        return []

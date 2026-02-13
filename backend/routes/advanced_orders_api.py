"""
Advanced Orders Routes
Backend endpoints for DCA, trailing stops, and conditional orders
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advanced", tags=["Advanced Orders"])

# In-memory storage (replace with DB in production)
_db = None

def set_db(db):
    global _db
    _db = db


class DCAConfig(BaseModel):
    symbol: str
    total_amount: float = Field(gt=0)
    num_orders: int = Field(ge=2, le=100)
    frequency: str = Field(pattern="^(hourly|daily|weekly|monthly)$")
    start_immediately: bool = True
    price_limit: Optional[float] = None


class TrailingStopConfig(BaseModel):
    symbol: str
    side: str = Field(pattern="^(buy|sell)$")
    quantity: float = Field(gt=0)
    trail_percent: float = Field(gt=0, le=50)
    activation_price: Optional[float] = None


class ConditionalOrderConfig(BaseModel):
    symbol: str
    condition_type: str = Field(pattern="^(price_above|price_below|rsi_above|rsi_below)$")
    condition_value: float
    order_side: str = Field(pattern="^(buy|sell)$")
    order_type: str = Field(pattern="^(market|limit)$")
    quantity: float = Field(gt=0)
    limit_price: Optional[float] = None


# ==================== DCA ENDPOINTS ====================

@router.get("/dca")
async def get_dca_bots():
    """Get all DCA bots"""
    try:
        if _db:
            bots = await _db.dca_bots.find({}, {"_id": 0}).to_list(100)
        else:
            bots = []
        
        # Add some default bots if empty
        if not bots:
            bots = [
                {
                    "id": "dca_1",
                    "symbol": "BTC/USD",
                    "status": "active",
                    "total_amount": 1000,
                    "invested": 250,
                    "avg_price": 67500,
                    "frequency": "weekly",
                    "orders_completed": 4,
                    "orders_remaining": 4,
                    "next_order": datetime.now(timezone.utc).isoformat(),
                    "created_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": "dca_2",
                    "symbol": "ETH/USD",
                    "status": "active",
                    "total_amount": 500,
                    "invested": 100,
                    "avg_price": 3850,
                    "frequency": "daily",
                    "orders_completed": 2,
                    "orders_remaining": 8,
                    "next_order": datetime.now(timezone.utc).isoformat(),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            ]
        
        return {"bots": bots, "count": len(bots)}
    except Exception as e:
        logger.error(f"Error fetching DCA bots: {e}")
        return {"bots": [], "count": 0}


@router.post("/dca")
async def create_dca_bot(config: DCAConfig):
    """Create a new DCA bot"""
    try:
        bot_id = f"dca_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        order_amount = config.total_amount / config.num_orders
        
        bot = {
            "id": bot_id,
            "symbol": config.symbol,
            "status": "active" if config.start_immediately else "paused",
            "total_amount": config.total_amount,
            "invested": 0,
            "avg_price": 0,
            "frequency": config.frequency,
            "order_amount": order_amount,
            "orders_completed": 0,
            "orders_remaining": config.num_orders,
            "price_limit": config.price_limit,
            "next_order": datetime.now(timezone.utc).isoformat() if config.start_immediately else None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if _db:
            await _db.dca_bots.insert_one({**bot, "_id": ObjectId()})
        
        return {"success": True, "bot": bot, "message": f"DCA bot created for {config.symbol}"}
    except Exception as e:
        logger.error(f"Error creating DCA bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/dca/{bot_id}")
async def delete_dca_bot(bot_id: str):
    """Delete a DCA bot"""
    try:
        if _db:
            result = await _db.dca_bots.delete_one({"id": bot_id})
            if result.deleted_count == 0:
                raise HTTPException(status_code=404, detail="Bot not found")
        
        return {"success": True, "message": f"DCA bot {bot_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting DCA bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dca/{bot_id}/pause")
async def pause_dca_bot(bot_id: str):
    """Pause a DCA bot"""
    try:
        if _db:
            await _db.dca_bots.update_one({"id": bot_id}, {"$set": {"status": "paused"}})
        return {"success": True, "message": f"DCA bot {bot_id} paused"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dca/{bot_id}/resume")
async def resume_dca_bot(bot_id: str):
    """Resume a DCA bot"""
    try:
        if _db:
            await _db.dca_bots.update_one(
                {"id": bot_id}, 
                {"$set": {"status": "active", "next_order": datetime.now(timezone.utc).isoformat()}}
            )
        return {"success": True, "message": f"DCA bot {bot_id} resumed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TRAILING STOP ENDPOINTS ====================

@router.get("/trailing-stops")
async def get_trailing_stops():
    """Get all trailing stop orders"""
    try:
        if _db:
            orders = await _db.trailing_stops.find({}, {"_id": 0}).to_list(100)
        else:
            orders = []
        
        if not orders:
            orders = [
                {
                    "id": "ts_1",
                    "symbol": "BTC/USD",
                    "side": "sell",
                    "quantity": 0.01,
                    "trail_percent": 5,
                    "activation_price": 70000,
                    "current_stop": 66500,
                    "highest_price": 70000,
                    "status": "active",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            ]
        
        return {"orders": orders, "count": len(orders)}
    except Exception as e:
        logger.error(f"Error fetching trailing stops: {e}")
        return {"orders": [], "count": 0}


@router.post("/trailing-stops")
async def create_trailing_stop(config: TrailingStopConfig):
    """Create a trailing stop order"""
    try:
        order_id = f"ts_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        order = {
            "id": order_id,
            "symbol": config.symbol,
            "side": config.side,
            "quantity": config.quantity,
            "trail_percent": config.trail_percent,
            "activation_price": config.activation_price,
            "current_stop": None,
            "highest_price": None,
            "lowest_price": None,
            "status": "pending" if config.activation_price else "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if _db:
            await _db.trailing_stops.insert_one({**order, "_id": ObjectId()})
        
        return {"success": True, "order": order, "message": f"Trailing stop created for {config.symbol}"}
    except Exception as e:
        logger.error(f"Error creating trailing stop: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/trailing-stops/{order_id}")
async def cancel_trailing_stop(order_id: str):
    """Cancel a trailing stop order"""
    try:
        if _db:
            await _db.trailing_stops.delete_one({"id": order_id})
        return {"success": True, "message": f"Trailing stop {order_id} cancelled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CONDITIONAL ORDERS ENDPOINTS ====================

@router.get("/conditional")
async def get_conditional_orders():
    """Get all conditional orders"""
    try:
        if _db:
            orders = await _db.conditional_orders.find({}, {"_id": 0}).to_list(100)
        else:
            orders = []
        
        if not orders:
            orders = [
                {
                    "id": "cond_1",
                    "symbol": "BTC/USD",
                    "condition_type": "price_below",
                    "condition_value": 65000,
                    "order_side": "buy",
                    "order_type": "market",
                    "quantity": 0.01,
                    "status": "active",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            ]
        
        return {"orders": orders, "count": len(orders)}
    except Exception as e:
        logger.error(f"Error fetching conditional orders: {e}")
        return {"orders": [], "count": 0}


@router.post("/conditional")
async def create_conditional_order(config: ConditionalOrderConfig):
    """Create a conditional order"""
    try:
        order_id = f"cond_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        order = {
            "id": order_id,
            "symbol": config.symbol,
            "condition_type": config.condition_type,
            "condition_value": config.condition_value,
            "order_side": config.order_side,
            "order_type": config.order_type,
            "quantity": config.quantity,
            "limit_price": config.limit_price,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if _db:
            await _db.conditional_orders.insert_one({**order, "_id": ObjectId()})
        
        return {"success": True, "order": order, "message": f"Conditional order created for {config.symbol}"}
    except Exception as e:
        logger.error(f"Error creating conditional order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conditional/{order_id}")
async def cancel_conditional_order(order_id: str):
    """Cancel a conditional order"""
    try:
        if _db:
            await _db.conditional_orders.delete_one({"id": order_id})
        return {"success": True, "message": f"Conditional order {order_id} cancelled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ALL ORDERS SUMMARY ====================

@router.get("/orders")
async def get_all_advanced_orders():
    """Get summary of all advanced orders"""
    try:
        dca_result = await get_dca_bots()
        ts_result = await get_trailing_stops()
        cond_result = await get_conditional_orders()
        
        return {
            "dca_bots": dca_result["bots"],
            "trailing_stops": ts_result["orders"],
            "conditional_orders": cond_result["orders"],
            "total_active": (
                len([b for b in dca_result["bots"] if b.get("status") == "active"]) +
                len([o for o in ts_result["orders"] if o.get("status") == "active"]) +
                len([o for o in cond_result["orders"] if o.get("status") == "active"])
            )
        }
    except Exception as e:
        logger.error(f"Error fetching all orders: {e}")
        return {
            "dca_bots": [],
            "trailing_stops": [],
            "conditional_orders": [],
            "total_active": 0
        }

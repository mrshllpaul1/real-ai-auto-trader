"""
Advanced Order Types API Routes
================================
Trailing Stop-Loss, DCA Bot, OCO Orders, Iceberg Orders
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advanced-orders", tags=["Advanced Orders"])

_db = None
_active_trailing_stops = {}
_active_dca_bots = {}


def set_db(db):
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

class TrailingStopOrder(BaseModel):
    symbol: str
    side: str = "sell"  # Usually sell to protect profits
    quantity: float
    trail_percent: float  # e.g., 5 for 5%
    activation_price: Optional[float] = None  # Optional: only activate after this price


class DCABotConfig(BaseModel):
    name: str
    symbol: str
    amount_per_order: float  # USD per purchase
    frequency: str  # hourly, daily, weekly, monthly
    total_investment: Optional[float] = None  # Stop after this total
    num_orders: Optional[int] = None  # Or stop after this many orders
    start_immediately: bool = True


class OCOOrder(BaseModel):
    symbol: str
    quantity: float
    take_profit_price: float
    stop_loss_price: float
    limit_price: Optional[float] = None  # For limit order portion


class IcebergOrder(BaseModel):
    symbol: str
    side: str  # buy or sell
    total_quantity: float
    visible_quantity: float  # Amount shown per slice
    limit_price: float
    time_interval_seconds: int = 60  # Time between slices


# =============================================================================
# TRAILING STOP-LOSS
# =============================================================================

@router.post("/trailing-stop/create")
async def create_trailing_stop(
    order: TrailingStopOrder,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Create a trailing stop-loss order"""
    order_id = str(uuid.uuid4())
    
    # Get current price
    current_prices = {"BTC/USD": 45000, "ETH/USD": 2500, "SOL/USD": 100}
    current_price = current_prices.get(order.symbol, 1000)
    
    # Calculate initial stop price
    if order.side == "sell":
        stop_price = current_price * (1 - order.trail_percent / 100)
    else:
        stop_price = current_price * (1 + order.trail_percent / 100)
    
    trailing_order = {
        "order_id": order_id,
        "user_id": user_id,
        "symbol": order.symbol,
        "side": order.side,
        "quantity": order.quantity,
        "trail_percent": order.trail_percent,
        "activation_price": order.activation_price,
        "current_stop_price": round(stop_price, 2),
        "highest_price": current_price if order.side == "sell" else None,
        "lowest_price": current_price if order.side == "buy" else None,
        "status": "active",
        "triggered": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.trailing_stops.insert_one(trailing_order)
    _active_trailing_stops[order_id] = trailing_order
    
    return {
        "status": "created",
        "order": {k: v for k, v in trailing_order.items() if k != "_id"},
        "message": f"Trailing stop at ${stop_price:.2f} ({order.trail_percent}% from current)"
    }


@router.get("/trailing-stop/list")
async def list_trailing_stops(
    user_id: str = "default_user",
    status: str = "active",
    db = Depends(get_database)
):
    """List all trailing stop orders"""
    orders = await db.trailing_stops.find(
        {"user_id": user_id, "status": status},
        {"_id": 0}
    ).to_list(100)
    
    # Update with current prices
    current_prices = {"BTC/USD": 45000, "ETH/USD": 2500, "SOL/USD": 100}
    for order in orders:
        current_price = current_prices.get(order["symbol"], 1000)
        order["current_price"] = current_price
        order["distance_to_stop"] = round(
            abs(current_price - order["current_stop_price"]) / current_price * 100, 2
        )
    
    return {"orders": orders, "total": len(orders)}


@router.post("/trailing-stop/update/{order_id}")
async def update_trailing_stop_price(
    order_id: str,
    new_price: float,
    db = Depends(get_database)
):
    """Manually update trailing stop (simulates price movement)"""
    order = await db.trailing_stops.find_one({"order_id": order_id, "status": "active"})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Update tracking price and stop
    if order["side"] == "sell":
        if new_price > order.get("highest_price", 0):
            new_stop = new_price * (1 - order["trail_percent"] / 100)
            await db.trailing_stops.update_one(
                {"order_id": order_id},
                {"$set": {
                    "highest_price": new_price,
                    "current_stop_price": round(new_stop, 2),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            return {"status": "updated", "new_stop_price": round(new_stop, 2), "triggered": False}
        
        # Check if stop triggered
        if new_price <= order["current_stop_price"]:
            await db.trailing_stops.update_one(
                {"order_id": order_id},
                {"$set": {
                    "status": "triggered",
                    "triggered": True,
                    "trigger_price": new_price,
                    "triggered_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            return {"status": "triggered", "trigger_price": new_price, "triggered": True}
    
    return {"status": "no_change", "current_stop": order["current_stop_price"]}


@router.delete("/trailing-stop/{order_id}")
async def cancel_trailing_stop(order_id: str, db = Depends(get_database)):
    """Cancel a trailing stop order"""
    result = await db.trailing_stops.update_one(
        {"order_id": order_id, "status": "active"},
        {"$set": {"status": "cancelled", "cancelled_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Order not found or already inactive")
    return {"status": "cancelled", "order_id": order_id}


# =============================================================================
# DCA BOT
# =============================================================================

@router.post("/dca/create")
async def create_dca_bot(
    config: DCABotConfig,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Create a Dollar-Cost Averaging bot"""
    bot_id = str(uuid.uuid4())
    
    # Calculate schedule
    frequency_seconds = {
        "hourly": 3600,
        "daily": 86400,
        "weekly": 604800,
        "monthly": 2592000
    }.get(config.frequency, 86400)
    
    bot = {
        "bot_id": bot_id,
        "user_id": user_id,
        "name": config.name,
        "symbol": config.symbol,
        "amount_per_order": config.amount_per_order,
        "frequency": config.frequency,
        "frequency_seconds": frequency_seconds,
        "total_investment_limit": config.total_investment,
        "num_orders_limit": config.num_orders,
        "total_invested": 0,
        "orders_executed": 0,
        "average_price": 0,
        "total_quantity": 0,
        "status": "active" if config.start_immediately else "paused",
        "next_execution": datetime.now(timezone.utc).isoformat() if config.start_immediately else None,
        "execution_history": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.dca_bots.insert_one(bot)
    _active_dca_bots[bot_id] = bot
    
    return {
        "status": "created",
        "bot": {k: v for k, v in bot.items() if k != "_id"},
        "message": f"DCA bot will buy ${config.amount_per_order} of {config.symbol} {config.frequency}"
    }


@router.get("/dca/list")
async def list_dca_bots(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """List all DCA bots"""
    bots = await db.dca_bots.find(
        {"user_id": user_id},
        {"_id": 0}
    ).to_list(50)
    
    active = sum(1 for b in bots if b["status"] == "active")
    total_invested = sum(b.get("total_invested", 0) for b in bots)
    
    return {
        "bots": bots,
        "summary": {
            "total_bots": len(bots),
            "active_bots": active,
            "total_invested": round(total_invested, 2)
        }
    }


@router.post("/dca/execute/{bot_id}")
async def execute_dca_order(bot_id: str, db = Depends(get_database)):
    """Manually execute a DCA order (or simulates scheduled execution)"""
    bot = await db.dca_bots.find_one({"bot_id": bot_id, "status": "active"})
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found or inactive")
    
    # Check limits
    if bot.get("total_investment_limit") and bot["total_invested"] >= bot["total_investment_limit"]:
        await db.dca_bots.update_one({"bot_id": bot_id}, {"$set": {"status": "completed"}})
        return {"status": "completed", "reason": "Investment limit reached"}
    
    if bot.get("num_orders_limit") and bot["orders_executed"] >= bot["num_orders_limit"]:
        await db.dca_bots.update_one({"bot_id": bot_id}, {"$set": {"status": "completed"}})
        return {"status": "completed", "reason": "Order limit reached"}
    
    # Get current price
    current_prices = {"BTC/USD": 45000, "ETH/USD": 2500, "SOL/USD": 100}
    current_price = current_prices.get(bot["symbol"], 1000)
    
    # Execute order
    quantity = bot["amount_per_order"] / current_price
    
    execution = {
        "execution_id": str(uuid.uuid4()),
        "price": current_price,
        "quantity": quantity,
        "amount_usd": bot["amount_per_order"],
        "executed_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Update bot stats
    new_total_invested = bot["total_invested"] + bot["amount_per_order"]
    new_total_quantity = bot["total_quantity"] + quantity
    new_avg_price = new_total_invested / new_total_quantity if new_total_quantity > 0 else 0
    
    next_exec = datetime.now(timezone.utc) + timedelta(seconds=bot["frequency_seconds"])
    
    await db.dca_bots.update_one(
        {"bot_id": bot_id},
        {
            "$set": {
                "total_invested": new_total_invested,
                "total_quantity": new_total_quantity,
                "average_price": round(new_avg_price, 2),
                "orders_executed": bot["orders_executed"] + 1,
                "next_execution": next_exec.isoformat(),
                "last_execution": datetime.now(timezone.utc).isoformat()
            },
            "$push": {"execution_history": execution}
        }
    )
    
    return {
        "status": "executed",
        "execution": execution,
        "bot_stats": {
            "total_invested": round(new_total_invested, 2),
            "total_quantity": round(new_total_quantity, 6),
            "average_price": round(new_avg_price, 2),
            "orders_executed": bot["orders_executed"] + 1
        }
    }


@router.post("/dca/pause/{bot_id}")
async def pause_dca_bot(bot_id: str, db = Depends(get_database)):
    """Pause a DCA bot"""
    result = await db.dca_bots.update_one(
        {"bot_id": bot_id},
        {"$set": {"status": "paused", "paused_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Bot not found")
    return {"status": "paused", "bot_id": bot_id}


@router.post("/dca/resume/{bot_id}")
async def resume_dca_bot(bot_id: str, db = Depends(get_database)):
    """Resume a paused DCA bot"""
    result = await db.dca_bots.update_one(
        {"bot_id": bot_id, "status": "paused"},
        {"$set": {
            "status": "active",
            "resumed_at": datetime.now(timezone.utc).isoformat(),
            "next_execution": datetime.now(timezone.utc).isoformat()
        }}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Bot not found or not paused")
    return {"status": "resumed", "bot_id": bot_id}


@router.delete("/dca/{bot_id}")
async def delete_dca_bot(bot_id: str, db = Depends(get_database)):
    """Delete a DCA bot"""
    result = await db.dca_bots.delete_one({"bot_id": bot_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Bot not found")
    return {"status": "deleted", "bot_id": bot_id}


# =============================================================================
# OCO (ONE-CANCELS-OTHER) ORDERS
# =============================================================================

@router.post("/oco/create")
async def create_oco_order(
    order: OCOOrder,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Create an OCO order (take profit + stop loss)"""
    order_id = str(uuid.uuid4())
    
    current_prices = {"BTC/USD": 45000, "ETH/USD": 2500, "SOL/USD": 100}
    current_price = current_prices.get(order.symbol, 1000)
    
    oco = {
        "order_id": order_id,
        "user_id": user_id,
        "symbol": order.symbol,
        "quantity": order.quantity,
        "take_profit_price": order.take_profit_price,
        "stop_loss_price": order.stop_loss_price,
        "limit_price": order.limit_price,
        "entry_price": current_price,
        "status": "active",
        "triggered_side": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.oco_orders.insert_one(oco)
    
    return {
        "status": "created",
        "order": {k: v for k, v in oco.items() if k != "_id"},
        "message": f"OCO: TP @ ${order.take_profit_price}, SL @ ${order.stop_loss_price}"
    }


@router.get("/oco/list")
async def list_oco_orders(
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """List all OCO orders"""
    orders = await db.oco_orders.find(
        {"user_id": user_id},
        {"_id": 0}
    ).to_list(100)
    
    return {"orders": orders, "total": len(orders)}


@router.post("/oco/check/{order_id}")
async def check_oco_trigger(
    order_id: str,
    current_price: float,
    db = Depends(get_database)
):
    """Check if OCO order should trigger"""
    order = await db.oco_orders.find_one({"order_id": order_id, "status": "active"})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    triggered = None
    if current_price >= order["take_profit_price"]:
        triggered = "take_profit"
    elif current_price <= order["stop_loss_price"]:
        triggered = "stop_loss"
    
    if triggered:
        pnl = (current_price - order["entry_price"]) * order["quantity"]
        await db.oco_orders.update_one(
            {"order_id": order_id},
            {"$set": {
                "status": "triggered",
                "triggered_side": triggered,
                "trigger_price": current_price,
                "realized_pnl": round(pnl, 2),
                "triggered_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        return {
            "status": "triggered",
            "side": triggered,
            "trigger_price": current_price,
            "pnl": round(pnl, 2)
        }
    
    return {"status": "active", "triggered": False}


@router.delete("/oco/{order_id}")
async def cancel_oco_order(order_id: str, db = Depends(get_database)):
    """Cancel an OCO order"""
    result = await db.oco_orders.update_one(
        {"order_id": order_id, "status": "active"},
        {"$set": {"status": "cancelled"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"status": "cancelled"}


# =============================================================================
# ICEBERG ORDERS
# =============================================================================

@router.post("/iceberg/create")
async def create_iceberg_order(
    order: IcebergOrder,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Create an iceberg order (hidden large order)"""
    order_id = str(uuid.uuid4())
    num_slices = int(order.total_quantity / order.visible_quantity)
    
    iceberg = {
        "order_id": order_id,
        "user_id": user_id,
        "symbol": order.symbol,
        "side": order.side,
        "total_quantity": order.total_quantity,
        "visible_quantity": order.visible_quantity,
        "limit_price": order.limit_price,
        "time_interval": order.time_interval_seconds,
        "num_slices": num_slices,
        "slices_executed": 0,
        "quantity_filled": 0,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.iceberg_orders.insert_one(iceberg)
    
    return {
        "status": "created",
        "order": {k: v for k, v in iceberg.items() if k != "_id"},
        "message": f"Iceberg: {num_slices} slices of {order.visible_quantity} {order.symbol}"
    }


@router.get("/iceberg/list")
async def list_iceberg_orders(user_id: str = "default_user", db = Depends(get_database)):
    """List iceberg orders"""
    orders = await db.iceberg_orders.find({"user_id": user_id}, {"_id": 0}).to_list(50)
    return {"orders": orders}


# =============================================================================
# SUMMARY ENDPOINT
# =============================================================================

@router.get("/summary")
async def get_orders_summary(user_id: str = "default_user", db = Depends(get_database)):
    """Get summary of all advanced orders"""
    trailing = await db.trailing_stops.count_documents({"user_id": user_id, "status": "active"})
    dca = await db.dca_bots.count_documents({"user_id": user_id, "status": "active"})
    oco = await db.oco_orders.count_documents({"user_id": user_id, "status": "active"})
    iceberg = await db.iceberg_orders.count_documents({"user_id": user_id, "status": "active"})
    
    return {
        "active_orders": {
            "trailing_stops": trailing,
            "dca_bots": dca,
            "oco_orders": oco,
            "iceberg_orders": iceberg
        },
        "total_active": trailing + dca + oco + iceberg
    }

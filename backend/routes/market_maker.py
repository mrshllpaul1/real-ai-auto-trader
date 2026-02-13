"""
Market Maker Mode API Routes
=============================
Provide liquidity by placing buy/sell orders around the current price.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import asyncio
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market-maker", tags=["Market Maker"])

# Global state
_db = None
_mm_engine = None
_running = False


def set_db(db):
    """Set database reference"""
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

class MarketMakerConfig(BaseModel):
    symbol: str = "BTC/USD"
    spread_percentage: float = 0.5  # 0.5% spread
    order_size_usd: float = 100.0
    num_levels: int = 3  # Number of order levels on each side
    level_spacing_pct: float = 0.2  # Spacing between levels
    max_position_usd: float = 1000.0
    rebalance_threshold: float = 0.3  # Rebalance when position > 30% of max
    min_profit_pct: float = 0.1  # Minimum profit per round trip
    enabled: bool = True


class OrderUpdate(BaseModel):
    order_id: str
    new_price: Optional[float] = None
    new_size: Optional[float] = None
    cancel: bool = False


# =============================================================================
# MARKET MAKER ENGINE
# =============================================================================

class MarketMakerEngine:
    """Simple market making engine"""
    
    def __init__(self, db):
        self.db = db
        self.config = None
        self.is_running = False
        self.position = 0.0  # Net position in base currency
        self.total_pnl = 0.0
        self.trades_executed = 0
        self.active_orders = {"bids": [], "asks": []}
        self.last_mid_price = 0.0
        self.session_start = None
        
    async def start(self, config: MarketMakerConfig):
        """Start market making"""
        self.config = config
        self.is_running = True
        self.session_start = datetime.now(timezone.utc)
        logger.info(f"Market Maker started for {config.symbol}")
        
    def stop(self):
        """Stop market making"""
        self.is_running = False
        logger.info("Market Maker stopped")
        
    async def update_orders(self, mid_price: float):
        """Update order book with new price levels"""
        if not self.is_running or not self.config:
            return
        
        self.last_mid_price = mid_price
        spread = self.config.spread_percentage / 100
        level_spacing = self.config.level_spacing_pct / 100
        
        # Calculate bid/ask prices for each level
        bids = []
        asks = []
        
        for i in range(self.config.num_levels):
            # Bids below mid price
            bid_price = mid_price * (1 - spread/2 - i * level_spacing)
            bids.append({
                "order_id": f"bid_{i}_{uuid.uuid4().hex[:8]}",
                "side": "buy",
                "price": round(bid_price, 2),
                "size_usd": self.config.order_size_usd,
                "level": i,
                "status": "active"
            })
            
            # Asks above mid price
            ask_price = mid_price * (1 + spread/2 + i * level_spacing)
            asks.append({
                "order_id": f"ask_{i}_{uuid.uuid4().hex[:8]}",
                "side": "sell",
                "price": round(ask_price, 2),
                "size_usd": self.config.order_size_usd,
                "level": i,
                "status": "active"
            })
        
        self.active_orders = {"bids": bids, "asks": asks}
        return self.active_orders
    
    def get_status(self) -> Dict:
        """Get current market maker status"""
        return {
            "is_running": self.is_running,
            "symbol": self.config.symbol if self.config else None,
            "config": self.config.dict() if self.config else None,
            "position": round(self.position, 4),
            "total_pnl": round(self.total_pnl, 2),
            "trades_executed": self.trades_executed,
            "active_orders": self.active_orders,
            "last_mid_price": self.last_mid_price,
            "session_start": self.session_start.isoformat() if self.session_start else None,
            "session_duration": str(datetime.now(timezone.utc) - self.session_start) if self.session_start else None
        }
    
    async def simulate_fill(self, side: str, price: float, size_usd: float):
        """Simulate an order fill (for demo purposes)"""
        if side == "buy":
            self.position += size_usd / price
        else:
            self.position -= size_usd / price
        
        self.trades_executed += 1
        
        # Store trade
        trade = {
            "trade_id": str(uuid.uuid4()),
            "symbol": self.config.symbol,
            "side": side,
            "price": price,
            "size_usd": size_usd,
            "position_after": self.position,
            "executed_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.market_maker_trades.insert_one(trade)
        return trade


# Global engine instance
def get_mm_engine():
    global _mm_engine
    if _mm_engine is None:
        _mm_engine = MarketMakerEngine(_db)
    return _mm_engine


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.post("/start")
async def start_market_maker(
    config: MarketMakerConfig,
    background_tasks: BackgroundTasks,
    db = Depends(get_database)
):
    """Start market maker with specified configuration"""
    engine = get_mm_engine()
    engine.db = db
    
    if engine.is_running:
        return {"status": "already_running", "config": engine.config.dict()}
    
    await engine.start(config)
    
    # Store config
    await db.market_maker_config.replace_one(
        {"symbol": config.symbol},
        {
            "symbol": config.symbol,
            "config": config.dict(),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "running"
        },
        upsert=True
    )
    
    return {
        "status": "started",
        "message": f"Market Maker started for {config.symbol}",
        "config": config.dict()
    }


@router.post("/stop")
async def stop_market_maker(db = Depends(get_database)):
    """Stop market maker"""
    engine = get_mm_engine()
    
    if not engine.is_running:
        return {"status": "not_running"}
    
    engine.stop()
    
    # Update status in DB
    await db.market_maker_config.update_many(
        {"status": "running"},
        {"$set": {"status": "stopped", "stopped_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {
        "status": "stopped",
        "final_position": engine.position,
        "total_pnl": engine.total_pnl,
        "trades_executed": engine.trades_executed
    }


@router.get("/status")
async def get_market_maker_status(db = Depends(get_database)):
    """Get current market maker status"""
    engine = get_mm_engine()
    return engine.get_status()


@router.post("/update-orders")
async def refresh_orders(
    mid_price: float,
    db = Depends(get_database)
):
    """Update order book based on new mid price"""
    engine = get_mm_engine()
    
    if not engine.is_running:
        raise HTTPException(status_code=400, detail="Market maker not running")
    
    orders = await engine.update_orders(mid_price)
    return {
        "status": "updated",
        "mid_price": mid_price,
        "orders": orders
    }


@router.get("/orders")
async def get_active_orders(db = Depends(get_database)):
    """Get current active orders"""
    engine = get_mm_engine()
    return {
        "orders": engine.active_orders,
        "mid_price": engine.last_mid_price
    }


@router.get("/history")
async def get_trade_history(
    limit: int = 50,
    db = Depends(get_database)
):
    """Get market maker trade history"""
    trades = await db.market_maker_trades.find(
        {},
        {"_id": 0}
    ).sort("executed_at", -1).limit(limit).to_list(limit)
    
    # Calculate stats
    total_pnl = 0
    buy_volume = sum(t.get("size_usd", 0) for t in trades if t.get("side") == "buy")
    sell_volume = sum(t.get("size_usd", 0) for t in trades if t.get("side") == "sell")
    
    return {
        "trades": trades,
        "stats": {
            "total_trades": len(trades),
            "buy_volume": round(buy_volume, 2),
            "sell_volume": round(sell_volume, 2),
            "total_volume": round(buy_volume + sell_volume, 2)
        }
    }


@router.put("/config")
async def update_config(
    config: MarketMakerConfig,
    db = Depends(get_database)
):
    """Update market maker configuration"""
    engine = get_mm_engine()
    
    if engine.is_running:
        engine.config = config
        
        # Update in DB
        await db.market_maker_config.update_one(
            {"symbol": config.symbol},
            {"$set": {"config": config.dict(), "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {"status": "updated", "config": config.dict()}
    
    return {"status": "not_running", "message": "Start market maker first"}


@router.get("/pnl")
async def get_pnl_summary(db = Depends(get_database)):
    """Get P&L summary for market making"""
    engine = get_mm_engine()
    
    # Get all trades
    trades = await db.market_maker_trades.find({}, {"_id": 0}).to_list(1000)
    
    # Calculate realized P&L from completed round trips
    # Simplified: just track buy/sell difference
    buy_total = sum(t.get("size_usd", 0) for t in trades if t.get("side") == "buy")
    sell_total = sum(t.get("size_usd", 0) for t in trades if t.get("side") == "sell")
    
    return {
        "realized_pnl": round(sell_total - buy_total, 2),
        "unrealized_pnl": round(engine.position * engine.last_mid_price, 2) if engine.last_mid_price else 0,
        "total_pnl": engine.total_pnl,
        "current_position": engine.position,
        "position_value_usd": round(engine.position * engine.last_mid_price, 2) if engine.last_mid_price else 0
    }


@router.get("/analytics")
async def get_analytics(
    timeframe: str = "24h",
    db = Depends(get_database)
):
    """Get market maker analytics"""
    from datetime import timedelta
    
    hours_map = {"1h": 1, "6h": 6, "24h": 24, "7d": 168}
    hours = hours_map.get(timeframe, 24)
    
    start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    trades = await db.market_maker_trades.find({
        "executed_at": {"$gte": start_time.isoformat()}
    }, {"_id": 0}).to_list(1000)
    
    if not trades:
        return {
            "timeframe": timeframe,
            "trades": 0,
            "volume": 0,
            "avg_spread_captured": 0,
            "turnover": 0
        }
    
    volume = sum(t.get("size_usd", 0) for t in trades)
    
    return {
        "timeframe": timeframe,
        "trades": len(trades),
        "volume": round(volume, 2),
        "avg_trade_size": round(volume / len(trades), 2) if trades else 0,
        "buy_trades": sum(1 for t in trades if t.get("side") == "buy"),
        "sell_trades": sum(1 for t in trades if t.get("side") == "sell"),
        "hours": hours
    }


@router.get("/presets")
async def get_presets():
    """Get predefined market maker configurations"""
    return {
        "presets": [
            {
                "name": "Conservative",
                "description": "Wide spreads, small positions. Lower risk, lower reward.",
                "config": {
                    "spread_percentage": 1.0,
                    "order_size_usd": 50,
                    "num_levels": 2,
                    "level_spacing_pct": 0.5,
                    "max_position_usd": 500
                }
            },
            {
                "name": "Balanced",
                "description": "Moderate spreads and position sizes. Good for most conditions.",
                "config": {
                    "spread_percentage": 0.5,
                    "order_size_usd": 100,
                    "num_levels": 3,
                    "level_spacing_pct": 0.2,
                    "max_position_usd": 1000
                }
            },
            {
                "name": "Aggressive",
                "description": "Tight spreads, larger positions. Higher risk, higher reward.",
                "config": {
                    "spread_percentage": 0.25,
                    "order_size_usd": 200,
                    "num_levels": 5,
                    "level_spacing_pct": 0.1,
                    "max_position_usd": 2000
                }
            },
            {
                "name": "High Frequency",
                "description": "Very tight spreads for high-volume markets. Requires fast execution.",
                "config": {
                    "spread_percentage": 0.1,
                    "order_size_usd": 50,
                    "num_levels": 10,
                    "level_spacing_pct": 0.05,
                    "max_position_usd": 500
                }
            }
        ]
    }

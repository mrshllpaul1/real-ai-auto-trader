"""
Copy Trading API Routes
========================
Enable users to follow and copy trades from successful traders.
Enhanced with real-time sync, advanced risk management, and performance analytics.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, WebSocket
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/copy-trading", tags=["Copy Trading"])

# Global database and service references
_db = None
_enhanced_service = None


def set_db(db):
    """Set database reference"""
    global _db
    _db = db


def set_enhanced_service(service):
    """Set enhanced copy trading service"""
    global _enhanced_service
    _enhanced_service = service


async def get_database():
    global _db
    if _db is None:
        from server import db
        _db = db
    return _db


# =============================================================================
# MODELS
# =============================================================================

class TraderProfile(BaseModel):
    trader_id: str
    display_name: str
    bio: Optional[str] = None
    is_public: bool = True
    min_copy_amount: float = 50.0
    max_copiers: int = 100
    profit_share_pct: float = 10.0  # Percentage of profits shared with copier


class FollowRequest(BaseModel):
    trader_id: str
    copy_amount: float
    copy_percentage: float = 100.0  # Copy 100% of trades by default
    max_trade_size: Optional[float] = None
    stop_loss_pct: Optional[float] = None


class CopySettings(BaseModel):
    copy_percentage: float = 100.0
    max_trade_size: Optional[float] = None
    stop_loss_pct: Optional[float] = None
    enabled: bool = True


# =============================================================================
# LEADERBOARD ENDPOINTS
# =============================================================================

@router.get("/leaderboard")
async def get_leaderboard(
    timeframe: str = "30d",
    sort_by: str = "roi",
    limit: int = 20,
    db = Depends(get_database)
):
    """
    Get top traders leaderboard.
    Timeframes: 7d, 30d, 90d, all
    Sort by: roi, win_rate, total_trades, copiers
    """
    try:
        # Calculate date filter
        days_map = {"7d": 7, "30d": 30, "90d": 90, "all": 3650}
        days = days_map.get(timeframe, 30)
        
        from datetime import timedelta
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get all public traders with their stats
        traders = await db.trader_profiles.find(
            {"is_public": True}
        ).to_list(100)
        
        leaderboard = []
        for trader in traders:
            trader_id = trader.get("trader_id")
            
            # Get trade history for this trader
            trades = await db.copy_trade_history.find({
                "trader_id": trader_id,
                "executed_at": {"$gte": start_date.isoformat()}
            }).to_list(1000)
            
            if not trades:
                # Use mock data for demo
                stats = {
                    "total_trades": 0,
                    "win_rate": 0,
                    "roi": 0,
                    "avg_trade_size": 0,
                    "copiers": 0
                }
            else:
                wins = sum(1 for t in trades if t.get("profit", 0) > 0)
                total_profit = sum(t.get("profit", 0) for t in trades)
                total_invested = sum(t.get("amount", 0) for t in trades)
                
                stats = {
                    "total_trades": len(trades),
                    "win_rate": round((wins / len(trades)) * 100, 1) if trades else 0,
                    "roi": round((total_profit / total_invested) * 100, 1) if total_invested > 0 else 0,
                    "avg_trade_size": round(total_invested / len(trades), 2) if trades else 0
                }
            
            # Get copier count
            copier_count = await db.copy_relationships.count_documents({
                "trader_id": trader_id,
                "active": True
            })
            
            leaderboard.append({
                "trader_id": trader_id,
                "display_name": trader.get("display_name", f"Trader_{trader_id[:8]}"),
                "bio": trader.get("bio"),
                "profit_share_pct": trader.get("profit_share_pct", 10),
                "copiers": copier_count,
                "stats": stats,
                "joined_at": trader.get("created_at")
            })
        
        # Sort by requested field
        sort_key = {
            "roi": lambda x: x["stats"]["roi"],
            "win_rate": lambda x: x["stats"]["win_rate"],
            "total_trades": lambda x: x["stats"]["total_trades"],
            "copiers": lambda x: x["copiers"]
        }.get(sort_by, lambda x: x["stats"]["roi"])
        
        leaderboard.sort(key=sort_key, reverse=True)
        
        # If empty, provide sample data
        if not leaderboard:
            leaderboard = [
                {
                    "trader_id": "sample_trader_1",
                    "display_name": "CryptoWhale",
                    "bio": "10+ years trading experience. Focus on BTC and ETH.",
                    "profit_share_pct": 10,
                    "copiers": 245,
                    "stats": {"total_trades": 892, "win_rate": 67.5, "roi": 142.3, "avg_trade_size": 1500},
                    "joined_at": "2024-01-15T00:00:00Z"
                },
                {
                    "trader_id": "sample_trader_2",
                    "display_name": "AltcoinHunter",
                    "bio": "Specializing in finding hidden gem altcoins.",
                    "profit_share_pct": 15,
                    "copiers": 189,
                    "stats": {"total_trades": 567, "win_rate": 71.2, "roi": 198.7, "avg_trade_size": 500},
                    "joined_at": "2024-03-22T00:00:00Z"
                },
                {
                    "trader_id": "sample_trader_3",
                    "display_name": "SwingMaster",
                    "bio": "Swing trading with strict risk management.",
                    "profit_share_pct": 12,
                    "copiers": 156,
                    "stats": {"total_trades": 423, "win_rate": 62.8, "roi": 89.4, "avg_trade_size": 2000},
                    "joined_at": "2024-02-10T00:00:00Z"
                }
            ]
        
        return {
            "leaderboard": leaderboard[:limit],
            "timeframe": timeframe,
            "sort_by": sort_by,
            "total_traders": len(leaderboard)
        }
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# TRADER PROFILE ENDPOINTS
# =============================================================================

@router.post("/profile/create")
async def create_trader_profile(
    profile: TraderProfile,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Create or update trader profile to become a signal provider"""
    try:
        profile_data = {
            "trader_id": profile.trader_id or user_id,
            "user_id": user_id,
            "display_name": profile.display_name,
            "bio": profile.bio,
            "is_public": profile.is_public,
            "min_copy_amount": profile.min_copy_amount,
            "max_copiers": profile.max_copiers,
            "profit_share_pct": profile.profit_share_pct,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.trader_profiles.replace_one(
            {"trader_id": profile.trader_id},
            profile_data,
            upsert=True
        )
        
        return {"status": "success", "message": "Trader profile created", "profile": profile_data}
    except Exception as e:
        logger.error(f"Error creating trader profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{trader_id}")
async def get_trader_profile(trader_id: str, db = Depends(get_database)):
    """Get detailed trader profile"""
    try:
        profile = await db.trader_profiles.find_one(
            {"trader_id": trader_id},
            {"_id": 0}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Trader not found")
        
        # Get recent trades
        recent_trades = await db.copy_trade_history.find(
            {"trader_id": trader_id}
        ).sort("executed_at", -1).limit(10).to_list(10)
        
        # Get copier count
        copier_count = await db.copy_relationships.count_documents({
            "trader_id": trader_id,
            "active": True
        })
        
        return {
            "profile": profile,
            "copiers": copier_count,
            "recent_trades": [{k: v for k, v in t.items() if k != "_id"} for t in recent_trades]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trader profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# FOLLOWING ENDPOINTS
# =============================================================================

@router.post("/follow")
async def follow_trader(
    request: FollowRequest,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Start copying a trader's trades"""
    try:
        # Check if trader exists
        trader = await db.trader_profiles.find_one({"trader_id": request.trader_id})
        if not trader:
            raise HTTPException(status_code=404, detail="Trader not found")
        
        # Check minimum copy amount
        if request.copy_amount < trader.get("min_copy_amount", 50):
            raise HTTPException(
                status_code=400, 
                detail=f"Minimum copy amount is ${trader.get('min_copy_amount', 50)}"
            )
        
        # Check if already following
        existing = await db.copy_relationships.find_one({
            "user_id": user_id,
            "trader_id": request.trader_id
        })
        
        if existing and existing.get("active"):
            raise HTTPException(status_code=400, detail="Already following this trader")
        
        # Create copy relationship
        relationship = {
            "relationship_id": str(uuid.uuid4()),
            "user_id": user_id,
            "trader_id": request.trader_id,
            "copy_amount": request.copy_amount,
            "copy_percentage": request.copy_percentage,
            "max_trade_size": request.max_trade_size,
            "stop_loss_pct": request.stop_loss_pct,
            "active": True,
            "total_copied": 0,
            "total_profit": 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.copy_relationships.replace_one(
            {"user_id": user_id, "trader_id": request.trader_id},
            relationship,
            upsert=True
        )
        
        return {
            "status": "success",
            "message": f"Now copying {trader.get('display_name', request.trader_id)}",
            "relationship": relationship
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error following trader: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unfollow/{trader_id}")
async def unfollow_trader(
    trader_id: str,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Stop copying a trader"""
    try:
        result = await db.copy_relationships.update_one(
            {"user_id": user_id, "trader_id": trader_id},
            {"$set": {"active": False, "ended_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Not following this trader")
        
        return {"status": "success", "message": "Unfollowed trader"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unfollowing trader: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/following")
async def get_following(user_id: str = "default_user", db = Depends(get_database)):
    """Get list of traders user is following"""
    try:
        relationships = await db.copy_relationships.find(
            {"user_id": user_id, "active": True},
            {"_id": 0}
        ).to_list(50)
        
        # Enrich with trader details
        for rel in relationships:
            trader = await db.trader_profiles.find_one(
                {"trader_id": rel["trader_id"]},
                {"_id": 0, "display_name": 1, "profit_share_pct": 1}
            )
            if trader:
                rel["trader_name"] = trader.get("display_name")
                rel["profit_share_pct"] = trader.get("profit_share_pct")
        
        return {
            "following": relationships,
            "total": len(relationships)
        }
    except Exception as e:
        logger.error(f"Error getting following list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings/{trader_id}")
async def update_copy_settings(
    trader_id: str,
    settings: CopySettings,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """Update copy trading settings for a specific trader"""
    try:
        result = await db.copy_relationships.update_one(
            {"user_id": user_id, "trader_id": trader_id},
            {"$set": {
                "copy_percentage": settings.copy_percentage,
                "max_trade_size": settings.max_trade_size,
                "stop_loss_pct": settings.stop_loss_pct,
                "enabled": settings.enabled,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Copy relationship not found")
        
        return {"status": "success", "message": "Settings updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating copy settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# COPY HISTORY ENDPOINTS
# =============================================================================

@router.get("/history")
async def get_copy_history(
    user_id: str = "default_user",
    limit: int = 50,
    db = Depends(get_database)
):
    """Get history of copied trades"""
    try:
        history = await db.copied_trades.find(
            {"copier_id": user_id},
            {"_id": 0}
        ).sort("copied_at", -1).limit(limit).to_list(limit)
        
        # Calculate stats
        total_profit = sum(t.get("profit", 0) for t in history)
        total_invested = sum(t.get("amount", 0) for t in history)
        wins = sum(1 for t in history if t.get("profit", 0) > 0)
        
        return {
            "history": history,
            "stats": {
                "total_trades": len(history),
                "total_profit": round(total_profit, 2),
                "total_invested": round(total_invested, 2),
                "win_rate": round((wins / len(history)) * 100, 1) if history else 0,
                "roi": round((total_profit / total_invested) * 100, 1) if total_invested > 0 else 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting copy history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_copy_trading_stats(user_id: str = "default_user", db = Depends(get_database)):
    """Get overall copy trading statistics"""
    try:
        # Get all active relationships
        relationships = await db.copy_relationships.find(
            {"user_id": user_id, "active": True}
        ).to_list(50)
        
        # Get all copied trades
        all_trades = await db.copied_trades.find(
            {"copier_id": user_id}
        ).to_list(1000)
        
        total_allocated = sum(r.get("copy_amount", 0) for r in relationships)
        total_profit = sum(t.get("profit", 0) for t in all_trades)
        total_trades = len(all_trades)
        
        return {
            "traders_following": len(relationships),
            "total_allocated": round(total_allocated, 2),
            "total_profit": round(total_profit, 2),
            "total_trades_copied": total_trades,
            "active_copies": sum(1 for r in relationships if r.get("enabled", True)),
            "best_performing_trader": None  # Would calculate from data
        }
    except Exception as e:
        logger.error(f"Error getting copy trading stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENHANCED COPY TRADING ENDPOINTS
# =============================================================================

@router.post("/signal/broadcast")
async def broadcast_trade_signal(
    trader_id: str,
    trade: Dict[str, Any],
    signal_type: str = "entry",
    db = Depends(get_database)
):
    """
    Broadcast a real-time trade signal to all copiers
    
    Args:
        trader_id: ID of trader making the trade
        trade: Trade details (symbol, action, price, amount, etc.)
        signal_type: "entry", "exit", "stop_loss", or "take_profit"
    """
    if not _enhanced_service:
        raise HTTPException(status_code=503, detail="Enhanced service not available")
    
    try:
        result = await _enhanced_service.broadcast_trade_signal(
            trader_id=trader_id,
            trade=trade,
            signal_type=signal_type
        )
        return result
    except Exception as e:
        logger.error(f"Error broadcasting trade signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/trader/{trader_id}")
async def get_trader_analytics(
    trader_id: str,
    timeframe_days: int = 30,
    db = Depends(get_database)
):
    """
    Get comprehensive performance analytics for a trader
    
    Includes:
    - Win rate, profit metrics
    - Sharpe ratio, Sortino ratio
    - Maximum drawdown
    - Average trade duration
    - Risk-reward ratio
    """
    if not _enhanced_service:
        raise HTTPException(status_code=503, detail="Enhanced service not available")
    
    try:
        metrics = await _enhanced_service.calculate_trader_performance_metrics(
            trader_id=trader_id,
            timeframe_days=timeframe_days
        )
        return metrics
    except Exception as e:
        logger.error(f"Error getting trader analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/equity-curve/{copier_id}")
async def get_copier_equity_curve(
    copier_id: str,
    days: int = 30,
    db = Depends(get_database)
):
    """
    Get copier's equity curve for visualization and drawdown analysis
    """
    if not _enhanced_service:
        raise HTTPException(status_code=503, detail="Enhanced service not available")
    
    try:
        curve = await _enhanced_service.get_copier_equity_curve(
            copier_id=copier_id,
            days=days
        )
        return {
            "copier_id": copier_id,
            "days": days,
            "data_points": len(curve),
            "equity_curve": curve
        }
    except Exception as e:
        logger.error(f"Error getting equity curve: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profit-share/calculate")
async def calculate_profit_share(
    trader_id: str,
    copier_id: str,
    period_start: str,
    period_end: Optional[str] = None,
    db = Depends(get_database)
):
    """
    Calculate profit share owed to trader from copier's profits
    """
    if not _enhanced_service:
        raise HTTPException(status_code=503, detail="Enhanced service not available")
    
    try:
        start = datetime.fromisoformat(period_start.replace('Z', '+00:00'))
        end = datetime.fromisoformat(period_end.replace('Z', '+00:00')) if period_end else None
        
        share = await _enhanced_service.calculate_profit_share(
            trader_id=trader_id,
            copier_id=copier_id,
            period_start=start,
            period_end=end
        )
        return share
    except Exception as e:
        logger.error(f"Error calculating profit share: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profit-share/{share_id}/distribute")
async def distribute_profit_share(
    share_id: str,
    db = Depends(get_database)
):
    """
    Process and distribute profit share to trader
    """
    if not _enhanced_service:
        raise HTTPException(status_code=503, detail="Enhanced service not available")
    
    try:
        result = await _enhanced_service.process_profit_distribution(share_id)
        return result
    except Exception as e:
        logger.error(f"Error distributing profit share: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify/{trader_id}")
async def verify_trader(
    trader_id: str,
    db = Depends(get_database)
):
    """
    Verify trader's performance legitimacy
    
    Checks for:
    - Wash trading
    - Suspiciously high win rates
    - Unusual trading patterns
    - Performance manipulation
    """
    if not _enhanced_service:
        raise HTTPException(status_code=503, detail="Enhanced service not available")
    
    try:
        verification = await _enhanced_service.verify_trader_performance(trader_id)
        return verification
    except Exception as e:
        logger.error(f"Error verifying trader: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/compare/{copier_id}")
async def compare_copier_performance(
    copier_id: str,
    db = Depends(get_database)
):
    """
    Compare copier's performance across all traders they follow
    """
    if not _enhanced_service:
        raise HTTPException(status_code=503, detail="Enhanced service not available")
    
    try:
        comparison = await _enhanced_service.get_copy_performance_comparison(copier_id)
        return comparison
    except Exception as e:
        logger.error(f"Error comparing performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings/{trader_id}/risk")
async def update_risk_settings(
    trader_id: str,
    max_drawdown_pct: Optional[float] = None,
    max_daily_trades: Optional[int] = None,
    max_position_pct: Optional[float] = None,
    max_slippage_pct: Optional[float] = None,
    user_id: str = "default_user",
    db = Depends(get_database)
):
    """
    Update advanced risk management settings for copy relationship
    """
    try:
        updates = {}
        if max_drawdown_pct is not None:
            updates["max_drawdown_pct"] = max_drawdown_pct
        if max_daily_trades is not None:
            updates["max_daily_trades"] = max_daily_trades
        if max_position_pct is not None:
            updates["max_position_pct"] = max_position_pct
        if max_slippage_pct is not None:
            updates["max_slippage_pct"] = max_slippage_pct
        
        if updates:
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            result = await db.copy_relationships.update_one(
                {"user_id": user_id, "trader_id": trader_id},
                {"$set": updates}
            )
            
            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="Copy relationship not found")
            
            return {"status": "success", "message": "Risk settings updated", "updates": updates}
        else:
            raise HTTPException(status_code=400, detail="No settings provided")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating risk settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/leaderboard/enhanced")
async def get_enhanced_leaderboard(
    timeframe: str = "30d",
    sort_by: str = "sharpe_ratio",
    min_trades: int = 20,
    limit: int = 20,
    db = Depends(get_database)
):
    """
    Enhanced leaderboard with advanced performance metrics
    
    Sort options:
    - sharpe_ratio: Risk-adjusted returns
    - sortino_ratio: Downside risk-adjusted returns
    - profit_factor: Ratio of gross profit to gross loss
    - roi: Return on investment
    - max_drawdown: Lowest drawdown (best first)
    """
    if not _enhanced_service:
        # Fallback to basic leaderboard
        return await get_leaderboard(timeframe=timeframe, sort_by="roi", limit=limit, db=db)
    
    try:
        days_map = {"7d": 7, "30d": 30, "90d": 90, "all": 365}
        days = days_map.get(timeframe, 30)
        
        # Get all public traders
        traders = await db.trader_profiles.find({
            "is_public": True
        }).to_list(200)
        
        enhanced_traders = []
        
        for trader in traders:
            trader_id = trader.get("trader_id")
            
            # Get enhanced metrics
            metrics = await _enhanced_service.calculate_trader_performance_metrics(
                trader_id=trader_id,
                timeframe_days=days
            )
            
            # Filter by minimum trades
            if metrics.get("total_trades", 0) < min_trades:
                continue
            
            # Get copier count
            copier_count = await db.copy_relationships.count_documents({
                "trader_id": trader_id,
                "active": True
            })
            
            enhanced_traders.append({
                "trader_id": trader_id,
                "display_name": trader.get("display_name", f"Trader_{trader_id[:8]}"),
                "bio": trader.get("bio"),
                "profit_share_pct": trader.get("profit_share_pct", 10),
                "copiers": copier_count,
                "metrics": metrics,
                "badges": trader.get("badges", [])
            })
        
        # Sort by requested metric
        sort_key_map = {
            "sharpe_ratio": lambda x: x["metrics"].get("sharpe_ratio", 0),
            "sortino_ratio": lambda x: x["metrics"].get("sortino_ratio", 0),
            "profit_factor": lambda x: x["metrics"].get("profit_factor", 0),
            "roi": lambda x: x["metrics"].get("total_profit", 0),
            "max_drawdown": lambda x: -x["metrics"].get("max_drawdown_pct", 100)  # Negative for ascending
        }
        
        sort_key = sort_key_map.get(sort_by, lambda x: x["metrics"].get("sharpe_ratio", 0))
        enhanced_traders.sort(key=sort_key, reverse=True)
        
        return {
            "leaderboard": enhanced_traders[:limit],
            "timeframe": timeframe,
            "sort_by": sort_by,
            "total_traders": len(enhanced_traders),
            "enhanced": True
        }
        
    except Exception as e:
        logger.error(f"Error getting enhanced leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# =============================================================================
# WEBSOCKET ENDPOINT
# =============================================================================

@router.websocket("/ws/signals/{copier_id}")
async def websocket_trade_signals(
    websocket: WebSocket,
    copier_id: str,
    trader_ids: str = ""
):
    """
    WebSocket endpoint for real-time trade signals
    
    Usage:
        ws://host/api/copy-trading/ws/signals/{copier_id}?trader_ids=trader1,trader2
    
    Client receives:
        - trade_signal: When a followed trader makes a trade
        - notification: System notifications (risk alerts, etc.)
        - market_update: General market updates
    
    Client can send:
        - ping: Keepalive (receives pong)
        - update_subscriptions: Change followed traders
    """
    from services.copy_trading_websocket import handle_copy_trading_websocket
    
    await handle_copy_trading_websocket(websocket, copier_id, trader_ids)


@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    from services.copy_trading_websocket import get_websocket_manager
    
    manager = get_websocket_manager()
    stats = manager.get_connection_stats()
    
    return stats

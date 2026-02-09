"""
Upgrades API Routes
===================
Routes for all upgraded features: P0, P1, PWA, P3
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

router = APIRouter(prefix="/upgrades", tags=["upgrades"])


# ============================================================================
# Push Notifications Routes
# ============================================================================

class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: Dict[str, str]
    device_info: Optional[str] = None


class NotificationPreferencesRequest(BaseModel):
    preferences: Dict[str, bool]


@router.post("/notifications/subscribe")
async def subscribe_push(request: PushSubscriptionRequest):
    """Subscribe to push notifications"""
    from services.push_notifications import get_push_service
    service = get_push_service()
    if not service:
        raise HTTPException(500, "Push service not available")
    
    user_id = "demo_user"  # Would come from auth in production
    return await service.subscribe(user_id, request.dict(), request.device_info)


@router.post("/notifications/unsubscribe")
async def unsubscribe_push(endpoint: str):
    """Unsubscribe from push notifications"""
    from services.push_notifications import get_push_service
    service = get_push_service()
    if not service:
        raise HTTPException(500, "Push service not available")
    
    return await service.unsubscribe("demo_user", endpoint)


@router.get("/notifications/pending")
async def get_pending_notifications():
    """Get pending notifications for polling"""
    from services.push_notifications import get_push_service
    service = get_push_service()
    if not service:
        return []
    
    return await service.get_pending_notifications("demo_user")


@router.get("/notifications/history")
async def get_notification_history(limit: int = 50, unread_only: bool = False):
    """Get notification history"""
    from services.push_notifications import get_push_service
    service = get_push_service()
    if not service:
        return []
    
    return await service.get_notification_history("demo_user", limit, unread_only)


@router.post("/notifications/preferences")
async def set_notification_preferences(request: NotificationPreferencesRequest):
    """Set notification preferences"""
    from services.push_notifications import get_push_service
    service = get_push_service()
    if not service:
        raise HTTPException(500, "Push service not available")
    
    return await service.set_preferences("demo_user", request.preferences)


@router.get("/notifications/status")
async def get_notifications_status():
    """Get push notification service status"""
    from services.push_notifications import get_push_service
    service = get_push_service()
    if not service:
        return {"active": False}
    
    return await service.get_status()


# ============================================================================
# Arbitrage Routes
# ============================================================================

class ArbitrageSettingsRequest(BaseModel):
    min_spread_pct: Optional[float] = None
    min_profit_usd: Optional[float] = None
    max_trade_size_usd: Optional[float] = None
    auto_execute: Optional[bool] = None
    enabled_exchanges: Optional[List[str]] = None


@router.get("/arbitrage/status")
async def get_arbitrage_status():
    """Get arbitrage service status"""
    from services.arbitrage_service import get_arbitrage_service
    service = get_arbitrage_service()
    if not service:
        return {"is_monitoring": False, "message": "Service not initialized"}
    
    return await service.get_status()


@router.post("/arbitrage/start")
async def start_arbitrage_monitoring():
    """Start arbitrage monitoring"""
    from services.arbitrage_service import get_arbitrage_service
    service = get_arbitrage_service()
    if not service:
        raise HTTPException(500, "Arbitrage service not available")
    
    return await service.start_monitoring()


@router.post("/arbitrage/stop")
async def stop_arbitrage_monitoring():
    """Stop arbitrage monitoring"""
    from services.arbitrage_service import get_arbitrage_service
    service = get_arbitrage_service()
    if not service:
        raise HTTPException(500, "Arbitrage service not available")
    
    return await service.stop_monitoring()


@router.get("/arbitrage/prices")
async def get_exchange_prices():
    """Get current prices from all exchanges"""
    from services.arbitrage_service import get_arbitrage_service
    service = get_arbitrage_service()
    if not service:
        return {}
    
    return await service.get_prices()


@router.get("/arbitrage/opportunities")
async def get_arbitrage_opportunities():
    """Get current arbitrage opportunities"""
    from services.arbitrage_service import get_arbitrage_service
    service = get_arbitrage_service()
    if not service:
        return []
    
    return await service.get_opportunities()


@router.post("/arbitrage/execute/{opportunity_id}")
async def execute_arbitrage(opportunity_id: str):
    """Execute an arbitrage trade"""
    from services.arbitrage_service import get_arbitrage_service
    service = get_arbitrage_service()
    if not service:
        raise HTTPException(500, "Arbitrage service not available")
    
    return await service.execute_arbitrage(opportunity_id)


@router.post("/arbitrage/settings")
async def update_arbitrage_settings(request: ArbitrageSettingsRequest):
    """Update arbitrage settings"""
    from services.arbitrage_service import get_arbitrage_service
    service = get_arbitrage_service()
    if not service:
        raise HTTPException(500, "Arbitrage service not available")
    
    return await service.update_settings(request.dict(exclude_none=True))


@router.get("/arbitrage/history")
async def get_arbitrage_history(limit: int = 50):
    """Get arbitrage opportunity history"""
    from services.arbitrage_service import get_arbitrage_service
    service = get_arbitrage_service()
    if not service:
        return []
    
    return await service.get_history(limit)


# ============================================================================
# Rebalancer Routes
# ============================================================================

class AllocationRequest(BaseModel):
    allocations: Dict[str, float]
    tolerance_pct: Optional[float] = 5.0


class RebalancerSettingsRequest(BaseModel):
    rebalance_threshold_pct: Optional[float] = None
    min_trade_usd: Optional[float] = None
    max_trade_pct: Optional[float] = None
    check_interval_hours: Optional[int] = None
    auto_execute: Optional[bool] = None


@router.get("/rebalancer/status")
async def get_rebalancer_status():
    """Get rebalancer service status"""
    from services.portfolio_rebalancer import get_rebalancer
    service = get_rebalancer()
    if not service:
        return {"enabled": False, "message": "Service not initialized"}
    
    return await service.get_status()


@router.get("/rebalancer/allocations")
async def get_current_allocations():
    """Get current portfolio allocations"""
    from services.portfolio_rebalancer import get_rebalancer
    service = get_rebalancer()
    if not service:
        raise HTTPException(500, "Rebalancer service not available")
    
    return await service.get_current_allocations()


@router.post("/rebalancer/allocations")
async def set_target_allocations(request: AllocationRequest):
    """Set target allocations"""
    from services.portfolio_rebalancer import get_rebalancer
    service = get_rebalancer()
    if not service:
        raise HTTPException(500, "Rebalancer service not available")
    
    return await service.set_target_allocations(request.allocations, request.tolerance_pct)


@router.post("/rebalancer/template/{template_name}")
async def apply_allocation_template(template_name: str):
    """Apply a predefined allocation template"""
    from services.portfolio_rebalancer import get_rebalancer
    service = get_rebalancer()
    if not service:
        raise HTTPException(500, "Rebalancer service not available")
    
    return await service.apply_template(template_name)


@router.get("/rebalancer/analyze")
async def analyze_rebalance():
    """Analyze portfolio and get rebalance recommendations"""
    from services.portfolio_rebalancer import get_rebalancer
    service = get_rebalancer()
    if not service:
        raise HTTPException(500, "Rebalancer service not available")
    
    return await service.analyze_rebalance()


@router.post("/rebalancer/execute")
async def execute_rebalance(dry_run: bool = True):
    """Execute rebalancing trades"""
    from services.portfolio_rebalancer import get_rebalancer
    service = get_rebalancer()
    if not service:
        raise HTTPException(500, "Rebalancer service not available")
    
    return await service.execute_rebalance(dry_run)


@router.post("/rebalancer/start")
async def start_auto_rebalance():
    """Start automatic rebalancing"""
    from services.portfolio_rebalancer import get_rebalancer
    service = get_rebalancer()
    if not service:
        raise HTTPException(500, "Rebalancer service not available")
    
    return await service.start_auto_rebalance()


@router.post("/rebalancer/stop")
async def stop_auto_rebalance():
    """Stop automatic rebalancing"""
    from services.portfolio_rebalancer import get_rebalancer
    service = get_rebalancer()
    if not service:
        raise HTTPException(500, "Rebalancer service not available")
    
    return await service.stop_auto_rebalance()


@router.get("/rebalancer/history")
async def get_rebalance_history(limit: int = 20):
    """Get rebalancing history"""
    from services.portfolio_rebalancer import get_rebalancer
    service = get_rebalancer()
    if not service:
        return []
    
    return await service.get_history(limit)


# ============================================================================
# Trailing Stop Routes
# ============================================================================

class TrailingStopRequest(BaseModel):
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    quantity: float
    trail_pct: Optional[float] = None


class TrailingStopUpdateRequest(BaseModel):
    trail_pct: Optional[float] = None
    quantity: Optional[float] = None


@router.get("/trailing-stops/status")
async def get_trailing_stops_status():
    """Get trailing stop service status"""
    from services.trailing_stop_service import get_trailing_stop_service
    service = get_trailing_stop_service()
    if not service:
        return {"is_monitoring": False, "message": "Service not initialized"}
    
    return await service.get_status()


@router.post("/trailing-stops/create")
async def create_trailing_stop(request: TrailingStopRequest):
    """Create a new trailing stop"""
    from services.trailing_stop_service import get_trailing_stop_service
    service = get_trailing_stop_service()
    if not service:
        raise HTTPException(500, "Trailing stop service not available")
    
    return await service.create_trailing_stop(
        user_id="demo_user",
        symbol=request.symbol,
        side=request.side,
        entry_price=request.entry_price,
        quantity=request.quantity,
        trail_pct=request.trail_pct
    )


@router.put("/trailing-stops/{stop_id}")
async def update_trailing_stop(stop_id: str, request: TrailingStopUpdateRequest):
    """Update a trailing stop"""
    from services.trailing_stop_service import get_trailing_stop_service
    service = get_trailing_stop_service()
    if not service:
        raise HTTPException(500, "Trailing stop service not available")
    
    return await service.update_trailing_stop(stop_id, request.trail_pct, request.quantity)


@router.delete("/trailing-stops/{stop_id}")
async def cancel_trailing_stop(stop_id: str):
    """Cancel a trailing stop"""
    from services.trailing_stop_service import get_trailing_stop_service
    service = get_trailing_stop_service()
    if not service:
        raise HTTPException(500, "Trailing stop service not available")
    
    return await service.cancel_trailing_stop(stop_id)


@router.get("/trailing-stops/active")
async def get_active_trailing_stops():
    """Get all active trailing stops"""
    from services.trailing_stop_service import get_trailing_stop_service
    service = get_trailing_stop_service()
    if not service:
        return []
    
    return await service.get_active_stops("demo_user")


@router.post("/trailing-stops/start")
async def start_trailing_stop_monitoring():
    """Start trailing stop monitoring"""
    from services.trailing_stop_service import get_trailing_stop_service
    service = get_trailing_stop_service()
    if not service:
        raise HTTPException(500, "Trailing stop service not available")
    
    return await service.start_monitoring()


@router.post("/trailing-stops/stop")
async def stop_trailing_stop_monitoring():
    """Stop trailing stop monitoring"""
    from services.trailing_stop_service import get_trailing_stop_service
    service = get_trailing_stop_service()
    if not service:
        raise HTTPException(500, "Trailing stop service not available")
    
    return await service.stop_monitoring()


@router.get("/trailing-stops/history")
async def get_trailing_stop_history(limit: int = 50):
    """Get trailing stop history"""
    from services.trailing_stop_service import get_trailing_stop_service
    service = get_trailing_stop_service()
    if not service:
        return []
    
    return await service.get_history("demo_user", limit)


# ============================================================================
# Whale Tracking Routes
# ============================================================================

class WalletRequest(BaseModel):
    address: str
    label: str


@router.get("/whale/status")
async def get_whale_status():
    """Get whale tracking service status"""
    from services.whale_tracking import get_whale_service
    service = get_whale_service()
    if not service:
        return {"is_monitoring": False, "message": "Service not initialized"}
    
    return await service.get_status()


@router.post("/whale/start")
async def start_whale_monitoring():
    """Start whale monitoring"""
    from services.whale_tracking import get_whale_service
    service = get_whale_service()
    if not service:
        raise HTTPException(500, "Whale service not available")
    
    return await service.start_monitoring()


@router.post("/whale/stop")
async def stop_whale_monitoring():
    """Stop whale monitoring"""
    from services.whale_tracking import get_whale_service
    service = get_whale_service()
    if not service:
        raise HTTPException(500, "Whale service not available")
    
    return await service.stop_monitoring()


@router.get("/whale/transactions")
async def get_whale_transactions(limit: int = 50):
    """Get recent whale transactions"""
    from services.whale_tracking import get_whale_service
    service = get_whale_service()
    if not service:
        return []
    
    return await service.get_recent_transactions(limit)


@router.get("/whale/wallets")
async def get_watched_wallets():
    """Get all watched wallets"""
    from services.whale_tracking import get_whale_service
    service = get_whale_service()
    if not service:
        return []
    
    return await service.get_watched_wallets()


@router.post("/whale/wallets")
async def add_watched_wallet(request: WalletRequest):
    """Add a wallet to watch"""
    from services.whale_tracking import get_whale_service
    service = get_whale_service()
    if not service:
        raise HTTPException(500, "Whale service not available")
    
    return await service.add_wallet(request.address, request.label)


@router.delete("/whale/wallets/{address}")
async def remove_watched_wallet(address: str):
    """Remove a wallet from watch list"""
    from services.whale_tracking import get_whale_service
    service = get_whale_service()
    if not service:
        raise HTTPException(500, "Whale service not available")
    
    return await service.remove_wallet(address)


@router.get("/whale/flows")
async def get_exchange_flows(hours: int = 24):
    """Get exchange in/out flows"""
    from services.whale_tracking import get_whale_service
    service = get_whale_service()
    if not service:
        return {"error": "Service not available"}
    
    return await service.get_exchange_flows(hours)


@router.get("/whale/history")
async def get_whale_history(limit: int = 100):
    """Get whale transaction history"""
    from services.whale_tracking import get_whale_service
    service = get_whale_service()
    if not service:
        return []
    
    return await service.get_history(limit)


# ============================================================================
# Sentiment Analysis Routes (P1)
# ============================================================================

@router.get("/sentiment/status")
async def get_sentiment_status():
    """Get sentiment analysis service status"""
    from services.sentiment_analysis import get_sentiment_service
    service = get_sentiment_service()
    if not service:
        return {"is_monitoring": False, "message": "Service not initialized"}
    
    return await service.get_status()


@router.post("/sentiment/start")
async def start_sentiment_monitoring():
    """Start sentiment monitoring"""
    from services.sentiment_analysis import get_sentiment_service
    service = get_sentiment_service()
    if not service:
        raise HTTPException(500, "Sentiment service not available")
    
    return await service.start_monitoring()


@router.post("/sentiment/stop")
async def stop_sentiment_monitoring():
    """Stop sentiment monitoring"""
    from services.sentiment_analysis import get_sentiment_service
    service = get_sentiment_service()
    if not service:
        raise HTTPException(500, "Sentiment service not available")
    
    return await service.stop_monitoring()


@router.get("/sentiment/data")
async def get_sentiment_data(coin: Optional[str] = None):
    """Get sentiment data for a coin or all coins"""
    from services.sentiment_analysis import get_sentiment_service
    service = get_sentiment_service()
    if not service:
        return {}
    
    return await service.get_sentiment(coin)


@router.get("/sentiment/trending")
async def get_trending_sentiment(limit: int = 10):
    """Get trending coins by sentiment activity"""
    from services.sentiment_analysis import get_sentiment_service
    service = get_sentiment_service()
    if not service:
        return []
    
    return await service.get_trending(limit)


@router.get("/sentiment/posts")
async def get_sentiment_posts(coin: Optional[str] = None, limit: int = 50):
    """Get recent sentiment posts"""
    from services.sentiment_analysis import get_sentiment_service
    service = get_sentiment_service()
    if not service:
        return []
    
    return await service.get_recent_posts(coin, limit)


# ============================================================================
# Backtest Simulator Routes (P1)
# ============================================================================

class BacktestRequest(BaseModel):
    strategy: str
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float = 10000
    params: Optional[Dict[str, Any]] = None


@router.get("/backtest/strategies")
async def get_backtest_strategies():
    """Get available backtest strategies"""
    from services.backtest_service import get_backtest_service
    service = get_backtest_service()
    if not service:
        return {}
    
    return await service.get_strategies()


@router.post("/backtest/run")
async def run_backtest(request: BacktestRequest):
    """Run a backtest simulation"""
    from services.backtest_service import get_backtest_service
    service = get_backtest_service()
    if not service:
        raise HTTPException(500, "Backtest service not available")
    
    return await service.run_backtest(
        strategy=request.strategy,
        symbol=request.symbol,
        start_date=request.start_date,
        end_date=request.end_date,
        initial_capital=request.initial_capital,
        params=request.params
    )


@router.get("/backtest/results")
async def get_backtest_results(limit: int = 20):
    """Get recent backtest results"""
    from services.backtest_service import get_backtest_service
    service = get_backtest_service()
    if not service:
        return []
    
    return await service.get_results(limit)


@router.get("/backtest/results/{result_id}")
async def get_backtest_result(result_id: str):
    """Get a specific backtest result"""
    from services.backtest_service import get_backtest_service
    service = get_backtest_service()
    if not service:
        raise HTTPException(500, "Backtest service not available")
    
    result = await service.get_result(result_id)
    if not result:
        raise HTTPException(404, "Result not found")
    
    return result


# ============================================================================
# AI Model A/B Testing Routes (P1)
# ============================================================================

class ABTestRequest(BaseModel):
    name: str
    model_a: str
    model_b: str
    symbol: str = 'BTC'


@router.get("/ab-testing/status")
async def get_ab_testing_status():
    """Get A/B testing service status"""
    from services.ab_testing_service import get_ab_testing_service
    service = get_ab_testing_service()
    if not service:
        return {"is_monitoring": False, "message": "Service not initialized"}
    
    return await service.get_status()


@router.get("/ab-testing/models")
async def get_available_models():
    """Get available models for testing"""
    from services.ab_testing_service import get_ab_testing_service
    service = get_ab_testing_service()
    if not service:
        return []
    
    return await service.get_models()


@router.post("/ab-testing/create")
async def create_ab_test(request: ABTestRequest):
    """Create a new A/B test"""
    from services.ab_testing_service import get_ab_testing_service
    service = get_ab_testing_service()
    if not service:
        raise HTTPException(500, "A/B testing service not available")
    
    return await service.create_test(
        name=request.name,
        model_a=request.model_a,
        model_b=request.model_b,
        symbol=request.symbol
    )


@router.post("/ab-testing/start")
async def start_ab_testing():
    """Start A/B test monitoring"""
    from services.ab_testing_service import get_ab_testing_service
    service = get_ab_testing_service()
    if not service:
        raise HTTPException(500, "A/B testing service not available")
    
    return await service.start_monitoring()


@router.post("/ab-testing/stop")
async def stop_ab_testing():
    """Stop A/B test monitoring"""
    from services.ab_testing_service import get_ab_testing_service
    service = get_ab_testing_service()
    if not service:
        raise HTTPException(500, "A/B testing service not available")
    
    return await service.stop_monitoring()


@router.get("/ab-testing/tests")
async def get_active_tests():
    """Get all active A/B tests"""
    from services.ab_testing_service import get_ab_testing_service
    service = get_ab_testing_service()
    if not service:
        return []
    
    return await service.get_active_tests()


@router.get("/ab-testing/tests/{test_id}")
async def get_test_details(test_id: str):
    """Get details for a specific test"""
    from services.ab_testing_service import get_ab_testing_service
    service = get_ab_testing_service()
    if not service:
        raise HTTPException(500, "A/B testing service not available")
    
    return await service.get_test(test_id)


@router.get("/ab-testing/tests/{test_id}/results")
async def get_test_results(test_id: str):
    """Get results for a specific test"""
    from services.ab_testing_service import get_ab_testing_service
    service = get_ab_testing_service()
    if not service:
        raise HTTPException(500, "A/B testing service not available")
    
    return await service.get_test_results(test_id)


@router.post("/ab-testing/tests/{test_id}/stop")
async def stop_test(test_id: str):
    """Stop a specific test"""
    from services.ab_testing_service import get_ab_testing_service
    service = get_ab_testing_service()
    if not service:
        raise HTTPException(500, "A/B testing service not available")
    
    return await service.end_test(test_id)


@router.get("/ab-testing/leaderboard")
async def get_model_leaderboard():
    """Get model performance leaderboard"""
    from services.ab_testing_service import get_ab_testing_service
    service = get_ab_testing_service()
    if not service:
        return []
    
    return await service.get_model_leaderboard()


# ============================================================================
# Combined Status Endpoint
# ============================================================================

@router.get("/status")
async def get_all_upgrades_status():
    """Get status of all upgraded features"""
    from services.push_notifications import get_push_service
    from services.arbitrage_service import get_arbitrage_service
    from services.portfolio_rebalancer import get_rebalancer
    from services.trailing_stop_service import get_trailing_stop_service
    from services.whale_tracking import get_whale_service
    from services.sentiment_analysis import get_sentiment_service
    from services.backtest_service import get_backtest_service
    
    status = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": {}
    }
    
    # Push notifications
    push = get_push_service()
    status["features"]["push_notifications"] = await push.get_status() if push else {"active": False}
    
    # Arbitrage
    arb = get_arbitrage_service()
    status["features"]["arbitrage"] = await arb.get_status() if arb else {"is_monitoring": False}
    
    # Rebalancer
    reb = get_rebalancer()
    status["features"]["rebalancer"] = await reb.get_status() if reb else {"enabled": False}
    
    # Trailing stops
    trail = get_trailing_stop_service()
    status["features"]["trailing_stops"] = await trail.get_status() if trail else {"is_monitoring": False}
    
    # Whale tracking
    whale = get_whale_service()
    status["features"]["whale_tracking"] = await whale.get_status() if whale else {"is_monitoring": False}
    
    # Sentiment Analysis (P1)
    sentiment = get_sentiment_service()
    status["features"]["sentiment"] = await sentiment.get_status() if sentiment else {"is_monitoring": False}
    
    # Backtest Simulator (P1)
    backtest = get_backtest_service()
    status["features"]["backtest"] = {"available": backtest is not None, "strategies": len(backtest.STRATEGIES) if backtest else 0}
    
    return status

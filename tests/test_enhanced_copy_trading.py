"""
Tests for Enhanced Copy Trading Features
Tests real-time sync, risk management, analytics, and profit sharing
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient

# Import services to test
from backend.services.enhanced_copy_trading import EnhancedCopyTradingService


# Test configuration
TEST_DB_URL = "mongodb://localhost:27017"
TEST_DB_NAME = "test_copy_trading_db"


@pytest.fixture
async def test_db():
    """Create a test database connection"""
    client = AsyncIOMotorClient(TEST_DB_URL)
    db = client[TEST_DB_NAME]
    
    yield db
    
    # Cleanup
    await client.drop_database(TEST_DB_NAME)
    client.close()


@pytest.fixture
async def copy_service(test_db):
    """Create an enhanced copy trading service instance"""
    return EnhancedCopyTradingService(test_db)


# === Trade Broadcasting Tests ===

@pytest.mark.asyncio
async def test_broadcast_trade_signal(copy_service, test_db):
    """Test broadcasting a trade signal to copiers"""
    # Setup: Create a trader and copiers
    trader_id = "test_trader_1"
    copier_id = "test_copier_1"
    
    # Create copy relationship
    await test_db.copy_relationships.insert_one({
        "user_id": copier_id,
        "trader_id": trader_id,
        "active": True,
        "enabled": True,
        "copy_percentage": 100,
        "max_trade_size": 1000,
        "max_position_pct": 10.0
    })
    
    # Broadcast a trade signal
    trade = {
        "symbol": "BTC/USD",
        "action": "buy",
        "price": 97000,
        "amount": 100,
        "stop_loss": 95000,
        "take_profit": 100000
    }
    
    result = await copy_service.broadcast_trade_signal(
        trader_id=trader_id,
        trade=trade,
        signal_type="entry"
    )
    
    # Verify signal was created
    assert "signal_id" in result
    assert result["copiers_notified"] == 1
    assert result["executed_successfully"] >= 0
    
    # Verify signal was stored in database
    signal = await test_db.trade_signals.find_one({"signal_id": result["signal_id"]})
    assert signal is not None
    assert signal["trader_id"] == trader_id


@pytest.mark.asyncio
async def test_copy_trade_execution(copy_service, test_db):
    """Test execution of a copy trade with intelligent scaling"""
    copier = {
        "user_id": "test_copier_1",
        "trader_id": "test_trader_1",
        "copy_percentage": 50,  # Copy 50% of trade size
        "max_trade_size": 500,
        "max_position_pct": 5.0,
        "enabled": True
    }
    
    original_trade = {
        "symbol": "ETH/USD",
        "action": "buy",
        "price": 2700,
        "amount": 1000  # Original trade
    }
    
    signal_id = "test_signal_123"
    signal_time = datetime.now(timezone.utc)
    
    result = await copy_service._execute_copy_trade(
        copier=copier,
        original_trade=original_trade,
        signal_id=signal_id,
        signal_type="entry",
        signal_time=signal_time
    )
    
    # Verify trade was copied with scaling
    assert result["success"] == True
    assert result["copier_id"] == "test_copier_1"
    assert "trade_id" in result
    # Amount should be scaled: 1000 * 50% = 500 (within max_trade_size)
    assert result["amount"] <= 500


# === Risk Management Tests ===

@pytest.mark.asyncio
async def test_drawdown_protection(copy_service, test_db):
    """Test that drawdown protection blocks trades when exceeded"""
    copier_id = "test_copier_drawdown"
    
    # Simulate equity curve with significant drawdown
    peak_equity = 10000
    current_equity = 7500  # 25% drawdown
    
    await test_db.copier_equity.insert_many([
        {
            "copier_id": copier_id,
            "equity": peak_equity,
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        },
        {
            "copier_id": copier_id,
            "equity": current_equity,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    ])
    
    copier = {
        "user_id": copier_id,
        "trader_id": "test_trader",
        "max_drawdown_pct": 20.0,  # Max 20% drawdown allowed
        "active": True,
        "enabled": True
    }
    
    # Should fail risk check due to exceeded drawdown
    passed = await copy_service._check_copier_risk_limits(copier)
    
    assert passed == False
    
    # Verify copy relationship was disabled
    updated = await test_db.copy_relationships.find_one(
        {"user_id": copier_id, "trader_id": "test_trader"}
    )
    assert updated is not None
    assert updated["enabled"] == False
    assert updated["disabled_reason"] == "max_drawdown_exceeded"


@pytest.mark.asyncio
async def test_daily_trade_limit(copy_service, test_db):
    """Test daily trade limit protection"""
    copier_id = "test_copier_limits"
    
    # Insert trades for today (exceeding limit)
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    
    for i in range(25):  # 25 trades today
        await test_db.copied_trades.insert_one({
            "copier_id": copier_id,
            "executed_at": (today + timedelta(hours=i % 12)).isoformat()
        })
    
    copier = {
        "user_id": copier_id,
        "trader_id": "test_trader",
        "max_daily_trades": 20,  # Max 20 trades per day
        "active": True,
        "enabled": True
    }
    
    # Should fail risk check due to daily limit
    passed = await copy_service._check_copier_risk_limits(copier)
    
    assert passed == False


# === Performance Analytics Tests ===

@pytest.mark.asyncio
async def test_calculate_performance_metrics(copy_service, test_db):
    """Test comprehensive performance metrics calculation"""
    trader_id = "test_trader_analytics"
    
    # Insert sample trades
    start_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    trades = [
        # Winning trades
        {"trader_id": trader_id, "profit": 100, "return_pct": 10, "status": "closed",
         "executed_at": (start_date + timedelta(days=1)).isoformat(),
         "entry_time": (start_date + timedelta(days=1)).isoformat(),
         "exit_time": (start_date + timedelta(days=1, hours=2)).isoformat()},
        {"trader_id": trader_id, "profit": 150, "return_pct": 15, "status": "closed",
         "executed_at": (start_date + timedelta(days=2)).isoformat(),
         "entry_time": (start_date + timedelta(days=2)).isoformat(),
         "exit_time": (start_date + timedelta(days=2, hours=3)).isoformat()},
        {"trader_id": trader_id, "profit": 200, "return_pct": 20, "status": "closed",
         "executed_at": (start_date + timedelta(days=3)).isoformat(),
         "entry_time": (start_date + timedelta(days=3)).isoformat(),
         "exit_time": (start_date + timedelta(days=3, hours=1)).isoformat()},
        # Losing trades
        {"trader_id": trader_id, "profit": -50, "return_pct": -5, "status": "closed",
         "executed_at": (start_date + timedelta(days=4)).isoformat(),
         "entry_time": (start_date + timedelta(days=4)).isoformat(),
         "exit_time": (start_date + timedelta(days=4, hours=4)).isoformat()},
        {"trader_id": trader_id, "profit": -75, "return_pct": -7.5, "status": "closed",
         "executed_at": (start_date + timedelta(days=5)).isoformat(),
         "entry_time": (start_date + timedelta(days=5)).isoformat(),
         "exit_time": (start_date + timedelta(days=5, hours=2)).isoformat()},
    ]
    
    await test_db.copy_trade_history.insert_many(trades)
    
    # Calculate metrics
    metrics = await copy_service.calculate_trader_performance_metrics(
        trader_id=trader_id,
        timeframe_days=30
    )
    
    # Verify metrics
    assert metrics["trader_id"] == trader_id
    assert metrics["total_trades"] == 5
    assert metrics["winning_trades"] == 3
    assert metrics["losing_trades"] == 2
    assert metrics["win_rate"] == 60.0  # 3/5 = 60%
    assert metrics["total_profit"] == 325  # 100+150+200-50-75
    assert metrics["avg_win"] > 0
    assert metrics["avg_loss"] < 0
    assert metrics["profit_factor"] > 1  # Profitable trader
    assert "sharpe_ratio" in metrics
    assert "sortino_ratio" in metrics


@pytest.mark.asyncio
async def test_equity_curve_tracking(copy_service, test_db):
    """Test equity curve tracking for drawdown analysis"""
    copier_id = "test_copier_equity"
    
    # Get initial equity curve (should be empty)
    curve = await copy_service.get_copier_equity_curve(copier_id, days=30)
    assert len(curve) == 0
    
    # Simulate trades and update equity
    trade = {
        "trade_id": "test_trade_1",
        "copier_id": copier_id,
        "profit": 100
    }
    
    await copy_service._update_equity_curve(copier_id, trade)
    
    # Verify equity curve was updated
    curve = await copy_service.get_copier_equity_curve(copier_id, days=30)
    assert len(curve) > 0
    assert curve[0]["copier_id"] == copier_id


# === Profit Sharing Tests ===

@pytest.mark.asyncio
async def test_calculate_profit_share(copy_service, test_db):
    """Test profit share calculation"""
    trader_id = "test_trader_profit"
    copier_id = "test_copier_profit"
    
    # Create copy relationship with 10% profit share
    await test_db.copy_relationships.insert_one({
        "user_id": copier_id,
        "trader_id": trader_id,
        "profit_share_pct": 15.0  # 15% profit share
    })
    
    # Insert profitable trades
    period_start = datetime.now(timezone.utc) - timedelta(days=7)
    
    trades = [
        {"copier_id": copier_id, "trader_id": trader_id, "profit": 100, "status": "closed",
         "executed_at": (period_start + timedelta(days=1)).isoformat()},
        {"copier_id": copier_id, "trader_id": trader_id, "profit": 200, "status": "closed",
         "executed_at": (period_start + timedelta(days=2)).isoformat()},
        {"copier_id": copier_id, "trader_id": trader_id, "profit": -50, "status": "closed",
         "executed_at": (period_start + timedelta(days=3)).isoformat()},  # Loss - not counted
    ]
    
    await test_db.copied_trades.insert_many(trades)
    
    # Calculate profit share
    share = await copy_service.calculate_profit_share(
        trader_id=trader_id,
        copier_id=copier_id,
        period_start=period_start
    )
    
    # Verify calculation
    assert share["trader_id"] == trader_id
    assert share["copier_id"] == copier_id
    assert share["total_copier_profit"] == 300  # 100 + 200 (loss not counted)
    assert share["profit_share_pct"] == 15.0
    assert share["profit_share_amount"] == 45.0  # 300 * 15%
    assert share["trades_count"] == 2  # Only profitable trades
    assert share["status"] == "pending"


@pytest.mark.asyncio
async def test_profit_distribution(copy_service, test_db):
    """Test profit share distribution processing"""
    share_id = "test_share_123"
    trader_id = "test_trader_dist"
    
    # Create pending profit share
    await test_db.profit_shares.insert_one({
        "share_id": share_id,
        "trader_id": trader_id,
        "copier_id": "test_copier",
        "profit_share_amount": 50.0,
        "status": "pending"
    })
    
    # Create trader profile
    await test_db.trader_profiles.insert_one({
        "trader_id": trader_id,
        "total_earnings": 0
    })
    
    # Process distribution
    result = await copy_service.process_profit_distribution(share_id)
    
    # Verify distribution
    assert result["status"] == "success"
    assert result["amount_distributed"] == 50.0
    
    # Verify share status updated
    share = await test_db.profit_shares.find_one({"share_id": share_id})
    assert share["status"] == "distributed"
    assert "distributed_at" in share
    
    # Verify trader earnings updated
    trader = await test_db.trader_profiles.find_one({"trader_id": trader_id})
    assert trader["total_earnings"] == 50.0


# === Trader Verification Tests ===

@pytest.mark.asyncio
async def test_trader_verification_legitimate(copy_service, test_db):
    """Test verification of a legitimate trader"""
    trader_id = "test_trader_legit"
    
    # Insert realistic trade history
    trades = []
    for i in range(50):
        profit = 100 if i % 3 != 0 else -50  # ~67% win rate
        trades.append({
            "trader_id": trader_id,
            "profit": profit,
            "executed_at": (datetime.now(timezone.utc) - timedelta(hours=i)).isoformat()
        })
    
    await test_db.copy_trade_history.insert_many(trades)
    
    # Verify trader
    verification = await copy_service.verify_trader_performance(trader_id)
    
    # Should pass verification
    assert verification["verified"] == True
    assert verification["confidence_score"] >= 50
    assert len(verification["issues"]) == 0 or "Low trade count" not in verification["issues"]


@pytest.mark.asyncio
async def test_trader_verification_suspicious(copy_service, test_db):
    """Test verification detects suspicious patterns"""
    trader_id = "test_trader_suspicious"
    
    # Insert suspiciously good trades (98% win rate)
    trades = []
    for i in range(100):
        profit = 100 if i < 98 else -50  # 98% win rate - suspicious
        trades.append({
            "trader_id": trader_id,
            "profit": profit,
            "executed_at": (datetime.now(timezone.utc) - timedelta(hours=i)).isoformat()
        })
    
    await test_db.copy_trade_history.insert_many(trades)
    
    # Verify trader
    verification = await copy_service.verify_trader_performance(trader_id)
    
    # Should fail verification
    assert verification["verified"] == False
    assert "Suspiciously high win rate" in str(verification["issues"])
    assert verification["confidence_score"] < 100


# === Performance Comparison Tests ===

@pytest.mark.asyncio
async def test_performance_comparison(copy_service, test_db):
    """Test comparing copier's performance across multiple traders"""
    copier_id = "test_copier_compare"
    trader1_id = "trader_1"
    trader2_id = "trader_2"
    
    # Create copy relationships
    await test_db.copy_relationships.insert_many([
        {"user_id": copier_id, "trader_id": trader1_id, "active": True},
        {"user_id": copier_id, "trader_id": trader2_id, "active": True}
    ])
    
    # Insert trades for both traders
    trades = [
        # Trader 1 - profitable
        {"copier_id": copier_id, "trader_id": trader1_id, "profit": 100, "status": "closed"},
        {"copier_id": copier_id, "trader_id": trader1_id, "profit": 150, "status": "closed"},
        # Trader 2 - less profitable
        {"copier_id": copier_id, "trader_id": trader2_id, "profit": 50, "status": "closed"},
        {"copier_id": copier_id, "trader_id": trader2_id, "profit": -25, "status": "closed"},
    ]
    
    await test_db.copied_trades.insert_many(trades)
    
    # Get comparison
    comparison = await copy_service.get_copy_performance_comparison(copier_id)
    
    # Verify comparison
    assert comparison["copier_id"] == copier_id
    assert comparison["traders_followed"] == 2
    assert len(comparison["performance_by_trader"]) == 2
    
    # First trader should be more profitable
    assert comparison["performance_by_trader"][0]["total_profit"] == 250
    assert comparison["performance_by_trader"][1]["total_profit"] == 25


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

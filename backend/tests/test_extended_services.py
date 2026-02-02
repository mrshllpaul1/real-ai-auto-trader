"""
Extended Pytest tests for critical backend services.
Tests: Growth Engine, Automated Trader, AI Weekly Trainer, AI Portfolio Manager
Run with: pytest /app/backend/tests/ -v
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


# ============ Growth Engine Tests ============

class TestGrowthEngineExtended:
    """Extended tests for AggressiveGrowthEngine"""
    
    @pytest.fixture
    def mock_deps(self):
        """Create comprehensive mock dependencies"""
        db = MagicMock()
        db.growth_positions = MagicMock()
        db.growth_executions = MagicMock()
        db.growth_history = MagicMock()
        db.growth_positions.find = MagicMock(return_value=MagicMock(
            to_list=AsyncMock(return_value=[])
        ))
        db.growth_positions.find_one = AsyncMock(return_value=None)
        db.growth_positions.insert_one = AsyncMock()
        db.growth_positions.update_one = AsyncMock()
        db.growth_executions.insert_one = AsyncMock()
        db.growth_history.insert_one = AsyncMock()
        
        kraken = MagicMock()
        kraken.get_balance = AsyncMock(return_value={"ZUSD": "500", "XXBT": "0.01"})
        kraken.get_ticker = AsyncMock(return_value={"c": ["75000"]})
        kraken.place_order = AsyncMock(return_value={"txid": ["TEST123"]})
        
        gem_finder = MagicMock()
        gem_finder.find_gems = AsyncMock(return_value=[
            {"coin_id": "solana", "gem_score": 85, "is_gem": True}
        ])
        
        ai_trainer = MagicMock()
        ai_trainer.select_portfolio = AsyncMock(return_value={
            "main_coins": [
                {"coin_id": "bitcoin", "allocation": 40, "ai_score": 78},
                {"coin_id": "ethereum", "allocation": 30, "ai_score": 75}
            ]
        })
        
        budget_manager = MagicMock()
        budget_manager.can_trade_real = AsyncMock(return_value={"allowed": True, "available": 500})
        budget_manager.allocate_funds = AsyncMock(return_value={"success": True, "remaining_budget": 400})
        budget_manager.release_funds = AsyncMock(return_value={"success": True})
        
        return db, kraken, gem_finder, ai_trainer, budget_manager
    
    @pytest.mark.asyncio
    async def test_calculate_position_size(self, mock_deps):
        """Test position size calculation with risk management"""
        from services.growth_engine import AggressiveGrowthEngine
        
        db, kraken, gem_finder, ai_trainer, budget_manager = mock_deps
        
        engine = AggressiveGrowthEngine(db, kraken, gem_finder, ai_trainer)
        
        # Test gem position (larger allocation)
        gem_size = engine._calculate_position_size(1000, is_gem=True)
        assert gem_size <= 250  # Max 25% for gems
        
        # Test main coin position
        main_size = engine._calculate_position_size(1000, is_gem=False)
        assert main_size <= 150  # Max 15% for main coins
    
    @pytest.mark.asyncio
    async def test_gem_allocation_priority(self, mock_deps):
        """Test that hidden gems get priority allocation"""
        from services.growth_engine import AggressiveGrowthEngine
        
        db, kraken, gem_finder, ai_trainer, budget_manager = mock_deps
        
        engine = AggressiveGrowthEngine(db, kraken, gem_finder, ai_trainer)
        result = await engine.execute_growth_strategy(capital=500, paper_trade=True)
        
        assert result["success"] == True
        # Verify gem finder was called
        gem_finder.find_gems.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_loss_monitoring(self, mock_deps):
        """Test stop-loss position monitoring"""
        from services.growth_engine import AggressiveGrowthEngine
        
        db, kraken, gem_finder, ai_trainer, budget_manager = mock_deps
        
        # Add a position that's below stop-loss
        db.growth_positions.find = MagicMock(return_value=MagicMock(
            to_list=AsyncMock(return_value=[{
                "coin_id": "bitcoin",
                "entry_price": 80000,
                "amount": 0.01,
                "stop_loss": 72000,  # -10%
                "take_profit": 100000,
                "status": "open"
            }])
        ))
        
        # Mock current price below stop loss
        kraken.get_ticker = AsyncMock(return_value={"c": ["70000"]})  # Below stop loss
        
        engine = AggressiveGrowthEngine(db, kraken, gem_finder, ai_trainer)
        result = await engine.monitor_positions()
        
        assert "checked" in result
    
    @pytest.mark.asyncio
    async def test_compound_profits_calculation(self, mock_deps):
        """Test profit compounding logic"""
        from services.growth_engine import AggressiveGrowthEngine
        
        db, kraken, gem_finder, ai_trainer, budget_manager = mock_deps
        
        # Mock profitable closed positions
        db.growth_positions.find = MagicMock(return_value=MagicMock(
            to_list=AsyncMock(return_value=[{
                "coin_id": "bitcoin",
                "entry_price": 70000,
                "exit_price": 80000,
                "amount": 0.01,
                "pnl": 100,
                "status": "closed",
                "compounded": False
            }])
        ))
        
        engine = AggressiveGrowthEngine(db, kraken, gem_finder, ai_trainer)
        result = await engine.compound_profits()
        
        assert "compounded" in result


# ============ Automated Trader Tests ============

class TestAutomatedTrader:
    """Tests for AutomatedWeeklyTrader"""
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies for automated trader"""
        db = MagicMock()
        db.weekly_strategies = MagicMock()
        db.weekly_executions = MagicMock()
        db.ai_trades = MagicMock()
        db.weekly_strategies.find_one = AsyncMock(return_value=None)
        db.weekly_strategies.insert_one = AsyncMock()
        db.weekly_executions.insert_one = AsyncMock()
        db.ai_trades.insert_one = AsyncMock()
        
        strategy_engine = MagicMock()
        strategy_engine.generate_strategies = AsyncMock(return_value={
            "strategies": [
                {"coin_id": "bitcoin", "action": "BUY", "confidence_score": 80},
                {"coin_id": "ethereum", "action": "BUY", "confidence_score": 75}
            ]
        })
        
        kraken_service = MagicMock()
        kraken_service.get_balance = AsyncMock(return_value={"ZUSD": "1000"})
        kraken_service.place_order = AsyncMock(return_value={"txid": ["ORDER123"]})
        
        learning_engine = MagicMock()
        learning_engine.record_strategy_outcome = AsyncMock(return_value={"recorded": True})
        
        return db, strategy_engine, kraken_service, learning_engine
    
    @pytest.mark.asyncio
    async def test_generate_weekly_strategies(self, mock_deps):
        """Test weekly strategy generation"""
        from services.automated_trader import AutomatedWeeklyTrader
        
        db, strategy_engine, kraken_service, learning_engine = mock_deps
        
        trader = AutomatedWeeklyTrader(
            db=db,
            strategy_engine=strategy_engine,
            kraken_service=kraken_service,
            learning_engine=learning_engine
        )
        
        result = await trader.generate_weekly_strategy()
        
        assert "strategies" in result
        strategy_engine.generate_strategies.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_paper_trades(self, mock_deps):
        """Test paper trade execution"""
        from services.automated_trader import AutomatedWeeklyTrader
        
        db, strategy_engine, kraken_service, learning_engine = mock_deps
        
        trader = AutomatedWeeklyTrader(
            db=db,
            strategy_engine=strategy_engine,
            kraken_service=kraken_service,
            learning_engine=learning_engine
        )
        
        result = await trader.execute_weekly_trades(paper_trade=True)
        
        assert result["success"] == True
        assert result["mode"] == "paper"
        # Kraken should NOT be called for paper trades
        kraken_service.place_order.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_real_trades_with_budget(self, mock_deps):
        """Test real trade execution respects budget"""
        from services.automated_trader import AutomatedWeeklyTrader
        
        db, strategy_engine, kraken_service, learning_engine = mock_deps
        
        budget_manager = MagicMock()
        budget_manager.can_trade_real = AsyncMock(return_value={"allowed": True, "available": 500})
        budget_manager.allocate_funds = AsyncMock(return_value={"success": True})
        
        trader = AutomatedWeeklyTrader(
            db=db,
            strategy_engine=strategy_engine,
            kraken_service=kraken_service,
            learning_engine=learning_engine,
            budget_manager=budget_manager
        )
        
        result = await trader.execute_weekly_trades(paper_trade=False)
        
        # Should check budget before trading
        budget_manager.can_trade_real.assert_called()
    
    @pytest.mark.asyncio
    async def test_strategy_confidence_threshold(self, mock_deps):
        """Test that low confidence strategies are skipped"""
        from services.automated_trader import AutomatedWeeklyTrader
        
        db, strategy_engine, kraken_service, learning_engine = mock_deps
        
        # Return low confidence strategies
        strategy_engine.generate_strategies = AsyncMock(return_value={
            "strategies": [
                {"coin_id": "bitcoin", "action": "BUY", "confidence_score": 30},  # Too low
            ]
        })
        
        trader = AutomatedWeeklyTrader(
            db=db,
            strategy_engine=strategy_engine,
            kraken_service=kraken_service,
            learning_engine=learning_engine,
            min_confidence=60  # Threshold
        )
        
        result = await trader.execute_weekly_trades(paper_trade=True)
        
        # Low confidence trade should be filtered
        assert result["success"] == True


# ============ AI Weekly Trainer Tests ============

class TestAIWeeklyTrainer:
    """Tests for AIWeeklyTrainer"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database"""
        db = MagicMock()
        db.historical_prices = MagicMock()
        db.ai_training_runs = MagicMock()
        db.weekly_training_results = MagicMock()
        db.ai_preferences = MagicMock()
        db.historical_prices.find = MagicMock(return_value=MagicMock(
            sort=MagicMock(return_value=MagicMock(
                to_list=AsyncMock(return_value=[
                    {"coin_id": "bitcoin", "close": 75000, "timestamp": "2025-01-01"},
                    {"coin_id": "bitcoin", "close": 76000, "timestamp": "2025-01-02"}
                ])
            ))
        ))
        db.ai_training_runs.insert_one = AsyncMock()
        db.weekly_training_results.insert_one = AsyncMock()
        db.ai_preferences.find_one = AsyncMock(return_value=None)
        db.ai_preferences.update_one = AsyncMock()
        return db
    
    @pytest.mark.asyncio
    async def test_fetch_real_historical_data(self, mock_db):
        """Test fetching real historical data for training"""
        from services.ai_weekly_trainer import AIWeeklyTrainer
        
        trainer = AIWeeklyTrainer(mock_db)
        
        # Fetch week data
        data = await trainer._fetch_week_data(
            coin_id="bitcoin",
            week_start=datetime(2025, 1, 1),
            week_end=datetime(2025, 1, 7)
        )
        
        # Should query real data from database
        mock_db.historical_prices.find.assert_called()
    
    @pytest.mark.asyncio
    async def test_calculate_weekly_performance(self, mock_db):
        """Test weekly performance calculation"""
        from services.ai_weekly_trainer import AIWeeklyTrainer
        
        trainer = AIWeeklyTrainer(mock_db)
        
        # Mock week data
        week_data = [
            {"close": 70000, "volume": 1000000},
            {"close": 75000, "volume": 1200000},
            {"close": 73000, "volume": 900000}
        ]
        
        perf = trainer._calculate_performance(week_data)
        
        assert "return_pct" in perf
        assert "volatility" in perf
        assert "volume_trend" in perf
    
    @pytest.mark.asyncio
    async def test_update_ai_preferences(self, mock_db):
        """Test AI preference learning and update"""
        from services.ai_weekly_trainer import AIWeeklyTrainer
        
        trainer = AIWeeklyTrainer(mock_db)
        
        # Simulate successful trade outcome
        outcome = {
            "coin_id": "solana",
            "entry_price": 100,
            "exit_price": 150,
            "pnl_pct": 50,
            "indicators_at_entry": {
                "rsi": 35,
                "macd": "bullish",
                "volume_surge": True
            }
        }
        
        await trainer._update_preferences_from_outcome(outcome)
        
        # Should update preferences in DB
        mock_db.ai_preferences.update_one.assert_called()
    
    @pytest.mark.asyncio
    async def test_select_best_coins(self, mock_db):
        """Test AI coin selection based on learned preferences"""
        from services.ai_weekly_trainer import AIWeeklyTrainer
        
        # Mock preferences
        mock_db.ai_preferences.find_one = AsyncMock(return_value={
            "preferred_rsi_range": [30, 40],
            "preferred_volume_surge": True,
            "success_by_coin": {
                "solana": {"wins": 8, "losses": 2},
                "cardano": {"wins": 3, "losses": 7}
            }
        })
        
        trainer = AIWeeklyTrainer(mock_db)
        
        available_coins = [
            {"coin_id": "solana", "rsi": 35, "volume_surge": True},
            {"coin_id": "cardano", "rsi": 65, "volume_surge": False}
        ]
        
        selected = await trainer.select_coins_with_preferences(available_coins)
        
        # Solana should be preferred (better historical success)
        assert any(c["coin_id"] == "solana" for c in selected)


# ============ AI Portfolio Manager Tests ============

class TestAIPortfolioManager:
    """Tests for AIPortfolioManager"""
    
    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies"""
        db = MagicMock()
        db.ai_portfolios = MagicMock()
        db.ai_trades = MagicMock()
        db.strategies = MagicMock()
        db.ai_portfolios.find_one = AsyncMock(return_value={
            "user_id": "default",
            "type": "ai_managed",
            "initial_capital": 500,
            "current_capital": 600,
            "holdings": {"USD": 300, "BTC": 0.003, "ETH": 0.05},
            "target_allocation": {"USD": 20, "BTC": 40, "ETH": 30, "SOL": 10}
        })
        db.ai_portfolios.update_one = AsyncMock()
        db.ai_portfolios.replace_one = AsyncMock()
        db.ai_trades.insert_one = AsyncMock()
        db.strategies.find = MagicMock(return_value=MagicMock(
            sort=MagicMock(return_value=MagicMock(
                limit=MagicMock(return_value=MagicMock(
                    to_list=AsyncMock(return_value=[])
                ))
            ))
        ))
        
        kraken = MagicMock()
        kraken.place_order = AsyncMock(return_value={"txid": ["ORDER456"]})
        
        market_service = MagicMock()
        market_service.get_coin_price = AsyncMock(return_value={
            "bitcoin": {"price_usd": 75000, "price_change_24h": 2.5},
            "ethereum": {"price_usd": 2500, "price_change_24h": -1.2},
            "solana": {"price_usd": 150, "price_change_24h": 5.0}
        })
        
        news_service = MagicMock()
        news_service.get_aggregated_news = AsyncMock(return_value=[
            {"sentiment": "positive"},
            {"sentiment": "positive"},
            {"sentiment": "neutral"}
        ])
        
        return db, kraken, market_service, news_service
    
    @pytest.mark.asyncio
    async def test_initialize_portfolio(self, mock_deps):
        """Test AI portfolio initialization"""
        from services.ai_portfolio_manager import AIPortfolioManager
        
        db, kraken, market_service, news_service = mock_deps
        db.ai_portfolios.find_one = AsyncMock(return_value=None)
        
        manager = AIPortfolioManager(
            db=db, 
            kraken_service=kraken,
            market_service=market_service,
            news_service=news_service
        )
        
        portfolio = await manager.initialize_ai_portfolio("test_user", 500)
        
        assert portfolio["initial_capital"] == 500
        assert portfolio["type"] == "ai_managed"
        db.ai_portfolios.replace_one.assert_called()
    
    @pytest.mark.asyncio
    async def test_develop_bullish_strategy(self, mock_deps):
        """Test strategy development in bullish market"""
        from services.ai_portfolio_manager import AIPortfolioManager
        
        db, kraken, market_service, news_service = mock_deps
        
        # All coins bullish
        market_service.get_coin_price = AsyncMock(return_value={
            "bitcoin": {"price_usd": 75000, "price_change_24h": 5.0},
            "ethereum": {"price_usd": 2500, "price_change_24h": 3.0},
            "solana": {"price_usd": 150, "price_change_24h": 8.0}
        })
        
        manager = AIPortfolioManager(
            db=db,
            kraken_service=kraken,
            market_service=market_service,
            news_service=news_service
        )
        
        result = await manager.develop_portfolio_strategy("test_user")
        
        # In bullish market, should have low cash allocation
        assert result["target_allocation"]["USD"] <= 15
    
    @pytest.mark.asyncio
    async def test_develop_bearish_strategy(self, mock_deps):
        """Test strategy development in bearish market"""
        from services.ai_portfolio_manager import AIPortfolioManager
        
        db, kraken, market_service, news_service = mock_deps
        
        # All coins bearish
        market_service.get_coin_price = AsyncMock(return_value={
            "bitcoin": {"price_usd": 75000, "price_change_24h": -5.0},
            "ethereum": {"price_usd": 2500, "price_change_24h": -3.0},
            "solana": {"price_usd": 150, "price_change_24h": -8.0}
        })
        
        # Negative news sentiment
        news_service.get_aggregated_news = AsyncMock(return_value=[
            {"sentiment": "negative"},
            {"sentiment": "negative"},
            {"sentiment": "neutral"}
        ])
        
        manager = AIPortfolioManager(
            db=db,
            kraken_service=kraken,
            market_service=market_service,
            news_service=news_service
        )
        
        result = await manager.develop_portfolio_strategy("test_user")
        
        # In bearish market, should have high cash allocation
        assert result["target_allocation"]["USD"] >= 40
    
    @pytest.mark.asyncio
    async def test_execute_rebalance(self, mock_deps):
        """Test portfolio rebalancing execution"""
        from services.ai_portfolio_manager import AIPortfolioManager
        
        db, kraken, market_service, news_service = mock_deps
        
        manager = AIPortfolioManager(
            db=db,
            kraken_service=kraken,
            market_service=market_service,
            news_service=news_service
        )
        
        result = await manager.execute_rebalance("test_user")
        
        assert result["success"] == True
        assert "trades_executed" in result
    
    @pytest.mark.asyncio
    async def test_get_portfolio_status(self, mock_deps):
        """Test getting portfolio status"""
        from services.ai_portfolio_manager import AIPortfolioManager
        
        db, kraken, market_service, news_service = mock_deps
        
        manager = AIPortfolioManager(
            db=db,
            kraken_service=kraken,
            market_service=market_service,
            news_service=news_service
        )
        
        status = await manager.get_portfolio_status("default")
        
        assert status["initialized"] == True or "holdings" in status


# ============ Integration Tests ============

class TestAPIIntegration:
    """Integration tests for API endpoints"""
    
    @pytest.mark.asyncio
    async def test_ai_decisions_endpoint(self):
        """Test /api/ai-decisions/recent endpoint"""
        import httpx
        
        api_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{api_url}/api/ai-decisions/recent")
            
            assert response.status_code == 200
            data = response.json()
            assert "decisions" in data
            assert "gem_candidates" in data
    
    @pytest.mark.asyncio
    async def test_training_status_endpoint(self):
        """Test /api/training/status endpoint"""
        import httpx
        
        api_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{api_url}/api/training/status")
            
            assert response.status_code == 200
            data = response.json()
            assert "trained" in data
    
    @pytest.mark.asyncio
    async def test_hidden_gems_endpoint(self):
        """Test /api/training/hidden-gems endpoint"""
        import httpx
        
        api_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{api_url}/api/training/hidden-gems?min_multiplier=2")
            
            assert response.status_code == 200
            data = response.json()
            assert "hidden_gems" in data
            assert "count" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
